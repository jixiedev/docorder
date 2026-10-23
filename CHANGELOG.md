# Changelog

[English](CHANGELOG.en.md)

本文件遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。

## [Unreleased]

- 使用指南新增两章。第四章「指纹与哈希」讲清 docorder 里的三种哈希分别算什么、记在哪里：上游快照里的哈希、`fingerprint.depend` 与 `fingerprint.record`。这一章说明 `depend` 与 `record` 的分工与渲染时机、路径模板能用的占位符、节点 `config` 对指纹的整份覆盖规则，以及一个实体每次运行都被重做时该怎么逐条排查。第十一章「数据治理案例」用 `examples/data-governance/` 下的真实作业把这些机制串起来：四个作业接力，从 dbt 模型的指标清单到词根表、归属表与成员表，途中用到 fanout 拆出十四个词根实体。原有章节往后挪一位，最佳实践落到第十二章；README、术语表、贡献指南、文档首页与指南目录里的章号一并更新。
- 文档站构建前先清空 `docs/site/`。章节改名后不会留下指向旧章号的孤儿页面。
- 使用指南新增八张内联 SVG 配图，讲解只靠文字说不清的地方：概念之间的层次关系、一个 stage 的经过、再次运行时的判定、一次运行留下的目录、五种算子的输入输出对应、内置模板变量的分组，以及两类哈希如何合成一个判定、数据治理案例的四个作业怎么接力。新增 `scripts/build_figures.py` 生成这些图，图的源码就写在 `docs/guide.md` 与 `docs/guide.en.md` 里，GitHub 上看 Markdown 也能看到图，文档站构建时原样带进网页。配色跟随文档站自己的暖纸底色与青绿主色，中英文各出一套文案。文档站补上配图的样式：图包在带边框的卡片里，图注带「图 N」标记；窄屏下图在卡片内横向滚动，不缩到看不清。
- 文档编译成静态网页站点。新增 `scripts/build_docs.py`，把仓库里的 Markdown 编译成 `docs/site/` 下的网页：使用指南按二级标题切成每章一页，另加指南目录页、快速开始、术语表、行为准则、参与贡献、安全和更新日志各一页，中英文各一套。首页正文是手写片段，放在 `scripts/templates/` 下，由脚本套进统一的页面外壳。生成结果不再出现指向裸 Markdown 文件的链接，正文里的交叉引用改写成网页链接。
- 文档站改造为 Apache Hudi 文档站那样的结构。`docs/index.html` 与 `docs/index.en.html` 从介绍页改成文档首页：顶栏之下是左侧分组侧栏、正文、右侧「本页内容」目录三栏，正文带上面包屑与上下页导航。使用指南的各章以锚点链接进入侧栏，「文档」一节列出全部章节卡。窄屏下侧栏收成一个可展开的目录，正文优先呈现。
- 文档合并为单一手册。`docs/design.md` 与 `docs/functions.md` 的内容并入 `docs/guide.md`，两份文档删除；英文版同样合并为 `docs/guide.en.md`，`docs/design.en.md` 与 `docs/functions.en.md` 删除。README、贡献指南、术语表和介绍页的链接一并更新。
- 文档首页重排。章节标题与导航一一对应，「模型」一节拆成实体、算子类型、作业图三块，补上作业图的示意和术语对照的错误（算子类型应为五种）。去掉了内联样式，文件卡的隐喻在各处保持一致，窄屏下标题不再被挤断。
- 使用指南新增第十章「最佳实践」，覆盖目录与命名、增量与幂等、算子 home 的组织、错误处理、大模型调用成本、失败恢复，以及一张常见反模式对照表。

- 文档按当前代码再次核对。README 补上 `docorder status` 命令和完整依赖列表，`make quality` 与 CI 改为运行 `examples/data-governance/documentation/` 下的示例作业。使用指南补上 `FileHashSource`、`EntityTemplateToLLM`、`TemplateToLLM` 三个内置 function 的小节，内置 function 表补齐，并把第九章的输入数据改成实体子目录的写法。function 文档把 `Output` 从 map 章节拆成独立的 apply 章节。文档首页补上 apply 算子和 `docorder status`。
- `Output` 增加参数 `filename`，固定写出的文件名。文件名要随实体变化时仍覆盖 `rename`。
- 新增 `EntityTemplateToLLM`。它是 map：每个上游实体用 Jinja 渲染一份 prompt，交给 LLM。模板变量是单个 `source` 的路径和 tag，以及 `staging(name)`。`header` 与 `tag_template` 和 `TemplateToLLM` 相同。
- 新增 `TemplateToLLM`。它是 reduce：用 Jinja 把上游整批渲染成一份 prompt，交给 LLM。`header` 从回复里抽出 CSV，`tag_template` 渲染实体 tag。模板只放路径：`source.path` 是上游 `data` 文件，`staging(name)` 是 `.staging` 里一个已存在文件的路径。
- 新增 `fingerprint`。`record` 在写出实体后把文件 sha256 记进 tag，不因此重做本算子；`depend` 在运行前比较，不一致则重做。source 只记 `record`，apply 不能声明指纹。`FileHashSource` 只把 `paths` 的绝对路径写进 tag，正文保持输入原文。
- 去掉输出目录标记 `.docorder-output`。stage 开始时只创建节点输出目录，不再因为目录非空而拒绝运行。`docorder status` 把名字不以 `.` 开头的子目录当作 stage。
- `Output` 仍是 apply function，没有单独的 output 算子。缺省目录改为作业根下的 `.staging`。文件名由 `rename` 决定，缺省返回实体名，子类覆盖该方法。去掉 `name_template`。
- 用 `apply` 算子替换 `output` 算子。apply 对上游每个实体调用 `apply`，结束后调用 `finish`；两者都不能返回值。它不写实体，也不能有下游。原先写出作业结果文件的行为改由 apply function `Output` 完成。
- `tag.json` 不再写入 `current`。下游快照按上游实体此刻的正文和用户 tag 计算；手动改已写出实体的 `data` 或 `tag.json`，下一次运行会重做依赖它的下游。
- `PromptToLLM` 在工具自己写出目标实体的 `data` 时保留该文件，检查它是非空 UTF-8 文本后只补 `tag.json`。没有这份文件时，正文仍是标准输出。
- 上游快照改写在 `tag.json` 的 `upstream` 里，不再写 `upstream.json`。写出时会删掉目录里残留的那份文件。
- 每个 stage 在标准错误输出上打印一条进度条，标题是节点名。map、fanout、reduce、apply 的总数是这次要处理的个数；source 在 `emit` 时逐条推进。
- `DirectorySource` 读取已经符合实体约定的子目录：目录名是实体名，正文来自 `data`，tag 来自 `tag.json`。普通文件和残缺目录会被跳过。
- `Output` 把上游正文写成作业根目录 `.staging` 下的文件。文件名缺省是实体名，子类覆盖 `rename` 改名。参数 `directory` 可以换成别的写出目录，相对路径相对算子 home 解析。
- `LLMTool` 移到 `docorder.utils.llm_tool`。
- `Artifact` 和 `Environment` 移到 `docorder.core`。
- 内置 function 移到 `docorder.functions.impl`。基类改名为 `source_function`、`map_function`、`reduce_function`、`fanout_function`、`rendered_map`。`props.json` 的 `class` 要写成新模块路径。
- `Environment` 只保留 `operator_props`（function 参数）和 `template_env`（模板用的 `operator` / `job` / `entity`）。去掉 `config`、`bind`、`namespace`、`bindings`、`format_named`。
- map 和 fanout 的 `parallelism` 改为线程池，不再使用进程池。分片线程共享算子，参数不必能被 pickle，也不再要求启动脚本写 `if __name__ == "__main__":`。
- `OperatorNode` 构造时把节点 `config` 覆盖进 `props`，之后不再保留 `config`，对外只暴露 `props`。`Operator.of` 再把节点的公开字段抬到算子上，此后 runner、function 和模板环境都读算子，不再经过节点。`Function` 持有 `environment`：`environment.operator_props` 是 function 参数，`environment.template_env` 是模板用的 `operator` / `job` / `entity`，都从 operator 生成。新增对应的契约测试。
- 新增 `docs/guide.md` 使用指南：背景、核心概念、工作流程、使用场景、配置、按算子类型列出的内置 function、渲染类 function 的模板变量及扩充方法、开发自己的 function、在自己的项目中使用 docorder 的完整示例，以及最佳实践。英文版为 `docs/guide.en.md`。
- 文档按当前代码核对并改写。README 改为从仓库用 `uv sync` 安装，补上获取代码、环境要求、可运行的快速开始与再跑示例、配置和排错。使用指南更正了同名节点、reduce 空上游、整段清场、并行失败和 source `emit` 失败时的行为，并新增再跑判定表、指纹说明、失败与重试对照表和端到端示例。`SECURITY.md` 与文档首页删去并不存在的 `cursor` 预设。
- 使用指南的第二、三章按当前的 stage 调度重写：实体、算子与作业的状态，epoch 目录，以及同一次运行如何比较上游并落盘。
- 文档提供中英两份。中文使用原文件名，英文使用同名加 `.en` 后缀。README 按当前的 `Job` 与 `execute` 重写。
- 文档首页在 `docs/index.html`。
- function 的说明集中在使用指南的第六章。每个 function 是 `src/docorder/functions/` 下的一个模块。
- source 算子只接收 function。function 用 `emit` 交出实体的 data 和 tag。`DirectorySource` 从目录产出实体，读取已有的实体子目录（`data` 与 `tag.json`）。`FilteredDirectorySource` 按 `filter` 的名字结尾和 `data` 大小筛选。
- 包内不再附带算子 home。home 由 `DOCORDER_HOMES` 提供，具体算子随后再实现。
- `execute` 只接收 epoch。一次运行按拓扑顺序跑完整张图。
- 算子 `props.json` 只用 `type`：`source`、`map`、`reduce`、`fanout`。
- 实体按 epoch 子目录存放。上游算子、实体名、epoch 和 hash 写在实体目录的 `upstream.json` 里。同一 epoch 再跑时执行未做的、删除多出来的、重做上游变了的。
- 项目名为 docorder。包、命令行，以及 `DOCORDER_DG`、`DOCORDER_LLM`、`DOCORDER_HOMES` 都使用这个名字。
- 可复用算子实现放在 `src/docorder/operators/`，stage 调度放在 `src/docorder/runner.py`。
- data-governance 的示例作业改为 `examples/data-governance/` 下的脚本（`documentation`、`dbt_model`、`semantic_layer`），不再通过 `docorder run` 打进安装包。
- `llm` / `llm_batch` 这两个算子去掉，大模型改由 `PromptToLLM`、`EntityTemplateToLLM`、`TemplateToLLM` 三个 function 调用。工具预设是算子 home 里的 JSON 文件，也可以直接传入一份命令 JSON。

## [0.1.0] - 2026-10-12

- 按 stage 调度目录实体，支持重试、epoch checkpoint、跳过算子和从指定算子恢复。
- 随包提供 jsonnet、模板 prompt、Cursor、命令、CSV fan-out、拼接和 review 算子。
- 提供 documentation、data-quality、semantic-physical、semantic-ontology 四类 job。这些 job 需要一份布局相符的外部仓库，路径用 `--dg` 或 `DOCORDER_DG` 指定。
