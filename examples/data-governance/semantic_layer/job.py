from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from docorder.core.job import Job
from docorder.core.runner import execute

JOB_ROOT = Path(__file__).resolve().parent
load_dotenv(JOB_ROOT / ".env")
# .env 里没有写 DOCORDER_HOMES 时，用本目录下的 .op_home。
os.environ.setdefault("DOCORDER_HOMES", str(JOB_ROOT / ".op_home"))

DEFAULT_MODEL_HOME = "/Users/jixie/wbox/data-governance/semantic_layer/models/hive"
# DEFAULT_MODEL_HOME = "/Users/cdpac/wbox/data-governance/semantic_layer/models/hive"
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
# MiniMax 用本机的 MiniMax Code 客户端：提示词从标准输入进来，客户端在工作目录里
# 自己读文件、改文件，跑完把答案打到标准输出。工具循环、权限和重试都归客户端管。
MCODE_BIN = os.environ.get("MCODE_BIN") or ""
if not MCODE_BIN:
    installed = Path.home() / ".minimax-code" / "bin" / "mcode"
    MCODE_BIN = str(installed) if installed.is_file() else "mcode"
MCODE_MODEL = os.environ.get("MCODE_MODEL", "minimax/MiniMax-M3.1-Flash")
MCODE_TIMEOUT = os.environ.get("MCODE_TIMEOUT", "30m")
MINIMAX_TOOL = {
    "name": "minimax",
    "run": [
        MCODE_BIN,
        "exec",
        "--input", "-",
        "--cwd", "{workspace}",
        "--permission", "full",
        "--output-format", "text",
        "--model", MCODE_MODEL,
        "--timeout", MCODE_TIMEOUT,
    ],
    "prompt": "stdin",
}
# DOCORDER_LLM 写这里的名字就选这个工具，写别的就当预设名或文件路径交给 docorder。
TOOLS = {"cursor": CURSOR_TOOL, "minimax": MINIMAX_TOOL}
# map/fanout 上的 LLM 并发。optimizer_root 必须保持 1（多线程会同时改同一份 patch 文件）。
MAP_PARALLELISM = int(os.environ.get("SEMANTIC_LAYER_PARALLELISM", "8"))


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
    job.add_operator_node(
        "librarian",
        "librarian",
        upstream="source",
        parallelism=MAP_PARALLELISM,
    )

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

    # apply：共用 publish home，config.filename 写成 .staging/raw_root.csv。
    job.add_operator_node(
        "publish",
        "publish",
        upstream="taxonomist_root",
        config={"filename": "raw_root.csv"},
    )
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
    job.add_operator_node(
        "publish_final",
        "publish",
        upstream="merge_root",
        config={"filename": "final_root.csv"},
    )
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
        parallelism=MAP_PARALLELISM,
        config=llm,
    )

    # reduce：把每个 model 的 JSON 收成 {"models": [...]}。
    job.add_operator_node("reduce_assigner", "reduce_assigner", upstream="root_assigner")

    # apply：写成 .staging/root_assign.json。
    job.add_operator_node(
        "publish_assigner",
        "publish",
        upstream="reduce_assigner",
        config={"filename": "root_assign.json"},
    )

    # fanout：按 root_id 拆开，跳过 unassigned。实体正文带上该 root 在词根表里的那一行。
    # final_root.csv 在 fingerprint.depend 里，词根表变了即使归属 JSON 没变也重跑。
    job.add_operator_node(
        "extract_root",
        "extract_root",
        upstream="reduce_assigner",
        parallelism=MAP_PARALLELISM,
    )

    # map：每个 root 一次 LLM，正文是这个 root 的 member CSV。
    job.add_operator_node(
        "taxonomist_member",
        "taxonomist_member",
        upstream="extract_root",
        parallelism=MAP_PARALLELISM,
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
        "publish",
        upstream="combine_root_member",
        config={"filename": "root_member.csv"},
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
        parallelism=MAP_PARALLELISM,
        config=llm,
    )

    job.add_operator_node(
        "combine_assign_member",
        "combine_assign_member",
        upstream="assign_member",
    )

    job.add_operator_node(
        "publish_assign_member",
        "publish",
        upstream="combine_assign_member",
        config={"filename": "root_member_assign.json"},
    )
    return job


def _llm_tool() -> str | dict:
    configured = os.environ.get("DOCORDER_LLM", "").strip()
    if configured:
        return TOOLS.get(configured, configured)
    return CURSOR_TOOL


_JOBS = {
    "raw_root": build_root_job,
    "refine": build_root_refine_job,
    "assign": build_root_assigner_job,
    "member_attribute": build_member_attribute_job,
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run semantic layer docorder jobs.")
    parser.add_argument(
        "job",
        choices=tuple(_JOBS),
        help="Pipeline stage: raw_root → refine → assign → member_attribute.",
    )
    parser.add_argument("--epoch", default="demo", help="Epoch name passed to execute.")
    parser.add_argument(
        "--from-scratch",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Clear prior outputs for this job before running (default: true).",
    )
    args = parser.parse_args(argv)
    execute(_JOBS[args.job](), args.epoch, start_from_scratch=args.from_scratch)


if __name__ == "__main__":
    main()
