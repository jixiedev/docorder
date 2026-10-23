# docorder 使用指南

**目录**

- [文档结构](#文档结构)
- [一、背景](#一背景)
  - [要解决的问题](#要解决的问题)
  - [一个最小的例子](#一个最小的例子)
  - [设计取舍](#设计取舍)
  - [本版边界](#本版边界)
- [二、核心概念与术语](#二核心概念与术语)
  - [实体](#实体)
  - [上游快照](#上游快照)
  - [算子与算子 home](#算子与算子-home)
  - [function](#function)
  - [作业与节点](#作业与节点)
  - [epoch 与 stage](#epoch-与-stage)
  - [runner 与应得名单](#runner-与应得名单)
  - [概念之间的关系](#概念之间的关系)
  - [术语对照](#术语对照)
- [三、工作流程](#三工作流程)
  - [装配](#装配)
  - [一个 stage 的经过](#一个-stage-的经过)
  - [并行与重试](#并行与重试)
  - [source 节点的 stage](#source-节点的-stage)
  - [再次运行时的判定](#再次运行时的判定)
  - [常见的再跑场景](#常见的再跑场景)
  - [一次运行留下的目录](#一次运行留下的目录)
- [四、指纹与哈希](#四指纹与哈希)
  - [docorder 里有三种哈希](#docorder-里有三种哈希)
  - [上游快照里的哈希](#上游快照里的哈希)
  - [声明指纹](#声明指纹)
  - [两处判断如何合成一个结果](#两处判断如何合成一个结果)
  - [路径模板与占位符](#路径模板与占位符)
  - [一次运行里的时序](#一次运行里的时序)
  - [会被拒绝的声明](#会被拒绝的声明)
  - [空正文](#空正文)
  - [节点的 config 会整份覆盖指纹](#节点的-config-会整份覆盖指纹)
  - [排查](#排查)
- [五、使用场景](#五使用场景)
  - [批量生成提示词并交给大模型](#批量生成提示词并交给大模型)
  - [从结构化数据生成配置文件](#从结构化数据生成配置文件)
  - [为每个实体运行命令行工具](#为每个实体运行命令行工具)
  - [汇总与拆分](#汇总与拆分)
  - [不适合的场景](#不适合的场景)
- [六、配置](#六配置)
  - [让 docorder 找到算子 home](#让-docorder-找到算子-home)
  - [props.json](#propsjson)
  - [作业与节点](#作业与节点-1)
  - [execute](#execute)
  - [function 读到的参数与模板读到的算子信息](#function-读到的参数与模板读到的算子信息)
  - [环境变量](#环境变量)
- [七、算子分类与内置 function](#七算子分类与内置-function)
  - [五种算子](#五种算子)
  - [source 算子](#source-算子)
  - [map 算子](#map-算子)
  - [reduce 算子](#reduce-算子)
  - [fanout 算子](#fanout-算子)
  - [apply 算子](#apply-算子)
  - [失败与重试](#失败与重试)
- [八、渲染类 function 与模板变量](#八渲染类-function-与模板变量)
  - [RenderedMap 的三个步骤](#renderedmap-的三个步骤)
  - [渲染环境](#渲染环境)
  - [内置模板变量](#内置模板变量)
  - [增加模板变量](#增加模板变量)
  - [变量同名时以谁为准](#变量同名时以谁为准)
- [九、开发自己的 function](#九开发自己的-function)
  - [选择基类](#选择基类)
  - [function 中可以使用的对象](#function-中可以使用的对象)
  - [必须遵守的约定](#必须遵守的约定)
  - [代码放在哪里](#代码放在哪里)
  - [示例：自定义 source](#示例自定义-source)
  - [示例：map](#示例map)
  - [示例：基于 RenderedMap](#示例基于-renderedmap)
  - [示例：reduce](#示例reduce)
  - [示例：fanout](#示例fanout)
  - [测试 function](#测试-function)
- [十、在自己的项目中使用 docorder](#十在自己的项目中使用-docorder)
  - [第一步：安装 docorder](#第一步安装-docorder)
  - [第二步：规划目录](#第二步规划目录)
  - [第三步：准备输入数据](#第三步准备输入数据)
  - [第四步：编写算子 home](#第四步编写算子-home)
  - [第五步：编写启动脚本](#第五步编写启动脚本)
  - [第六步：运行并查看结果](#第六步运行并查看结果)
  - [第七步：修改之后再次运行](#第七步修改之后再次运行)
  - [纳入版本管理](#纳入版本管理)
- [十一、数据治理案例](#十一数据治理案例)
  - [案例在仓库里的位置](#案例在仓库里的位置)
  - [业务问题](#业务问题)
  - [第一个作业：建词根表](#第一个作业建词根表)
  - [第二个作业：修词根表](#第二个作业修词根表)
  - [第三个作业：给模型分配词根](#第三个作业给模型分配词根)
  - [第四个作业：补成员属性](#第四个作业补成员属性)
  - [这个案例用到的机制](#这个案例用到的机制)
  - [怎么跑](#怎么跑)
- [十二、最佳实践](#十二最佳实践)
  - [先想清楚这件事适不适合 docorder](#先想清楚这件事适不适合-docorder)
  - [目录与命名](#目录与命名)
  - [增量与幂等](#增量与幂等)
  - [算子 home 的组织](#算子-home-的组织)
  - [错误处理](#错误处理)
  - [调用大模型](#调用大模型)
  - [常见反模式](#常见反模式)
- [附录 A：内置 function 一览](#附录-a内置-function-一览)
- [附录 B：实现索引](#附录-b实现索引)
- [附录 C：相关文档](#附录-c相关文档)

---

docorder 是一个 Python 库，用来批量处理一组结构相同的对象。所谓「对象」，可以是一张表的定义、一篇笔记、一份配置文件，或者任何能用一段文本表示的东西。使用者先把要做的加工拆成几个先后相连的步骤，例如「读取文件」「套用模板生成提示词」「把提示词交给大模型」「把所有回答汇总成一份清单」，然后把这些步骤连成一张作业图交给 docorder 执行。docorder 会把每个对象在每一步的结果都写成磁盘上的一个目录，并在目录里记下这个结果是根据哪份上游内容算出来的；因此，当某一步中途失败，或者输入发生了变化时，再运行一次，docorder 只会补做失败的部分和受变化影响的部分，已经完成而且仍然有效的结果会原样保留。

本指南面向第一次使用 docorder 的读者，不要求事先了解项目里的任何术语。第一章先说明 docorder 想解决什么问题，并用一个只有两步的最小例子演示一个作业从配置到运行的全过程，后面各章会反复借用这个例子。第二章逐一定义例子里出现的概念，第三章按时间顺序讲一次运行内部发生了什么，第四章讲指纹与哈希，也就是增量判断的依据，第五章介绍适合使用 docorder 的场景，第六章到第八章分别讲配置项、docorder 自带的各种转换，以及模板里能使用的变量，第九章讲如何编写自己的转换，第十章用一个完整的项目示例，一步一步说明如何在自己的仓库里使用 docorder，第十一章用一个真实的数据治理作业把这些机制串起来，第十二章讲怎么用它才稳。

本指南的内容以当前代码为准。有两点需要事先说明：docorder 目前还没有发布到 PyPI，需要从源码仓库安装，安装步骤在第十章第一步；运行作业仍然在 Python 脚本里调用 `execute`。安装后的 `docorder status <输出根目录>` 用来查看这个目录里有哪些 epoch、每个 epoch 的结果是否与上游快照一致，以及每个 stage 在每个 epoch 下有多少实体。

如果你是第一次接触 docorder，建议按顺序读完前三章，建立整体印象之后，再根据需要查阅第六章到第八章；如果你打算编写自己的转换逻辑，请阅读第九章；如果你希望尽快在自己的项目中用起来，可以直接跳到第十章照着做，遇到不理解的名词时再回到前面对应的章节；想看一个完整的真实例子，可以读第十一章；真正开始长期使用之前，第十二章值得一读。

## 文档结构

1. 背景：docorder 要解决的问题，一个两步作业的最小例子，docorder 在设计上做了哪些取舍，以及当前版本有哪些能力边界。
2. 核心概念与术语：实体、上游快照、算子与算子 home、function、作业与节点、epoch 与 stage、runner 与应得名单，每个概念都说明它是什么、由谁创建、保存在哪里。
3. 工作流程：一次运行从检查作业图开始，到逐个节点执行结束，中间每一步做了什么；还包括并行执行、失败重试、source 节点的特殊处理，以及再次运行时 docorder 如何决定每个结果的去留。
4. 指纹与哈希：docorder 里的三种哈希各算什么，怎么用 `fingerprint` 声明对外部文件的依赖，`record` 与 `depend` 的分工，路径模板怎么写，以及怎么排查一个每次运行都重做的实体。
5. 使用场景：几种典型的作业图分别适合什么任务，以及哪些任务不适合用 docorder。
6. 配置：docorder 如何找到算子、`props.json` 里每个键的含义、作业和节点的参数、运行函数 `execute` 的参数、转换代码和模板分别读到哪些配置，以及相关的环境变量。
7. 算子分类与内置 function：五种算子的区别，每种算子可以搭配哪些 docorder 自带的转换类，每个转换类有哪些配置项、产生什么结果、在什么情况下失败。
8. 渲染类 function 与模板变量：模板里可以直接使用的全部变量，以及在内置变量不够用时，六种增加模板变量的方法。
9. 开发自己的 function：应该继承哪个基类、需要实现哪些方法、在方法里可以使用哪些对象、必须遵守哪些约定、代码文件放在哪里，以及如何为它编写测试。
10. 在自己的项目中使用 docorder：从安装、规划目录、准备输入数据、编写算子、编写启动脚本，到运行、查看结果和修改后再次运行的完整步骤。
11. 数据治理案例：`examples/data-governance/` 下的真实作业，从 dbt 模型的指标清单到词根表、归属表和成员表，四个作业怎么接力。
12. 最佳实践：把 docorder 用稳的几条约定，覆盖目录与命名、增量与幂等、算子 home 的组织、错误处理、大模型调用成本、失败恢复和常见反模式。

文中有几张结构示意图，分别展示最小例子的文件与运行结果，一个实体目录的组成，各个概念之间的关系，一次运行在磁盘上留下的目录，模板渲染时可用数据的组成，两类哈希如何合成一个判定，以及第十章示例项目的目录树。

这份文档是 docorder 的唯一参考手册。早期它拆成 `design.md`（内部机制）与 `functions.md`（转换类参考）两份，内容与本文件大量重复；现在两者已并入本文，磁盘机制见第二、三、四章，转换类参考见第七、八章。

## 一、背景

### 要解决的问题

很多批处理任务都有相同的形状：手里有一批对象，例如几百张数据表的定义、一批笔记或者一组服务的配置，需要对每个对象依次做几步加工，例如先把表定义渲染成一段提示词，再把提示词交给大模型生成说明文字，最后把所有表的说明汇总成一份清单。这样的任务有两个共同的麻烦。第一个麻烦是每一步都可能很慢，也可能失败：调用外部命令可能超时，大模型接口可能限流或者返回错误，模板里也可能有写错的地方。第二个麻烦是输入会不断变化：今天改了其中一张表的定义，明天又新增了几张表，每次变化之后都需要更新结果。

如果只写一个普通的脚本，用循环逐个处理这些对象，那么处理到第三百个对象时出了错，修好问题之后往往只能从头再跑一遍，前面已经花掉的时间和大模型调用费用都白白浪费了。为了避免这种情况，很多人会自己记录「哪些对象已经处理完」，但这份记录放在数据库里，就多了一个需要部署和维护的组件；放在内存里，进程一退出记录就丢失了。更难处理的是判断「已经算好的结果还能不能继续用」：修改了某个输入文件之后，到底哪些下游结果需要重新计算，哪些可以保留，普通脚本通常没有可靠的依据，只能全部重算，或者靠人工判断。

docorder 的做法是把每个对象在每一步的结果都写成磁盘上的一个目录，并在这个目录里记下这一步读取的上游内容的哈希值。哈希值是根据一段内容计算出来的一串固定长度的字符，内容只要有一点变化，哈希值就会完全不同，因此可以用它来判断内容是否被改动过。下次运行时，docorder 只需要把目录里记下的哈希值与上游当前内容的哈希值作比较，就能知道哪些对象还没有处理、哪些对象的结果已经过时需要重做、哪些对象的结果仍然有效可以保留。整个判断过程只依赖磁盘上的文件，不需要数据库，也不依赖上一次运行留在内存里的任何状态。

### 一个最小的例子

下面这个作业读取一个目录中的笔记实体，把每个笔记的正文放进一个模板，生成一段提示词。它只有两个步骤，但已经包含了 docorder 的全部基本组成部分，后面各章会反复用它来解释概念。要实际运行这个例子，需要先按第十章第一步安装 docorder。

#### 准备文件

先在任意位置建立下面这样的目录结构。其中 `notes/` 是输入数据，`homes/` 存放描述「每一步做什么」的配置，`run.py` 是启动整个作业的 Python 脚本。

```text
hello-docorder/
  run.py                    启动脚本
  notes/
    hello/
      data                  输入正文，内容是 hello
      tag.json              输入附加信息
  homes/                    存放算子的目录
    notes_source/
      props.json
    prompt/
      props.json
      lib/note.jinja        模板文件，内容是 Note: {{ entity.source_data }}
```

在 docorder 里，作业中的每一种步骤称为一个算子（operator），描述一个算子的那个目录称为算子 home。上面的 `homes/notes_source/` 和 `homes/prompt/` 就是两个算子 home：前者描述「从一个目录里读取文件」这个步骤，后者描述「用模板生成提示词」这个步骤。docorder 安装包里不附带任何算子 home，算子 home 总是由使用者自己放在项目里。每个算子 home 里都必须有一份名为 `props.json` 的 JSON 配置文件，docorder 正是通过它来认出一个目录是算子 home，并了解这个算子该怎么运行。

`homes/notes_source/props.json` 的内容如下：

```json
{
  "type": "source",
  "class": "docorder.functions.impl.directory_source:DirectorySource"
}
```

`homes/prompt/props.json` 的内容如下：

```json
{
  "type": "map",
  "class": "docorder.functions.impl.template_to_prompt:TemplateToPrompt",
  "template": "lib/note.jinja"
}
```

`type` 说明这个算子属于哪一类。`source` 类型的算子位于作业的起点，它不读取其它步骤的结果，而是从外部（例如磁盘上的一个目录）产生最初的一批对象；`map` 类型的算子读取上一步的结果，并对其中的每个对象分别做一次转换，每个输入对象对应一个输出对象。`class` 指向真正执行转换的 Python 类，写法是「模块路径:类名」，这个类在 docorder 中称为 function。这里用到的两个 function 都是 docorder 自带的：`DirectorySource` 把一个目录中已经写成实体形状的子目录变成对象，`TemplateToPrompt` 用一个 Jinja 模板为每个对象渲染出一段文本。Jinja 是 Python 中常用的模板语言，模板里用两对花括号包住的部分，例如 `{{ entity.source_data }}`，会在渲染时被替换成对应变量的值。`props.json` 中除 `type` 和 `class` 以外的键，都会作为参数交给 function 使用，例如 `template` 告诉 `TemplateToPrompt` 使用哪个模板文件，这个路径是相对于算子 home 的。

#### 配置并运行作业

`run.py` 的内容如下：

```python
import os
from pathlib import Path

from docorder.core.job import Job
from docorder.core.runner import execute

ROOT = Path(__file__).resolve().parent


def main() -> None:
    os.environ["DOCORDER_HOMES"] = str(ROOT / "homes")

    job = Job("hello", ROOT / "runs")
    job.add_operator_node("notes", "notes_source", config={"directory": str(ROOT / "notes")})
    job.add_operator_node("prompt", "prompt", upstream="notes")

    execute(job, "demo", start_from_scratch=True)


if __name__ == "__main__":
    main()
```

脚本的第一行实质性代码设置了环境变量 `DOCORDER_HOMES`，它告诉 docorder 到哪个目录里寻找算子 home。这里把它设为项目里的 `homes/` 目录，于是后面提到的 `notes_source` 和 `prompt` 这两个名字，就会分别对应到 `homes/notes_source/` 和 `homes/prompt/`。

`Job("hello", ROOT / "runs")` 创建一个作业。作业描述的是「这一次要把哪些步骤按什么顺序连起来执行，结果写到哪里」。第一个参数是作业的名字；第二个参数是输出根目录，这个作业所有步骤的结果都会写在这个目录下面。

`add_operator_node` 向作业中加入一个节点。节点是作业图中的一个点，它表示「在这个作业里使用某个算子执行一个步骤」。第一次调用加入了一个名为 `notes` 的节点，它使用 `notes_source` 这个算子 home；`config` 参数给这个节点补充了一个名为 `directory` 的参数，指明要读取的输入目录。输入目录的位置属于具体的项目，而不属于「读取目录」这个可以在许多项目中复用的步骤，所以它没有写进 `props.json`，而是在作业里传入。第二次调用加入了一个名为 `prompt` 的节点，它使用 `prompt` 这个算子 home，`upstream="notes"` 表示这个节点读取 `notes` 节点的结果作为输入，也就是说 `notes` 是 `prompt` 的上游。

`execute(job, "demo", start_from_scratch=True)` 真正开始执行这个作业。第二个参数 `"demo"` 称为 epoch，可以把它理解为「这一批结果的名字」，它会成为输出目录中的一层子目录。如果以后用同一个 epoch 再次运行，docorder 会在这批已有结果的基础上继续工作；如果换一个新的 epoch，docorder 就会在一个空目录里从头开始，原来那批结果保持不动。`start_from_scratch=True` 要求 source 类型的节点重新读取外部输入；如果不传这个参数，source 节点会保留上一次读到的内容，不去重新读取输入目录。

在已经安装了 docorder 的环境中，进入 `hello-docorder/` 目录，执行 `uv run python run.py` 就能运行这个作业。脚本最后的 `if __name__ == "__main__":` 是普通脚本的写法。并行执行用的是线程，不再另起子进程。

#### 运行留下的文件

运行结束后，输出根目录 `runs/` 中会出现下面这些文件：

```text
runs/
  notes/
    demo/                             epoch 目录
      hello/                          一个实体，名字来自输入目录 hello
        data                          hello
        tag.json                      来自输入实体的 tag.json
  prompt/
    demo/
      hello/
        data                          Note: hello
        tag.json                      与上游的 tag.json 相同，并含 upstream
                                      {"operator": "notes", "name": "hello",
                                       "epoch": "demo", "hash": "5891b5b5…"}
```

每个节点在输出根目录下都有一个与节点同名的目录，例如 `runs/notes/` 和 `runs/prompt/`；节点目录下是以 epoch 命名的目录，这里是 `demo/`；epoch 目录下，每个被处理的对象各占一个子目录，docorder 把这样一个目录称为一个实体（entity）。在这个例子里，输入目录中只有 `hello` 一个实体目录，所以每个节点都只产生了一个名为 `hello` 的实体。

实体目录里的 `data` 文件称为正文，保存的是这一步的主要结果：在 `notes` 节点里，它是输入实体目录里 `data` 的原始内容；在 `prompt` 节点里，它是模板渲染后的文本 `Note: hello`。`tag.json` 保存的是正文之外的附加信息，格式是一个 JSON 对象：`DirectorySource` 把输入目录里的 `tag.json` 读进来；`TemplateToPrompt` 不产生新的附加信息，而是把上游实体的 `tag.json` 原样复制过来，传给下一步使用。

`tag.json` 里的 `upstream` 只出现在 `prompt` 节点的实体里，docorder 称它为上游快照。它记录了这个实体是根据哪个上游实体计算出来的：上游节点是 `notes`，上游实体是 `hello`，读取时的 epoch 是 `demo`，以及当时那份上游实体的正文连同用户 tag 算出的 sha256 哈希值（sha256 是一种常用的哈希算法，结果是 64 个十六进制字符，上图只显示了开头几位）。docorder 判断这个结果是否仍然有效，依靠的就是这份记录。`notes` 节点是 source 类型，它没有上游，所以它的实体里没有这个键。

#### 再跑一次

如果什么都不修改，再执行一次 `run.py`，会发生下面的事情：`notes` 节点重新读取输入目录，`hello` 的正文和 tag 仍然没有变化；轮到 `prompt` 节点时，docorder 把 `tag.json` 里 `upstream` 记录的哈希值，与 `runs/notes/demo/hello` 当前正文和用户 tag 的哈希值进行比较，发现两者一致，于是认为已有的结果仍然有效，直接保留它，不再重新渲染模板。

如果把已经写出的 `runs/notes/demo/hello/data` 改成 `changed`，或者改同一目录里的 `tag.json`，再执行一次且不传 `start_from_scratch`，`notes` 节点不会重读输入目录，但 `prompt` 节点比较时发现哈希不一致，于是删除旧的 `hello` 实体并重新处理。如果改的是输入目录里的源文件，则必须传入 `start_from_scratch=True`，`notes` 才会读到新内容。如果再往输入目录中放入一个 `bye` 实体目录并从头读取，两个节点都会新建一个名为 `bye` 的实体，而没有变化的 `hello` 会继续保持原样。

需要特别注意相反的情况：如果只修改了模板，而上游实体没有变化，`prompt` 节点的结果并不会更新，因为 `tag.json` 里的 `upstream` 只记录上游实体的正文和用户 tag，并不记录模板的内容。这是当前版本的一个重要边界，下文「本版边界」一节还会再讲。运行中途失败时，道理也是一样的：已经成功写下 `upstream` 的实体，在下一次运行时会因为比较通过而被保留，只有那些还没有完成的实体会被重新处理。

这个例子中出现的名词，包括算子、算子 home、`props.json`、function、作业、节点、epoch、实体、正文、tag 和上游快照，在第二章中都有更完整的定义，后面各章都以它们为基础。

### 设计取舍

第一个取舍是把处理进度保存在每个实体自己的目录里，而不是保存在一个集中的状态数据库里。在上面的例子中，`prompt` 节点的 `hello` 实体是否需要重做，只取决于它 `tag.json` 里的 `upstream` 和上游实体当前的正文与用户 tag，docorder 不需要查询任何数据库，也不依赖上一次运行留在内存中的信息。这样做的好处是，即使换了一个进程、甚至换了一份作业脚本，只要输出根目录和 epoch 不变，就能在上一次的进度上继续运行；使用者也可以直接打开 `runs/` 目录，查看每一步、每个对象的中间结果，排查问题非常方便。相应的代价是，所有状态都必须用文件来表达：docorder 以 `tag.json` 里的 `upstream` 作为一个实体处理完成的标志，它随 `tag.json` 最后写入，如果正文已经写好而 tag 还没来得及写入，进程就退出了，这个实体在下一次运行时会被当作未完成而重新处理。

第二个取舍是把转换逻辑放在可以复用的算子 home 里，而不是直接写在作业脚本里。在上面的例子中，模板文件和 `props.json` 都放在 `homes/prompt/` 中，而 `run.py` 只负责说明使用哪个算子 home、上游是哪个节点、结果写到哪里。这样，同一个算子 home 可以被许多不同的作业引用，每个作业可以通过节点的 `config` 参数覆盖其中的部分参数，例子中的输入目录就是用这种方式传进去的。

第三个取舍是把调度和转换分开。像 `TemplateToPrompt` 这样的 function 只负责一件事：拿到一个上游实体，计算出目标实体的正文和 tag。至于读写实体目录、比较 `tag.json` 里的 `upstream`、清理过时的结果、并行执行和失败重试，都由 docorder 中负责调度的部分完成，这部分称为 runner。由于这种分工，编写一种新的转换时，通常只需要实现一两个方法，而不必关心进度记录、并发和重试这些繁琐的细节。

### 本版边界

在设计作业时，需要了解当前版本的以下几项限制。

每个节点只能有一个上游节点，因此整张作业图由一棵或几棵以 source 节点为根的树组成，不能让一个节点同时读取两个上游节点的结果。如果某一步确实需要合并两路结果，只能在 function 的代码里自己去读取另一路结果的文件，而这部分读取不会被记进快照，另一路结果发生变化时，docorder 不会因此自动重做这个实体。

docorder 按节点逐个执行，一个节点的一次完整执行称为一个 stage。一个节点必须处理完本 epoch 中的全部实体，它的下游节点才会开始执行；docorder 不支持「上游刚处理完一个实体，下游就立即开始处理这个实体」这种流水线式的执行方式。

并行执行只发生在一台机器上，依靠的是 Python 标准库提供的线程池，也就是在当前进程里启动若干个线程分担工作；docorder 不支持把任务分发到多台机器上执行。

上游快照覆盖上游的正文和用户 tag，但不覆盖模板、参数或代码。如果修改了模板、`props.json` 中的参数、function 的代码或者它调用的外部工具，而上游实体没有变化，docorder 不会察觉到这些修改，旧的结果会被保留下来。要让这类修改生效，需要手动删除相应的输出目录，或者换一个新的 epoch 运行。

换一个新的 epoch，意味着所有节点都从空目录开始重新计算。旧 epoch 下的结果既不会被新 epoch 复用，也不会被自动清理，不再需要时要由使用者手动删除。

## 二、核心概念与术语

本章给出 docorder 中每个概念的准确定义。第一章的例子已经让这些概念各自露过面，这里会进一步说明它们由谁创建、保存在哪里、能存在多久，以及彼此之间是什么关系。

### 实体

实体是 docorder 处理的基本单位，它表示「某一个对象在某一个步骤中的结果」。同一个对象经过三个步骤，就会在三个节点下各有一个实体。在磁盘上，一个实体就是一个目录，它位于某个节点的输出目录下、某个 epoch 子目录之中，目录的名字就是实体的名字。

```text
<输出根目录>/<节点名>/<epoch>/<实体名>/
  data            正文，UTF-8 编码的文本
  tag.json        附加信息，一个 JSON 对象；有上游时含 upstream 快照
```

`data` 文件保存实体的正文。正文的含义取决于产生它的步骤：在读取目录的步骤里，它是原始文件的内容；在渲染模板的步骤里，它是渲染出来的文本；在运行外部命令的步骤里，它是命令的输出。docorder 在调度时只要求正文是一段文本，并不关心其中的格式，所以正文可以是普通文字、Markdown、JSON 或者任何其它文本格式，但不能是图片这样的二进制数据。

`tag.json` 保存实体的附加信息，它必须是一个 JSON 对象，也就是由若干「键: 值」组成的结构。附加信息里有哪些键，主要由产生这个实体的 function 决定，它的主要用途是给下游步骤提供额外的数据，例如在模板中引用原始文件名，或者根据某个字段做筛选。docorder 自己还管理两个键。`upstream` 是直接上游实体此刻的快照；下游实体会带上上游的整份附加信息，所以写出前一定要重置这个键，并丢掉可能残留的 `current`。`global_prop` 则把一些数据沿着作业图一路传到末端。第三章「填写与写出」一节会详细说明。

实体的名字必须能够安全地作为一层目录名使用，因此有以下要求：名字不能为空；名字的开头和结尾不能有空白字符；名字中不能含有斜杠 `/` 或反斜杠 `\`；名字不能是 `.` 或 `..`；名字也不能以 `.` 或 `_` 开头，因为以这两个字符开头的名字被留给了 docorder 的标记文件和运行时的临时文件。此外，只有包含 `data` 文件或 `tag.json` 文件的目录才会被认作实体，空目录和更深层的目录都不算。

### 上游快照

上游快照写在 `tag.json` 的 `upstream` 里，它记录了「这个实体是根据哪些上游实体的哪个版本计算出来的」。一个上游时是一条记录，没有或多个上游时是列表。每条记录有四个字段：`operator` 是上游节点的名字，`name` 是上游实体的名字，`epoch` 是读取时所在的 epoch，`hash` 是那份上游实体的正文连同用户 tag（不含 `upstream` 和残留的 `current`）算出的 sha256 哈希值，写成十六进制。大多数步骤的每个输出只依赖一个上游实体，所以快照里只有一条记录；只有把一批实体合并成一个的 reduce 类步骤，快照里才会有多条记录，每个参与合并的上游实体各占一条。

快照只覆盖上游的正文和用户 tag。手动改上游实体的 `data` 或 `tag.json`，下一次运行会让依赖它的下游重做；而本算子的参数或模板变了、function 的代码变了，都不会让快照失配——这正是下一节「算子本身变了怎么办」要处理的情况。

上游快照是 docorder 判断一个结果是否仍然有效的唯一依据。对于有上游的实体，只有当 `tag.json` 里的 `upstream` 已经写下，并且其中的记录与上游的当前状态完全吻合时，这个实体才被视为已经完成；即使正文已经写好，只要 tag 里还没有这份快照，这个实体仍然被视为未完成。有一种特殊情况需要留意：如果上游的正文是一个空字符串，记录中的哈希值也会是空的，而空的哈希值在比较时永远不会被认为一致，因此依赖空正文的实体在每次运行时都会被重新处理。

### 算子与算子 home

算子是一种可以重复使用的步骤，例如「读取一个目录中的文件」或者「用某个模板渲染文本」。描述一个算子所需要的文件都放在同一个目录中，这个目录称为算子 home。算子 home 里至少要有一份 `props.json`，其中写明算子的类型 `type`、负责转换的 Python 类 `class`、控制执行方式的调度参数，以及交给转换类使用的默认参数。除此之外，算子 home 里还可以放置这个算子需要的其它文件，按习惯，模板文件放在 `lib/` 子目录中，外部工具的定义放在 `tools/` 子目录中，使用者自己编写的转换代码放在 `primary.py` 文件中。

算子 home 只描述「这一步怎么做」，不记录结果写到哪里，也不属于某一次具体的运行，所以同一个算子 home 可以被很多作业重复使用。docorder 的安装包里不包含任何算子 home，使用者需要把算子 home 放在环境变量 `DOCORDER_HOMES` 所列出的目录中，docorder 会在这些目录里按名字查找它们，具体规则见第六章。

查找规则有两个细节。一个 home 可以直接放在某个列出的目录下，也可以放在其下一层分类目录中，例如 `homes/sources/table_source`；名字以 `.` 或 `_` 开头的分类目录会被跳过。判断一个目录是不是 home，看它里面有没有 `props.json`。查找发生在 `add_operator_node` 被调用的那一刻，因此环境变量必须在这之前设好；找不到时抛出 `FileNotFoundError`，错误信息里会列出搜过的目录。

算子分为五种类型。source 类型没有上游，它从外部数据产生最初的一批实体；map 类型为上游的每一个实体产生一个同名的输出实体；reduce 类型把上游的全部实体合并成一个输出实体；fanout 类型把上游的每一个实体拆分成若干个输出实体；apply 类型不写实体，对上游的每一个实体调用一次 function，function 不能返回值，这个节点也不能再有下游。第七章会逐一介绍这五种类型。

### function

function 是算子 home 的 `props.json` 中 `class` 所指向的那个 Python 类，它承担真正的转换工作。在处理每个实体时，runner 会创建一个新的 function 对象，把上游实体和一个还没有填写内容的目标实体交给它；function 负责为目标实体填好正文和附加信息，然后由 runner 把它们写入磁盘。每种算子类型都有一个对应的 function 基类，使用者编写自己的转换时需要继承相应的基类。docorder 还自带了几个可以直接通过配置使用的 function，例如读取目录的 `DirectorySource` 和渲染 Jinja 模板的 `TemplateToPrompt`，第七章会完整列出它们。

### 作业与节点

作业描述的是「这一次要执行哪些步骤、它们之间的先后关系如何、结果写到哪里」，它是一张有向无环图。有向无环图的意思是：图中的每条连线都有方向，从上游指向下游，并且沿着连线的方向走，永远不会回到出发的地方，也就是说步骤之间不存在循环依赖。作业通过 `Job(name, root)` 创建，其中 `root` 是输出根目录。

作业中的每一个点称为节点，节点通过 `add_operator_node` 方法加入作业。每个节点引用一个算子 home，并且除 source 节点以外，必须指定唯一的一个上游节点。节点还可以通过 `config` 参数覆盖算子 home 中的转换参数，通过 `parallelism` 和 `retry` 参数覆盖调度参数。节点的输出目录总是「输出根目录/节点名」，不能另外指定。同一个算子 home 可以在同一个作业里被多个节点引用，例如用同一个模板算子分别处理两个不同的上游。同一个节点名再次添加时，后一次会替换前一次，不报错。

节点构造时，传入的 `config` 会覆盖到 home 的 function 参数上，写进节点的 `props`。`config` 里的 `class` 会被丢掉，不能用它更换 function。构造完成之后节点不再保留 `config`，对外只暴露 `props`；`parallelism` 和 `retry` 写进 `config` 只会成为 function 参数，调度仍然按 home 里的值或 `add_operator_node` 的同名参数来。

作业对象只存在于一次 Python 进程的内存中，它本身不保存任何处理进度，进度全部保存在各个实体的目录里。正因为进度在实体目录里，换一个进程、甚至换一份作业脚本，只要输出路径和 epoch 相同，都能接着上一次的进度跑。

### epoch 与 stage

epoch 是调用 `execute` 时传入的一个名字，通常使用日期或版本号，例如 `2026-10-16` 或 `v3`。它决定了每个节点输出目录下的那一层子目录，在同一次运行中，所有节点都使用同一个 epoch。换一个新的 epoch，相当于换了一套全新的空目录，所有结果从头计算；使用同一个 epoch 再次运行，则是在上一次的结果和进度上继续工作。

stage 指的是一个节点在一次运行中的执行过程。一次运行会按照作业图中的依赖顺序，依次执行每个节点的 stage；一个 stage 必须处理完本 epoch 中的全部实体，下一个 stage 才会开始。

### runner 与应得名单

runner 是 docorder 中负责调度的部分，调用 `docorder.core.runner.execute` 就是让 runner 开始工作。每个非 source 节点的 stage 开始时，runner 会先读取上游节点在本 epoch 中已有的全部实体，并据此列出应得名单。应得名单回答的问题是：「按照上游当前的状态，这个节点应该有哪些输出实体，每个输出实体又依赖哪些上游实体？」随后，runner 把应得名单与这个节点目录中已经存在的实体逐一比较，决定每个实体应该新建、重做、保留还是删除。第三章会详细讲解这个过程。

### 概念之间的关系

下面这张图先画出概念的层次关系，再用第一章的最小例子对照一遍。

<!-- figure:concepts:start -->
<figure class="figure" id="fig-concepts">
<svg role="img" aria-labelledby="concepts-title concepts-desc" viewBox="0 0 900 560" width="100%" style="max-width:900px">
  <title id="concepts-title">docorder 概念之间的关系</title>
  <desc>算子 home 被作业节点引用，节点在一次运行中写出输出目录，输出目录里包含实体，下游实体的上游快照指回上游实体。</desc>
  <defs>
    <marker id="concepts-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#5e584e"/>
    </marker>
    <marker id="concepts-arrow-teal" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1b4744"/>
    </marker>
    <marker id="concepts-arrow-moss" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1d6842"/>
    </marker>
  </defs>
  <rect width="900" height="560" fill="#f6f1e8"/>
  <path d="M 135 112 L 135 180 L 135 180 L 135 200" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#concepts-arrow)"/>
  <path d="M 395 112 L 395 180 L 427 180 Q 435 180 435 188 L 435 200" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#concepts-arrow)"/>
  <path d="M 135 252 L 135 330" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#concepts-arrow)"/>
  <path d="M 435 252 L 435 330" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#concepts-arrow)"/>
  <path d="M 135 382 L 135 450" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#concepts-arrow)"/>
  <path d="M 435 382 L 435 450" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#concepts-arrow)"/>
  <path d="M 230 226 L 260 226 L 260 182 Q 260 174 268 174 L 302 174 Q 310 174 310 182 L 310 218 Q 310 226 318 226 L 340 226" fill="none" stroke="#1b4744" stroke-width="1" marker-end="url(#concepts-arrow-teal)"/>
  <path d="M 340 476 L 310 476 L 310 430 Q 310 422 302 422 L 278 422 Q 270 422 270 430 L 270 468 Q 270 476 262 476 L 230 476" fill="none" stroke="#1b4744" stroke-width="1" stroke-dasharray="5,4" marker-end="url(#concepts-arrow-teal)"/>
  <rect x="120" y="128" width="30" height="16" rx="2" fill="#f6f1e8"/>
  <text x="135" y="140" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">引用</text>
  <rect x="380" y="128" width="30" height="16" rx="2" fill="#f6f1e8"/>
  <text x="395" y="140" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">引用</text>
  <rect x="120" y="266" width="30" height="16" rx="2" fill="#f6f1e8"/>
  <text x="135" y="278" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">写出</text>
  <rect x="120" y="396" width="30" height="16" rx="2" fill="#f6f1e8"/>
  <text x="135" y="408" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">包含</text>
  <rect x="274" y="148" width="30" height="16" rx="2" fill="#f6f1e8"/>
  <text x="304" y="160" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="end">上游</text>
  <rect x="257" y="396" width="66" height="16" rx="2" fill="#f6f1e8"/>
  <text x="290" y="408" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">快照指回上游</text>
  <rect x="40" y="60" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="60" width="190" height="52" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <rect x="48" y="67" width="28" height="14" rx="2" fill="transparent" stroke="#5e584e" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="62" y="77" fill="#5e584e" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">静态</text>
  <text x="135" y="84" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">算子 home</text>
  <text x="135" y="101" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">notes_source</text>
  <rect x="300" y="60" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="60" width="190" height="52" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <rect x="308" y="67" width="28" height="14" rx="2" fill="transparent" stroke="#5e584e" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="322" y="77" fill="#5e584e" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">静态</text>
  <text x="395" y="84" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">算子 home</text>
  <text x="395" y="101" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">prompt</text>
  <rect x="40" y="200" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="200" width="190" height="52" rx="6" fill="rgba(27,71,68,0.08)" stroke="#1b4744" stroke-width="1"/>
  <rect x="48" y="207" width="28" height="14" rx="2" fill="transparent" stroke="#1b4744" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="62" y="217" fill="#1b4744" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">作业</text>
  <text x="135" y="224" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">节点 notes</text>
  <text x="135" y="241" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">source · 无上游</text>
  <rect x="340" y="200" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="340" y="200" width="190" height="52" rx="6" fill="rgba(27,71,68,0.08)" stroke="#1b4744" stroke-width="1"/>
  <rect x="348" y="207" width="28" height="14" rx="2" fill="transparent" stroke="#1b4744" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="362" y="217" fill="#1b4744" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">作业</text>
  <text x="435" y="224" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">节点 prompt</text>
  <text x="435" y="241" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">map · 上游 notes</text>
  <rect x="40" y="330" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="330" width="190" height="52" rx="6" fill="#fffdf8" stroke="#5e584e" stroke-width="1"/>
  <text x="135" y="360" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">runs/notes/demo/</text>
  <rect x="340" y="330" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="340" y="330" width="190" height="52" rx="6" fill="#fffdf8" stroke="#5e584e" stroke-width="1"/>
  <text x="435" y="360" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">runs/prompt/demo/</text>
  <rect x="40" y="450" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="450" width="190" height="52" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="48" y="457" width="28" height="14" rx="2" fill="transparent" stroke="#5e584e" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="62" y="467" fill="#5e584e" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">结果</text>
  <text x="135" y="474" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">实体 hello</text>
  <text x="135" y="491" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">data · tag.json</text>
  <rect x="340" y="450" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="340" y="450" width="190" height="52" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="348" y="457" width="28" height="14" rx="2" fill="transparent" stroke="#5e584e" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="362" y="467" fill="#5e584e" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">结果</text>
  <text x="435" y="474" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">实体 hello</text>
  <text x="435" y="491" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">data · tag.json</text>
  <text x="888" y="90" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="end">算子 home</text>
  <text x="888" y="230" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="end">作业节点</text>
  <text x="888" y="360" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="end">输出目录</text>
  <text x="888" y="480" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="end">实体</text>
</svg>
<figcaption><span class="fig-label">图 1</span> 概念之间的关系：算子 home 被节点引用，节点写出输出目录，输出目录里是实体，下游实体的上游快照指回上游。</figcaption>
</figure>
<!-- figure:concepts:end -->

```text
DOCORDER_HOMES = homes/
  homes/notes_source/   算子 home：props.json（type=source, class=DirectorySource）
  homes/prompt/         算子 home：props.json（type=map, class=TemplateToPrompt）, lib/note.jinja
                          │ 被节点引用
                          ▼
作业 Job("hello", runs/)
  ├─ 节点 notes   ── 算子 home: notes_source ── config: directory ── 输出: runs/notes/
  └─ 节点 prompt  ── 算子 home: prompt       ── 上游: notes        ── 输出: runs/prompt/

execute(job, "demo")      epoch 为 demo，每个节点各执行一个 stage
  runs/notes/demo/hello/        实体：data, tag.json
  runs/prompt/demo/hello/       实体：data, tag.json（含 upstream）
                                  └─ 上游快照：记录 runs/notes/demo/hello 正文的哈希值
```

### 术语对照

| 术语 | 英文或代码中的名字 | 含义 |
| --- | --- | --- |
| 实体 | entity | 一个对象在某个节点、某个 epoch 下的结果，在磁盘上是一个目录 |
| 正文 | `data` | 实体的主要内容，一段文本 |
| tag | `tag.json` | 实体的附加信息，一个 JSON 对象 |
| 上游快照 | `tag.json` 的 `upstream` | 实体读取过的上游实体，以及当时上游正文与用户 tag 的哈希值 |
| 算子 | operator | 一种可以重复使用的步骤，属于五种类型之一 |
| 算子 home | operator home | 存放一个算子全部文件的目录，必须包含 `props.json` |
| function | function | `props.json` 中 `class` 指向的、执行转换的 Python 类 |
| 作业 | `Job` | 一次运行要执行的步骤及其先后关系 |
| 节点 | node | 作业中引用某个算子的一个步骤 |
| epoch | epoch | 一批结果的名字，也是输出目录中的一层子目录 |
| stage | stage | 一个节点在一次运行中的完整执行 |
| runner | runner | docorder 中负责调度的部分 |
| 应得名单 | expected names | 一个节点按上游当前状态应有的输出实体，以及每个输出依赖的上游实体 |

## 三、工作流程

本章按时间顺序讲解调用 `execute(job, epoch, start_from_scratch=False)` 之后发生的事情。整个过程分为两个阶段：第一阶段是装配，检查整个作业是否正确，并准备好每个节点要用的转换类；第二阶段是按依赖顺序逐个执行每个节点的 stage。在第二阶段中，只要任何一个 stage 抛出了异常，整次运行就会在这里停止，排在后面的节点不会开始执行。

### 装配

装配阶段首先检查作业图本身是否合理。以下几种情况会被拒绝：节点之间存在循环依赖；某个节点指定的上游节点在作业中并不存在；某个节点把自己指定为上游；apply 节点没有上游；有节点把 apply 节点当作上游；两个节点的输出目录解析后实际上是同一个目录；以及一个节点的输出目录位于另一个节点的输出目录之中。后两种情况可以由符号链接或带 `/` 的节点名造成。

作业图检查通过之后，runner 为每个节点加载 `props.json` 中 `class` 指向的 Python 类，并尝试创建一个对象。如果这个类找不到，或者它不是该算子类型对应基类的子类，或者它还有必须实现却没有实现的方法，运行就会以 `OperatorValidationError` 错误停止。由于这些检查都发生在任何节点开始执行之前，即使只是最后一个节点的类名写错了，也会在一开始就被发现，前面的节点不会白白执行一遍。

装配还为每个输出目录建立一份本 epoch 的实体表。同一个目录在一次运行里只有一份表，节点写出时更新它，下游把它当作上游来读。

各节点的执行顺序由作业图决定：一个节点总是排在它的上游节点之后，这种顺序称为拓扑顺序。当有几个节点同时满足执行条件时，先加入作业的节点先执行。

### 一个 stage 的经过

source 节点的 stage 与其它节点有很大不同，本章最后单独说明。本节描述 map、reduce 和 fanout 节点的 stage，它依次经过以下几个步骤。apply 节点不写实体，应得名单始终为空，但 `execute` 仍会调用 function。

<!-- figure:stage:start -->
<figure class="figure" id="fig-stage">
<svg role="img" aria-labelledby="stage-title stage-desc" viewBox="0 0 900 640" width="100%" style="max-width:900px">
  <title id="stage-title">docorder 中一个 stage 的经过</title>
  <desc>一个 stage 依次建立输出目录、列出应得名单、与磁盘上的实体比较、清理与预留、调用 function、处理附加信息，最后写 data 与 tag.json；比较通过的实体原样保留。</desc>
  <defs>
    <marker id="stage-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#5e584e"/>
    </marker>
    <marker id="stage-arrow-teal" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1b4744"/>
    </marker>
    <marker id="stage-arrow-moss" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1d6842"/>
    </marker>
  </defs>
  <rect width="900" height="640" fill="#f6f1e8"/>
  <path d="M 450.0 96 L 450.0 124" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#stage-arrow)"/>
  <path d="M 450.0 172 L 450.0 200" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#stage-arrow)"/>
  <path d="M 450.0 248 L 450.0 276" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#stage-arrow)"/>
  <path d="M 450.0 340 L 450.0 372" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#stage-arrow)"/>
  <path d="M 450.0 436 L 450.0 468" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#stage-arrow)"/>
  <path d="M 450.0 532 L 450.0 564" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#stage-arrow)"/>
  <path d="M 300 224.0 L 260 224.0" fill="none" stroke="#1d6842" stroke-width="1" marker-end="url(#stage-arrow-moss)"/>
  <rect x="265" y="200" width="30" height="16" rx="2" fill="#f6f1e8"/>
  <text x="280" y="212" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">通过</text>
  <rect x="300" y="48" width="300" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="48" width="300" height="48" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="76" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">建立输出目录</text>
  <rect x="300" y="124" width="300" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="124" width="300" height="48" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="146" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">列出应得名单</text>
  <text x="450" y="163" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">读上游在本 epoch 的实体</text>
  <rect x="300" y="200" width="300" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="200" width="300" height="48" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="228" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">与磁盘上的实体比较</text>
  <rect x="300" y="276" width="300" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="276" width="300" height="64" rx="6" fill="rgba(27,71,68,0.08)" stroke="#1b4744" stroke-width="1"/>
  <text x="450" y="306" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">清理与预留</text>
  <text x="450" y="323" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">删掉要删的 · 留空 tag.json</text>
  <rect x="300" y="372" width="300" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="372" width="300" height="64" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="402" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">调用 function</text>
  <text x="450" y="419" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">transform_data → transform_props</text>
  <rect x="300" y="468" width="300" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="468" width="300" height="64" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="498" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">处理附加信息</text>
  <text x="450" y="515" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">合并 global_prop · 重置 upstream</text>
  <rect x="300" y="564" width="300" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="564" width="300" height="48" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="592" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">写 data，再写 tag.json</text>
  <rect x="40" y="200" width="220" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="200" width="220" height="64" rx="6" fill="rgba(29,104,66,0.08)" stroke="#1d6842" stroke-width="1"/>
  <text x="150" y="230" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">比较通过</text>
  <text x="150" y="247" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">原样保留，不再调用 function</text>
  <rect x="640" y="176" width="240" height="208" rx="6" fill="#f6f1e8"/>
  <rect x="640" y="176" width="240" height="208" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="654" y="199" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">比较的四种结局</text>
  <rect x="654" y="226" width="8" height="8" rx="2" fill="#1d6842"/>
  <text x="668" y="234" fill="#1c1915" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">比较通过</text>
  <text x="668" y="249" fill="#5e584e" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">保留，不调用 function</text>
  <rect x="654" y="268" width="8" height="8" rx="2" fill="#1c1915"/>
  <text x="668" y="276" fill="#1c1915" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">名单里有、目录里没有</text>
  <text x="668" y="291" fill="#5e584e" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">新建并调用 function</text>
  <rect x="654" y="310" width="8" height="8" rx="2" fill="#1c1915"/>
  <text x="668" y="318" fill="#1c1915" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">快照或 depend 不吻合</text>
  <text x="668" y="333" fill="#5e584e" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">清空后重新处理</text>
  <rect x="654" y="352" width="8" height="8" rx="2" fill="#9a3412"/>
  <text x="668" y="360" fill="#1c1915" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">名单里没有、目录里有</text>
  <text x="668" y="375" fill="#5e584e" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">删除整个实体目录</text>
  <text x="40" y="28" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">stage 开始</text>
  <text x="40" y="630" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">stage 结束</text>
</svg>
<figcaption><span class="fig-label">图 2</span> 一个 stage 的经过：比较之后，保留的实体就此跳过，其余的走完清理、调用与写出。</figcaption>
</figure>
<!-- figure:stage:end -->

stage 开始时，runner 创建这个节点的输出目录。

#### 列出应得名单

接下来，runner 读取上游节点在本 epoch 中已有的全部实体，列出本节点的应得名单。不同类型的算子，应得名单的列法不同。对于 map 节点，上游的每个实体都对应一个同名的输出实体，这个输出实体只依赖那一个上游实体。对于 fanout 节点，runner 会调用 function 的 `output_names` 方法，询问每个上游实体要拆分出哪些输出实体，每个输出实体依赖产生它的那个上游实体。对于 reduce 节点，应得名单永远只有一项：一个名字由参数 `output` 决定的输出实体（未设置时名为 `result`），它依赖上游的全部实体。apply 节点不写实体，应得名单是空的。

如果应得名单是空的，这个 stage 就不比较、不删除实体。map 和 fanout 节点在上游一个实体都没有的时候就会出现这种情况，也不会调用 function，本节点已有的实体全部保持原样。apply 节点的应得名单始终为空，但 `execute` 仍会对每个上游实体调用 function。reduce 节点的应得名单不会为空，即使上游一个实体都没有，它仍然会产生那一个输出实体，只是交给 function 的上游实体列表是空的。

#### 与磁盘上的实体比较

应得名单不为空时，runner 读取本节点目录中已有的实体，把它们与应得名单逐一比较，分成以下几类。应得名单中有、但目录里还没有的实体，需要新建。目录里有、但应得名单中已经没有的实体，例如上游已经删除了对应的对象，需要删除。两边都有的实体，则要用它 `tag.json` 里的 `upstream` 与上游的当前状态作比较，只要下面任意一条成立，就需要重做：`upstream` 不存在或者内容无效；快照中记录的上游实体名字与应得名单中列出的不一致；记录中的节点名不是当前的上游节点；记录中的 epoch 不是本次运行的 epoch；记录中的哈希值为空，或者与上游实体当前正文和用户 tag 的哈希值不同；这个实体自己的 `tag.json` 无法读取或者不是 JSON 对象。上游比较通过之后，如果这个算子声明了 `fingerprint.depend`，还要核对依赖文件的哈希，见下面「指纹」一节。两处都通过的实体比较通过，会被原样保留，本次运行不会为它调用 function。`fingerprint.record` 不参与这次比较。

#### 指纹

上游快照只能覆盖「上游实体的正文和用户 tag」。如果某个算子还会读取上游实体没有携带的外部文件，例如一个表定义旁边的 `.sql` 文件，就要用 `fingerprint` 来声明这类依赖。

`props.json` 或节点 `config` 里的 `fingerprint` 是一个对象，最多两段：`record` 和 `depend`。每一段都是对象，键是路径模板，写在配置里的值不使用。落到实体 tag 的 `fingerprint` 用同样的键，值是文件字节的 sha256。这个键属于用户 tag，因此算进正文哈希。

模板用 `{name}`、`{staging}` 和算子参数里的字符串填空。`{name}` 是实体名，始终覆盖同名参数。`{staging}` 是作业的 `.staging` 目录，同名的字符串参数覆盖它。相对路径相对作业根目录解析。`record` 在 tag 已经写好之后渲染，所以还能用 tag 里的字符串字段，同名参数覆盖 tag。`depend` 在 function 运行前渲染，只能用 `{name}`、`{staging}` 和参数。

`record` 是算子自己写下、或者 source 指向的文件。map、reduce、fanout 在 `transform_props` 之后、快照之前记账；source 在 `emit` 交出正文和 tag 之后记账，并且仍然只在 `start_from_scratch` 时发生。这段哈希变了，不会让本算子重做。写完后文件必须存在，否则这一段以 `FatalError` 失败。function 没有留下正文、但声明了 `record` 时，runner 会把正文写成一个换行，避免空正文的哈希永远对不上；function 自己写了正文就保持不动。

`depend` 是本算子读取、上游实体却没有携带的文件。它在清场前渲染，并与 tag 里记下的哈希比较：键集合不同，或任一哈希不同，这个实体重做。成功写出后再更新，让下一次对的是这次看到的文件。文件不存在或占位符没有值时，这一段以 `FatalError` 停下，发生在清场之前，已有实体不会被删掉。

source 配了 `depend`，或者 apply 配了 `fingerprint`，作业在装配时以 `JobValidationError` 拒绝。source 不做运行前比较，apply 没有自己的实体。

#### 清理与预留

比较完成之后、开始调用任何 function 之前，runner 会对整个 stage 的目录做一次集中整理：先删除所有需要删除的实体目录和所有需要重做的实体目录，然后为每个需要新建或重做的实体建立一个只包含空 `tag.json` 的目录作为占位。这意味着，一旦 stage 开始执行，所有需要重做的实体都已经失去了它们的旧正文；如果这个 stage 在中途失败，那些还没有轮到处理的实体会停留在只有空 `tag.json` 的状态，它们的 `tag.json` 里没有 `upstream`，因此在下一次运行时会被识别为未完成并重新处理。

#### 填写与写出

对于每个等待处理的实体，runner 先调用 function 的 `transform_data` 方法填写正文，再调用 `transform_props` 方法填写附加信息。function 填写的正文必须是字符串，附加信息必须是字典（也就是 JSON 对象），否则这个实体会以 `FatalError` 错误失败。

function 填写完成后，runner 会处理附加信息中的 `global_prop` 和 `upstream`。如果上游实体的附加信息里有一个名为 `global_prop` 的对象，runner 会把它合并到目标实体附加信息的 `global_prop` 中；如果目标实体自己已经写了同名的键，以目标实体自己写的值为准。对于 reduce 节点，参与合并的上游实体有很多个，runner 按实体名字的顺序依次合并，排在后面的实体中的值会覆盖排在前面的。这个机制的意义在于，放进 `global_prop` 的数据可以从作业的起点一直传到末端，即使中间某个 function 没有把上游的附加信息复制下来，这些数据也不会丢失。

`upstream` 一定被重置，残留的 `current` 会被丢掉。上游实体会交给下游 function，function 常常把上游的整份附加信息复制过来，其中已经有上游自己的 `upstream`。runner 不保留这项：目标的 `upstream` 改成直接上游实体此刻的快照（只有一个上游时是这条记录，没有或多个上游时是这些记录组成的列表）。这条记录有四个字段：`operator` 是上游节点名，`name` 是上游实体名，`epoch` 是本次 epoch，`hash` 是上游实体正文连同用户 tag 的 sha256。source 节点没有上游，不写 `upstream`。

最后，runner 按固定顺序写入实体目录：先写 `data`，再写 `tag.json`。每个文件都先写到同一目录下的一个 `.tmp` 临时文件中，写完之后再替换成正式的文件名，所以不会出现一个文件只写了一半的情况。`tag.json` 最后写入，正是为了保证只有在正文和快照都写好之后，这个实体才会被视为完成。目录里若留着旧的 `upstream.json`，写出后会删掉。

每个 stage 在标准错误输出上打印一条进度条，标题是节点名。map、fanout、reduce 的总数是本段应得的实体个数，已经比较通过、本轮跳过的也会计入。apply 的总数是这次调用的上游实体个数。source 在 `emit` 时逐条推进，开始时不知道总数。并行的 map 和 fanout 共用这一条进度条。

### 并行与重试

map 和 fanout 节点可以利用多个线程同时处理实体，以缩短总的运行时间。具体做法是：runner 把等待处理的实体列表切成连续的若干段，段数不超过节点的 `parallelism` 参数，也不超过等待处理的实体个数。如果只切出一段，就在当前线程中按顺序逐个处理；如果切出了多段，就为每一段启动一个工作线程，每个线程在自己那一段内按顺序处理。这些线程共享当前进程里的算子和参数。reduce 节点只有一个输出实体，source 节点的处理方式也不同，所以这两类节点不会被切分。

工作线程通过 Python 标准库中的 `ThreadPoolExecutor` 启动，不另起进程，因此启动作业的代码不必为了并行而写在 `if __name__ == "__main__":` 之下，`config` 也不必能被 pickle。

在并行执行时，如果某一段中有一个实体最终失败，这一段中排在它后面的实体就不会再被处理，但其它段会继续执行到结束，所有段都结束之后，异常才会被抛出。因此，并行运行失败之后，磁盘上已经完成的实体可能比你预想的要多一些。

每个实体的处理都按照节点的 `retry` 参数进行重试。如果 function 抛出的是 `FatalError`，说明出现了重试也无法解决的问题，例如配置缺失或者模板写错，此时不会重试，这个 stage 立即失败；如果抛出的是其它类型的异常，例如外部命令返回了错误，runner 会等待一段时间后再试一次，等待的秒数是 `backoff_seconds` 乘以已经尝试过的次数，直到尝试的总次数达到 `max_attempts` 为止。一个实体只要成功写下了 `tag.json` 里的 `upstream`，就会一直保留在目录中；用同一个作业和同一个 epoch 再次运行时，这些实体会因为比较通过而被跳过，runner 只会处理剩下的实体。

### source 节点的 stage

source 节点没有上游，所以它不列应得名单，也不做上面那样的比较。它是否重新产生实体，只取决于本次调用 `execute` 时是否传入了 `start_from_scratch=True`。

如果没有传入，source 节点不会调用 function，也不会改动已有的实体，只确保输出目录和标记文件存在，下游节点读取的是它上一次留下的实体。需要注意的是，如果在一个全新的 epoch 上第一次运行时就没有传入这个参数，source 节点的目录是空的，下游看到的也就是一个空的上游：map 和 fanout 节点什么都不会做，reduce 节点会产生一个基于空输入的结果。

如果传入了，runner 会调用 function 的 `emit` 方法，逐条读取它交出的记录，每读到一条就写成一个实体。每条记录的实体名必须符合命名规则，同一个名字不能出现两次，正文必须是字符串，附加信息必须是字典。写入时，runner 直接覆盖实体目录中原有的 `data` 和 `tag.json`，并删除可能残留的 `upstream.json`。source 不写 `upstream`。全部记录都写完之后，本 epoch 中这一次没有被交出的实体会被删除，这样 source 节点目录中的实体就与外部数据完全一致了。source 节点的 `retry` 参数只作用于「把一条记录写入磁盘」这一个动作；如果 `emit` 方法本身抛出了异常，例如某个输入文件不是合法的 UTF-8 文本，这个异常不会被重试，此时那些还没来得及交出的旧实体也不会被删除，等到下一次带 `start_from_scratch=True` 的运行成功完成时，目录内容才会恢复一致。

### 再次运行时的判定

下表把上面介绍的各种情况集中在一起，说明在同一个 epoch 上再次运行时，每个实体会被如何处理。

<!-- figure:rerun:start -->
<figure class="figure" id="fig-rerun">
<svg role="img" aria-labelledby="rerun-title rerun-desc" viewBox="0 0 900 640" width="100%" style="max-width:900px">
  <title id="rerun-title">同一个 epoch 上再次运行时的判定</title>
  <desc>应得名单里有、目录里没有的实体被新建；目录里有、名单里没有的被删除；两边都有时，上游快照和 depend 都吻合的实体被保留，其余清空后重做。</desc>
  <defs>
    <marker id="rerun-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#5e584e"/>
    </marker>
    <marker id="rerun-arrow-teal" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1b4744"/>
    </marker>
    <marker id="rerun-arrow-moss" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1d6842"/>
    </marker>
  </defs>
  <rect width="900" height="640" fill="#f6f1e8"/>
  <path d="M 200 152 L 200 208" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#rerun-arrow)"/>
  <path d="M 200 272 L 200 328" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#rerun-arrow)"/>
  <path d="M 380 120 L 560 120" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#rerun-arrow)"/>
  <path d="M 380 240 L 560 240" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#rerun-arrow)"/>
  <path d="M 380 376 L 560 376" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#rerun-arrow)"/>
  <path d="M 290 424 L 290 468 L 560 468" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#rerun-arrow-moss)"/>
  <path d="M 110 424 L 110 540 L 560 540" fill="none" stroke="#9a3412" stroke-width="1" marker-end="url(#rerun-arrow)"/>
  <rect x="208" y="158" width="21" height="16" rx="2" fill="#f6f1e8"/>
  <text x="208" y="170" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="start">是</text>
  <rect x="208" y="278" width="21" height="16" rx="2" fill="#f6f1e8"/>
  <text x="208" y="290" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="start">是</text>
  <rect x="449.5" y="96" width="21" height="16" rx="2" fill="#f6f1e8"/>
  <text x="460" y="108" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">否</text>
  <rect x="449.5" y="216" width="21" height="16" rx="2" fill="#f6f1e8"/>
  <text x="460" y="228" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">否</text>
  <rect x="449.5" y="352" width="21" height="16" rx="2" fill="#f6f1e8"/>
  <text x="460" y="364" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">否</text>
  <rect x="298" y="444" width="21" height="16" rx="2" fill="#f6f1e8"/>
  <text x="298" y="456" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="start">是</text>
  <rect x="118" y="484" width="82.65" height="16" rx="2" fill="#f6f1e8"/>
  <text x="118" y="496" fill="#9a3412" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="start">depend 文件缺失</text>
  <rect x="40" y="88" width="340" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="88" width="340" height="64" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="124" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">应得名单里有它吗？</text>
  <rect x="40" y="208" width="340" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="208" width="340" height="64" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="244" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">目录里已经有它吗？</text>
  <rect x="40" y="328" width="340" height="96" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="328" width="340" height="96" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="374" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">快照吻合，且 depend 吻合或未声明？</text>
  <text x="210" y="391" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">名字 / 节点名 / epoch / 哈希都要对</text>
  <rect x="560" y="92" width="300" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="92" width="300" height="56" rx="6" fill="rgba(154,52,18,0.08)" stroke="#9a3412" stroke-width="1"/>
  <text x="710" y="124" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">删除整个实体目录</text>
  <rect x="560" y="212" width="300" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="212" width="300" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="710" y="244" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">新建 · 调用 function</text>
  <rect x="560" y="348" width="300" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="348" width="300" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="710" y="380" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">清空后重新处理</text>
  <rect x="560" y="440" width="300" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="440" width="300" height="56" rx="6" fill="rgba(29,104,66,0.08)" stroke="#1d6842" stroke-width="1"/>
  <text x="710" y="472" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">保留 · 不调用 function</text>
  <rect x="560" y="512" width="300" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="512" width="300" height="56" rx="6" fill="rgba(154,52,18,0.08)" stroke="#9a3412" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="710" y="544" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">FatalError · 不清场</text>
  <text x="40" y="596" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">应得名单为空时不比较：map / fanout 上游为空、apply 节点都属这一类；</text>
  <text x="40" y="614" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">reduce 节点的上游为空时照常比较，function 收到一个空列表。</text>
</svg>
<figcaption><span class="fig-label">图 3</span> 再次运行时的判定：三个判定框决定每个实体是被保留、重做、新建还是删除。</figcaption>
</figure>
<!-- figure:rerun:end -->

| 情况 | 处理方式 |
| --- | --- |
| 应得名单中有，目录中没有 | 新建，并调用 function 处理 |
| 目录中有，应得名单中没有 | 删除整个实体目录 |
| 两边都有，上游快照与上游当前状态吻合，且 `depend` 吻合或未声明 | 保留，不调用 function |
| 两边都有，没有上游快照、上游快照无效或 `tag.json` 无效 | 清空后重新处理 |
| 两边都有，上游实体名字、节点名、epoch 或实体哈希值不一致 | 清空后重新处理 |
| 两边都有，上游吻合，但 `fingerprint.depend` 的键或哈希不一致 | 清空后重新处理 |
| 声明了 `depend`，但文件不存在或模板占位符没有值 | 以 `FatalError` 停下，不清场 |
| map 或 fanout 节点的上游一个实体都没有 | 不做比较，目录保持原样 |
| reduce 节点的上游一个实体都没有 | 照常比较，function 收到一个空列表 |
| apply 节点 | 不比较实体。每次都对当前上游的每个实体调用 function；上游为空时只调用 `finish` |
| source 节点，未传入 `start_from_scratch=True` | 不调用 function，实体保持原样 |

### 常见的再跑场景

从这张表可以推出几条日常使用中最常用的规则。

#### 上一次停在半路

失败那一段里已经写好上游快照的实体会留下；只有空 `tag.json`、还没有快照的实体会重做；失败节点的下游上一次根本没开始，这次从头执行。失败节点之前的非 source 节点，只要上游没变，实体都比较通过，不会重新调用 function。

#### 上游实体变了

上游实体的正文或用户 tag 变了，依赖它们的下游实体会重做。重做的实体若写出与上次相同的正文和用户 tag，它的下游比较通过，重做就在这里停住；否则继续沿图向下传播。对 reduce 来说，上游任何一个实体的正文或用户 tag 变化、新增或消失，都会让那一个输出重做。不传 `start_from_scratch` 时，也可以直接改已经写出的上游实体目录里的 `data` 或 `tag.json`，下游会在下一次运行时重做。

#### 上游实体增减

上游新出现的实体，在 map 下游表现为新建；上游消失的实体，在 map 下游表现为删除。唯一的例外是上游一个实体都不剩：map 与 fanout 的应得名单为空，下游目录保持原样，不会因此被清空。

#### 算子本身变了

模板、参数、function 代码或外部工具变了，而上游实体没变时，上游快照仍然吻合，旧结果会被留下。要让新逻辑生效，删除该节点的 `<epoch>/` 目录或其中的某些实体目录，或者换一个 epoch。只删掉某个实体 `tag.json` 里的 `upstream` 也能让它重做，且保留目录给人查看，直到重做开始。

#### source 不从头生成

不传 `start_from_scratch=True` 时，源文件的改动不会进入 source 的实体，下游自然也看不到。只有传了它，source 才重读输入，变化才从图的根部开始传播。

### 一次运行留下的目录

一次运行结束后，输出根目录下是这样：

<!-- figure:layout:start -->
<figure class="figure" id="fig-layout">
<svg role="img" aria-labelledby="layout-title layout-desc" viewBox="0 0 900 500" width="100%" style="max-width:900px">
  <title id="layout-title">一次运行留下的目录</title>
  <desc>输出根目录下有 .staging 与每个节点各自的目录；节点目录按 epoch 分层，epoch 层下面是实体目录，实体目录里有 data 与 tag.json 两个文件。</desc>
  <defs>
    <marker id="layout-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#5e584e"/>
    </marker>
    <marker id="layout-arrow-teal" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1b4744"/>
    </marker>
    <marker id="layout-arrow-moss" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1d6842"/>
    </marker>
  </defs>
  <rect width="900" height="500" fill="#f6f1e8"/>
  <path d="M 150 84 L 150 104 L 138 104 Q 130 104 130 112 L 130 124" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#layout-arrow)"/>
  <path d="M 150 84 L 150 104 L 442 104 Q 450 104 450 112 L 450 124" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#layout-arrow)"/>
  <path d="M 130 168 L 130 208" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#layout-arrow)"/>
  <path d="M 450 168 L 450 188 L 408 188 Q 400 188 400 196 L 400 208" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#layout-arrow)"/>
  <path d="M 400 252 L 400 272 L 368 272 Q 360 272 360 280 L 360 292" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#layout-arrow)"/>
  <path d="M 360 336 L 360 356 L 268 356 Q 260 356 260 364 L 260 376" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#layout-arrow)"/>
  <path d="M 360 336 L 360 356 L 437 356 Q 445 356 445 364 L 445 376" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#layout-arrow)"/>
  <rect x="40" y="40" width="220" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="40" width="220" height="44" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="150" y="66" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;输出根目录&gt;/</text>
  <rect x="40" y="124" width="180" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="124" width="180" height="44" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="130" y="150" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">.staging/</text>
  <rect x="360" y="124" width="180" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="360" y="124" width="180" height="44" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="450" y="150" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;节点名&gt;/</text>
  <rect x="40" y="208" width="180" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="208" width="180" height="44" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="130" y="234" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;文件名&gt;</text>
  <rect x="320" y="208" width="160" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="320" y="208" width="160" height="44" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="400" y="234" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;epoch&gt;/</text>
  <rect x="560" y="208" width="200" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="208" width="200" height="44" rx="6" fill="#fffdf8" stroke="#6f685c" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="660" y="234" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;另一个 epoch&gt;/</text>
  <rect x="280" y="292" width="160" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="280" y="292" width="160" height="44" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="360" y="318" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;实体名&gt;/</text>
  <rect x="200" y="376" width="120" height="40" rx="6" fill="#f6f1e8"/>
  <rect x="200" y="376" width="120" height="40" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="260" y="394" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">data</text>
  <text x="260" y="411" fill="#5e584e" font-size="9" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">正文</text>
  <rect x="380" y="376" width="130" height="40" rx="6" fill="#f6f1e8"/>
  <rect x="380" y="376" width="130" height="40" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="445" y="394" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">tag.json</text>
  <text x="445" y="411" fill="#5e584e" font-size="9" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">附加信息</text>
  <text x="236" y="150" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">作业整体输出</text>
  <text x="236" y="234" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">内容是上游实体的正文</text>
  <text x="560" y="276" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">旧 epoch 留在原处，runner 不再读写</text>
  <text x="525" y="400" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">有上游时含 upstream 快照</text>
  <text x="40" y="446" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">epoch 是 execute 的参数，同一次运行里所有节点共用一个。</text>
  <text x="40" y="466" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">.staging 不属于任何节点，也不是某一层 epoch。</text>
</svg>
<figcaption><span class="fig-label">图 4</span> 一次运行留下的目录：节点目录下按 epoch 分层，实体目录里是 data 与 tag.json。</figcaption>
</figure>
<!-- figure:layout:end -->

```text
<输出根目录>/
  .staging/                 作业整体输出。apply function `Output` 写入
    <文件名>                内容是上游实体的正文
  <节点名>/
    <epoch>/
      <实体名>/
        data
        tag.json            有上游时含 upstream 快照
    <另一个 epoch>/
      ...
```

`.staging` 是作业整体的输出，不是某个节点的 epoch 实体目录。

epoch 是调用方传给 `execute` 的名字，也是实体所在的那层子目录名。同一次运行里，每个节点的输出都使用这个 epoch，快照里记下的 epoch 也是它。换一个 epoch 就是换一套子目录：新 epoch 从空目录开始，旧 epoch 的实体留在原处，runner 既不读它们，也不清理它们。快照里记录的 epoch 与本次不同时，该实体要重做。

runner 不检查 epoch 名，直接把它拼进路径。`2026/10` 这样的名字会建出两层目录，应传一层目录名，例如日期或版本号。

## 四、指纹与哈希

### docorder 里有三种哈希

判断一个结果还能不能继续用，靠的是比较哈希。docorder 里有三种哈希，它们各自回答一个问题：

| 哈希 | 算的是什么 | 记在哪里 | 用来判断什么 |
| --- | --- | --- | --- |
| 上游快照里的哈希 | 上游实体的正文加上它的用户 tag | 下游实体 `tag.json` 的 `upstream` 里 | 上游的结果有没有变 |
| `fingerprint.depend` | 算子读取的、但上游实体没有携带的外部文件 | 本实体 `tag.json` 的 `fingerprint` 里 | 这些外部文件有没有变 |
| `fingerprint.record` | 算子自己写下的外部文件 | 本实体 `tag.json` 的 `fingerprint` 里 | 不参与判断，只做记账 |

第一种第三章讲过。本章讲后面两种，以及三者如何合成一个判断。

### 上游快照里的哈希

第二章说过，`upstream` 记录的是直接上游实体此刻的快照。一条记录有四个字段：`operator` 是上游节点名，`name` 是上游实体名，`epoch` 是本次运行的 epoch，`hash` 是上游实体正文连同用户 tag 的 sha256。

这个 `hash` 的算法很简单：把上游实体的正文和它的用户 tag 拼成一个 JSON，再对这个 JSON 取 sha256。有两处细节值得记住。

第一，参与计算的是「用户 tag」，也就是 `tag.json` 去掉 `upstream` 和 `current` 这两个键之后剩下的部分。`upstream` 必须排除，否则哈希会把自己算进去，再也不会稳定；`current` 是早期版本留下的键，也一并排除。用户 tag 里的其它键全都参与计算，因此 function 往 tag 里写的每一个字段都算进去。

第二，正文为空时，哈希也是空字符串。空正文意味着这个实体的内容根本没有写下来，它不会和任何一次正常的结果匹配上。runner 比较时看到空哈希，一律判为不吻合。

### 声明指纹

上游快照只能覆盖「上游实体的正文和用户 tag」。有些算子要读别的文件：一张表定义旁边的 `.sql` 文件、一份词根表、一个上游写出来的中间文件。这些文件的内容不在上游实体里，上游快照看不到它们的变化。

`props.json` 里的 `fingerprint` 就是为这种情况准备的。它是一个对象，最多两段：

```json
{
  "type": "map",
  "class": "primary:RenderWithSchema",
  "fingerprint": {
    "record": {
      "{staging}/{name}.out": ""
    },
    "depend": {
      "{schema_home}/{name}.sql": ""
    }
  }
}
```

`record` 和 `depend` 都是对象，键是路径模板，值写什么都不算数——docorder 只读键，值只是占位。

两段的分工是固定的：

- `record` 列出这个算子自己写下的文件，或者 source 指向的输入文件。runner 在实体写好之后对这些文件取哈希，把结果记进这个实体的 `tag.json`。
- `depend` 列出这个算子读取的、但上游实体没有携带的文件。runner 在比较阶段就对这些文件取哈希，与实体里上一次记下的值作比较。

`record` 只是记账，不参与「要不要重做」的判断。改了 `record` 里的文件，不会让本算子重做；它只是把这次看到的文件状态记下来，供下游和排查使用。真正决定重做的是 `depend`。

### 两处判断如何合成一个结果

一个非 source 节点的实体要留下来，需要同时满足两件事：上游快照与上游当前的状态吻合，并且 `depend` 声明的每一个文件的哈希与上一次记下的一致。任意一条不成立，这个实体重做。两件事都成立时，实体被原样保留，function 不会被调用。

<!-- figure:hashes:start -->
<figure class="figure" id="fig-hashes">
<svg role="img" aria-labelledby="hashes-title hashes-desc" viewBox="0 0 900 640" width="100%" style="max-width:900px">
  <title id="hashes-title">两类哈希如何决定一个实体的去留</title>
  <desc>一个实体要留下来，需要上游快照与上游当前状态吻合，并且 depend 声明的每一个文件的哈希与上一次记下的一致；任何一条不成立，这个实体重做。record 只是记账，不参与判断。</desc>
  <defs>
    <marker id="hashes-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#5e584e"/>
    </marker>
    <marker id="hashes-arrow-teal" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1b4744"/>
    </marker>
    <marker id="hashes-arrow-moss" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1d6842"/>
    </marker>
  </defs>
  <rect width="900" height="640" fill="#f6f1e8"/>
  <path d="M 210 112 L 210 148" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#hashes-arrow)"/>
  <path d="M 210 192 L 210 228" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#hashes-arrow)"/>
  <path d="M 690 112 L 690 148" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#hashes-arrow)"/>
  <path d="M 690 192 L 690 228" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#hashes-arrow)"/>
  <path d="M 210 296 L 210 320 L 322 320 Q 330 320 330 328 L 330 344" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#hashes-arrow)"/>
  <path d="M 690 296 L 690 320 L 578 320 Q 570 320 570 328 L 570 344" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#hashes-arrow)"/>
  <path d="M 390 404 L 390 428 L 228 428 Q 220 428 220 436 L 220 452" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#hashes-arrow-moss)"/>
  <path d="M 510 404 L 510 428 L 672 428 Q 680 428 680 436 L 680 452" fill="none" stroke="#9a3412" stroke-width="1" marker-end="url(#hashes-arrow)"/>
  <rect x="289.5" y="404" width="21" height="16" rx="2" fill="#f6f1e8"/>
  <text x="300" y="416" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">是</text>
  <rect x="579.5" y="404" width="21" height="16" rx="2" fill="#f6f1e8"/>
  <text x="590" y="416" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">否</text>
  <rect x="40" y="56" width="340" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="56" width="340" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="82" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">上游实体的正文 + 用户 tag</text>
  <text x="210" y="99" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">正文变了，上游快照就对不上</text>
  <rect x="105" y="148" width="210" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="105" y="148" width="210" height="44" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="174" fill="#1c1915" font-size="13" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">sha256</text>
  <rect x="40" y="228" width="340" height="68" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="228" width="340" height="68" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="260" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">与快照里记录的 hash 比较</text>
  <text x="210" y="277" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">快照记的是上游正文与用户 tag 的哈希</text>
  <rect x="520" y="56" width="340" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="520" y="56" width="340" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="690" y="82" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">外部文件（fingerprint.depend）</text>
  <text x="690" y="99" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">上游实体没有携带的那些文件</text>
  <rect x="585" y="148" width="210" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="585" y="148" width="210" height="44" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="690" y="174" fill="#1c1915" font-size="13" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">sha256</text>
  <rect x="520" y="228" width="340" height="68" rx="6" fill="#f6f1e8"/>
  <rect x="520" y="228" width="340" height="68" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="690" y="260" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">与 tag.json 里 fingerprint.depend 比较</text>
  <text x="690" y="277" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">键集合不同或任一哈希不同，都会重做</text>
  <rect x="300" y="344" width="300" height="60" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="344" width="300" height="60" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="378" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">两处都吻合？</text>
  <rect x="80" y="452" width="280" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="80" y="452" width="280" height="56" rx="6" fill="rgba(29,104,66,0.08)" stroke="#1d6842" stroke-width="1"/>
  <text x="220" y="484" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">保留 · 不调用 function</text>
  <rect x="540" y="452" width="280" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="540" y="452" width="280" height="56" rx="6" fill="rgba(154,52,18,0.08)" stroke="#9a3412" stroke-width="1"/>
  <text x="680" y="484" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">重做 · 清空后重做</text>
  <rect x="40" y="548" width="820" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="548" width="820" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="574" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">fingerprint.record 只记账，不参与判定</text>
  <text x="450" y="591" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">它写进 tag.json，因而随用户 tag 一起算进本实体的哈希</text>
</svg>
<figcaption><span class="fig-label">图 7</span> 两类哈希如何合成一个判定：上游快照和 depend 都吻合，实体才被保留。</figcaption>
</figure>
<!-- figure:hashes:end -->

`depend` 还有一个连带效应。因为 `fingerprint` 写在 `tag.json` 里，而 `tag.json` 的用户 tag 部分参与上游快照的哈希计算，所以 `depend` 里的文件一变，本算子重做之后它的新哈希也就变了；下游看到上游变了，于是跟着重做。变化就是这样从图的中间往两边传开的。

### 路径模板与占位符

模板里的占位符写成 `{名字}` 的形式，可以填这些值：

| 占位符 | 值 |
| --- | --- |
| `{name}` | 当前实体的名字。它永远覆盖同名的参数 |
| `{staging}` | 作业的 `.staging` 目录。同名的字符串参数覆盖它 |
| `{参数名}` | 算子的字符串参数，也就是 `props.json` 去掉保留键之后、被节点 `config` 覆盖过的那一份 |
| `{tag 字段}` | 只有 `record` 能用：算子 tag 里的字符串字段。同名参数覆盖 tag 字段 |

一段文本里可以用多个占位符。填不上的占位符会让这一段以 `FatalError` 失败：文件不存在，或者占位符没有值。相对路径相对作业根目录解析，绝对路径按原样使用。

`record` 和 `depend` 的渲染时机不一样，这决定了它们能用到哪些值：

- `depend` 在 function 运行之前渲染，只能用 `{name}`、`{staging}` 和参数。那时候实体还没有写出来，tag 里什么都没有。
- `record` 在 tag 写好之后渲染，所以除了上面这些，还能用 tag 里的字符串字段。

### 一次运行里的时序

把上面这些放到一次 stage 里看：

1. 比较。runner 读出已有实体，对每个实体比上游快照，再比 `depend` 的文件哈希，得出新建、重做、保留、删除四类。
2. 清场。删除要删的目录，为要新建或重做的实体建一个只含空 `tag.json` 的占位目录。
3. 运行前。渲染 `depend` 的路径，取文件哈希。这时文件不存在就以 `FatalError` 停下，发生在清场之前，已经存在的实体不会被删掉。
4. 调用 function。`transform_data` 填正文，`transform_props` 填附加信息。
5. 记账。渲染 `record` 的路径，取文件哈希，写进 `tag.json` 的 `fingerprint`。这一步要求文件此刻已经存在，否则以 `FatalError` 失败。
6. 写出。先写 `data`，再写 `tag.json`。

source 节点不一样：它没有上游，所以不比较，也不列应得名单。它只在 `execute` 传了 `start_from_scratch=True` 时运行，跑起来之后在 `emit` 交出正文和 tag 之后记账。

### 会被拒绝的声明

有些声明在装配阶段就会被拒绝，作业不会开始：

- source 不能声明 `depend`。source 在运行前不做比较，没有机会用这个哈希判断什么。
- apply 不能声明 `fingerprint`。apply 不写实体，没有地方存这个哈希。

两种情况都以 `JobValidationError` 失败。

### 空正文

如果 function 没有留下正文，但这个算子声明了 `record`，runner 会把正文写成一个换行符。

原因在算法里：正文为空时哈希是空字符串，而空字符串永远不等于上一次记下的哈希，这个实体每次运行都会被判定为需要重做。写一个换行符之后正文有了内容，哈希稳定下来，比较才有意义。function 自己写了正文就保持不动。

### 节点的 config 会整份覆盖指纹

`props.json` 里的 `fingerprint` 和节点 `config` 里的 `fingerprint` 是同一个键，节点 `config` 整份覆盖它，不是合并：

```python
job.add_operator_node(
    "source_assign",
    "source",
    config={
        "directory": incoming,
        "fingerprint": {
            "record": {
                "{model_home}/{db}/{table}.sql": "",
                "{model_home}/{db}/{table}.yml": "",
                "{catalog}": "",
            }
        },
    },
)
```

上面的写法会丢掉算子 home 里 `props.json` 声明的全部指纹键，而不是在它之上再加一条。算子 home 里声明了三段指纹，节点 `config` 里就要把三段都写全。

### 排查

指纹记在实体的 `tag.json` 里，形如：

```json
{
  "fingerprint": {
    "depend": {
      "{staging}/raw_root.csv": "3a7bd3e2360a3d29eea436fcfb7e44c735d117c42d1c1835420b6b9942dd4f1b"
    }
  }
}
```

键是模板，不是渲染出来的路径。想知道某个模板这次指向了哪个文件，把模板里的占位符换成实际的值再看。

如果一个实体每次运行都被重做，按这个顺序查：

1. `upstream` 里的 `hash` 是不是空字符串。空哈希意味着上游实体没有正文。
2. `epoch` 是不是本次的 epoch。换 epoch 之后旧实体会重做。
3. `fingerprint.depend` 的键集合是不是和现在声明的一致。多一个键、少一个键都会导致重做。
4. 键下面的哈希是不是和文件当前的内容一致。
5. `fingerprint` 里的键是不是用错了模板，导致每次指向不同的文件。

## 五、使用场景

docorder 最适合这样一类任务：有一批彼此独立的对象，每个对象都要经过几个步骤的加工，而其中某些步骤比较慢、比较贵，或者容易失败。在这类任务中，docorder 能够保证失败之后只补做失败的部分，输入变化之后只重做受影响的部分。下面介绍几种典型的作业图，它们都只需要使用 docorder 自带的 function，或者编写很少量的代码就能搭建出来。

### 批量生成提示词并交给大模型

这是 docorder 最典型的用法。作业的第一步是一个 source 节点，它读取一个目录，把其中每个符合实体约定的子目录变成一个实体；第二步是一个使用 `TemplateToPrompt` 的 map 节点，它把每个实体套进模板，生成一段提示词；第三步是一个使用 `PromptToLLM` 的 map 节点，它把每段提示词交给一个命令行形式的大模型工具，工具在标准输出中打印的内容，或它自己写进目标实体的 `data`，就成为这一步的正文；最后还可以接一个使用 `TemplateToLLM` 的 reduce 节点，把所有回答汇总成一份清单。调用大模型的那个节点通常需要配置 `retry`，以便在接口偶尔出错时自动重试，并用 `parallelism` 控制同时发出的请求数量。如果有几个对象在多次重试后仍然失败，修复问题后用同一个 epoch 再运行一次，docorder 只会补做这几个对象，其余已经拿到回答的对象不会再次调用大模型。第十章的示例项目就是按这个结构搭建的。

### 从结构化数据生成配置文件

如果上游实体的正文是一个 JSON 对象，例如一张表的字段定义或者一个服务的描述，可以先用一个使用 `JinjaToJsonnet` 的 map 节点，把 JSON 对象中的每个键当作模板变量，渲染出一段 jsonnet 程序；再用一个使用 `JsonnetToPrompt` 的 map 节点，调用本机安装的 `jsonnet` 程序编译它，得到最终的 JSON 或文本。jsonnet 是一种专门用来生成 JSON 配置的语言，它支持变量、函数和列表推导等功能，比直接手写 JSON 更灵活。这种组合适合根据一批表定义或服务描述，批量生成格式统一的配置文件。

### 为每个实体运行命令行工具

使用 `Command` 的 map 节点会为每个实体运行一次外部命令。命令的参数里可以引用实体的附加信息、正文和输出目录，命令的结果可以取它在标准输出中打印的内容，也可以取它写到磁盘上的某个文件。这个 function 直接启动命令，不经过 shell，因此参数中的空格和特殊字符不会被 shell 另行解释。它适合批量调用代码格式化工具、格式转换工具或者团队内部的脚本。

### 汇总与拆分

reduce 节点把一批实体合并成一个实体，适合生成索引、目录、统计报告这类需要综合全部对象的结果。内置的 `TemplateToLLM` 可以把上游整批渲染成一份提示词交给大模型，再把回复写成那一个输出实体。fanout 节点把一个实体拆成多个实体，适合把一篇长文档按段落或章节切开，再交给后续步骤分别处理。fanout 没有内置 function，需要按照第九章的说明自己编写，通常只需要十几行代码。

### 不适合的场景

有些任务并不适合使用 docorder。如果某一步需要同时读取两个不同上游节点的结果，并且希望其中任何一个发生变化时都能自动重做，当前版本无法表达这样的依赖关系。如果需要把任务分发到多台机器上执行，或者希望上游刚处理完一个对象、下游就立即开始处理它，docorder 也无法满足。如果对象的内容是图片、音频这类二进制数据，同样不适合，因为正文只能是文本。另外，如果对象的数量很少，每个步骤都很快，而且失败后从头再跑一遍也没有什么代价，那么直接写一个普通的 Python 脚本会更简单。

## 六、配置

本章集中介绍使用 docorder 时需要配置的所有内容，包括 docorder 如何找到算子 home、`props.json` 中每个键的含义、创建作业和添加节点时的参数、运行函数 `execute` 的参数，以及 function 和模板分别能读到哪些配置。

### 让 docorder 找到算子 home

docorder 通过环境变量 `DOCORDER_HOMES` 寻找算子 home。这个环境变量的值是一个或多个目录，多个目录之间的分隔符与系统环境变量 `PATH` 相同，在 macOS 和 Linux 上是冒号 `:`，在 Windows 上是分号 `;`。查找时，docorder 按列出的顺序依次搜索这些目录，排在前面的目录优先，一旦找到就不再继续搜索。

算子 home 既可以直接放在列出的目录下面，也可以放在列出的目录下的某个分类子目录里，但不能嵌套得更深。分类子目录可以帮助你按用途整理很多个算子 home，名字以 `.` 或 `_` 开头的分类子目录会被跳过。一个目录只要包含 `props.json` 文件，就会被认作算子 home，算子 home 的名字就是这个目录的名字，添加节点时就用这个名字引用它。

```text
homes/                        DOCORDER_HOMES 指向这里
  sources/                    分类子目录，可以没有
    table_source/             名为 table_source 的算子 home
      props.json
  render/
    table_prompt/             名为 table_prompt 的算子 home
      props.json
      lib/table.jinja
```

docorder 是在调用 `add_operator_node` 添加节点的那一刻查找算子 home 的，因此环境变量必须在构建作业之前设置好。如果找不到指定名字的算子 home，会抛出 `FileNotFoundError` 错误，错误信息中会列出搜索过的所有目录，便于排查。最简单的做法是在启动脚本中用 `os.environ["DOCORDER_HOMES"] = ...` 设置这个环境变量，并行线程在同一个进程里，会读到同一份环境变量。

### props.json

`props.json` 是一个 JSON 对象。下表列出了 docorder 自己会解读的键，表中没有列出的其它键都会作为参数交给 function 使用。表中最后一列说明这个键的值能否在作业中被覆盖，以及用什么方式覆盖。

| 键 | 类型与默认值 | 含义 | 作业中能否覆盖 |
| --- | --- | --- | --- |
| `type` | 必须填写 | 算子类型，取 `source`、`map`、`reduce`、`fanout`、`apply` 之一 | 不能 |
| `class` | 必须填写 | function 类，写成 `模块路径:类名`；写成 `primary:类名` 表示算子 home 中 `primary.py` 文件里的类 | 不能 |
| `parallelism` | 整数，默认为 1 | map 和 fanout 节点最多同时使用的线程数 | 用 `add_operator_node` 的 `parallelism` 参数 |
| `retry.max_attempts` | 整数，默认为 1 | 每个实体最多尝试的次数，不能小于 1；默认值 1 表示不重试 | 用 `add_operator_node` 的 `retry` 参数 |
| `retry.backoff_seconds` | 数字，默认为 0 | 每次重试前等待的基础秒数，实际等待 `backoff_seconds × 已尝试次数` 秒 | 同上 |
| `output` | 字符串，默认为 `result` | 只对 reduce 节点有效，指定唯一那个输出实体的名字 | 用节点的 `config` |
| `fingerprint` | 对象 | 声明这个算子依赖哪些外部文件，分 `record` 和 `depend` 两段，见第三章「指纹」一节 | 用节点的 `config` |
| 其它键 | 任意 JSON 值 | function 的参数，例如 `template`、`directory` | 用节点的 `config` |

`retry` 写成一个嵌套的对象，例如 `"retry": {"max_attempts": 3, "backoff_seconds": 5}`，表示每个实体最多尝试三次，第一次失败后等待 5 秒，第二次失败后等待 10 秒。如果 `props.json` 不是一个 JSON 对象、`class` 中没有冒号，或者 `type` 不是上述五种之一，`add_operator_node` 会以 `JobValidationError` 错误失败。

### 作业与节点

`Job(name, root)` 用于创建一个作业，`name` 是作业的名字，`root` 是输出根目录。输出根目录建议使用绝对路径，这样无论从哪个目录启动脚本，结果都会写到同一个地方。节点通过下面的方法加入作业：

```python
job.add_operator_node(
    name,                 # 节点名，同时也是输出根目录下的子目录名
    operator_home,        # 算子 home 的名字，在 DOCORDER_HOMES 列出的目录中查找
    upstream=None,        # 上游节点名；source 节点不填，其它节点必须填，且只能是一个字符串
    config=None,          # 一个字典，覆盖算子 home 中的 function 参数
    parallelism=None,     # 覆盖 props.json 中的 parallelism
    retry=None,           # 覆盖 props.json 中的 retry，写成 RetryPolicy(max_attempts=..., backoff_seconds=...)
)
```

`RetryPolicy` 需要从 `docorder.utils.retry` 导入。使用这个方法时有几点需要注意：`upstream` 只能是一个字符串，传入列表或元组会被拒绝，这对应着「每个节点只有一个上游」的限制；如果用同一个节点名添加了两次节点，后一次会替换前一次，而且不会报错，所以要确保节点名互不相同；节点名会直接拼接到输出路径中，不做任何检查，应该使用由字母、数字、连字符或下划线组成的简单名字。

节点在构造时会把传入的 `config` 覆盖到算子 home 的 function 参数上，并写进 `props`。遇到同名的键时以 `config` 中的值为准，`config` 中的 `class` 会被忽略，因此不能通过 `config` 更换 function。构造完成之后节点不再保留 `config`，之后读参数都从 `props` 来。作业开始运行时，runner 会为每个节点构造一个算子，并把节点上的公开字段抬到算子上。此后读名字、参数、输出路径和上游，都走算子，不再回头去读节点。还有一点容易混淆：如果把 `parallelism` 或 `retry` 写进 `config`，并不会改变节点的并行度或重试策略，它们只会成为一个普通的 function 参数；要在作业中修改这两项调度参数，只能使用 `add_operator_node` 的同名参数。

### execute

```python
from docorder.core.runner import execute

execute(job, epoch, start_from_scratch=False)
```

`epoch` 会被直接用作一层目录名，docorder 不检查它的内容，所以应该使用日期、版本号这样的简单名字；如果传入 `2026/10` 这样带斜杠的名字，会建出两层目录。`start_from_scratch=True` 要求 source 节点调用 function 重新产生实体；不传入时，source 节点保持上一次留下的实体不变。在一个新的 epoch 上第一次运行时，通常都需要传入这个参数，否则 source 节点的目录是空的，整个作业也就没有任何输入。

### function 读到的参数与模板读到的算子信息

同一份参数会以两种形式提供给使用者，一种供 function 的代码读取，另一种供模板读取。两者包含的参数完全相同，都遵循「节点的 `config` 覆盖 `props.json`」这一约定，区别只在于模板读到的那一份还多了几项由 runner 填入的运行信息。

function 的代码通过 `self.environment.operator_props` 读取参数。它的内容是 `props.json` 去掉 `type`、`class`、`parallelism`、`retry`、`home` 这几个键之后剩下的部分，再用节点的 `config` 覆盖同名的键。function 根据这份参数决定具体怎么运行，例如 `TemplateToPrompt` 从这里读取 `template`，以确定使用哪个模板文件。模板读 `self.environment.template_env`，里面是 `operator`、`job`、`entity`。

模板通过名为 `operator` 的变量读取算子信息。它以 function 读到的那份参数为基础，也就是 `props.json` 中的参数被节点 `config` 覆盖之后的结果；在此之上，runner 还会填入本次运行的几项信息，包括 `name`、`home`、`function_class`、`type` 和 `operator_home`，它们会覆盖同名的参数，具体含义见第八章的变量表。因此，在节点的 `config` 中覆盖了 `template` 之后，实际使用的模板文件和模板里 `{{ operator.template }}` 显示的值会一起改变；只写在节点 `config` 中、`props.json` 里没有的键，在模板里同样可以通过 `operator.<键>` 读到。runner 填入的那几项是唯一的例外：即使在 `config` 中写了 `name`，模板读到的仍然是节点名。`parallelism` 和 `retry` 是 `props.json` 的保留键，不会作为 function 参数传下去，因此 `operator` 里没有这两项；本次运行的 epoch 在 `job.epoch` 中，不在 `operator` 中。

### 环境变量

| 变量 | 由谁读取 | 含义 |
| --- | --- | --- |
| `DOCORDER_HOMES` | `add_operator_node` | 寻找算子 home 的目录列表 |
| `DOCORDER_LLM` | `PromptToLLM` | 节点没有配置 `tool` 参数时使用的大模型工具，值是工具名或工具定义文件的路径 |

## 七、算子分类与内置 function

### 五种算子

五种算子的区别在于输入实体与输出实体之间如何对应，以及作业结果写到哪里。下表从几个方面对它们作了比较。其中「function 基类」一列是编写这种算子的 function 时必须继承的类，「内置 function」一列是 docorder 自带、可以直接在 `props.json` 中使用的 function。

<!-- figure:operators:start -->
<figure class="figure" id="fig-operators">
<svg role="img" aria-labelledby="operators-title operators-desc" viewBox="0 0 900 540" width="100%" style="max-width:900px">
  <title id="operators-title">五种算子的输入与输出</title>
  <desc>source 从外部数据产生若干实体；map 让一个上游实体对应一个同名输出实体；reduce 把全部上游实体合成一个；fanout 把一个上游实体拆成若干个；apply 只调用 function，不产生实体。</desc>
  <defs>
    <marker id="operators-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#5e584e"/>
    </marker>
    <marker id="operators-arrow-teal" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1b4744"/>
    </marker>
    <marker id="operators-arrow-moss" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1d6842"/>
    </marker>
  </defs>
  <rect width="900" height="540" fill="#f6f1e8"/>
  <text x="140" y="28" fill="#6f685c" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">上游实体</text>
  <text x="410" y="28" fill="#6f685c" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">算子</text>
  <text x="700" y="28" fill="#6f685c" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">输出实体</text>
  <rect x="70" y="52" width="140" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="70" y="52" width="140" height="48" rx="6" fill="rgba(27,71,68,0.08)" stroke="#1b4744" stroke-width="1"/>
  <text x="140" y="80" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">外部数据</text>
  <rect x="280" y="48" width="260" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="280" y="48" width="260" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="410" y="74" fill="#1c1915" font-size="13" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">source</text>
  <text x="410" y="91" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">SourceFunction</text>
  <rect x="623" y="62" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="632" y1="73" x2="660" y2="73" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="632" y1="80" x2="651" y2="80" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="677" y="62" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="686" y1="73" x2="714" y2="73" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="686" y1="80" x2="705" y2="80" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="731" y="62" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="740" y1="73" x2="768" y2="73" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="740" y1="80" x2="759" y2="80" stroke="#d8d0c1" stroke-width="1"/>
  <path d="M 220 76.0 L 272 76.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <path d="M 548 76.0 L 613.0 76.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <rect x="571.75" y="52" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="580.5" y="64" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">N</text>
  <rect x="117" y="146" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="126" y1="157" x2="154" y2="157" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="126" y1="164" x2="145" y2="164" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="280" y="132" width="260" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="280" y="132" width="260" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="410" y="158" fill="#1c1915" font-size="13" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">map</text>
  <text x="410" y="175" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">MapFunction</text>
  <rect x="677" y="146" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="686" y1="157" x2="714" y2="157" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="686" y1="164" x2="705" y2="164" stroke="#d8d0c1" stroke-width="1"/>
  <path d="M 173.0 160.0 L 272 160.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <path d="M 548 160.0 L 667.0 160.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <rect x="213.75" y="136" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="222.5" y="148" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">1</text>
  <rect x="598.75" y="136" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="607.5" y="148" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">1</text>
  <rect x="63" y="230" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="72" y1="241" x2="100" y2="241" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="72" y1="248" x2="91" y2="248" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="117" y="230" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="126" y1="241" x2="154" y2="241" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="126" y1="248" x2="145" y2="248" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="171" y="230" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="180" y1="241" x2="208" y2="241" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="180" y1="248" x2="199" y2="248" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="280" y="216" width="260" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="280" y="216" width="260" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="410" y="242" fill="#1c1915" font-size="13" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">reduce</text>
  <text x="410" y="259" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">ReduceFunction</text>
  <rect x="677" y="230" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="686" y1="241" x2="714" y2="241" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="686" y1="248" x2="705" y2="248" stroke="#d8d0c1" stroke-width="1"/>
  <path d="M 227.0 244.0 L 272 244.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <path d="M 548 244.0 L 667.0 244.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <rect x="240.75" y="220" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="249.5" y="232" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">N</text>
  <rect x="598.75" y="220" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="607.5" y="232" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">1</text>
  <rect x="117" y="314" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="126" y1="325" x2="154" y2="325" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="126" y1="332" x2="145" y2="332" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="280" y="300" width="260" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="280" y="300" width="260" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="410" y="326" fill="#1c1915" font-size="13" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">fanout</text>
  <text x="410" y="343" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">FanoutFunction</text>
  <rect x="623" y="314" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="632" y1="325" x2="660" y2="325" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="632" y1="332" x2="651" y2="332" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="677" y="314" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="686" y1="325" x2="714" y2="325" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="686" y1="332" x2="705" y2="332" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="731" y="314" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="740" y1="325" x2="768" y2="325" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="740" y1="332" x2="759" y2="332" stroke="#d8d0c1" stroke-width="1"/>
  <path d="M 173.0 328.0 L 272 328.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <path d="M 548 328.0 L 613.0 328.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <rect x="213.75" y="304" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="222.5" y="316" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">1</text>
  <rect x="571.75" y="304" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="580.5" y="316" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">N</text>
  <rect x="63" y="398" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="72" y1="409" x2="100" y2="409" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="72" y1="416" x2="91" y2="416" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="117" y="398" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="126" y1="409" x2="154" y2="409" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="126" y1="416" x2="145" y2="416" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="171" y="398" width="46" height="28" rx="4" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="180" y1="409" x2="208" y2="409" stroke="#d8d0c1" stroke-width="1"/>
  <line x1="180" y1="416" x2="199" y2="416" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="280" y="384" width="260" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="280" y="384" width="260" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="410" y="410" fill="#1c1915" font-size="13" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">apply</text>
  <text x="410" y="427" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">ApplyFunction</text>
  <rect x="630" y="388" width="140" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="630" y="388" width="140" height="48" rx="6" fill="rgba(154,52,18,0.08)" stroke="#9a3412" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="700" y="416" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">不写实体</text>
  <path d="M 227.0 412.0 L 272 412.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <path d="M 548 412.0 L 620 412.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <rect x="240.75" y="388" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="249.5" y="400" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">N</text>
  <rect x="575.25" y="388" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="584" y="400" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">0</text>
  <text x="40" y="470" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">实体名：source 由 emit 给出 · map 与上游同名</text>
  <text x="40" y="490" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">reduce 取参数 output（默认 result）· fanout 由 output_names 给出</text>
  <text x="40" y="510" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">apply 没有输出实体，也不能有下游</text>
</svg>
<figcaption><span class="fig-label">图 5</span> 五种算子：箭头上标的是实体个数，apply 是唯一不产生输出实体的类型。</figcaption>
</figure>
<!-- figure:operators:end -->

| 类型 | 输入与输出的对应关系 | 输出实体的名字从哪里来 | 能否并行 | function 基类 | 内置 function |
| --- | --- | --- | --- | --- | --- |
| source | 没有上游，从外部数据产生实体 | `emit` 方法交出的每条记录 | 否 | `SourceFunction` | `DirectorySource`、`FilteredDirectorySource`、`FileHashSource` |
| map | 一个上游实体对应一个输出实体 | 与上游实体同名 | 是 | `MapFunction` | `TemplateToPrompt`、`JinjaToJsonnet`、`JsonnetToPrompt`、`Command`、`PromptToLLM`、`EntityTemplateToLLM` |
| reduce | 全部上游实体对应一个输出实体 | 参数 `output`，默认为 `result` | 否 | `ReduceFunction` | `TemplateToLLM` |
| fanout | 一个上游实体对应多个输出实体 | `output_names` 方法的返回值 | 是 | `FanoutFunction` | 无 |
| apply | 每个上游实体调用一次 function，不产生实体 | 无 | 否 | `ApplyFunction` | `Output` |

`props.json` 中 `class` 指向的类必须是 `type` 所对应基类的子类。例如 `type` 写的是 `map`，`class` 就只能是 `MapFunction` 或它的子类，写成一个 source 类型的 function 会在装配阶段报错。docorder 自带的五个渲染类 map function 都继承自 `RenderedMap`，它是 `MapFunction` 的一个子类，提供了「读取、渲染、生成附加信息」的三步结构，第八章会专门介绍。`EntityTemplateToLLM` 也是 map，它不走这三步。

### source 算子

source 算子位于作业图的起点，负责把外部数据变成最初的一批实体。正如第三章所说，source 节点只有在调用 `execute` 时传入了 `start_from_scratch=True`，才会运行 function 重新读取外部数据。

#### DirectorySource

`DirectorySource` 的完整写法是 `docorder.functions.impl.directory_source:DirectorySource`，它把一个目录中已经写成实体形状的子目录收成实体。它只处理该目录下直接包含的子目录，不会再往下走。子目录名就是实体名；子目录里必须有 `data` 和 `tag.json`，正文来自 `data`，附加信息来自 `tag.json`。普通文件、缺这两个文件之一的子目录，以及名字以 `.` 或 `_` 开头的子目录，都会被跳过。

| 参数 | 是否必须 | 含义 |
| --- | --- | --- |
| `directory` | 必须 | 要读取的输入目录；如果写的是相对路径，会相对于算子 home 解析 |

以下几种情况会导致失败。如果某个 `data` 不是合法的 UTF-8 文本，或 `tag.json` 不是 JSON 对象，这个 stage 会失败，而且不会重试。如果 `directory` 指定的目录不存在，会以 `FatalError` 错误失败。

输入数据通常属于具体的项目，而不属于算子，所以一般不会把输入目录放在算子 home 里，而是在添加节点时通过 `config` 传入一个绝对路径：

```python
job.add_operator_node("tables", "table_source", config={"directory": str(ROOT / "data" / "tables")})
```

如果需要改变 `DirectorySource` 的部分行为，可以编写它的子类，并覆盖以下三个方法中的一个或几个：`extract_tag(name, content, tag)` 决定每个实体目录的附加信息，参数 `name` 是目录名，`content` 是 `data` 的文本，`tag` 是读到的 `tag.json`；`include(path)` 决定一个实体目录是否要收成记录，返回 `True` 表示保留；`generate(directory)` 则完全替换「从目录产生记录」的过程。第十章的 `TableSource` 就是覆盖 `extract_tag` 的一个例子。

#### FilteredDirectorySource

`FilteredDirectorySource` 的完整写法是 `docorder.functions.impl.directory_source:FilteredDirectorySource`。它在 `DirectorySource` 的基础上增加了一个 `filter` 参数，用来按实体目录名的结尾和 `data` 文件大小挑选需要的实体，其余行为与 `DirectorySource` 完全相同。

| 参数 | 是否必须 | 含义 |
| --- | --- | --- |
| `directory` | 必须 | 与 `DirectorySource` 相同 |
| `filter.disabled_suffix` | 可选 | 一个字符串或字符串列表；实体目录名以其中任意一个结尾时，排除这个目录 |
| `filter.enabled_suffix` | 可选 | 一个字符串或字符串列表；设置之后，只保留目录名以其中任意一个结尾的实体 |
| `filter.min_size` | 可选 | 非负整数，`data` 文件大小的下限，单位是字节，等于下限的会被保留 |
| `filter.max_size` | 可选 | 非负整数，`data` 文件大小的上限，单位是字节，等于上限的会被保留 |

对每个实体目录，判断的顺序是：先检查它是否命中 `disabled_suffix`，命中就排除；再检查是否设置了 `enabled_suffix`，设置了而目录名没有命中也排除；最后检查 `data` 文件大小是否在范围之内。如果 `filter` 不是一个对象、某个后缀是空字符串、大小不是非负整数，或者 `min_size` 大于 `max_size`，会以 `FatalError` 错误失败。

下面的配置只读取算子 home 下 `inputs/` 目录中、`data` 不超过 64 KB 的实体：

```json
{
  "type": "source",
  "class": "docorder.functions.impl.directory_source:FilteredDirectorySource",
  "directory": "inputs",
  "filter": { "max_size": 65536 }
}
```

#### FileHashSource

`FileHashSource` 的完整写法是 `docorder.functions.impl.directory_source:FileHashSource`。它在 `DirectorySource` 的基础上增加一个 `paths` 参数，把一组文件的绝对路径写进实体的附加信息。正文仍然是输入目录里 `data` 的原文，文件哈希不由这个 function 计算。

| 参数 | 是否必须 | 含义 |
| --- | --- | --- |
| `directory` | 必须 | 与 `DirectorySource` 相同 |
| `paths` | 必须 | 一个对象，键是写进附加信息的字段名，值是路径模板；写进附加信息的是解析后的绝对路径 |

`paths` 的值是路径模板，用 `{名字}` 占位。可以填入实体附加信息里的字符串，也可以填入算子参数里的字符串，同名时算子参数覆盖附加信息。相对路径相对算子 home 解析。文件不存在、占位符没有值，或者 `paths` 不是对象时，这一段会以 `FatalError` 错误失败。

```json
{
  "type": "source",
  "class": "docorder.functions.impl.directory_source:FileHashSource",
  "paths": {
    "sql": "{model_home}/{db}/{table}.sql",
    "yml": "{model_home}/{db}/{table}.yml"
  },
  "fingerprint": {
    "record": {
      "{model_home}/{db}/{table}.sql": "",
      "{model_home}/{db}/{table}.yml": ""
    }
  }
}
```

`fingerprint.record` 里的值不使用，只有它的键是模板。模板里的 `{名字}` 占位可以填 `{name}`（实体名）、`{staging}`（作业的 `.staging` 目录）、tag 中的字符串字段和算子参数中的字符串值，同名时参数覆盖 tag。相对路径相对作业根目录解析。它由 runner 在交出记录之后把文件的 sha256 记进实体的附加信息，用来判断源文件是否改动过，见本章的「指纹」一节。source 节点只能声明 `record`，不能声明 `depend`。

### map 算子

map 算子为上游的每一个实体产生一个同名的输出实体，是最常用的一种算子。docorder 自带的五个渲染类 map function 都继承自 `RenderedMap`，它们在模板或命令参数中能够使用哪些变量，会在第八章统一说明。`EntityTemplateToLLM` 另用一份只含路径的 Jinja 模板调用 LLM。

#### TemplateToPrompt

`TemplateToPrompt` 的完整写法是 `docorder.functions.impl.template_to_prompt:TemplateToPrompt`。它用算子 home 中的一个 Jinja 模板渲染每个实体，渲染得到的文本就是输出实体的正文，输出实体的附加信息是上游实体附加信息的一份副本。

| 参数 | 是否必须 | 含义 |
| --- | --- | --- |
| `template` | 必须 | 模板文件相对于算子 home 的路径，这个路径不能指向算子 home 之外 |

这个 function 使用 Jinja 的严格模式渲染模板：如果模板中引用了一个不存在的变量，渲染会直接失败，而不会悄悄地把它替换成空字符串，这样可以尽早发现模板中的拼写错误。模板语法错误和变量缺失都会以 `FatalError` 错误失败，不会重试，因为再试多少次结果都一样。

```json
{
  "type": "map",
  "class": "docorder.functions.impl.template_to_prompt:TemplateToPrompt",
  "template": "lib/note.jinja"
}
```

如果 `lib/note.jinja` 的内容是 `Note: {{ entity.source_data }}`，而上游实体的正文是 `hello`，那么输出实体的正文就是 `Note: hello`。这里的 `entity.source_data` 是 docorder 内置的模板变量，代表上游实体的正文。

#### JinjaToJsonnet

`JinjaToJsonnet` 的完整写法是 `docorder.functions.impl.jinja_to_jsonnet:JinjaToJsonnet`。它要求上游实体的正文是一个 JSON 对象，并把这个对象中的每个键作为 Jinja 模板的变量，渲染算子 home 中的模板，渲染结果是一段 jsonnet 程序，作为输出实体的正文。它产生的附加信息是一个空对象，不过 runner 仍会照常把上游的 `global_prop` 合并进去。

| 参数 | 是否必须 | 含义 |
| --- | --- | --- |
| `template` | 必须 | 模板文件相对于算子 home 的路径 |
| `variables` | 可选 | 一个 JSON 对象，为模板变量提供默认值；上游正文中的同名键会覆盖这里的值 |

在模板中，直接写 `{{ table }}` 会把变量的值作为普通文本插入；写成 `{{ columns | jsonnet }}`，则会通过 `jsonnet` 过滤器把变量的值转换成 jsonnet 能识别的字面量，例如字符串会带上引号，列表和对象会写成相应的语法。过滤器是 Jinja 的一种语法，用竖线 `|` 把一个值交给一个函数处理。如果上游正文为空、不是合法的 JSON、不是 JSON 对象，`variables` 不是对象，模板有错误，或者渲染结果全是空白，都会以 `FatalError` 错误失败。

下面是一个模板的例子：

```text
{
  table: {{ table | jsonnet }},
  owner: {{ owner | jsonnet }},
  columns: [c.name for c in {{ columns | jsonnet }}],
  column_count: std.length(self.columns),
}
```

假设上游实体的正文是 `{"table": "orders", "columns": [...]}`，其中 `columns` 列出了三个字段，`variables` 参数是 `{"owner": "data-team"}`。这个模板会渲染出一段 jsonnet 程序，再交给下一节介绍的 `JsonnetToPrompt` 编译，最终得到 `{"column_count": 3, "columns": ["order_id", "user_id", "amount"], "owner": "data-team", "table": "orders"}` 这样的 JSON。

如果需要定制它的行为，可以编写子类：覆盖 `template_text()` 方法可以由代码直接提供模板内容，而不必从文件读取；覆盖 `generate_props` 方法可以从渲染结果中提取信息，作为输出实体的附加信息。

#### JsonnetToPrompt

`JsonnetToPrompt` 的完整写法是 `docorder.functions.impl.jsonnet_to_prompt:JsonnetToPrompt`。它把上游实体的正文当作一段 jsonnet 程序，通过标准输入交给命令 `jsonnet -` 编译，编译器在标准输出中打印的结果就是输出实体的正文，输出实体的附加信息是上游附加信息的副本。这个 function 没有任何参数，但要求本机已经安装了 `jsonnet`，并且它所在的目录在环境变量 `PATH` 中。

如果找不到 `jsonnet` 命令，会以 `FatalError` 错误失败；如果编译过程返回了非零的退出码，会抛出普通的异常，并按节点的 `retry` 参数重试。如果 jsonnet 程序中用 `import` 引入了其它文件，路径会按照程序中写的样子解析；在 `JinjaToJsonnet` 的模板中，可以用 `{{ home }}` 得到算子 home 的绝对路径，从而拼出算子 home 中某个文件的完整路径。

#### Command

`Command` 的完整写法是 `docorder.functions.impl.command:Command`。它为每个实体运行一次外部命令，命令直接启动，不经过 shell。

| 参数 | 是否必须 | 含义 |
| --- | --- | --- |
| `argv` | 必须 | 一个列表，第一项是命令，后面各项是参数；每一项中的 `{名字}` 占位符会被替换成对应的值 |
| `cwd` | 可选 | 运行命令时的工作目录；其中的占位符不会被替换 |
| `output_file` | 可选 | 命令写出的结果文件；其中的占位符会被替换；相对路径相对于运行 Python 脚本时的当前目录 |
| `capture` | 可选 | 从哪里取得正文，可以是 `file`、`stdout` 或 `none`；设置了 `output_file` 时默认为 `file`，否则默认为 `stdout` |

`capture` 为 `file` 时，命令结束后读取 `output_file` 的内容作为正文；为 `stdout` 时，取命令在标准输出中打印的内容作为正文；为 `none` 时，正文是一个空字符串，适用于只关心命令副作用的场合。输出实体的附加信息是上游附加信息的副本，再加上一个 `command` 键，记录替换完占位符之后的完整命令行；如果设置了 `output_file`，还会加上一个 `output_file` 键，记录替换后的文件路径。

```json
{
  "type": "map",
  "class": "docorder.functions.impl.command:Command",
  "argv": ["cp", "{entity.source_data_path}", "{entity.output}/copy.json"],
  "output_file": "{entity.output}/copy.json"
}
```

这个例子中，`{entity.source_data_path}` 会被替换成上游实体正文文件的路径，`{entity.output}` 会被替换成正在写出的实体目录。命令把源文件复制到这个实体目录中，然后 `Command` 读取复制出来的文件作为正文。由于命令不经过 shell，参数中不能直接使用管道 `|` 或重定向 `>`；如果确实需要，可以显式写成 `["sh", "-c", "..."]`，但这时要注意，替换进命令行的值会被 shell 解释，如果这些值来自不可信的输入，可能带来命令注入的风险。

以下情况会以 `FatalError` 错误失败，不会重试：命令找不到；`argv` 为空；`capture` 的值无法识别；`capture` 为 `file` 却没有设置 `output_file`；占位符引用了一个不存在的名字。以下情况会抛出普通的异常，并按 `retry` 参数重试：命令返回了非零的退出码；`capture` 为 `file` 时命令没有写出 `output_file`。

#### PromptToLLM

`PromptToLLM` 的完整写法是 `docorder.functions.impl.prompt_to_llm:PromptToLLM`。它把上游实体的正文作为提示词，交给一个以命令行形式运行的大模型工具。工具返回后，如果目标实体目录里已经有 `data` 文件，这份文件就是正文：它必须是非空的 UTF-8 文本，通过检查后不再改写，只补上 `tag.json`。没有这份文件时，工具在标准输出中打印的内容就是正文。输出实体的附加信息是上游附加信息的副本。调用开始前若已有 `data`，会先删掉。docorder 不附带任何大模型工具的预设配置，工具需要由使用者自己定义。

| 参数 | 是否必须 | 含义 |
| --- | --- | --- |
| `workspace` | 必须 | 一个已经存在的目录，作为大模型工具进程的工作目录 |
| `tool` | 可选 | 要使用的工具，可以是工具名、工具定义文件的路径，或者直接写一个工具定义对象；不填时读取环境变量 `DOCORDER_LLM` |

当 `tool` 是一个字符串时，docorder 首先在算子 home 中寻找 `tools/<名字>.json` 文件，找不到时再把这个字符串当作一个文件路径。工具定义是一个 JSON 对象，包含以下字段：

| 字段 | 是否必须 | 含义 |
| --- | --- | --- |
| `run` | 必须 | 一个非空的字符串列表，表示要运行的命令及其参数；其中的 `{workspace}` 会被替换成工作目录 |
| `prompt` | 可选 | 提示词的传递方式：`stdin`（默认）表示通过标准输入传入，`arg` 表示追加为命令的最后一个参数 |
| `name` | 可选 | 工具的名字，出现在错误信息中，便于辨认 |

```json
{ "name": "my-llm", "run": ["my-llm-cli", "--cwd", "{workspace}"], "prompt": "stdin" }
```

上面的 `my-llm-cli` 只是一个占位的名字，实际使用时要换成你所用的大模型命令行工具。以下情况会以 `FatalError` 错误失败：没有设置 `workspace` 或者它指向的目录不存在；找不到指定的工具；工具定义的格式不正确；工具的可执行文件不在 `PATH` 中。如果工具运行后返回了非零的退出码，会抛出普通的异常，并按 `retry` 参数重试。由于大模型接口偶尔会因为限流或网络问题出错，使用 `PromptToLLM` 的算子通常都应该在 `props.json` 中配置 `retry`。

#### EntityTemplateToLLM

`EntityTemplateToLLM` 的完整写法是 `docorder.functions.impl.template_to_llm:EntityTemplateToLLM`。它为每个上游实体渲染一份 Jinja 模板，把渲染结果交给大模型工具，再把回复写成该实体的正文。它不走 `RenderedMap` 的三步流程，一次调用同时得到正文和附加信息。

| 参数 | 是否必须 | 含义 |
| --- | --- | --- |
| `template` | 必须 | 模板文件相对于算子 home 的路径 |
| `workspace` | 必须 | 一个已经存在的目录，作为大模型工具进程的工作目录 |
| `tool` | 可选 | 与 `PromptToLLM` 相同 |
| `header` | 可选 | 从回复中抽取正文的表头行，含义与 `TemplateToLLM` 相同 |
| `tag_template` | 可选 | 一段 Jinja 字符串，渲染结果是实体的附加信息 |

模板里能看到 `source`，它有 `name`、`path` 和 `tag` 三个字段。`path` 是上游实体的 `data` 文件路径。模板还可以调用 `staging(name)`，得到作业 `.staging` 目录下一个已存在文件的路径。模板拿不到文件正文，提示词里写路径，让大模型自己去读。

```json
{
  "type": "map",
  "class": "docorder.functions.impl.template_to_llm:EntityTemplateToLLM",
  "template": "lib/prompt.jinja",
  "header": "root_id|member_id|member_zh",
  "tag_template": "{\"root_id\": {{ (source.tag.get('root_id') or source.name)|tojson }}}",
  "workspace": "/data/workspace"
}
```

```jinja
root_id: {{ source.tag.get('root_id') or source.name }}
{{ source.path }}
```

模板引用了不存在的变量、找不到工具、工具定义不合法、或者 `header` 在回复里找不到对应行时，这一段会以 `FatalError` 错误失败；工具返回非零退出码时按 `retry` 重试。

### reduce 算子

reduce 算子把上游在本 epoch 中的全部实体合并成一个输出实体，输出实体的名字由参数 `output` 决定，未设置时为 `result`。function 会收到一个按实体名字排序的上游实体列表，以及这一个目标实体。由于这个输出依赖全部上游实体，上游中任何一个实体的正文发生变化、新增了实体或者删除了实体，都会导致这个输出被重新计算。

内置 function 是 `docorder.functions.impl.template_to_llm:TemplateToLLM`。它把上游全部实体渲染进一份 Jinja 模板，把渲染结果交给大模型工具，再把回复写成那一个输出实体的正文。模板里能看到 `sources`，它是按 reduce 收到的顺序排列的列表，每项有 `name`、`path` 和 `tag`；`path` 是该实体的 `data` 文件路径。模板还可以调用 `staging(name)`，得到作业 `.staging` 目录下一个已存在文件的路径。`header` 有值时，正文从回复里这一行表头开始；`tag_template` 是一段可选的 Jinja 字符串，渲染结果是实体的附加信息；`min_sources` 与 `max_sources` 限制上游个数。

其它 reduce 转换可以自己编写，第九章给出了编写方法和示例。

### fanout 算子

fanout 算子把上游的每一个实体拆分成多个输出实体。拆分出哪些输出实体，由 function 的 `output_names(source)` 方法决定：它接收一个上游实体，返回一个由输出实体名字组成的列表，默认只返回上游实体自己的名字。整个 stage 中，所有上游实体拆分出的名字必须互不相同，否则会以 `OperatorValidationError` 错误失败。`output_names` 方法在主进程中调用，而且在一次运行中可能被调用不止一次，因此它的结果应该只取决于传入的上游实体，也不应该产生写文件之类的副作用。docorder 没有自带 fanout 类型的 function，第九章给出了编写示例。

### apply 算子

apply 算子对上游本 epoch 的每个实体调用一次 function 的 `apply`，全部结束后再调用一次 `finish`。两个方法都必须返回 `None`。它不写实体，作业图里也不能再有节点把它当作上游；它自己必须有上游。上游为空时不调用 `apply`，仍然调用 `finish`。

内置 function 是 `docorder.functions.impl.output:Output`。它由 apply 算子调用，把每个实体的正文写成作业根目录 `.staging` 里的一个文件，作为作业整体的输出。参数 `directory` 可以换成别的路径，相对路径相对算子 home 解析。文件名由 `rename(entity)` 决定，缺省是实体名；参数 `filename` 换成固定文件名，子类覆盖这个方法来按实体改名。返回值必须是一层文件名。两个实体得到同一个文件名时，这一段以 `FatalError` 失败。这个 function 上次写出、这次不再产生的文件会在 `finish` 里删掉。

### 失败与重试

下表汇总了各种失败情况会抛出的异常，以及这些异常是否会按节点的 `retry` 参数重试。

| 情况 | 异常 | 是否按 `retry` 重试 |
| --- | --- | --- |
| 作业图中有循环依赖、上游节点不存在、输出目录冲突 | `JobValidationError` | 不适用，在开始执行前就失败 |
| function 类找不到，或者不是对应基类的子类 | `OperatorValidationError` | 不适用，在开始执行前就失败 |
| 找不到算子 home | `FileNotFoundError` | 不适用，在构建作业时就失败 |
| 配置缺失、模板错误、模板变量缺失、输入格式不正确 | `FatalError` | 否 |
| 外部命令、jsonnet 或大模型工具返回非零退出码 | `DocorderError` | 是 |
| function 抛出的其它异常 | 原来的异常 | 是 |

这些异常类都定义在 `docorder.utils.errors` 中，其中 `DocorderError` 是 `JobValidationError`、`OperatorValidationError` 和 `FatalError` 的共同父类。

#### 各个内置 function 的失败情形

`FatalError` 表示配置或输入本身有问题，再试一次也不会好，因此直接让这一段失败。其余异常，包括外部进程返回非零状态，都会在等待 `backoff_seconds × 已尝试次数` 秒之后再试，直到用完 `max_attempts`。判断一个错误该不该重试时，可以直接对照下表。

| function | 立即失败，不重试 | 按 `retry` 重试 |
| --- | --- | --- |
| `DirectorySource`、`FilteredDirectorySource`、`FileHashSource` | 缺 `directory`、目录不存在、`filter` 写错、`paths` 写错、占位符没有值、路径指向的文件不存在、`data` 不是 UTF-8、`tag.json` 不是对象 | 无 |
| `TemplateToPrompt` | 缺 `template`、模板文件不在 home 里、模板引用了不存在的变量 | 无 |
| `JinjaToJsonnet` | 缺 `template`、上游正文为空或不是 JSON 对象、渲染结果只有空白 | 无 |
| `JsonnetToPrompt` | 找不到 `jsonnet` | 编译器返回非零状态 |
| `Command` | 缺 `argv`、找不到第一项命令、花括号变量不存在、`capture` 取值不对 | 进程返回非零状态、命令没有写出 `output_file` |
| `PromptToLLM` | 缺 `workspace` 或目录不存在、找不到工具、工具定义不合法、找不到第一项命令 | 进程返回非零状态、写出的 `data` 为空、不是 UTF-8，或 `data` 不是文件 |
| `TemplateToLLM`、`EntityTemplateToLLM` | 缺 `template`、`workspace` 或目录不存在、`header` / `tag_template` 写错、模板引用了不存在的变量、`staging` 的文件名不合法或文件不存在、回复里没有 `header`、找不到工具、工具定义不合法、找不到第一项命令。`TemplateToLLM` 还会在上游个数写错时立即失败 | 进程返回非零状态 |
| `Output` | `directory` 不是非空字符串、`filename` 不是非空字符串、`rename` 得到的文件名不合法、两个实体得到同一个文件名 | 写出 `.staging` 文件时的瞬时错误 |

## 八、渲染类 function 与模板变量

本章说明 docorder 自带的 map function 在渲染模板或替换命令参数时，可以使用哪些数据，以及当这些内置数据不够用时，如何加入新的模板变量。

### RenderedMap 的三个步骤

`RenderedMap` 的完整写法是 `docorder.functions.rendered_map:RenderedMap`，它是 `MapFunction` 的子类，把处理一个实体的过程拆成三个先后进行的步骤。第一步是 `read_source`，读取上游实体，默认返回上游实体的正文；第二步是 `apply_render`，把第一步读到的内容转换成输出实体的正文，这是一个抽象方法，每个子类都必须实现它，例如 `TemplateToPrompt` 在这里渲染模板，`Command` 在这里运行命令；第三步是 `generate_props`，根据第二步的结果生成输出实体的附加信息，默认是上游实体附加信息的一份副本。这三个步骤都会收到同一个名为 `Environment` 的对象，称为渲染环境，它汇集了渲染时可以使用的全部数据。

普通的 `MapFunction` 需要分别实现 `transform_data` 和 `transform_props` 两个方法，runner 会先后调用它们。`RenderedMap` 已经替子类实现了这两个方法，并且保证对同一个上游实体和目标实体，上述三个步骤只执行一次，正文和附加信息都来自同一次执行的结果。因此，像外部命令或大模型这样耗时较长的调用，每个实体只会发生一次。

### 渲染环境

渲染环境是 `environment.template_env`，一份嵌套字典，模板和命令都读它。

```text
template_env
  operator                        function 参数，外加本次运行的 name、home
  job                             name、epoch
  entity                          正在渲染的实体
    source_name, source_data, source_tag, source_data_path
    target_name, target_data_path, output
```

`TemplateToPrompt` 把这份字典交给 Jinja。`Command` 按 `{operator.home}`、`{entity.output}` 这种点路径替换。`JinjaToJsonnet` 也用它，并另外把 `home` 放到最外层。实体的附加信息在 `entity.source_tag` 里，不再提升到最外层。

### 内置模板变量

下表列出了 `TemplateToPrompt` 的模板和 `Command` 的占位符可以使用的变量。Jinja 写成 `{{ operator.name }}`，`Command` 写成 `{operator.home}`。

<!-- figure:variables:start -->
<figure class="figure" id="fig-variables">
<svg role="img" aria-labelledby="variables-title variables-desc" viewBox="0 0 900 560" width="100%" style="max-width:900px">
  <title id="variables-title">内置模板变量</title>
  <desc>template_env 的顶层只有 operator、job、entity 三个名字；operator 是被 config 覆盖过的函数参数再加上 runner 填入的几项，job 是作业名和本次 epoch，entity 分成上游实体与正在写出的实体两组。</desc>
  <defs>
    <marker id="variables-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#5e584e"/>
    </marker>
    <marker id="variables-arrow-teal" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1b4744"/>
    </marker>
    <marker id="variables-arrow-moss" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1d6842"/>
    </marker>
  </defs>
  <rect width="900" height="560" fill="#f6f1e8"/>
  <path d="M 450 104 L 450 128 L 173 128 Q 165 128 165 136 L 165 156" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#variables-arrow)"/>
  <path d="M 450 104 L 450 128 L 418 128 Q 410 128 410 136 L 410 156" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#variables-arrow)"/>
  <path d="M 450 104 L 450 128 L 687 128 Q 695 128 695 136 L 695 156" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#variables-arrow)"/>
  <path d="M 165.0 332 L 165.0 396" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#variables-arrow)"/>
  <path d="M 410.0 332 L 410.0 396" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#variables-arrow)"/>
  <path d="M 695.0 332 L 695.0 396" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#variables-arrow)"/>
  <rect x="280" y="40" width="340" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="280" y="40" width="340" height="64" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="70" fill="#1c1915" font-size="13" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">template_env</text>
  <text x="450" y="87" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">模板读 {{…}}，Command 读 {…}</text>
  <rect x="30" y="156" width="270" height="176" rx="6" fill="#f6f1e8"/>
  <rect x="30" y="156" width="270" height="176" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="44" y="179" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">operator</text>
  <text x="44" y="201" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">name   home   function_class</text>
  <text x="44" y="219" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">type   operator_home</text>
  <text x="44" y="245" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">函数参数：props.json 去掉保留键，</text>
  <text x="44" y="263" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">再被节点的 config 覆盖</text>
  <text x="44" y="281" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">例：template · directory</text>
  <rect x="320" y="156" width="180" height="176" rx="6" fill="#f6f1e8"/>
  <rect x="320" y="156" width="180" height="176" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="334" y="179" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">job</text>
  <text x="334" y="201" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">name</text>
  <text x="334" y="219" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">epoch</text>
  <text x="334" y="245" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">作业的名字，和这次</text>
  <text x="334" y="263" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">运行使用的 epoch</text>
  <rect x="520" y="156" width="350" height="176" rx="6" fill="#f6f1e8"/>
  <rect x="520" y="156" width="350" height="176" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="534" y="179" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">entity</text>
  <text x="534" y="201" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source_name    source_data</text>
  <text x="534" y="219" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source_tag     source_data_path</text>
  <text x="534" y="237" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">target_name    target_data_path</text>
  <text x="534" y="255" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">output</text>
  <text x="534" y="281" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">前四个是上游实体，后三个是</text>
  <text x="534" y="299" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">正在写出的那个实体</text>
  <rect x="30" y="396" width="270" height="84" rx="6" fill="#f6f1e8"/>
  <rect x="30" y="396" width="270" height="84" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="44" y="419" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">参数来源</text>
  <text x="44" y="441" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">props.json + 节点 config</text>
  <text x="44" y="459" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">runner 再补上 name / home / type</text>
  <rect x="320" y="396" width="180" height="84" rx="6" fill="#f6f1e8"/>
  <rect x="320" y="396" width="180" height="84" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="334" y="419" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">作业来源</text>
  <text x="334" y="441" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">execute(job, epoch)</text>
  <text x="334" y="459" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">调用时给的两个参数</text>
  <rect x="520" y="396" width="350" height="84" rx="6" fill="#f6f1e8"/>
  <rect x="520" y="396" width="350" height="84" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="534" y="419" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">实体来源</text>
  <text x="534" y="441" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">上游实体 + 正在写出的实体</text>
  <text x="534" y="459" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">entity.source_tag 是上游的 tag.json</text>
  <text x="40" y="516" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">JinjaToJsonnet 的最外层不同：上游 JSON 的各个键 + variables 参数 + operator / job / entity / home。</text>
</svg>
<figcaption><span class="fig-label">图 6</span> 内置模板变量：顶层只有 operator、job、entity 三个名字，每一组都有各自的来源。</figcaption>
</figure>
<!-- figure:variables:end -->

| 变量 | 内容 |
| --- | --- |
| `operator.name` | 当前节点的名字 |
| `operator.home` | 当前算子 home 的绝对路径 |
| `operator.<参数名>` | function 的参数，例如 `operator.template` |
| `job.name`、`job.epoch` | 作业名和本次 epoch |
| `entity.source_name`、`entity.source_data`、`entity.source_tag`、`entity.source_data_path` | 上游实体 |
| `entity.target_name`、`entity.target_data_path`、`entity.output` | 正在写出的实体 |

不同的渲染类 function 使用这些变量的方式有所不同，下面分别说明。

`TemplateToPrompt` 使用 Jinja 渲染模板，因此可以使用 Jinja 的全部语法，例如用 `{% for column in entity.source_tag.columns %} ... {% endfor %}` 遍历一个列表，用 `{{ entity.source_name | upper }}` 把文本转换成大写。正如第七章所说，它使用严格模式，引用不存在的变量会导致失败。

`Command` 不使用 Jinja，它只识别 `{名字}` 形式的占位符。名字中可以用点号逐层访问嵌套的对象，例如 `{entity.source_tag.global_prop.project}` 表示上游附加信息中 `global_prop` 对象里的 `project`。占位符的名字只能由字母、数字、下划线和点号组成，它解析的字典和模板一样，就是 `template_env`，所以顶层只有 `operator`、`job`、`entity` 这三个名字可用。`Command` 会替换 `argv` 中的每一项和 `output_file`，但不会替换 `cwd`。如果占位符引用的名字不存在，会以 `FatalError` 错误失败。

`JinjaToJsonnet` 也使用 Jinja，但最外层的变量不同：最外层是上游正文这个 JSON 对象中的各个键和 `variables` 参数中的各个键，再加上 `operator`、`job`、`entity` 和 `home` 四个键，其中 `home` 就是 `operator.home`。上游附加信息中的键不在最外层，需要写成 `entity.source_tag.<键>` 来访问。如果上游 JSON 中恰好有名为 `operator`、`job`、`entity` 或 `home` 的键，它们会被这四个内置的键覆盖。此外，它还额外提供了 `jsonnet` 过滤器。

`JsonnetToPrompt` 不渲染任何模板。`PromptToLLM` 也不渲染提示词，它只在工具定义的 `run` 中替换 `{workspace}` 这一个占位符。

### 增加模板变量

当内置的变量不能满足需要时，可以用下面六种方法加入新的变量。它们按照所需改动从小到大的顺序排列，通常应该优先考虑排在前面的方法。

#### 在 props.json 或节点 config 中加入参数

function 参数中任何不属于保留键的键，都会出现在 `operator` 中。例如在 `props.json` 中写入 `"audience": "业务分析师"`，模板中就可以用 `{{ operator.audience }}` 引用它，`Command` 中可以用 `{operator.audience}` 引用它。同一个键也可以在添加节点时通过 `config` 指定，或者覆盖 `props.json` 中的默认值，例如 `config={"audience": "数据工程师"}`，模板读到的就是 `数据工程师`。这种方法适合放置固定不变的数据：写在 `props.json` 中，适合「同一个模板，在不同的算子 home 中取不同的值」；写在节点的 `config` 中，适合「同一个算子 home，在不同的作业或节点中取不同的值」。

#### 让上游把数据写进 tag.json

上游实体附加信息中的每个键，都会出现在下游模板的 `entity.source_tag` 下，因此可以让上游步骤把需要的数据写进它的 `tag.json`。如果上游是一个 source 节点，可以编写 `DirectorySource` 的子类并覆盖 `extract_tag` 方法，把从文件内容中解析出来的字段放进附加信息，下游的模板就能引用这些字段。例如第十章的 `TableSource` 把 JSON 格式的表定义解析成 `table`、`description`、`columns` 三个键，于是下游的模板中可以直接写 `{% for column in entity.source_tag.columns %}`。

#### 用 generate_props 产生新的键

如果上游本身是一个渲染类的 map 节点，可以覆盖它的 `generate_props` 方法，在上游附加信息的副本上添加新的键，这样它的下游模板就能读到这些新键。下面的例子统计上游正文中的单词数，把这个数字作为正文，同时把它记录在附加信息的 `words` 键中：

```python
from docorder.functions.rendered_map import RenderedMap


class WordCount(RenderedMap):
    def apply_render(self, source, source_entity, environment):
        return str(len(source.split()))

    def generate_props(self, rendered, source, source_entity, environment):
        props = source_entity.carried_tag()
        props["words"] = int(rendered)
        return props
```

在这个节点的下游，模板中就可以写 `{{ entity.source_tag.words }}` 了。这里的 `carried_tag()` 返回上游附加信息的一份副本，在副本上修改不会影响上游实体本身。

#### 用 global_prop 跨越多个步骤传递数据

附加信息中的 `global_prop` 对象会被 runner 自动合并到每一个下游实体中，即使中间某个 function 产生的附加信息没有包含它，例如 `JinjaToJsonnet` 产生的附加信息是一个空对象，它也不会丢失。这种方法适合放置「从作业起点开始，后面每一步都可能用到」的数据，例如项目名称或批次编号。在 source 节点的附加信息中写入 `"global_prop": {"project": "订单域"}`，之后任何一个下游节点的模板都可以用 `{{ entity.source_tag.global_prop.project }}` 引用它，`Command` 中则写成 `{entity.source_tag.global_prop.project}`。

#### 利用 JinjaToJsonnet 的上游 JSON 和 variables 参数

对于 `JinjaToJsonnet`，上游正文这个 JSON 对象中的每个键都是最外层的变量，`variables` 参数为这些变量提供默认值。因此，要为它加入新的变量，可以让上游在 JSON 中多写一个键，也可以在 `props.json` 或节点的 `config` 中往 `variables` 里加一项。`variables` 是一个普通的 function 参数，所以节点的 `config` 可以覆盖它。

#### 继承渲染类并覆盖 apply_render

如果需要的值必须在渲染时才能计算出来，例如当天的日期、正文的行数，或者需要从其它地方查询得到的数据，可以编写 `TemplateToPrompt` 的子类并覆盖 `apply_render` 方法：先调用 `environment.template_env` 取得全部内置变量，再往里面加入新的键，然后交给父类提供的 `render` 方法完成渲染。

```python
from datetime import date

from docorder.functions.impl.template_to_prompt import TemplateToPrompt


class DatedPrompt(TemplateToPrompt):
    def apply_render(self, source, source_entity, environment):
        values = environment.template_env
        values["today"] = date.today().isoformat()
        values["line_count"] = len(source.splitlines())
        template = self.artifact.read_text(self.environment.operator_props["template"])
        return self.render(template, values, source_entity.name)
```

把这个类放进算子 home 的 `primary.py` 文件，在 `props.json` 中写上 `"class": "primary:DatedPrompt"` 和 `"template": "lib/p.jinja"`，模板中就可以使用 `{{ today }}` 和 `{{ line_count }}`，原有的内置变量也照样可以使用。方法中的 `source` 是 `read_source` 返回的上游正文，`self.artifact.read_text` 用于读取算子 home 中的文件，第九章会介绍它。需要注意的是，这些在渲染时注入的值不会被记进上游快照，例如日期变了，已经完成的实体并不会因此被重新处理。

对于 `JinjaToJsonnet`，做法与此类似：编写它的子类并覆盖 `read_source` 方法，在它返回的字典中加入新的键即可，因为这个字典中的键就是模板最外层的变量。

### 变量同名时以谁为准

当不同来源的变量重名时，按照以下规则决定最终生效的值。在 `entity` 中，`source_name`、`source_data`、`source_tag`、`source_data_path`、`target_name`、`target_data_path` 和 `output` 这几个名字是固定的，上游附加信息中的同名键不会出现在这里，只在 `entity.source_tag` 中。在 `operator` 中，节点 `config` 里的参数先覆盖 `props.json` 中的同名参数，然后 runner 再填入 `name`、`home`、`function_class`、`type` 和 `operator_home`，这几个键会覆盖前面的同名键。`class`、`parallelism`、`retry`、`type` 和 `home` 是 `props.json` 的保留键，不会作为 function 参数传下去。在 `JinjaToJsonnet` 中，上游 JSON 中的键会覆盖 `variables` 中的同名键，而 `operator`、`job`、`entity` 和 `home` 这四个内置的键又会覆盖上游 JSON 中的同名键。

## 九、开发自己的 function

当 docorder 自带的 function 不能满足需要时，可以自己编写 function。编写 function 的基本方式是：定义一个 Python 类，让它继承 docorder 提供的某个基类，并实现基类规定的几个方法；然后在算子 home 的 `props.json` 中，把 `class` 指向这个类。本章依次说明应该选择哪个基类、方法中可以使用哪些对象、必须遵守哪些约定、代码文件放在哪里，并给出每种算子类型的完整示例和测试方法。本章的所有示例代码都已经实际运行验证过。

### 选择基类

下表按照「你要做的事情」列出了应该继承的基类，以及必须实现和可以选择覆盖的方法。「必须实现」的方法是基类中的抽象方法，也就是基类只声明了名字、没有提供实现的方法，如果子类没有实现它们，装配阶段会以 `OperatorValidationError` 错误失败；「可以覆盖」的方法在基类中已经有默认实现，只有需要改变默认行为时才需要重写。

| 要做的事情 | `type` | 继承的基类 | 必须实现 | 可以覆盖 |
| --- | --- | --- | --- | --- |
| 从任意外部数据产生实体 | source | `docorder.functions.source_function:SourceFunction` | `emit()` | 无 |
| 从目录产生实体，但需要修改附加信息或挑选文件 | source | `DirectorySource` 或 `FilteredDirectorySource` | 无 | `extract_tag(name, content, tag)`、`include(path)`、`generate(directory)` |
| 逐个转换实体，正文和附加信息可以分别计算 | map | `docorder.functions.map_function:MapFunction` | `transform_data(source, target)`、`transform_props(source, target)` | 无 |
| 逐个转换实体，附加信息依赖转换的结果 | map | `docorder.functions.rendered_map:RenderedMap` | `apply_render(source, source_entity, environment)` | `read_source`、`generate_props` |
| 在自带的渲染类 function 上增加功能 | map | `TemplateToPrompt` 等自带的类 | 无 | `apply_render`、`generate_props` 等 |
| 把全部实体合并成一个 | reduce | `docorder.functions.reduce_function:ReduceFunction` | `transform_data(sources, target)`、`transform_props(sources, target)` | 无 |
| 把一个实体拆成多个 | fanout | `docorder.functions.fanout_function:FanoutFunction` | `transform_data(source, target)`、`transform_props(source, target)` | `output_names(source)` |
| 对每个上游实体做一次不产生数据的操作 | apply | `docorder.functions.apply_function:ApplyFunction` | `apply(entity)`，可选 `finish()` | 无 |

`SourceFunction` 的 `emit` 方法应该写成一个生成器，也就是在方法中用 `yield` 逐个交出结果，每次交出一个 `SourceRecord(name, data, tag)` 对象，三个参数分别是实体名、正文和附加信息。`SourceRecord` 同样定义在 `docorder.functions.source_function` 中。

### function 中可以使用的对象

在 function 的方法中，可以通过 `self` 访问以下属性：

| 属性 | 内容 |
| --- | --- |
| `self.operator` | 正在运行的算子。`name`、`props`、`output_path`、`operator_home`、`upstream` 都在算子上，不要再经过节点 |
| `self.environment` | 由 operator 构造。`operator_props` 是 function 参数；`template_env` 是模板里的 `operator` / `job` / `entity` |
| `self.artifact` | 对算子 home 的只读访问：`home` 是算子 home 的路径；`path(rel)` 把一个相对路径解析成算子 home 中的完整路径；`exists(rel)` 判断算子 home 中的某个文件是否存在；`read_text(rel)` 读取算子 home 中的某个文件。传入的路径都不能指向算子 home 之外 |
| `self.operator_name` | 当前节点的名字 |
| `self.epoch` | 本次运行的 epoch |

传给方法的上游实体和目标实体都是 `Entity` 对象，它们提供以下成员：

| 成员 | 内容 |
| --- | --- |
| `name` | 实体的名字 |
| `directory` | 实体目录的路径 |
| `read_text()` | 读取实体的正文；如果没有 `data` 文件，返回空字符串 |
| `tag` | 实体的附加信息，一个字典 |
| `carried_tag()` | 返回附加信息的一份浅拷贝，用于传给下游 |
| `staging_data` | 目标实体等待写入的正文，function 在 `transform_data` 中给它赋值 |

### 必须遵守的约定

`transform_data` 必须给 `target.staging_data` 赋一个字符串，`transform_props` 必须给 `target.tag` 赋一个字典，否则这个实体会以 `FatalError` 错误失败。如果目标目录里已经有 `data` 文件，可以不设 `staging_data`，runner 会保留该文件，只写 `tag.json`。如果要在上游附加信息的基础上做修改，应该先调用 `carried_tag()` 取得一份副本再修改，不要直接修改上游实体的 `tag`。`carried_tag()` 返回的是浅拷贝，也就是说只复制了最外层，嵌套在里面的列表和字典仍然与上游共用，所以如果要修改嵌套的内容，应该先自己复制一份。

function 不需要、也不应该自己写 `data` 和 `tag.json`，它们都由 runner 负责写入。function 也不需要自己创建线程池或者实现重试逻辑，并行和重试分别由节点的 `parallelism` 和 `retry` 参数控制。

function 中出现错误时，应该区分两类情况。第一类是重试也无法解决的问题，例如缺少必需的配置、输入的格式不正确，这时应该抛出 `docorder.utils.errors.FatalError`，让 stage 立即停止，避免白白浪费重试的时间。第二类是可能自行恢复的问题，例如网络错误、外部服务暂时不可用、外部进程偶尔失败，这时应该抛出其它类型的异常，交给 `retry` 机制自动重试。

runner 在处理每个实体的每一次尝试时，都会创建一个新的 function 对象，因此不要在对象的属性中保存需要跨实体使用的状态。并行执行时，function 运行在工作线程中，和算子共享同一份内存。

function 可以在 `target.directory` 也就是目标实体的目录中写入一些辅助文件，例如 `Command` 就会把命令的输出文件写在这里。这些辅助文件会在实体被重做或删除时随着实体目录一起被清除。

function 读取的、不属于上游实体的任何内容，例如算子 home 中的模板、其它节点的结果文件、外部服务返回的数据，都不会被记进上游快照，它们发生变化时，runner 不会自动重做已经完成的实体。

### 代码放在哪里

function 的代码有两种放置方式。

第一种方式是放在算子 home 自己的 `primary.py` 文件中，并在 `props.json` 中写 `"class": "primary:类名"`。这是最简单的方式，代码和配置、模板一起放在算子 home 里，复制算子 home 时代码也随之带走。一个算子 home 只能有一个 `primary.py`，但其中可以定义多个类。需要注意的是，`primary.py` 是按照文件路径直接加载的，算子 home 所在的目录并不在 Python 的模块搜索路径 `sys.path` 中，所以 `primary.py` 不能用 `import` 引入同一个算子 home 中的其它 Python 文件；不过它可以正常引入 docorder 和其它已经安装的包。

第二种方式是放在你自己项目的 Python 包中，并在 `props.json` 中写 `"class": "包名.模块名:类名"`。当多个算子 home 需要共用同一段代码，或者 function 的代码较多、需要拆分成多个模块时，适合使用这种方式。这个包必须能够被 Python 导入，例如已经安装在同一个虚拟环境中，或者与启动脚本位于同一个目录下。并行执行也在同一进程里，用的是同一份导入。

### 示例：自定义 source

下面的 source function 从一个 JSON Lines 文件中产生实体。JSON Lines 是一种每行一个 JSON 对象的文本格式，常用于存放一批记录。这个 function 为文件中的每一行产生一个实体：

```python
import json
from pathlib import Path

from docorder.functions.source_function import SourceFunction, SourceRecord
from docorder.utils.errors import FatalError


class JsonLinesSource(SourceFunction):
    def emit(self):
        raw = self.environment.operator_props.get("file")
        if not raw:
            raise FatalError("jsonl source config missing file")
        path = Path(raw)
        if not path.is_absolute():
            path = self.artifact.home / path
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            yield SourceRecord(
                name=record["id"],
                data=json.dumps(record, ensure_ascii=False),
                tag={"kind": record.get("kind", "")},
            )
```

对应的 `props.json`：

```json
{ "type": "source", "class": "primary:JsonLinesSource", "file": "items.jsonl" }
```

这个 function 从参数 `file` 读取文件路径，相对路径按算子 home 解析；参数缺失时抛出 `FatalError`，因为这是重试也无法解决的配置问题。`items.jsonl` 中每一行的 `id` 字段成为实体的名字，整行 JSON 成为实体的正文，`kind` 字段被记入附加信息。每行的 `id` 必须符合实体命名规则，而且彼此不能重复，否则这个 stage 会以 `OperatorValidationError` 错误失败。

### 示例：map

下面的 map function 把上游正文转换成大写，并在附加信息中加上一个标记：

```python
from docorder.functions.map_function import MapFunction


class Uppercase(MapFunction):
    def transform_data(self, source, target):
        target.staging_data = source.read_text().upper()

    def transform_props(self, source, target):
        tag = source.carried_tag()
        tag["uppercased"] = True
        target.tag = tag
```

对应的 `props.json`：

```json
{ "type": "map", "class": "primary:Uppercase" }
```

runner 会先调用 `transform_data`，再调用 `transform_props`，两者是分开调用的。如果两个方法都需要用到同一个中间结果，特别是需要一次耗时的外部调用才能得到的结果，就不适合直接继承 `MapFunction`，因为那样的话这个调用可能要做两次；这时应该改为继承 `RenderedMap`，它保证每个实体只计算一次。

### 示例：基于 RenderedMap

第八章「用 generate_props 产生新的键」一节中的 `WordCount`，就是一个完整的 `RenderedMap` 子类：`apply_render` 返回输出实体的正文，`generate_props` 在上游附加信息的副本上加入 `words` 键作为输出实体的附加信息。如果在转换之前需要先读取其它内容，例如把上游正文解析成 JSON，可以覆盖 `read_source` 方法，它的返回值会作为第一个参数 `source` 传给 `apply_render`。

### 示例：reduce

下面的 reduce function 把上游全部实体的正文用一个分隔符连接起来，合并成一个实体：

```python
from docorder.functions.reduce_function import ReduceFunction


class JoinBodies(ReduceFunction):
    def transform_data(self, sources, target):
        separator = self.environment.operator_props.get("separator", "\n")
        target.staging_data = separator.join(entity.read_text() for entity in sources)

    def transform_props(self, sources, target):
        target.tag = {"count": len(sources), "names": [entity.name for entity in sources]}
```

对应的 `props.json`：

```json
{ "type": "reduce", "class": "primary:JoinBodies", "output": "all", "separator": "\n---\n" }
```

输出实体的名字由 `output` 参数决定，这里是 `all`；`separator` 是这个 function 自己定义的参数，通过 `self.environment.operator_props` 读取。传入的 `sources` 是按实体名字排序的上游实体列表；如果上游一个实体都没有，`sources` 是一个空列表，function 仍然会被调用一次，所以代码要能正确处理空列表的情况。

### 示例：fanout

下面的 fanout function 把上游的每个实体按行拆开，每一行成为一个新的实体：

```python
from docorder.functions.fanout_function import FanoutFunction


class SplitLines(FanoutFunction):
    def output_names(self, source):
        count = len(source.read_text().splitlines())
        return [f"{source.name}-{index}" for index in range(count)]

    def transform_data(self, source, target):
        index = int(target.name.rsplit("-", 1)[1])
        target.staging_data = source.read_text().splitlines()[index]

    def transform_props(self, source, target):
        target.tag = source.carried_tag()
```

对应的 `props.json`：

```json
{ "type": "fanout", "class": "primary:SplitLines" }
```

如果上游实体 `notes` 的正文有三行，这个 function 会产生 `notes-0`、`notes-1`、`notes-2` 三个实体。由于整个 stage 中所有输出实体的名字必须互不相同，这里在名字前面加上了上游实体的名字作为前缀，以免不同上游实体拆出的名字发生冲突。`output_names` 必须返回一个列表；`transform_data` 根据目标实体名字中的序号，取出对应的那一行作为正文。

### 测试 function

测试 function 最直接的方法，是在一个临时目录中搭建一个只有几个节点的小作业，运行之后检查输出文件的内容。下面的 pytest 测试用例检查第十章中的 `TableIndex`：它把项目中的 `homes/` 目录复制到 pytest 提供的临时目录 `tmp_path` 中，用 pytest 的 `monkeypatch` 工具设置 `DOCORDER_HOMES` 环境变量（测试结束后会自动恢复），写入一个输入文件，然后运行 source 和 reduce 两个节点，最后检查汇总结果中是否包含这张表。

```python
import json
import shutil
from pathlib import Path

from docorder.core.job import Job
from docorder.core.runner import execute

PROJECT = Path(__file__).resolve().parents[1]


def test_index_lists_every_table(tmp_path, monkeypatch):
    homes = tmp_path / "homes"
    shutil.copytree(PROJECT / "homes", homes)
    data = tmp_path / "tables"
    data.mkdir()
    (data / "orders.json").write_text(
        json.dumps({"table": "orders", "description": "订单", "columns": []}),
        encoding="utf-8",
    )
    monkeypatch.setenv("DOCORDER_HOMES", str(homes))

    job = Job("test", tmp_path / "runs")
    job.add_operator_node("tables", "table_source", config={"directory": str(data)})
    job.add_operator_node("index", "table_index", upstream="tables")
    execute(job, "t", start_from_scratch=True)

    index = (tmp_path / "runs" / "index" / "t" / "index" / "data").read_text(encoding="utf-8")
    assert "- orders：订单" in index
```

这个测试中的节点都没有设置 `parallelism`，所以全部在当前进程中运行，出错时异常信息和调用栈都比较直观，也方便设置断点调试。代码中的 `PROJECT` 假定这个测试文件位于项目的 `tests/` 目录下，`parents[1]` 就是项目的根目录。

## 十、在自己的项目中使用 docorder

本章用一个完整的例子，说明在自己的项目中使用 docorder 的全部步骤。假设项目名为 `my-docs`，其中有一批用 JSON 文件描述的数据表定义，我们希望为每张表生成一段提示词，交给命令行形式的大模型工具，让它写出这张表的说明，最后把所有表汇总成一份表清单。这个作业由四个节点组成，依次是 source、map、map 和 reduce，其中用到了两个 docorder 自带的 function 和两个自己编写的 function。本章的所有文件和命令都已经实际运行验证过。

### 第一步：安装 docorder

docorder 目前没有发布到 PyPI，所以不能直接用 `pip install docorder` 安装，需要先从源码仓库构建出安装包。下面的命令会克隆仓库，并用 uv 构建安装包。uv 是一个 Python 的包和项目管理工具，可以在它的官网找到安装方法。

```bash
git clone https://github.com/jixie-wish/docorder.git
cd docorder
uv build
```

构建完成后，仓库的 `dist/` 目录下会生成一个名为 `docorder-0.1.0-py3-none-any.whl` 的文件，这是 Python 的标准安装包格式。接下来创建自己的项目，并把这个安装包安装进去：

```bash
mkdir my-docs && cd my-docs
uv init --bare
uv add /path/to/docorder/dist/docorder-0.1.0-py3-none-any.whl
```

`uv init --bare` 只在当前目录生成一个最基本的 `pyproject.toml`，也就是 Python 项目的配置文件；`uv add` 会创建项目自己的虚拟环境，把 docorder 安装进去，并把这个依赖记录到 `pyproject.toml` 中。命令中的 `/path/to/docorder` 要换成你实际克隆仓库的位置。

如果你在使用 docorder 的同时还会修改 docorder 本身的代码，可以改用 `uv add --editable /path/to/docorder`，这种方式安装的 docorder 直接指向源码目录，修改源码后立即生效，不需要重新构建和安装。如果不使用 uv，也可以在自己的虚拟环境中执行 `pip install /path/to/docorder-0.1.0-py3-none-any.whl`。docorder 要求 Python 3.10 或更高的版本，它依赖的 jinja2、python-dotenv、pyyaml 和 tqdm 四个包会在安装时一并装好。

### 第二步：规划目录

在开始编写文件之前，先规划好项目的目录结构。下面是这个示例项目最终的样子：

```text
my-docs/
  pyproject.toml
  run.py                          启动脚本：构建作业并执行
  data/
    tables/                       输入数据，每张表一个实体目录
      orders/
        data                      表定义，正文
        tag.json                  表的附加信息
      users/
        data
        tag.json
  homes/                          DOCORDER_HOMES 指向这里
    sources/
      table_source/               source 算子：读取 data/tables
        props.json
        primary.py                自己编写的 function：TableSource
    render/
      table_prompt/               map 算子：渲染提示词
        props.json
        lib/table.jinja
    llm/
      ask_llm/                    map 算子：调用大模型工具
        props.json
        tools/echo.json
    summary/
      table_index/                reduce 算子：汇总表清单
        props.json
        primary.py                自己编写的 function：TableIndex
  workspace/                      大模型工具的工作目录，由 run.py 自动创建
  runs/                           输出根目录，不纳入版本管理
```

这个结构中的每个部分各有分工。输入数据放在 `data/` 目录中，它属于项目本身，由 source 节点读取，docorder 不会修改其中的任何文件。算子放在 `homes/` 目录中，按用途分在几个分类子目录下，每个算子 home 一个目录，自己编写的 function 放在各自算子 home 的 `primary.py` 文件中。运行结果全部写在 `runs/` 目录中，它完全由 docorder 管理，可以随时删除后重新生成。`run.py` 是整个作业唯一的入口，负责设置 `DOCORDER_HOMES`、构建作业和启动运行。

### 第三步：准备输入数据

`DirectorySource` 读取的是已经写成实体形状的子目录：每个子目录是一张表，目录名是实体名，里面要有 `data` 和 `tag.json` 两个文件。因此 `data/tables/` 下的结构是这样的：

```text
data/tables/
  orders/
    data                          表定义，正文
    tag.json                      表的附加信息
  users/
    data
    tag.json
```

`data/tables/orders/data` 的内容是这张表的定义：

```json
{
  "table": "orders",
  "description": "每笔订单一行",
  "columns": [
    {"name": "order_id", "type": "bigint", "comment": "订单号"},
    {"name": "user_id", "type": "bigint", "comment": "下单用户"},
    {"name": "amount", "type": "decimal(10,2)", "comment": "订单金额"}
  ]
}
```

`data/tables/orders/tag.json` 的内容是这张表的附加信息，最少写一个空对象：

```json
{}
```

`users` 的结构与 `orders` 相同，只是描述的是用户表，有 `user_id` 和 `city` 两个字段。实体名就是目录名本身，因此目录名需要符合实体命名规则：不能为空，不能含 `/` 或 `\`，也不能以 `.` 或 `_` 开头。这个目录中如果还有普通文件，例如一份说明文档，它们不是实体，不会被读取。

### 第四步：编写算子 home

#### table_source：读取表定义

这个算子负责读取 `data/tables/` 中的实体目录，并把正文里的字段解析出来，放进实体的附加信息中，供下游的模板使用。

`homes/sources/table_source/props.json` 的内容如下：

```json
{
  "type": "source",
  "class": "primary:TableSource",
  "project": "订单域"
}
```

`homes/sources/table_source/primary.py` 的内容如下：

```python
import json

from docorder.functions.impl.directory_source import FilteredDirectorySource
from docorder.utils.errors import FatalError


class TableSource(FilteredDirectorySource):
    def extract_tag(self, name, content, tag):
        tag = dict(tag)
        try:
            spec = json.loads(content)
        except json.JSONDecodeError as exc:
            raise FatalError(f"{name} is not valid JSON: {exc}") from exc
        tag["table"] = spec["table"]
        tag["description"] = spec.get("description", "")
        tag["columns"] = spec.get("columns", [])
        tag["global_prop"] = {"project": self.environment.operator_props.get("project", "")}
        return tag
```

`TableSource` 继承了 `FilteredDirectorySource`，因此「读取实体目录」的行为直接沿用父类的实现。这个例子没有配置 `filter`，父类的筛选规则不生效，`data/tables/` 下的每个实体目录都会被收成记录。它只覆盖了 `extract_tag` 方法：先拿到输入目录里的 `tag.json`，再解析 `data` 的 JSON，把 `table`、`description` 和 `columns` 三个字段加进去；如果正文不是合法的 JSON，就抛出 `FatalError`，因为这种错误重试也无法解决。最后，它把 `props.json` 中自定义的参数 `project` 放进 `global_prop`，这样项目名称会被 runner 一路传递到最后的汇总节点。你可能注意到 `props.json` 中没有写 `directory` 参数，这是因为输入目录属于项目而不属于算子，它会由 `run.py` 通过节点的 `config` 传入，这样这个算子 home 就可以原样复制到其它项目中使用。

#### table_prompt：渲染提示词

这个算子直接使用 docorder 自带的 `TemplateToPrompt`，不需要编写任何代码，只需要准备 `props.json` 和模板文件。

`homes/render/table_prompt/props.json` 的内容如下：

```json
{
  "type": "map",
  "class": "docorder.functions.impl.template_to_prompt:TemplateToPrompt",
  "template": "lib/table.jinja",
  "audience": "业务分析师"
}
```

`homes/render/table_prompt/lib/table.jinja` 的内容如下：

```text
请为{{ operator.audience }}写一段 {{ entity.source_tag.table }} 表的说明。

项目：{{ entity.source_tag.global_prop.project }}
用途：{{ entity.source_tag.description }}

| 字段 | 类型 | 含义 |
| --- | --- | --- |
{% for column in entity.source_tag.columns -%}
| {{ column.name }} | {{ column.type }} | {{ column.comment }} |
{% endfor %}
```

模板中用到的变量来自三个不同的地方。`entity.source_tag.table`、`entity.source_tag.description` 和 `entity.source_tag.columns` 来自上游实体的附加信息，也就是 `TableSource` 解析出来的字段；`entity.source_tag.global_prop.project` 同样来自上游附加信息中的 `global_prop`；`operator.audience` 则来自这个算子 home 的 `props.json` 中自定义的参数 `audience`。模板中的 `{% for column in entity.source_tag.columns -%}` 遍历字段列表，为每个字段输出一行表格，`-%}` 中的减号用于去掉这个标签之后的换行，使输出的表格行之间不留空行。

#### ask_llm：调用大模型工具

这个算子使用 docorder 自带的 `PromptToLLM`，把上一步生成的提示词交给大模型工具。

`homes/llm/ask_llm/props.json` 的内容如下：

```json
{
  "type": "map",
  "class": "docorder.functions.impl.prompt_to_llm:PromptToLLM",
  "tool": "echo",
  "retry": { "max_attempts": 3, "backoff_seconds": 5 }
}
```

`homes/llm/ask_llm/tools/echo.json` 的内容如下：

```json
{
  "name": "echo",
  "run": ["cat"],
  "prompt": "stdin"
}
```

`tool` 参数的值 `echo` 会让 `PromptToLLM` 去读取这个算子 home 中的 `tools/echo.json`。这个工具定义使用系统命令 `cat`，把从标准输入收到的提示词原样打印出来，它只是为了让这个示例不依赖任何真实的大模型服务也能完整运行。在实际使用时，你需要在 `tools/` 目录中另外新建一个工具定义文件，把其中的 `run` 换成你所用的大模型命令行工具，再把 `props.json` 中的 `tool` 改成这个新工具的名字。`retry` 配置表示每个实体最多尝试三次，这对于偶尔出错的大模型接口很有必要。`PromptToLLM` 必需的 `workspace` 参数同样由 `run.py` 通过节点的 `config` 传入。

#### table_index：汇总表清单

这个算子是一个自己编写的 reduce function，它把所有表的信息汇总成一份 Markdown 格式的表清单。

`homes/summary/table_index/props.json` 的内容如下：

```json
{
  "type": "reduce",
  "class": "primary:TableIndex",
  "output": "index",
  "title": "表清单"
}
```

`homes/summary/table_index/primary.py` 的内容如下：

```python
from docorder.functions.reduce_function import ReduceFunction


class TableIndex(ReduceFunction):
    def transform_data(self, sources, target):
        lines = [f"# {self.environment.operator_props.get('title', '表清单')}", ""]
        for entity in sources:
            lines.append(f"- {entity.tag.get('table', entity.name)}：{entity.tag.get('description', '')}")
        target.staging_data = "\n".join(lines) + "\n"

    def transform_props(self, sources, target):
        target.tag = {"tables": [entity.name for entity in sources]}
```

这个 reduce 节点的上游是 `ask_llm` 节点。由于 `TemplateToPrompt` 和 `PromptToLLM` 都会把上游的附加信息原样复制给下游，`TableSource` 最初解析出来的 `table` 和 `description` 一直被保留到了这里，所以 `TableIndex` 可以直接从每个上游实体的 `tag` 中读取它们。`title` 是这个 function 自定义的参数，用作清单的标题。输出实体的名字由 `output` 参数决定，即 `index`。

### 第五步：编写启动脚本

`run.py` 的内容如下：

```python
import argparse
import os
from pathlib import Path

from docorder.core.job import Job
from docorder.core.runner import execute

ROOT = Path(__file__).resolve().parent


def build_job() -> Job:
    job = Job("table-docs", ROOT / "runs")
    job.add_operator_node(
        "tables",
        "table_source",
        config={"directory": str(ROOT / "data" / "tables")},
    )
    job.add_operator_node("prompts", "table_prompt", upstream="tables", parallelism=2)
    job.add_operator_node(
        "answers",
        "ask_llm",
        upstream="prompts",
        config={"workspace": str(ROOT / "workspace")},
    )
    job.add_operator_node("index", "table_index", upstream="answers")
    return job


def main() -> None:
    parser = argparse.ArgumentParser(description="为 data/tables 下的表生成说明")
    parser.add_argument("epoch", help="本次运行的 epoch，例如 2026-10-16")
    parser.add_argument("--scratch", action="store_true", help="让 source 重新读取 data/tables")
    args = parser.parse_args()

    homes = [str(ROOT / "homes"), os.environ.get("DOCORDER_HOMES", "")]
    os.environ["DOCORDER_HOMES"] = os.pathsep.join(path for path in homes if path)
    (ROOT / "workspace").mkdir(exist_ok=True)

    execute(build_job(), args.epoch, start_from_scratch=args.scratch)
    print((ROOT / "runs" / "index" / args.epoch / "index" / "data").read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
```

这个脚本有几处值得说明。`build_job` 函数构建了一个包含四个节点的作业：`tables` 节点使用 `table_source` 算子，并通过 `config` 传入输入目录；`prompts` 节点以 `tables` 为上游，使用 `table_prompt` 算子，并设置 `parallelism=2`，允许最多两个线程同时渲染；`answers` 节点以 `prompts` 为上游，使用 `ask_llm` 算子，并通过 `config` 传入大模型工具的工作目录；`index` 节点以 `answers` 为上游，使用 `table_index` 算子。

`main` 函数用 Python 标准库 `argparse` 解析命令行参数：第一个参数是 epoch，可选的 `--scratch` 开关决定是否传入 `start_from_scratch=True`。设置 `DOCORDER_HOMES` 的代码必须放在调用 `build_job()` 之前，因为算子 home 是在添加节点时查找的；这里把项目自己的 `homes/` 放在最前面，使项目中的算子 home 优先于环境中原有的同名算子 home，同时保留环境变量中原有的目录。`os.pathsep` 是当前系统的路径分隔符，这样写可以同时适用于 macOS、Linux 和 Windows。脚本中的所有路径都从 `ROOT`，也就是脚本所在的目录出发计算，所以无论从哪个目录执行这个脚本，结果都相同。

项目特有的路径，也就是输入目录和工作目录，都通过节点的 `config` 传入，算子 home 中不包含任何与项目有关的路径，因此这些算子 home 可以原样复制到其它项目中使用。`prompts` 节点的 `parallelism=2` 会在当前进程里用两个线程同时渲染，不另起子进程。

### 第六步：运行并查看结果

在一个新的 epoch 上第一次运行时，需要加上 `--scratch`，让 source 节点读取输入数据：

```bash
uv run python run.py 2026-10-16 --scratch
```

运行结束后，脚本会打印汇总节点的结果：

```text
# 表清单

- orders：每笔订单一行
- users：注册用户
```

此时 `runs/` 目录的结构如下，每个节点都有一个与节点同名的目录，其中的 `2026-10-16/` 是 epoch 目录：

```text
runs/
  tables/   2026-10-16/{orders,users}/  data, tag.json
  prompts/  2026-10-16/{orders,users}/  data, tag.json
  answers/  2026-10-16/{orders,users}/  data, tag.json
  index/    2026-10-16/index/           data, tag.json
```

打开 `runs/prompts/2026-10-16/orders/data`，可以看到渲染好的提示词，模板中的各个变量都已经被替换成了实际的值：

```text
请为业务分析师写一段 orders 表的说明。

项目：订单域
用途：每笔订单一行

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| order_id | bigint | 订单号 |
| user_id | bigint | 下单用户 |
| amount | decimal(10,2) | 订单金额 |
```

再打开 `runs/index/2026-10-16/index/tag.json`，可以看到除了 `TableIndex` 写入的 `tables` 之外，还有从 source 节点一路传下来的 `global_prop`，尽管 `TableIndex` 并没有主动复制它。runner 另外还写了一个 `upstream` 键，记录参与这次汇总的每一个上游实体的快照，下面为了简洁没有列出：

```json
{
  "global_prop": {
    "project": "订单域"
  },
  "tables": [
    "orders",
    "users"
  ]
}
```

### 第七步：修改之后再次运行

项目投入使用之后，输入数据、模板和代码都会不断修改。不同的修改需要用不同的方式再次运行，这些方式都源自第三章「再次运行时的判定」一节中的规则。

如果运行中途失败了，例如大模型工具在用完全部重试次数后仍然报错，先修复导致失败的问题，然后用同一个 epoch 再运行一次，不需要加 `--scratch`：`uv run python run.py 2026-10-16`。已经完成的实体会因为比较通过而被保留，docorder 只会补做失败的实体，以及受它们影响的下游实体。

如果修改了输入数据，也就是在 `data/tables/` 中新增、修改或删除了实体目录，再次运行时必须加上 `--scratch`，source 节点才会重新读取目录。之后，只有正文真正发生变化的表会沿着作业图被重新处理，新增的表会被新建，删除的表会从下游各个节点中被删除，而汇总节点由于上游发生了变化，会重新生成表清单。例如新增一个 `payments/` 实体目录后加上 `--scratch` 再运行，表清单中会多出一行 `payments`；如果忘了加 `--scratch`，source 节点不会读取新目录，表清单也不会有任何变化。

如果修改了模板、`props.json` 中的参数或者 function 的代码，docorder 不会察觉到这些修改，需要先删除受影响节点的 epoch 目录，再运行一次。例如修改了 `table.jinja` 之后，执行 `rm -rf runs/prompts/2026-10-16` 删除提示词节点的结果，再执行 `uv run python run.py 2026-10-16`：`prompts` 节点会重新渲染所有提示词，由于提示词的内容变了，`answers` 和 `index` 两个节点也会随之重新处理。如果只希望个别实体被重新处理，可以只删除对应的实体目录，例如 `runs/prompts/2026-10-16/orders`。

如果希望保留当前的全部结果，另外完整地重新运行一遍，可以换一个新的 epoch，例如 `uv run python run.py 2026-10-17 --scratch`。旧 epoch 的目录不会被自动清理，不再需要时要手动删除。

### 纳入版本管理

项目中的 `data/`、`homes/`、`run.py`、`pyproject.toml` 和 `uv.lock`（uv 生成的依赖锁定文件）都应该纳入版本管理。`runs/` 和 `workspace/` 是运行时产生的文件，应该写进 `.gitignore`，避免被提交：

```text
runs/
workspace/
```

另外，不要把访问令牌、密码之类的凭据写进 `props.json` 或工具定义文件，因为这些文件会随项目一起被提交到代码仓库中。大模型工具需要的凭据应该放在环境变量中，由工具自己读取。

## 十一、数据治理案例

### 案例在仓库里的位置

`examples/data-governance/` 下有三个可运行的作业，都是真实的数据治理任务：

| 目录 | 作业做什么 | 规模 |
| --- | --- | --- |
| `documentation/` | 把表定义渲染成提示词，交给大模型写说明 | 最小，`make quality` 跑的就是它 |
| `dbt_model/` | 按表文档生成 dbt 模型（sql 与 yaml） | 中等，需要外部的大模型工具 |
| `semantic_layer/` | 建词根表、给模型分配词根、补成员属性 | 最完整，本章讲它 |

三个作业的代码都在各自的 `job.py` 里，算子 home 放在 `.op_home/` 下。第十章讲过怎么从零搭一个作业，这里讲一个已经搭好、而且比教程复杂得多的作业。

### 业务问题

数仓里有几百张 Hive 表，每张表由一个 dbt 模型描述。模型的 yml 里写着它的指标：指标名、描述、聚合方式。一个叫 `fct_refund` 的模型有 `refund_amount` 这样的指标，另一个模型可能有 `gmv_refunded`。

数据治理要回答的问题是：这些指标说的是不是同一件事。如果是，就要让它们共用一个名字、一份定义、一组别名，这样分析师写 SQL 时不用猜「退款金额」在下游到底叫什么。

这件事手工做要读几百份 yml，维护一张词根表，再给每个模型的每个指标填一个归属。工作量大，而且模型一改就得重来。

这个案例用四个作业接力完成，每个作业的产物交给下一个作业：

<!-- figure:pipeline:start -->
<figure class="figure" id="fig-pipeline">
<svg role="img" aria-labelledby="pipeline-title pipeline-desc" viewBox="0 0 900 500" width="100%" style="max-width:900px">
  <title id="pipeline-title">数据治理案例的四个作业</title>
  <desc>四个作业接力：建词根表、修词根表、给模型分配词根、补成员属性，每个作业的产物写进 .staging，交给下一个作业读取。</desc>
  <defs>
    <marker id="pipeline-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#5e584e"/>
    </marker>
    <marker id="pipeline-arrow-teal" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1b4744"/>
    </marker>
    <marker id="pipeline-arrow-moss" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1d6842"/>
    </marker>
  </defs>
  <rect width="900" height="500" fill="#f6f1e8"/>
  <path d="M 540 92 L 600 92" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#pipeline-arrow)"/>
  <path d="M 540 200 L 600 200" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#pipeline-arrow)"/>
  <path d="M 540 308 L 600 308" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#pipeline-arrow)"/>
  <path d="M 540 416 L 600 416" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#pipeline-arrow)"/>
  <path d="M 730 136 L 730 144 L 296 144 Q 290 144 290 150 L 290 156" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#pipeline-arrow)"/>
  <path d="M 730 244 L 730 252 L 296 252 Q 290 252 290 258 L 290 264" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#pipeline-arrow)"/>
  <path d="M 730 352 L 730 360 L 296 360 Q 290 360 290 366 L 290 372" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#pipeline-arrow)"/>
  <rect x="555" y="68" width="30" height="16" rx="2" fill="#f6f1e8"/>
  <text x="570" y="80" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">写出</text>
  <rect x="555" y="176" width="30" height="16" rx="2" fill="#f6f1e8"/>
  <text x="570" y="188" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">写出</text>
  <rect x="555" y="284" width="30" height="16" rx="2" fill="#f6f1e8"/>
  <text x="570" y="296" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">写出</text>
  <rect x="555" y="392" width="30" height="16" rx="2" fill="#f6f1e8"/>
  <text x="570" y="404" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">写出</text>
  <rect x="40" y="48" width="500" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="48" width="500" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="54" y="71" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">raw_root 作业：建词根表</text>
  <text x="54" y="93" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source → librarian → taxonomist_root → publish</text>
  <rect x="40" y="156" width="500" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="156" width="500" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="54" y="179" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">refine_root 作业：修词根表</text>
  <text x="54" y="201" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source → optimizer_root → merge_root → publish_final</text>
  <rect x="40" y="264" width="500" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="264" width="500" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="54" y="287" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">root_assigner 作业：给模型分配词根</text>
  <text x="54" y="309" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source_assign → root_assigner → reduce_assigner → publish_assigner</text>
  <text x="54" y="327" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">→ extract_root → taxonomist_member → combine_root_member → publish_root_member</text>
  <rect x="40" y="372" width="500" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="372" width="500" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="54" y="395" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">member_attribute 作业：补成员属性</text>
  <text x="54" y="417" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source_member → assign_member → combine_assign_member → publish_assign_member</text>
  <rect x="600" y="48" width="260" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="600" y="48" width="260" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="614" y="71" fill="#1c1915" font-size="11" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">raw_root.csv</text>
  <text x="614" y="93" fill="#5e584e" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">词根表初稿</text>
  <rect x="600" y="156" width="260" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="600" y="156" width="260" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="614" y="179" fill="#1c1915" font-size="11" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">final_root.csv</text>
  <text x="614" y="201" fill="#5e584e" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">词根表定稿</text>
  <rect x="600" y="264" width="260" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="600" y="264" width="260" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="614" y="287" fill="#1c1915" font-size="11" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">root_assign.json</text>
  <text x="614" y="309" fill="#5e584e" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">归属表</text>
  <text x="614" y="327" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">root_member.csv</text>
  <rect x="600" y="372" width="260" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="600" y="372" width="260" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="614" y="395" fill="#1c1915" font-size="11" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">成员属性</text>
  <text x="614" y="417" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">root_member_assign.json</text>
</svg>
<figcaption><span class="fig-label">图 8</span> 案例的四个作业：产物写在 .staging 里，后一个作业读前一个的产出。</figcaption>
</figure>
<!-- figure:pipeline:end -->

### 第一个作业：建词根表

| 节点 | 类型 | 做什么 |
| --- | --- | --- |
| `source` | source | 读 `.input/` 下每个模型一份的输入，产出实体 |
| `librarian` | map | 读模型的 yml，抽出指标清单，写成一份 JSON |
| `taxonomist_root` | reduce | 把全部模型的 JSON 合成一份提示词，交给大模型一次，得到词根表 |
| `publish` | apply | 把词根表写成 `.staging/raw_root.csv` |

`source` 用的是内置的 `FileHashSource`。`.input/` 里每个子目录是一个实体，`tag.json` 里写着库名和表名：

```json
{
  "db": "core_data",
  "table": "fct_refund"
}
```

`FileHashSource` 的 `paths` 把这两个字段拼成模型文件的绝对路径，写进实体的 tag：

```json
{
  "type": "source",
  "class": "docorder.functions.impl.directory_source:FileHashSource",
  "paths": {
    "sql": "{model_home}/{db}/{table}.sql",
    "yml": "{model_home}/{db}/{table}.yml"
  },
  "fingerprint": {
    "record": {
      "{model_home}/{db}/{table}.sql": "",
      "{model_home}/{db}/{table}.yml": ""
    }
  }
}
```

`{model_home}` 是算子的一个字符串参数，指向模型文件所在的目录。`librarian` 拿这个绝对路径去读 yml，解析出指标清单。它是普通的 map function，只依赖 `MapFunction` 基类，不调用大模型，因此很快。

`taxonomist_root` 是个 reduce，把上游全部实体的 JSON 合成一份提示词，一次调用大模型。返回值是一张 CSV，第一行是表头：

```text
root_id|root_zh|kind|definition|not_a|aliases
product_click_count|商品点击次数|count|Count of product click events, one per user, ...|已归因点击次数, 未归因点击次数|how many product clicks, ...
```

每一行是一个词根：英文 ID、中文名、类别（`count`、`rate`、`amount`、`score`、`duration`）、定义、明确不是什么的说明、别名。

`publish` 是 apply，用内置的 `Output` 把这个实体写成 `.staging/raw_root.csv`。apply 不写实体，只调用 function，所以它没有下游。

### 第二个作业：修词根表

初稿里的词根往往不完美：定义写得不准、别名漏了、两个词根其实是一回事。这个作业让大模型按初稿逐个模型地提修改意见，再把意见合进词根表。

| 节点 | 类型 | 做什么 |
| --- | --- | --- |
| `source` | source | 与第一个作业共用同一个节点 |
| `optimizer_root` | map | 每个模型一次大模型调用，只在词根表盖不住时改 `raw_root_patch_log.csv` |
| `merge_root` | reduce | 一次大模型调用，把这份文件合进词根表 |
| `publish_final` | apply | 写出 `.staging/final_root.csv` |

`optimizer_root` 的算子 home 声明了两段指纹：

```json
{
  "fingerprint": {
    "record": {
      "{staging}/raw_root_patch_log.csv": ""
    },
    "depend": {
      "{staging}/raw_root.csv": ""
    }
  }
}
```

`depend` 指的就是 `.staging/raw_root.csv`，也就是第一个作业的产出。词根表改了，这个算子的每个实体重做；模型定义没变、词根表也没变，就一个都不重做，模型的钱一分不花。

`record` 记的是 `.staging/raw_root_patch_log.csv`。提示词要求大模型对照 `raw_root.csv` 改这份文件：文件不存在就创建，存在就原地修改，词根已经够用的行不要动。

`merge_root` 直接读这两份文件，不经过中间实体。它的 `depend` 同时记下 `.staging/raw_root.csv` 和 `.staging/raw_root_patch_log.csv`，所以任一份变了都会重跑。

### 第三个作业：给模型分配词根

有了定稿的词根表，下一步是给每个模型的每个指标找到它的词根。

| 节点 | 类型 | 做什么 |
| --- | --- | --- |
| `source_assign` | source | 单独的 source，节点名与第一个作业的 `source` 不同 |
| `root_assigner` | map | 每个模型一次大模型调用，决定这个模型的指标属于哪些词根 |
| `reduce_assigner` | reduce | 把所有模型的归属合成一份 JSON |
| `publish_assigner` | apply | 写出 `.staging/root_assign.json` |
| `extract_root` | fanout | 按词根把归属 JSON 拆开，一个词根一个实体 |
| `taxonomist_member` | map | 每个词根一次大模型调用，写这个词根的成员表 |
| `combine_root_member` | reduce | 把所有词根的成员表拼成一份 CSV |
| `publish_root_member` | apply | 写出 `.staging/root_member.csv` |

`source_assign` 声明了 `record`，把模型文件和词根表都记下来：

```python
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
```

这里的 `catalog` 指向 `.staging/final_root.csv`，所以词根表一变，这个 source 的实体就带着新的哈希，下游跟着重做。

注意节点 `config` 里的 `fingerprint` 是整份覆盖算子 home 的，所以上面把 home 里那两条也一起写了。第四章「指纹与哈希」讲了这个覆盖规则。

`extract_root` 是这个案例里唯一的 fanout。它的 `output_names` 从归属 JSON 里读出所有用到的词根 ID，跳过 `unassigned`：

```python
class ExtractRoot(FanoutFunction):
    def output_names(self, source_entity):
        payload = _document(source_entity.read_text(), self.operator_name, source_entity.name)
        names: set[str] = set()
        for model in payload["models"]:
            for metric in model["metrics"]:
                root_id = metric.get("root_id")
                if isinstance(root_id, str) and root_id and root_id != "unassigned":
                    names.add(root_id)
        return sorted(names)
```

上游只有一份归属 JSON，输出却是每个词根一个实体。fanout 的输出实体数量和上游实体数量无关，这正是它存在的理由。仓库里这份输入跑出来是十四个词根实体。

### 第四个作业：补成员属性

最后一个作业给每个词根的成员补充描述。它的结构最简单：`source_member`、`assign_member`、`combine_assign_member`、`publish_assign_member` 四个节点，依次是 source、map、reduce、apply。

### 这个案例用到的机制

| 机制 | 在案例里用在哪 |
| --- | --- |
| 五种算子 | source、map、reduce、fanout、apply 全用上了 |
| `fingerprint.record` | 记下模型文件、词根表和中间产物 |
| `fingerprint.depend` | 让词根表的变化传到下游 |
| `.staging` | 四个作业之间传数据 |
| `retry` | 大模型调用失败时重试 |

### 怎么跑

```bash
cd examples/data-governance/semantic_layer
uv run python job.py                   # 建词根表
uv run python job.py refine            # 修词根表
uv run python job.py assign            # 给模型分配词根
uv run python job.py member_attribute  # 补成员属性
```

`.env` 里只有 `DOCORDER_HOMES` 一项，指向本目录的 `.op_home`。模型文件的位置用环境变量 `SEMANTIC_LAYER_MODELS` 指定，输入目录用 `SEMANTIC_LAYER_INPUT`。大模型工具用 `DOCORDER_LLM` 指定，没写就用脚本里配好的默认工具。

这几个作业需要本机装好大模型工具、并且有模型文件可读，因此不在 CI 中运行；CI 跑的是 `documentation/` 那个最小作业。

## 十二、最佳实践

这一章不讲 docorder 的机制，讲怎么用它才稳。前面的章节说明「它会怎样做」，这一章说明「你应该怎样组织项目和作业」。这些约定不是强制的，但每一条都对应一类实际踩过的坑。

### 先想清楚这件事适不适合 docorder

docorder 的核心假设是：被处理的对象形状相同、可以放在磁盘上、可以重复处理，而且处理一次的代价高于读一次磁盘。因此它擅长「一批表各生成一段说明」「一批文档各切一段摘要」「一批配置各渲染一份产物」这类事。

如果任务不符合这个形状，就不该硬套。典型的反例：

- 一次性的任务，写个脚本跑一次就完了。为了断点续跑去搭一套目录和算子，是额外成本。
- 对象数量很少但每一步都很重。docorder 的目录、快照和比较会带来固定的复杂度开销。
- 需要全局视野的一次性聚合。reduce 可以做，但只能把上游整批交给一次调用，输入太大时不如直接写脚本。

先按第五章「使用场景」对一遍，再决定要不要用。

### 目录与命名

**输入目录按实体形状准备。** `DirectorySource` 只认「一个子目录里有 `data` 或 `tag.json`」这种形状。输入是散落的普通文件时，先写一个 source 把它们整理成实体目录，而不是去改 `DirectorySource` 的读法。

**实体名守规矩。** 非空、不含 `/` 和 `\`，不以 `.` 或 `_` 开头。名字会直接变成目录名，也会进模板和命令行参数。带空格、中文或 shell 特殊字符的名字虽然能用，但排查问题时很难受，建议只用小写字母、数字和下划线。

**epoch 用一层目录名。** epoch 会被直接拼进路径，`2026/10` 会建出两层目录。用 `2026-10-16`、`v3` 这样的单层名字。它是版本标识，不是时间路径。

**输出根目录保持稳定。** 同一个作业固定写到一个输出根目录，中断后重跑才能接上进度。放在临时目录或带随机数的路径里，续跑就无从谈起。

**输出目录不要提交。** 它是进度和产物，不是源码。把输出根目录（`runs/` 之类）写进 `.gitignore`。作业的输入数据如果来自真实业务，同样不要提交。

### 增量与幂等

这是 docorder 最容易用错的地方。

**同一件事用同一个 epoch。** 续跑就是用同一个 epoch 再执行一次。换个 epoch 等于从头再来一遍，之前算过的全部白算。epoch 的作用是「这批数据的一个版本」，不是「每次运行的标识」。

**改逻辑要显式作废旧结果。** 改了模板、参数、function 代码或外部工具，而上游实体没变时，上游快照仍然吻合，旧结果会被原样保留。这时要么删掉该节点的 epoch 目录，要么只删需要重做的实体目录，要么换 epoch。docorder 不会替你判断「代码变了」。

**改了输入要传 `--scratch`。** source 节点的 `start_from_scratch=True` 是输入数据进入作业的开关。不传它，源文件的改动不会进入 source 的实体，下游自然看不到。

**不要手改上游实体目录。** 直接改已经写出的 `data` 或 `tag.json` 会让依赖它的下游重做，这在调试时有用，但把它当成常规工作流会让「谁是上游」变得不可追踪。要改就改源头。

**别让正文为空。** 上游正文是空字符串时，它的哈希每次都是空值，与快照永远对不上，依赖它的实体每次运行都会重做。大模型调用一次不便宜，这等于每次运行都重新付一遍钱。实在拿不到内容时，写一个占位符也好。

**作业脚本要能重复执行。** 同一个 epoch 跑两遍应该得到同样的结果，而不是报错或叠加。写脚本时把 epoch 当参数传进来，而不是写死在代码里。

### 算子 home 的组织

**home 按角色命名，不要按项目命名。** `table_source`、`ask_llm`、`render_prompt` 这类名字可以跨项目复用；`my_project_table_source` 就只能用一个项目。项目的差异用节点的 `config` 传。

**home 里放静态文件，代码放 `primary.py`。** 模板、工具定义这类纯文件直接放在 home 目录里；需要写代码时用 `class: "primary:类名"`，代码写在 home 的 `primary.py` 里。

**用 `config` 传差异，用 home 传共性。** `props.json` 里的自定义键是这套 home 的默认参数，节点 `config` 覆盖同名键。一个 home 服务多个项目时，项目相关的值都应该走 `config`。

**`DOCORDER_HOMES` 的顺序就是优先级。** 靠前的目录先被搜索，同名 home 以靠前的为准。这条在本地调试时很好用：把自己的 home 目录放在最前面，改坏了也不影响别人。

**环境变量要在建作业之前设好。** home 的查找发生在 `add_operator_node` 被调用的那一刻。

### 错误处理

**配置错误用 `FatalError`。** 缺参数、模板写错、输入格式不对这类问题，重试多少次都一样，应该立刻失败。函数里抛普通的异常则会触发重试，把时间浪费在必然失败的调用上。

**外部进程的失败用普通异常。** 大模型接口超时、外部命令返回非零状态这类问题，值得重试。`PromptToLLM` 这类 function 已经内置了这个区分，你只要在包装自己的 function 时保持同样的判断。

**给调用大模型的节点配上 `retry` 和 `parallelism`。** 默认的并发度对外部接口来说往往太激进，容易触发限流。先用小一点的并发度跑通，再按接口的配额往上调。

**失败的实体会留下现场。** 一个失败的实体会留下一个只有空 `tag.json`、没有 `data` 的目录，里面没有 `upstream` 快照。修好问题后用同一个 epoch 重跑，它会被重做，之前成功的实体不会重来。所以排查问题时可以直接去看那个目录。

### 调用大模型

**选对 function。** 一批对象各要一段结果，用 `EntityTemplateToLLM`（map）；整批对象要一份汇总，用 `TemplateToLLM`（reduce）；上游已经是一段提示词，直接用 `PromptToLLM`。

**尽量把调用放在 map 上。** map 的粒度是单个实体，失败只影响一个对象，续跑的成本最低。reduce 的粒度是整批，一次失败整批重来。

**用 `tag_template` 保留元信息。** 大模型返回的正文之外，让 function 顺便把结构化的结果写进 tag，后续步骤就不用再解析正文。

**用 `header` 约束输出格式。** 给 `PromptToLLM` 配上 `header`，模型回复里的表格就能被稳定地截出来当正文，下游不用再处理模型可能加的寒暄。

**把大模型的输入写成路径而不是内容。** `EntityTemplateToLLM` 和 `TemplateToLLM` 的模板里能拿到上游 `data` 文件的路径，让模型自己去读，比把大段内容塞进提示词更省 token，也更不容易超长。

**用 `fingerprint.depend` 跟踪外部文件。** 如果一段结果依赖某个不在上游实体里的文件（例如表定义旁边的 `.sql`），用 `depend` 声明它，文件变了对应的实体才会重做。

### 常见反模式

| 反模式 | 问题 | 更好的做法 |
| --- | --- | --- |
| 每个对象起一个子进程单独处理 | 丢掉了批量、重试和续跑能力 | 用 map 算子，交给 runner 调度 |
| 在 function 里自己写重试或线程池 | 和 runner 的机制重复，失败语义不一致 | 抛普通异常让 runner 重试，用 `parallelism` 控制并发 |
| 在 function 里创建作业或调用 `execute` | 进度无处存放，续跑失效 | function 只处理一个实体，作业由脚本构建 |
| 把大块数据塞进 tag | 快照的哈希随数据变大，比较变慢 | tag 只放标识和路径，正文放文件 |
| 每次运行换一个 epoch | 每次都从头算 | 固定 epoch，用目录清理来控制重做范围 |
| 改了模板却不清理旧结果 | 旧结果被原样保留，看起来「没生效」 | 删掉该节点的 epoch 目录，或换 epoch |
| 用一个 epoch 装互不相关的实体 | 一个实体失败牵连整批，多个作业互相干扰 | 一个作业一个输出根目录，一个 epoch 一批数据 |

## 附录 A：内置 function 一览

| 类 | `class` 的写法 | `type` | 参数 |
| --- | --- | --- | --- |
| `DirectorySource` | `docorder.functions.impl.directory_source:DirectorySource` | source | `directory` |
| `FilteredDirectorySource` | `docorder.functions.impl.directory_source:FilteredDirectorySource` | source | `directory`、`filter` |
| `FileHashSource` | `docorder.functions.impl.directory_source:FileHashSource` | source | `directory`、`paths`、`fingerprint` |
| `TemplateToPrompt` | `docorder.functions.impl.template_to_prompt:TemplateToPrompt` | map | `template` |
| `JinjaToJsonnet` | `docorder.functions.impl.jinja_to_jsonnet:JinjaToJsonnet` | map | `template`、`variables` |
| `JsonnetToPrompt` | `docorder.functions.impl.jsonnet_to_prompt:JsonnetToPrompt` | map | 无 |
| `Command` | `docorder.functions.impl.command:Command` | map | `argv`、`cwd`、`output_file`、`capture` |
| `PromptToLLM` | `docorder.functions.impl.prompt_to_llm:PromptToLLM` | map | `workspace`、`tool` |
| `EntityTemplateToLLM` | `docorder.functions.impl.template_to_llm:EntityTemplateToLLM` | map | `template`、`workspace`、`tool`、`header`、`tag_template` |
| `TemplateToLLM` | `docorder.functions.impl.template_to_llm:TemplateToLLM` | reduce | `template`、`workspace`、`tool`、`header`、`tag_template`、`min_sources`、`max_sources` |
| `Output` | `docorder.functions.impl.output:Output` | apply | `directory`、`filename` |

编写 function 时用到的基类和辅助类分别定义在以下模块中：`SourceFunction` 和 `SourceRecord` 在 `docorder.functions.source_function` 中，`MapFunction` 在 `docorder.functions.map_function` 中，`RenderedMap` 在 `docorder.functions.rendered_map` 中，`ReduceFunction` 在 `docorder.functions.reduce_function` 中，`FanoutFunction` 在 `docorder.functions.fanout_function` 中，`ApplyFunction` 在 `docorder.functions.apply_function` 中。`Artifact` 在 `docorder.core.artifact` 中，`Environment` 在 `docorder.core.environment` 中。异常类 `DocorderError`、`JobValidationError`、`OperatorValidationError` 和 `FatalError` 都在 `docorder.utils.errors` 中，重试策略 `RetryPolicy` 在 `docorder.utils.retry` 中。

## 附录 B：实现索引

| 路径 | 职责 |
| --- | --- |
| `src/docorder/core/artifact.py` | 算子 home 的只读文件入口 |
| `src/docorder/core/entity.py` | 检查实体名字，读写实体目录，计算和比较上游快照 |
| `src/docorder/core/storage.py` | 管理一个 epoch 目录中的实体，负责新建、清理和删除 |
| `src/docorder/core/operator.py` | 解读 `props.json`，表示节点，列出应得名单，执行五种算子并切分并行任务 |
| `src/docorder/core/job.py` | 作业图的构建、检查和拓扑排序 |
| `src/docorder/core/runner.py` | 装配作业，逐个执行 stage，管理输出目录标记 |
| `src/docorder/core/epoch_diff.py` | 比较两次运行的实体差异，给出新增、修改、删除的数量 |
| `src/docorder/core/external_hash.py` | `fingerprint` 的 `record` 与 `depend`：渲染路径模板、计算文件哈希 |
| `src/docorder/core/environment.py` | 渲染环境：`operator_props` 与 `template_env` |
| `src/docorder/functions/` | function 基类；内置实现在 `functions/impl/` |
| `src/docorder/utils/paths.py` | 解析 `DOCORDER_HOMES`，查找算子 home |
| `src/docorder/utils/modules.py` | 加载 `primary:类名` 和 `模块:类名` 形式的 function 类 |
| `src/docorder/utils/llm_tool.py` | 大模型工具：读取 home 里的工具预设，启动外部进程 |
| `src/docorder/utils/retry.py` | 重试策略，以及它如何作用到一次实体调用 |
| `src/docorder/utils/progress.py` | 一个 stage 的进度显示 |
| `src/docorder/utils/errors.py` | `DocorderError` 及其子类 |
| `src/docorder/cli/` | `docorder status` 命令：查看输出目录里的 epoch |
| `tests/test_contract.py` | 以上各项行为的契约测试 |

## 附录 C：相关文档

- [README](../README.md)：安装、快速开始和常见问题排查。
- [glossary.md](../glossary.md)：术语表。
- [CONTRIBUTING.md](../CONTRIBUTING.md)：开发约定和提交要求。
- [文档首页](index.html)：概览、核心概念、模型、快速开始与再跑，以及本指南的各章入口。
- [Jinja 模板文档](https://jinja.palletsprojects.com/en/stable/templates/)：`TemplateToPrompt` 和 `JinjaToJsonnet` 使用的模板语法。
- [Jsonnet](https://jsonnet.org/)：`JsonnetToPrompt` 编译的配置语言。
- [concurrent.futures.ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor)：map 和 fanout 节点并行执行时使用的线程池。
