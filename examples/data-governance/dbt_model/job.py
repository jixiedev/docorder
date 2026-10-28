from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from docorder.core.job import Job
from docorder.core.runner import execute

JOB_ROOT = Path(__file__).resolve().parent
load_dotenv(JOB_ROOT / ".env")
# .env 里没有写 DOCORDER_HOMES 时，用本目录下的 .op_home。
os.environ.setdefault("DOCORDER_HOMES", str(JOB_ROOT / ".op_home"))

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
        return TOOLS.get(configured, configured)
    return CURSOR_TOOL


def main() -> None:
    execute(build_job(), "demo", start_from_scratch=True)


if __name__ == "__main__":
    main()
