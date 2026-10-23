from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from docorder.core.job import Job
from docorder.core.runner import execute

JOB_ROOT = Path(__file__).resolve().parent
load_dotenv(JOB_ROOT / ".env")

DEFAULT_MODEL_HOME = "/Users/jixie/wbox/data-governance/semantic_layer/models/hive"
CURSOR_TOOL = {
    "name": "cursor",
    "run": [
        "cursor",
        "agent",
        "--print",
        "--force",
        "--approve-mcps",
        "--trust",
        "--sandbox",
        "disabled",
        "--workspace",
        "{workspace}",
    ],
    "prompt": "stdin",
}


def build_root_job(root: Path | None = None) -> Job:
    output_root = JOB_ROOT / "runs" if root is None else root
    model_home = os.environ.get("SEMANTIC_LAYER_MODELS", DEFAULT_MODEL_HOME)
    incoming = os.environ.get("SEMANTIC_LAYER_INPUT", str(JOB_ROOT / ".input"))
    job = Job("raw_root", output_root)

    # input 里的 db+table 对应 model_home/{db}/{table}.sql 和 .yml。
    # 正文是输入原文。fingerprint.record 记下这两份文件。tag 带上绝对路径。
    job.add_operator_node(
        "source",
        "source",
        config={"directory": incoming, "model_home": model_home},
    )

    # map：每个 model 一份 JSON，里面是 metric 列表。
    job.add_operator_node("librarian", "librarian", upstream="source")

    # reduce：一次 LLM 调用，根据全部 model JSON 产出 raw_root 正文。
    job.add_operator_node(
        "taxonomist_root",
        "taxonomist_root",
        upstream="librarian",
        config={
            "output": "raw_root",
            "workspace": str(JOB_ROOT),
            "tool": _llm_tool(),
        },
    )

    # apply：Output.rename 把该实体写成 .staging/raw_root.csv。
    job.add_operator_node("publish", "publish", upstream="taxonomist_root")
    return job

def build_root_refine_job(root: Path | None = None) -> Job:
    output_root = JOB_ROOT / "runs" if root is None else root
    model_home = os.environ.get("SEMANTIC_LAYER_MODELS", DEFAULT_MODEL_HOME)
    incoming = os.environ.get("SEMANTIC_LAYER_INPUT", str(JOB_ROOT / ".input"))
    llm = {"workspace": str(JOB_ROOT), "tool": _llm_tool()}

    job = Job("refine_root", output_root)

    # 与 raw_root 共用 source：fingerprint.record 记下 sql 与 yml，tag 带路径。
    job.add_operator_node(
        "source",
        "source",
        config={"directory": incoming, "model_home": model_home},
    )

    # map：每个 model 一次 LLM。提示词让模型按需改 .staging/raw_root_patch_log.csv。
    # record 记下 patch 文件，depend 记下 raw_root.csv。词根表变了就重跑。
    # 并行度为 1，避免多个 model 同时改同一份文件。上游 hash 不变且词根表 hash 不变的 model 不重跑。
    job.add_operator_node(
        "optimizer_root",
        "optimizer_root",
        upstream="source",
        parallelism=1,
        config=llm,
    )

    # reduce：一次 LLM，读 .staging/raw_root_patch_log.csv 和 .staging/raw_root.csv，写出 final_root 正文。
    # 两份文件都在 fingerprint.depend 里。任一 model 的 hash 变了，或这两份文件变了，就重跑。
    job.add_operator_node(
        "merge_root",
        "merge_root",
        upstream="optimizer_root",
        config=llm,
    )

    # apply：写成 .staging/final_root.csv，不覆盖 raw_root.csv。
    job.add_operator_node("publish_final", "publish_final", upstream="merge_root")
    return job

def build_root_assigner_job(root: Path | None = None) -> Job:
    output_root = JOB_ROOT / "runs" if root is None else root
    model_home = os.environ.get("SEMANTIC_LAYER_MODELS", DEFAULT_MODEL_HOME)
    incoming = os.environ.get("SEMANTIC_LAYER_INPUT", str(JOB_ROOT / ".input"))
    llm = {"workspace": str(JOB_ROOT), "tool": _llm_tool()}
    catalog = output_root / ".staging" / "final_root.csv"

    job = Job("root_assigner", output_root)

    # 单独的 source。fingerprint.record 记下 sql、yml 和 final_root.csv。
    # 词根表变了就重跑。节点名不用 source，避免写进另外两个 job 的 runs/source。
    # config 里的 fingerprint 整份覆盖 home，所以这里要带上 sql 和 yml。
    job.add_operator_node(
        "source_assign",
        "source",
        config={
            "directory": incoming,
            "model_home": model_home,
            "catalog": str(catalog),
            "fingerprint": {
                "record": {
                    "{model_home}/{db}/{table}.sql": "",
                    "{model_home}/{db}/{table}.yml": "",
                    "{catalog}": "",
                }
            },
        },
    )

    # map：每个 model 一次 LLM。正文是该 model 的归属 JSON。
    # final_root.csv 的 hash 在 fingerprint.depend 里，词根表变了就重跑。
    job.add_operator_node(
        "root_assigner",
        "root_assigner",
        upstream="source_assign",
        config=llm,
    )

    # reduce：把每个 model 的 JSON 收成 {"models": [...]}。
    job.add_operator_node("reduce_assigner", "reduce_assigner", upstream="root_assigner")

    # apply：写成 .staging/root_assign.json。
    job.add_operator_node("publish_assigner", "publish_assigner", upstream="reduce_assigner")

    # fanout：按 root_id 拆开，跳过 unassigned。实体正文带上该 root 在词根表里的那一行。
    # final_root.csv 在 fingerprint.depend 里，词根表变了即使归属 JSON 没变也重跑。
    job.add_operator_node("extract_root", "extract_root", upstream="reduce_assigner")

    # map：每个 root 一次 LLM，正文是这个 root 的 member CSV。
    job.add_operator_node(
        "taxonomist_member",
        "taxonomist_member",
        upstream="extract_root",
        config=llm,
    )

    # reduce：拼成一份 CSV，只留一行表头。
    job.add_operator_node(
        "combine_root_member",
        "combine_root_member",
        upstream="taxonomist_member",
    )

    # apply：写成 .staging/root_member.csv。
    job.add_operator_node(
        "publish_root_member",
        "publish_root_member",
        upstream="combine_root_member",
    )
    return job


def build_member_attribute_job(root: Path | None = None) -> Job:
    output_root = JOB_ROOT / "runs" if root is None else root
    model_home = os.environ.get("SEMANTIC_LAYER_MODELS", DEFAULT_MODEL_HOME)
    incoming = os.environ.get("SEMANTIC_LAYER_INPUT", str(JOB_ROOT / ".input"))
    llm = {"workspace": str(JOB_ROOT), "tool": _llm_tool()}
    staging = output_root / ".staging"
    root_assign = staging / "root_assign.json"
    root_member = staging / "root_member.csv"

    job = Job("member_attribute", output_root)

    # fingerprint.record 记下 sql、yml、root_assign.json 和 root_member.csv。
    job.add_operator_node(
        "source_member",
        "source_member",
        config={
            "directory": incoming,
            "model_home": model_home,
            "root_assign": str(root_assign),
            "root_member": str(root_member),
        },
    )

    job.add_operator_node(
        "assign_member",
        "assign_member",
        upstream="source_member",
        config=llm,
    )

    job.add_operator_node(
        "combine_assign_member",
        "combine_assign_member",
        upstream="assign_member",
    )

    job.add_operator_node(
        "publish_assign_member",
        "publish_assign_member",
        upstream="combine_assign_member",
    )
    return job


def _llm_tool() -> str | dict:
    configured = os.environ.get("DOCORDER_LLM", "").strip()
    if configured:
        return configured
    return CURSOR_TOOL


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "refine":
        execute(build_root_refine_job(), "demo", start_from_scratch=True)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "assign":
        execute(build_root_assigner_job(), "demo", start_from_scratch=True)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "member_attribute":
        execute(build_member_attribute_job(), "demo", start_from_scratch=True)
        return
    execute(build_root_job(), "demo", start_from_scratch=True)


if __name__ == "__main__":
    main()
