# 参与贡献

[English](CONTRIBUTING.en.md)

## 环境

需要 Python 3.10 以上和 [uv](https://docs.astral.sh/uv/)。要用 `JsonnetToPrompt` 时，再安装 `jsonnet` 可执行文件。

```bash
uv sync --group dev
uv run ruff check
uv run pytest
```

`tests/test_contract.py` 是调度行为的契约测试。改动实体、比较、清场、重试或 source 的行为时，先在这里补用例。`make quality` 和 CI 还会运行 `examples/data-governance/documentation/` 下的示例作业。

## 改哪里

运行时在 `src/docorder/`。`core/` 是实体、作业、算子和 stage 调度。`functions/` 是 source、map、reduce、fanout、apply 基类。内置实现在 `functions/impl/`。`utils/` 是错误、模块加载、home 搜索和重试。

算子 home 放在 `DOCORDER_HOMES` 指向的目录里，不打进安装包。路径分隔符与 `PATH` 相同，靠前的目录优先。新的转换优先复用已有 function。现有类型表达不了时，在 home 的 `primary.py` 里实现与 `props.json` 的 `type` 对应的 function 基类，并把 `class` 写成 `primary:类名`。重试和线程池由 runner 负责，不要在 function 里再做一套。写法见 [docs/guide.md](docs/guide.md) 第九章。

## 改文档

文档的源文件是仓库里的 Markdown。`docs/guide.md` 是使用指南的唯一源文件，`README.md`、`glossary.md`、`CONTRIBUTING.md`、`SECURITY.md`、`CHANGELOG.md` 各自成页。

改完 Markdown 重新生成网页：

```bash
uv run python scripts/build_figures.py
uv run python scripts/build_docs.py
```

产物在 `docs/site/` 下，包括使用指南按章拆开的页面。生成出来的网页不要手工改，改源文件再重新运行脚本。首页的正文片段在 `scripts/templates/` 下，那是手写内容，生成脚本会把它套进统一的页面外壳。

新增章节的做法：在 `docs/guide.md` 和 `docs/guide.en.md` 里各加一个二级标题，两边的标题按顺序一一对应，脚本按位置配对生成中英文页面。编号列表形式的章节摘要写在「文档结构」一章里，脚本从那里取每一章的简介。

使用指南里的配图由 `scripts/build_figures.py` 生成，图直接写进 `docs/guide.md` 和 `docs/guide.en.md`。脚本按成对的注释就地替换图，可以反复运行：

```text
<!-- figure:slug:start -->
<!-- figure:slug:end -->
```

要改图，改 `scripts/build_figures.py` 里对应的函数，再重新运行脚本；不要手工编辑注释之间的内容。

文档改动同时改中文和同名的 `.en` 文件。文档里的命令和示例代码，提交前在本机实际跑一遍。

## 提交

贡献以 [MIT 许可](LICENSE) 发布。提交说明写清原因。不要提交密钥、访问令牌、`runs/` 或真实业务数据。

行为变更记入 `CHANGELOG.md` 的 Unreleased 小节。文档改动同时改中文和同名的 `.en` 文件。文档里的命令和示例代码，提交前在本机实际跑一遍。
