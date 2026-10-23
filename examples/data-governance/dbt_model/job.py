from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from docorder.core.job import Job
from docorder.core.runner import execute

JOB_ROOT = Path(__file__).resolve().parent
load_dotenv(JOB_ROOT / ".env")

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


def build_job(root: Path | None = None) -> Job:
    output_root = JOB_ROOT / "runs" if root is None else root
    incoming = os.environ.get("DBT_MODEL_INPUT", str(JOB_ROOT / ".input"))
    doc_home = os.environ.get("DBT_MODEL_DOCS", str(JOB_ROOT / "docs"))
    job = Job("dbt_model", output_root)
    staging = str(job.staging_path)

    # .input 里每个实体对应一份表文档。正文是输入原文。fingerprint.record 记下文档 sha256，tag 带上绝对路径。
    job.add_operator_node(
        "source",
        "source",
        config={"directory": incoming, "doc_home": doc_home},
    )

    # 渲染 prompt。正文是 prompt 本身。prompt 引用文档路径，并要求在 staging 下创建 sql 和 yaml。
    job.add_operator_node(
        "doc_to_generate_prompt",
        "doc_to_generate_prompt",
        upstream="source",
        config={"staging": staging},
    )

    # 把上一步的 prompt 交给 LLM。写完文件后，fingerprint.record 分别记下 sql 和 yaml。
    job.add_operator_node(
        "generate_model",
        "generate_model",
        upstream="doc_to_generate_prompt",
        config={"workspace": str(JOB_ROOT), "tool": _llm_tool(), "staging": staging},
    )

    # review 还没接。上游用 generate_model，sql/yaml 的 hash 变了才重跑。
    # job.add_operator_node("doc_to_review_prompt", "doc_to_review_prompt", upstream="generate_model")
    return job


def _llm_tool() -> str | dict:
    configured = os.environ.get("DOCORDER_LLM", "").strip()
    if configured:
        return configured
    return CURSOR_TOOL


def main() -> None:
    execute(build_job(), "demo", start_from_scratch=True)


if __name__ == "__main__":
    main()
