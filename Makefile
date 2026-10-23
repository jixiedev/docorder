.PHONY: quality docs figures

quality:
	uv run ruff check
	uv run python examples/data-governance/documentation/job.py

# 重新生成使用指南里的内联配图。脚本按成对的注释就地替换图，可以反复运行。
figures:
	uv run python scripts/build_figures.py

# 重新生成文档站。docs/site/ 下的网页是产物，不要手工改。
docs: figures
	uv run python scripts/build_docs.py
