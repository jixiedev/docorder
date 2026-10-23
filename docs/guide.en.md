# docorder Guide

[中文](guide.md)

**Contents**

- [Document structure](#document-structure)
- [1. Background](#1-background)
  - [The problem to solve](#the-problem-to-solve)
  - [A minimal example](#a-minimal-example)
  - [Design trade-offs](#design-trade-offs)
  - [The boundaries of this version](#the-boundaries-of-this-version)
- [2. Core concepts and terms](#2-core-concepts-and-terms)
  - [Entity](#entity)
  - [Upstream snapshot](#upstream-snapshot)
  - [Operator and operator home](#operator-and-operator-home)
  - [Function](#function)
  - [Job and node](#job-and-node)
  - [Epoch and stage](#epoch-and-stage)
  - [Runner and expected names](#runner-and-expected-names)
  - [How the concepts relate](#how-the-concepts-relate)
  - [Terminology](#terminology)
- [3. How a run works](#3-how-a-run-works)
  - [Assembly](#assembly)
  - [The life of one stage](#the-life-of-one-stage)
  - [Parallelism and retry](#parallelism-and-retry)
  - [The stage of a source node](#the-stage-of-a-source-node)
  - [Decisions on a later run](#decisions-on-a-later-run)
  - [Common situations when running again](#common-situations-when-running-again)
  - [The directories one run leaves behind](#the-directories-one-run-leaves-behind)
- [4. Fingerprints and hashes](#4-fingerprints-and-hashes)
  - [The three kinds of hash in docorder](#the-three-kinds-of-hash-in-docorder)
  - [The hash inside the upstream snapshot](#the-hash-inside-the-upstream-snapshot)
  - [Declaring a fingerprint](#declaring-a-fingerprint)
  - [How the two checks make one decision](#how-the-two-checks-make-one-decision)
  - [Path templates and placeholders](#path-templates-and-placeholders)
  - [The order of things in one run](#the-order-of-things-in-one-run)
  - [Declarations that are refused](#declarations-that-are-refused)
  - [An empty body](#an-empty-body)
  - [A node config replaces the whole fingerprint](#a-node-config-replaces-the-whole-fingerprint)
  - [Troubleshooting](#troubleshooting)
- [5. Use cases](#5-use-cases)
  - [Batch prompt generation and a model call](#batch-prompt-generation-and-a-model-call)
  - [Generating configuration files from structured data](#generating-configuration-files-from-structured-data)
  - [Running a command line tool for each entity](#running-a-command-line-tool-for-each-entity)
  - [Gathering and splitting](#gathering-and-splitting)
  - [Cases that do not fit](#cases-that-do-not-fit)
- [6. Configuration](#6-configuration)
  - [Letting docorder find the operator homes](#letting-docorder-find-the-operator-homes)
  - [props.json](#propsjson)
  - [Job and node](#job-and-node-1)
  - [execute](#execute)
  - [What a function reads and what a template reads](#what-a-function-reads-and-what-a-template-reads)
  - [Environment variables](#environment-variables)
- [7. Operator types and the built-in functions](#7-operator-types-and-the-built-in-functions)
  - [The five operator types](#the-five-operator-types)
  - [The source operator](#the-source-operator)
  - [The map operator](#the-map-operator)
  - [The reduce operator](#the-reduce-operator)
  - [The fanout operator](#the-fanout-operator)
  - [The apply operator](#the-apply-operator)
  - [Failure and retry](#failure-and-retry)
- [8. Rendering functions and template variables](#8-rendering-functions-and-template-variables)
  - [The three steps of RenderedMap](#the-three-steps-of-renderedmap)
  - [The rendering environment](#the-rendering-environment)
  - [Built-in template variables](#built-in-template-variables)
  - [Adding a template variable](#adding-a-template-variable)
  - [Which value wins when names collide](#which-value-wins-when-names-collide)
- [9. Writing your own function](#9-writing-your-own-function)
  - [Choosing a base class](#choosing-a-base-class)
  - [What a function can use](#what-a-function-can-use)
  - [Rules you must follow](#rules-you-must-follow)
  - [Where the code goes](#where-the-code-goes)
  - [Example: a custom source](#example-a-custom-source)
  - [Example: map](#example-map)
  - [Example: based on RenderedMap](#example-based-on-renderedmap)
  - [Example: reduce](#example-reduce)
  - [Example: fanout](#example-fanout)
  - [Testing a function](#testing-a-function)
- [10. Using docorder in your own project](#10-using-docorder-in-your-own-project)
  - [Step 1: install docorder](#step-1-install-docorder)
  - [Step 2: plan the directories](#step-2-plan-the-directories)
  - [Step 3: prepare the input data](#step-3-prepare-the-input-data)
  - [Step 4: write the operator homes](#step-4-write-the-operator-homes)
  - [Step 5: write the start script](#step-5-write-the-start-script)
  - [Step 6: run it and look at the result](#step-6-run-it-and-look-at-the-result)
  - [Step 7: run again after a change](#step-7-run-again-after-a-change)
  - [Version control](#version-control)
- [11. A data governance case study](#11-a-data-governance-case-study)
  - [Where the case lives in the repository](#where-the-case-lives-in-the-repository)
  - [The problem](#the-problem)
  - [The first job: building the root catalogue](#the-first-job-building-the-root-catalogue)
  - [The second job: correcting the root catalogue](#the-second-job-correcting-the-root-catalogue)
  - [The third job: assigning roots to models](#the-third-job-assigning-roots-to-models)
  - [The fourth job: filling in member attributes](#the-fourth-job-filling-in-member-attributes)
  - [The mechanisms this case uses](#the-mechanisms-this-case-uses)
  - [How to run it](#how-to-run-it)
- [12. Best practices](#12-best-practices)
  - [Decide first whether the task suits docorder](#decide-first-whether-the-task-suits-docorder)
  - [Directories and naming](#directories-and-naming)
  - [Incremental runs and idempotence](#incremental-runs-and-idempotence)
  - [Organizing the operator homes](#organizing-the-operator-homes)
  - [Error handling](#error-handling)
  - [Calling a model](#calling-a-model)
  - [Common anti-patterns](#common-anti-patterns)
- [Appendix A: The built-in functions](#appendix-a-the-built-in-functions)
- [Appendix B: Implementation index](#appendix-b-implementation-index)
- [Appendix C: Related documents](#appendix-c-related-documents)

---

docorder is a Python library for processing a batch of objects that share one shape in bulk. An "object" here can be the definition of a table, a note, a configuration file, or anything that can be expressed as a piece of text. The user first splits the work into a few steps that follow one another, for example "read the files", "apply a template to produce a prompt", "hand the prompt to a model", and "collect every answer into one list", then joins those steps into a job graph and gives it to docorder to run. docorder writes the result of each object at each step as a directory on disk, and records in that directory which upstream content the result was computed from. Therefore, when a step fails halfway, or when the input changes, running it again makes docorder redo only the part that failed and the part affected by the change; results that are already done and still valid are kept as they are.

This guide is written for readers who use docorder for the first time and assumes no prior knowledge of the project's terms. Chapter 1 explains the problem docorder wants to solve and uses a two-step minimal example to show a whole job from configuration to run; the later chapters keep coming back to that example. Chapter 2 defines every concept that appears in the example. Chapter 3 walks through one run in time order. Chapter 4 covers the fingerprints and hashes, that is, the basis of every incremental decision. Chapter 5 introduces the cases that suit docorder. Chapters 6 to 8 cover the configuration keys, the transforms that ship with docorder, and the variables a template can use. Chapter 9 shows how to write your own transform, and chapter 10 uses one complete project example to walk through using docorder in your own repository, step by step. Chapter 11 puts those mechanisms together in a real data governance job. Chapter 12 is about using it so that it stays reliable.

The content of this guide follows the current code. Two things are worth saying up front: docorder has not been published to PyPI yet, so it has to be installed from the source repository, and the installation steps are in the first step of chapter 10; and a job is still run by calling `execute` from a Python script. After installation, `docorder status <output root>` shows which epochs the output root contains, whether the results of each epoch still match their upstream snapshots, and how many entities each stage has in each epoch.

If docorder is new to you, read the first three chapters in order to get the overall picture, and consult chapters 6 to 8 as needed afterwards. If you plan to write your own transform, read chapter 9. If you want to start using docorder in your own project as soon as possible, jump to chapter 10 and follow it, and go back to the earlier chapter when you meet a term you do not know. If you want to see one complete real example, read chapter 11. Before you rely on it for the long run, chapter 12 is worth a read.

## Document structure

1. Background: the problem docorder solves, a minimal two-step job, the design trade-offs docorder makes, and the capability boundaries of the current version.
2. Core concepts and terms: entity, upstream snapshot, operator and operator home, function, job and node, epoch and stage, runner and expected names. For each concept it says what it is, who creates it, and where it is stored.
3. How a run works: what happens from the moment a run checks the job graph until each node has run, step by step. It also covers parallel execution, failure and retry, the special handling of a source node, and how docorder decides the fate of each result when it runs again.
4. Fingerprints and hashes: the three kinds of hash in docorder, how to declare a dependency on external files with `fingerprint`, what `record` and `depend` are for, how to write a path template, and how to trace an entity that is redone on every run.
5. Use cases: what kind of task each of several typical job graphs suits, and which tasks do not suit docorder.
6. Configuration: how docorder finds the operators, what every key in `props.json` means, the arguments of a job and of a node, the arguments of the run function `execute`, which configuration the transform code and the template each read, and the environment variables involved.
7. Operator types and the built-in functions: what separates the five operator types, which of docorder's own functions each type can use, and for each function which configuration keys it has, what it produces, and when it fails.
8. Rendering functions and template variables: every variable a template can use directly, and the six ways to add a template variable when the built-in ones are not enough.
9. Writing your own function: which base class to inherit, which methods to implement, which objects are available inside those methods, the conventions you must follow, where the code file goes, and how to write tests for it.
10. Using docorder in your own project: the complete steps from installing, planning the directories, preparing the input data, and writing the operators and the start script, to running it, looking at the result, and running it again after a change.
11. A data governance case study: the real jobs under `examples/data-governance/`, from the metric list of a dbt model to the root catalogue, the assignment table and the member tables, and how the four jobs hand their results to each other.
12. Best practices: the conventions that keep docorder reliable, covering directories and naming, incremental runs and idempotence, how to organize operator homes, error handling, the cost of model calls, recovering from failures, and the common anti-patterns.

Several structural sketches appear in the text: the files and the run results of the minimal example, the composition of one entity directory, how the concepts relate to each other, the directories one run leaves on disk, the shape of the data available during a template render, how the two kinds of hash make one decision, and the directory tree of the example project in chapter 10.

This document is the single reference manual for docorder. It used to be split into `design.md` (the internal mechanisms) and `functions.md` (the function reference), which overlapped heavily with this file. Both are now merged in here: the disk mechanisms are in chapters 2, 3 and 4, and the function reference is in chapters 7 and 8.

## 1. Background

### The problem to solve

Many batch jobs have the same shape: you have a batch of objects, for example the definitions of several hundred data tables, a set of notes, or the configurations of a group of services, and each object has to go through a few processing steps, for example rendering the table definition into a prompt, handing the prompt to a model to produce a description, and finally collecting the descriptions of all the tables into one list. Such tasks have two problems in common. The first is that every step can be slow and can fail: calling an external command can time out, a model API can rate-limit or return an error, and a template can contain a mistake. The second is that the input keeps changing: today you change the definition of one table, tomorrow you add a few more tables, and after every change the results have to be updated.

If you only write an ordinary script that loops over the objects, then when the three hundredth object fails, fixing the problem usually means running the whole thing again from the start, and the time already spent and the model calls already paid for are wasted. To avoid that, many people keep their own record of "which objects are already done", but a record in a database means one more component to deploy and maintain, and a record in memory is lost as soon as the process exits. The harder problem is deciding whether "a result that has already been computed can still be used": after an input file changes, which downstream results have to be recomputed and which can be kept? An ordinary script has no reliable basis for that answer, so it either recomputes everything or leaves it to human judgement.

docorder's answer is to write the result of each object at each step as a directory on disk, and to record in that directory the hash of the upstream content this step read. A hash is a fixed-length string computed from a piece of content; as soon as the content changes in any way the hash is completely different, so it can be used to tell whether the content was modified. On the next run docorder only has to compare the hash recorded in the directory with the hash of the current upstream content, and it knows which objects have not been processed yet, which results are out of date and have to be redone, and which results are still valid and can be kept. The whole decision depends only on files on disk: no database, and no state left in memory by the previous run.

### A minimal example

The job below reads the note entities in a directory, puts the body of each note into a template, and produces a prompt. It has only two steps, but it already contains every basic part of docorder, and the later chapters keep using it to explain the concepts. To actually run this example, install docorder first, as described in the first step of chapter 10.

#### Prepare the files

Create the directory structure below anywhere you like. `notes/` is the input data, `homes/` holds the configuration that describes "what each step does", and `run.py` is the Python script that starts the whole job.

```text
hello-docorder/
  run.py                    start script
  notes/
    hello/
      data                  input body, the content is hello
      tag.json              input tag
  homes/                    directory that holds the operators
    notes_source/
      props.json
    prompt/
      props.json
      lib/note.jinja        template file, the content is Note: {{ entity.source_data }}
```

In docorder, every kind of step in a job is called an operator, and the directory that describes one operator is called the operator home. `homes/notes_source/` and `homes/prompt/` above are two operator homes: the first describes the step "read the files in a directory", the second describes the step "produce a prompt with a template". The docorder package ships no operator homes; you always put them in your own project. Every operator home must contain a JSON configuration file named `props.json`, and it is exactly through this file that docorder recognizes a directory as an operator home and learns how the operator is supposed to run.

The content of `homes/notes_source/props.json` is:

```json
{
  "type": "source",
  "class": "docorder.functions.impl.directory_source:DirectorySource"
}
```

The content of `homes/prompt/props.json` is:

```json
{
  "type": "map",
  "class": "docorder.functions.impl.template_to_prompt:TemplateToPrompt",
  "template": "lib/note.jinja"
}
```

`type` says which kind the operator is. A `source` operator sits at the start of the job: it does not read the results of other steps but produces the first batch of objects from outside, for example from a directory on disk. A `map` operator reads the result of the previous step and transforms each of its objects once, so each input object has one output object. `class` points at the Python class that performs the transform, written as "module path:ClassName"; this class is called a function in docorder. Both functions used here ship with docorder: `DirectorySource` turns the subdirectories of a directory that are already shaped like entities into objects, and `TemplateToPrompt` renders a piece of text for each object with a Jinja template. Jinja is a template language commonly used in Python; the part of a template between two pairs of braces, such as `{{ entity.source_data }}`, is replaced by the value of the matching variable at render time. Every key in `props.json` other than `type` and `class` is passed to the function as a parameter: `template`, for example, tells `TemplateToPrompt` which template file to use, and that path is relative to the operator home.

#### Configure and run the job

The content of `run.py` is:

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

The first real line of the script sets the environment variable `DOCORDER_HOMES`, which tells docorder where to look for operator homes. It is set to the `homes/` directory of the project, so the two names used below, `notes_source` and `prompt`, refer to `homes/notes_source/` and `homes/prompt/`.

`Job("hello", ROOT / "runs")` creates a job. A job describes "which steps this run connects, in what order, and where the results are written". The first argument is the job name; the second is the output root, under which the results of every step of this job are written.

`add_operator_node` adds a node to the job. A node is a point in the job graph: it means "in this job, one step is executed with this operator". The first call adds a node named `notes`, which uses the `notes_source` operator home; the `config` argument gives that node an extra parameter named `directory`, which names the input directory to read. The location of the input directory belongs to the concrete project and not to the step "read a directory", which can be reused in many projects, so it is not written into `props.json` but passed in through the job. The second call adds a node named `prompt`, which uses the `prompt` operator home; `upstream="notes"` says that this node reads the result of the `notes` node as its input, in other words `notes` is upstream of `prompt`.

`execute(job, "demo", start_from_scratch=True)` actually starts the job. The second argument, `"demo"`, is called the epoch; you can think of it as "the name of this batch of results", and it becomes one level of subdirectory in the output directories. If you run again later with the same epoch, docorder continues on the basis of the results that are already there; with a new epoch, docorder starts from an empty directory and the previous batch of results stays untouched. `start_from_scratch=True` asks the source nodes to reread the external input; without it, a source node keeps what it read last time and does not reread the input directory.

In an environment where docorder is installed, enter the `hello-docorder/` directory and run `uv run python run.py` to run the job. The `if __name__ == "__main__":` at the end of the script is the ordinary way to write a script. Parallel execution uses threads; it does not start another subprocess.

#### What the run leaves on disk

After the run finishes, the output root `runs/` contains these files:

```text
runs/
  notes/
    demo/                             epoch directory
      hello/                          one entity, the name comes from the input directory hello
        data                          hello
        tag.json                      the tag.json of the input entity
  prompt/
    demo/
      hello/
        data                          Note: hello
        tag.json                      the same as the upstream tag.json, plus upstream
                                      {"operator": "notes", "name": "hello",
                                       "epoch": "demo", "hash": "5891b5b5…"}
```

Every node has a directory under the output root named after the node, for example `runs/notes/` and `runs/prompt/`; inside the node directory are the directories named after the epochs, here `demo/`; inside the epoch directory each processed object has one subdirectory of its own, and docorder calls such a directory an entity. In this example the input directory holds a single entity directory, `hello`, so each node produces a single entity named `hello`.

The `data` file in the entity directory is called the body, and it holds the main result of this step: in the `notes` node it is the original content of `data` in the input entity directory; in the `prompt` node it is the rendered text `Note: hello`. `tag.json` holds the information beyond the body, in the form of a JSON object: `DirectorySource` reads the `tag.json` of the input directory; `TemplateToPrompt` produces no new information of its own but copies the `tag.json` of the upstream entity over unchanged, so the next step can use it.

The `upstream` key in `tag.json` appears only in the entities of the `prompt` node, and docorder calls it the upstream snapshot. It records which upstream entity this entity was computed from: the upstream node is `notes`, the upstream entity is `hello`, the epoch at the time of reading was `demo`, and the sha256 hash of that upstream entity's body together with its user tag (sha256 is a common hash algorithm; its result is 64 hexadecimal characters, and only the first few are shown above). Whether this result is still valid is decided by exactly this record. The `notes` node is of type source, so it has no upstream and its entities do not have this key.

#### Running it again

If you change nothing and run `run.py` again, the following happens: the `notes` node rereads the input directory, and the body and tag of `hello` are still unchanged; when the `prompt` node comes, docorder compares the hash recorded in `upstream` in `tag.json` with the hash of the current body and user tag of `runs/notes/demo/hello`, finds that the two match, and therefore treats the existing result as still valid, keeps it as it is, and does not render the template again.

If you change the already written `runs/notes/demo/hello/data` to `changed`, or change the `tag.json` in the same directory, and then run again without `start_from_scratch`, the `notes` node does not reread the input directory, but the `prompt` node finds that the hashes differ while comparing, so it deletes the old `hello` entity and processes it again. If what you change is a source file in the input directory, you have to pass `start_from_scratch=True` for `notes` to read the new content. If you put a `bye` entity directory into the input directory and read from scratch, both nodes create an entity named `bye`, and the unchanged `hello` stays as it is.

The opposite case deserves special attention: if you only change the template and the upstream entities stay the same, the result of the `prompt` node is not updated, because the `upstream` in `tag.json` records only the body and user tag of the upstream entity, not the content of the template. This is an important boundary of the current version, and the section "The boundaries of this version" below talks about it again. The same holds when a run fails halfway: entities that already wrote a valid `upstream` are kept on the next run because the comparison passes, and only the entities that are not finished yet are processed again.

The terms that appear in this example, including operator, operator home, `props.json`, function, job, node, epoch, entity, body, tag, and upstream snapshot, are all defined more fully in chapter 2, and the later chapters build on them.

### Design trade-offs

The first trade-off is to keep the processing progress in each entity's own directory instead of in a centralized state database. In the example above, whether the `hello` entity of the `prompt` node has to be redone depends only on the `upstream` in its `tag.json` and the current body and user tag of the upstream entity; docorder does not query any database and does not depend on anything the previous run left in memory. The benefit is that even in another process, or with another job script, as long as the output root and the epoch are the same, the run continues on the progress of the last run. You can also open the `runs/` directory directly and look at the intermediate result of every step and every object, which makes troubleshooting very convenient. The cost is that all state has to be expressed in files: docorder uses the `upstream` in `tag.json` as the mark of a finished entity, and it is written last, so if the body is already written and the process exits before the tag is written, the entity is treated as unfinished on the next run and processed again.

The second trade-off is to put the transform logic in a reusable operator home instead of writing it directly into the job script. In the example above, both the template file and `props.json` live in `homes/prompt/`, and `run.py` only says which operator home is used, which node is upstream, and where the results are written. The same operator home can therefore be referenced by many different jobs, and each job can override some of its parameters through the node's `config` argument; the input directory in the example is passed in exactly this way.

The third trade-off is to separate scheduling from transformation. A function such as `TemplateToPrompt` does one thing: it takes an upstream entity and computes the body and tag of the target entity. Reading and writing entity directories, comparing the `upstream` in `tag.json`, clearing outdated results, parallel execution, and retry are all done by the part of docorder that handles scheduling, which is called the runner. Because of this split, writing a new transform usually means implementing one or two methods, without worrying about progress records, concurrency, and retry.

### The boundaries of this version

When you design a job, you need to know the following limits of the current version.

Every node has exactly one upstream node, so the whole job graph is a set of trees rooted at source nodes, and no node can read the results of two upstream nodes at once. If a step really needs to merge two branches, you have to read the files of the other branch yourself in the code of the function, and that read is not recorded in the snapshot, so when the other branch changes docorder does not automatically redo the entity.

docorder executes one node at a time; one complete execution of a node is called a stage. A node must finish all the entities of this epoch before its downstream node starts; docorder does not support a pipelined execution where the downstream starts as soon as one upstream entity is done.

Parallel execution happens only on one machine, and it relies on the thread pool of the Python standard library, that is, on starting a number of threads inside the current process to share the work. docorder does not distribute tasks across several machines.

The upstream snapshot covers the upstream body and user tag, but not the template, the parameters, or the code. If you change the template, a parameter in `props.json`, the code of the function, or an external tool it calls, while the upstream entities stay the same, docorder does not notice the change and the old result is kept. To make such a change take effect, you have to delete the corresponding output directory by hand, or run with a new epoch.

Switching to a new epoch means that every node starts computing again from empty directories. The results under the old epoch are neither reused by the new epoch nor cleaned up automatically; when they are no longer needed you have to delete them yourself.

## 2. Core concepts and terms

This chapter gives the precise definition of every concept in docorder. The example in chapter 1 has already introduced each of them; here they are described further: who creates them, where they are stored, how long they live, and how they relate to one another.

### Entity

An entity is the basic unit docorder works on: it is "the result of one object at one step". The same object that goes through three steps has one entity under each of the three nodes. On disk an entity is one directory, inside an epoch subdirectory of some node's output directory, and the name of the directory is the name of the entity.

```text
<output root>/<node name>/<epoch>/<entity name>/
  data            the body, UTF-8 encoded text
  tag.json        the tag, a JSON object; with an upstream it holds the upstream snapshot
```

The `data` file holds the body of the entity. What the body means depends on the step that produced it: in a step that reads a directory it is the content of the original file; in a step that renders a template it is the rendered text; in a step that runs an external command it is the output of the command. docorder only requires the body to be a piece of text while scheduling and does not care about its format, so the body can be plain text, Markdown, JSON, or any other text format, but not binary data such as an image.

`tag.json` holds the tag of the entity. It has to be a JSON object, that is, a structure of so many "key: value" pairs. Which keys the tag has is decided mainly by the function that produced the entity, and its main purpose is to give the downstream steps extra data, for example to refer to the original file name in a template, or to filter on some field. docorder itself manages two keys. `upstream` is a live snapshot of the direct upstream entity; a downstream entity carries the whole tag of the upstream, so this key has to be reset before writing, and a leftover `current` has to be dropped. `global_prop` carries some data along the job graph all the way to the end. The section "Filling and writing" in chapter 3 describes this in detail.

The name of an entity has to be safe to use as one directory level, so there are these requirements: the name must not be empty; it must not begin or end with whitespace; it must not contain a slash `/` or a backslash `\`; it must not be `.` or `..`; and it must not start with `.` or `_`, because names starting with those two characters are reserved for docorder's marker files and runtime temporary files. In addition, only a directory that holds a `data` file or a `tag.json` file is recognized as an entity; empty directories and deeper directories do not count.

### Upstream snapshot

The upstream snapshot is written in `tag.json` under `upstream`, and it records "which version of which upstream entities this entity was computed from". One upstream is one record; no upstream or several upstreams are a list. Each record has four fields: `operator` is the name of the upstream node, `name` is the name of the upstream entity, `epoch` is the epoch it was read in, and `hash` is the sha256 hash of the body of that upstream entity together with its user tag (excluding `upstream` and a leftover `current`), written in hexadecimal. Most steps depend on one upstream entity per output, so the snapshot holds only one record; only a reduce step, which merges a batch of entities into one, has several records, one for each upstream entity that took part in the merge.

The snapshot covers only the upstream body and user tag. Editing the `data` or `tag.json` of an upstream entity by hand makes the dependent downstream redo on the next run; a change to this operator's parameters or template, or to the function code, does not make the snapshot mismatch — that is exactly the case the section "The operator itself changed" in chapter 3 handles.

The upstream snapshot is the only thing docorder uses to decide whether a result is still valid. For an entity that has an upstream, it counts as finished only when the `upstream` in `tag.json` has been written and its record matches the current state of the upstream exactly; even if the body is already written, an entity whose tag has no snapshot yet still counts as unfinished. One special case deserves attention: if the body of the upstream is an empty string, the hash in the record is empty as well, and an empty hash never passes the comparison, so entities that depend on an empty body are processed again on every run.

### Operator and operator home

An operator is a reusable step, for example "read the files in a directory" or "render text with a certain template". All the files needed to describe one operator live in one directory, and that directory is called the operator home. An operator home has to contain at least a `props.json`, which holds the type of the operator `type`, the Python class that performs the transform `class`, the scheduling parameters that control how it runs, and the default parameters handed to the function. Besides that, an operator home can hold the other files the operator needs; by convention, template files go in the `lib/` subdirectory, external tool definitions in the `tools/` subdirectory, and your own transform code in the `primary.py` file.

An operator home only describes "how this step is done". It does not record where the results are written and does not belong to any one particular run, so the same operator home can be used by many jobs. The docorder package contains no operator homes; you have to put them in the directories listed by the environment variable `DOCORDER_HOMES`, and docorder looks for them there by name. The exact rules are in chapter 6.

Lookup has two details. A home can sit directly in one of the listed directories, or in a category directory one level below it, for example `homes/sources/table_source`; category directories whose names start with `.` or `_` are skipped. A directory is a home when it contains `props.json`. The lookup happens at the moment `add_operator_node` is called, so the environment variable has to be set before that; when the home is not found, a `FileNotFoundError` is raised, and the message lists the directories that were searched.

There are five types of operator. A source has no upstream and produces the first batch of entities from external data; a map produces one same-named output entity for each upstream entity; a reduce merges all upstream entities into one output entity; a fanout splits each upstream entity into several output entities; an apply writes no entities, calls the function once for each upstream entity, the function must not return a value, and no node can be placed downstream of it. Chapter 7 introduces the five types one by one.

### Function

A function is the Python class that the `class` key of the operator home's `props.json` points at, and it does the actual transformation. While processing each entity, the runner creates a new function object and hands it the upstream entity and a target entity that has no content yet; the function fills in the body and the tag of the target entity, and the runner then writes them to disk. Every operator type has a corresponding function base class, and you inherit the right one when you write your own transform. docorder also ships several functions that can be used straight from the configuration, for example the `DirectorySource` that reads a directory and the `TemplateToPrompt` that renders a Jinja template. Chapter 7 lists them all.

### Job and node

A job describes "which steps this run executes, in what order they relate to each other, and where the results are written". It is a directed acyclic graph. A directed acyclic graph means that every edge has a direction, from upstream to downstream, and following the edges never brings you back to where you started, in other words there are no cyclic dependencies between the steps. A job is created with `Job(name, root)`, where `root` is the output root.

Every point in the job is called a node, and nodes are added to the job with the `add_operator_node` method. Each node refers to one operator home and, except for a source node, must name exactly one upstream node. A node can also override the function parameters of the operator home through its `config` argument, and override the scheduling parameters through its `parallelism` and `retry` arguments. The output directory of a node is always "output root/node name" and cannot be specified otherwise. The same operator home can be referenced by several nodes in the same job, for example to process two different upstreams with the same template operator. Adding the same node name again replaces the earlier node, without an error.

When a node is constructed, the `config` that was passed in is applied over the function parameters of the home and stored in the node's `props`. A `class` key in `config` is dropped, so it cannot swap the function. After construction the node no longer keeps `config`; the public object is `props`. Writing `parallelism` and `retry` into `config` only turns them into function parameters; scheduling still follows the values in the home, or the same-named arguments of `add_operator_node`.

A job object only exists in the memory of one Python process. It does not keep any processing progress itself; all progress is stored in the directories of the individual entities. Precisely because the progress lives in the entity directories, another process, or even another job script, can continue where the last run stopped as long as the output paths and the epoch are the same.

### Epoch and stage

An epoch is a name passed to `execute`, usually a date or a version number, such as `2026-10-16` or `v3`. It decides the level of subdirectory under the output directory of every node, and within one run all nodes use the same epoch. Switching to a new epoch means switching to a completely new set of empty directories, with every result computed from scratch; running again with the same epoch continues on the results and the progress of the last run.

A stage is the execution of one node in one run. One run executes the stage of every node in turn, following the dependency order of the job graph; a stage has to finish all the entities of this epoch before the next stage begins.

### Runner and expected names

The runner is the part of docorder that handles scheduling; calling `docorder.core.runner.execute` is what makes the runner start working. At the beginning of the stage of every non-source node, the runner first reads all the entities the upstream node already has in this epoch, and uses them to list the expected names. The expected names answer the question: "given the current state of the upstream, which output entities should this node have, and which upstream entities does each output entity depend on?" The runner then compares the expected names with the entities that already exist in this node's directory, one by one, and decides for each entity whether it should be created, redone, kept, or deleted. Chapter 3 describes this process in detail.

### How the concepts relate

The diagram below first draws the layers of the concepts, and then walks through the minimal example from chapter 1 again.

<!-- figure:concepts:start -->
<figure class="figure" id="fig-concepts">
<svg role="img" aria-labelledby="concepts-title concepts-desc" viewBox="0 0 900 560" width="100%" style="max-width:900px">
  <title id="concepts-title">How docorder's concepts relate</title>
  <desc>An operator home is referenced by a job node; the node writes an output directory during a run; the directory holds entities; the upstream snapshot of a downstream entity points back to its upstream.</desc>
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
  <rect x="104.25" y="128" width="61.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="135" y="140" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">referenced</text>
  <rect x="364.25" y="128" width="61.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="395" y="140" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">referenced</text>
  <rect x="114.15" y="266" width="41.7" height="16" rx="2" fill="#f6f1e8"/>
  <text x="135" y="278" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">writes</text>
  <rect x="116.625" y="396" width="36.75" height="16" rx="2" fill="#f6f1e8"/>
  <text x="135" y="408" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">holds</text>
  <rect x="252.4" y="148" width="51.6" height="16" rx="2" fill="#f6f1e8"/>
  <text x="304" y="160" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="end">upstream</text>
  <rect x="234.5" y="396" width="111" height="16" rx="2" fill="#f6f1e8"/>
  <text x="290" y="408" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">snapshot points back</text>
  <rect x="40" y="60" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="60" width="190" height="52" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <rect x="48" y="67" width="38.4" height="14" rx="2" fill="transparent" stroke="#5e584e" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="67.2" y="77" fill="#5e584e" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">static</text>
  <text x="135" y="84" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">operator home</text>
  <text x="135" y="101" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">notes_source</text>
  <rect x="300" y="60" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="60" width="190" height="52" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <rect x="308" y="67" width="38.4" height="14" rx="2" fill="transparent" stroke="#5e584e" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="327.2" y="77" fill="#5e584e" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">static</text>
  <text x="395" y="84" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">operator home</text>
  <text x="395" y="101" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">prompt</text>
  <rect x="40" y="200" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="200" width="190" height="52" rx="6" fill="rgba(27,71,68,0.08)" stroke="#1b4744" stroke-width="1"/>
  <rect x="48" y="207" width="25.2" height="14" rx="2" fill="transparent" stroke="#1b4744" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="60.6" y="217" fill="#1b4744" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">job</text>
  <text x="135" y="224" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">node notes</text>
  <text x="135" y="241" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">source · no upstream</text>
  <rect x="340" y="200" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="340" y="200" width="190" height="52" rx="6" fill="rgba(27,71,68,0.08)" stroke="#1b4744" stroke-width="1"/>
  <rect x="348" y="207" width="25.2" height="14" rx="2" fill="transparent" stroke="#1b4744" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="360.6" y="217" fill="#1b4744" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">job</text>
  <text x="435" y="224" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">node prompt</text>
  <text x="435" y="241" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">map · upstream notes</text>
  <rect x="40" y="330" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="330" width="190" height="52" rx="6" fill="#fffdf8" stroke="#5e584e" stroke-width="1"/>
  <text x="135" y="360" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">runs/notes/demo/</text>
  <rect x="340" y="330" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="340" y="330" width="190" height="52" rx="6" fill="#fffdf8" stroke="#5e584e" stroke-width="1"/>
  <text x="435" y="360" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">runs/prompt/demo/</text>
  <rect x="40" y="450" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="450" width="190" height="52" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="48" y="457" width="38.4" height="14" rx="2" fill="transparent" stroke="#5e584e" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="67.2" y="467" fill="#5e584e" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">result</text>
  <text x="135" y="474" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">entity hello</text>
  <text x="135" y="491" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">data · tag.json</text>
  <rect x="340" y="450" width="190" height="52" rx="6" fill="#f6f1e8"/>
  <rect x="340" y="450" width="190" height="52" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <rect x="348" y="457" width="38.4" height="14" rx="2" fill="transparent" stroke="#5e584e" stroke-width="0.8" stroke-opacity="0.5"/>
  <text x="367.2" y="467" fill="#5e584e" font-size="8" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle" letter-spacing="0.08em" fill-opacity="0.85">result</text>
  <text x="435" y="474" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">entity hello</text>
  <text x="435" y="491" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">data · tag.json</text>
  <text x="888" y="90" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="end">operator home</text>
  <text x="888" y="230" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="end">job node</text>
  <text x="888" y="360" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="end">output directory</text>
  <text x="888" y="480" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="end">entity</text>
</svg>
<figcaption><span class="fig-label">Figure 1</span> How the concepts fit together: an operator home is referenced by a node, the node writes an output directory, the directory holds entities, and a downstream entity's upstream snapshot points back to its upstream.</figcaption>
</figure>
<!-- figure:concepts:end -->

```text
DOCORDER_HOMES = homes/
  homes/notes_source/   operator home: props.json (type=source, class=DirectorySource)
  homes/prompt/         operator home: props.json (type=map, class=TemplateToPrompt), lib/note.jinja
                          │ referenced by a node
                          ▼
job Job("hello", runs/)
  ├─ node notes   ── operator home: notes_source ── config: directory ── output: runs/notes/
  └─ node prompt  ── operator home: prompt       ── upstream: notes        ── output: runs/prompt/

execute(job, "demo")      the epoch is demo, each node runs one stage
  runs/notes/demo/hello/        entity: data, tag.json
  runs/prompt/demo/hello/       entity: data, tag.json (with upstream)
                                  └─ upstream snapshot: records the hash of the body of runs/notes/demo/hello
```

### Terminology

| Term | Name in English or in the code | Meaning |
| --- | --- | --- |
| Entity | entity | The result of one object under one node and one epoch; on disk it is a directory |
| Body | `data` | The main content of an entity, a piece of text |
| Tag | `tag.json` | The additional information of an entity, a JSON object |
| Upstream snapshot | `upstream` in `tag.json` | The upstream entities an entity read, and the hash of the upstream body and user tag at that time |
| Operator | operator | A reusable step, of one of the five types |
| Operator home | operator home | The directory that holds all the files of one operator; it must contain `props.json` |
| Function | function | The Python class that performs the transform, named by `class` in `props.json` |
| Job | `Job` | The steps one run executes and the order between them |
| Node | node | One step of the job that refers to an operator |
| Epoch | epoch | The name of a batch of results, and one level of subdirectory in the output directory |
| Stage | stage | The complete execution of one node in one run |
| Runner | runner | The part of docorder that handles scheduling |
| Expected names | expected names | The output entities a node should have given the current state of the upstream, and the upstream entities each output depends on |

## 3. How a run works

This chapter explains in time order what happens after `execute(job, epoch, start_from_scratch=False)` is called. The whole process has two parts: the first is assembly, which checks whether the whole job is correct and prepares the transform class of every node; the second is the execution of the stage of every node in turn, in dependency order. In the second part, as soon as one stage raises an exception, the whole run stops there and the nodes behind it never start.

### Assembly

The assembly phase first checks whether the job graph itself is reasonable. These cases are rejected: a cyclic dependency between nodes; an upstream node named by a node that does not exist in the job; a node that names itself as its upstream; an apply node with no upstream; a node that names an apply node as its upstream; two nodes whose output directories resolve to the same directory; and a node whose output directory lies inside another node's output directory. The last two can be caused by symbolic links or by node names that contain `/`.

After the job graph passes the check, the runner loads the Python class that the `class` key of `props.json` names for every node and tries to create an instance. If the class cannot be found, or is not a subclass of the base class for that operator type, or still has a method it must implement but does not, the run stops with an `OperatorValidationError`. Because all these checks happen before any node starts, a wrong class name on the very last node is caught right away and the nodes before it do not run for nothing.

Assembly also builds one entity table for this epoch per output directory. The same directory has only one table within one run; a node updates it when it writes, and its downstream reads it as the upstream.

The execution order of the nodes is decided by the job graph: a node always comes after its upstream node, and this order is called topological order. When several nodes are ready at the same time, the one added to the job first runs first.

### The life of one stage

The stage of a source node is very different from the others and is described separately at the end of this chapter. This section describes the stage of a map, reduce, and fanout node, which goes through the following steps in order. An apply node writes no entities, so its expected names are always empty, but `execute` still calls the function.

<!-- figure:stage:start -->
<figure class="figure" id="fig-stage">
<svg role="img" aria-labelledby="stage-title stage-desc" viewBox="0 0 900 640" width="100%" style="max-width:900px">
  <title id="stage-title">What one stage does</title>
  <desc>A stage creates the output directory, lists the expected names, compares them with the entities on disk, cleans up and reserves, calls the function, post-processes the tag, and finally writes data and tag.json; entities that match are kept as they are.</desc>
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
  <rect x="261.625" y="200" width="36.75" height="16" rx="2" fill="#f6f1e8"/>
  <text x="280" y="212" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">match</text>
  <rect x="300" y="48" width="300" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="48" width="300" height="48" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="76" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">create the output directory</text>
  <rect x="300" y="124" width="300" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="124" width="300" height="48" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="146" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">list the expected names</text>
  <text x="450" y="163" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">read the upstream entities</text>
  <rect x="300" y="200" width="300" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="200" width="300" height="48" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="228" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">compare with the entities on disk</text>
  <rect x="300" y="276" width="300" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="276" width="300" height="64" rx="6" fill="rgba(27,71,68,0.08)" stroke="#1b4744" stroke-width="1"/>
  <text x="450" y="306" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">clean up and reserve</text>
  <text x="450" y="323" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">delete what is gone · empty tag.json</text>
  <rect x="300" y="372" width="300" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="372" width="300" height="64" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="402" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">call the function</text>
  <text x="450" y="419" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">transform_data → transform_props</text>
  <rect x="300" y="468" width="300" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="468" width="300" height="64" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="498" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">post-process the tag</text>
  <text x="450" y="515" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">merge global_prop · reset upstream</text>
  <rect x="300" y="564" width="300" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="564" width="300" height="48" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="592" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">write data, then tag.json</text>
  <rect x="40" y="200" width="220" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="200" width="220" height="64" rx="6" fill="rgba(29,104,66,0.08)" stroke="#1d6842" stroke-width="1"/>
  <text x="150" y="230" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">matches</text>
  <text x="150" y="247" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">kept as is, function not called</text>
  <rect x="640" y="176" width="240" height="208" rx="6" fill="#f6f1e8"/>
  <rect x="640" y="176" width="240" height="208" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="654" y="199" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">four outcomes of the comparison</text>
  <rect x="654" y="226" width="8" height="8" rx="2" fill="#1d6842"/>
  <text x="668" y="234" fill="#1c1915" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">snapshot matches</text>
  <text x="668" y="249" fill="#5e584e" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">keep, skip the function</text>
  <rect x="654" y="268" width="8" height="8" rx="2" fill="#1c1915"/>
  <text x="668" y="276" fill="#1c1915" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">expected, not on disk</text>
  <text x="668" y="291" fill="#5e584e" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">create it and run the function</text>
  <rect x="654" y="310" width="8" height="8" rx="2" fill="#1c1915"/>
  <text x="668" y="318" fill="#1c1915" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">snapshot or depend differs</text>
  <text x="668" y="333" fill="#5e584e" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">clear it and reprocess</text>
  <rect x="654" y="352" width="8" height="8" rx="2" fill="#9a3412"/>
  <text x="668" y="360" fill="#1c1915" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">on disk, not expected</text>
  <text x="668" y="375" fill="#5e584e" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">delete the entity directory</text>
  <text x="40" y="28" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">stage begins</text>
  <text x="40" y="630" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">stage ends</text>
</svg>
<figcaption><span class="fig-label">Figure 2</span> One stage: after the comparison, matching entities are skipped and the rest go through cleanup, the function call and the write.</figcaption>
</figure>
<!-- figure:stage:end -->

When the stage starts, the runner creates the output directory of this node.

#### Listing the expected names

Next, the runner reads all the entities the upstream node already has in this epoch and lists the expected names of this node. Different operator types list them differently. For a map node, each upstream entity has one same-named output entity, and that output entity depends on that one upstream entity. For a fanout node, the runner calls the `output_names` method of the function to ask which output entities each upstream entity splits into; each output entity depends on the upstream entity that produced it. For a reduce node, the expected names always have exactly one entry: one output entity whose name is decided by the parameter `output` (`result` when it is not set), and it depends on all the upstream entities. An apply node writes no entities, so its expected names are empty.

When the expected names are empty, the stage neither compares nor deletes anything. This is what happens for a map or fanout node when the upstream has no entity at all; the function is not called, and the entities already in this epoch stay as they are. The expected names of an apply node are always empty, but `execute` still calls the function for every upstream entity. The expected names of a reduce node are never empty: even with no upstream entity at all it still produces that one output entity, only the list of upstream entities handed to the function is empty.

#### Comparing with the entities on disk

When the expected names are not empty, the runner reads the entities already in this node's directory and compares them with the expected names one by one, sorting them into these groups. An entity that is in the expected names but not yet in the directory has to be created. An entity that is in the directory but no longer in the expected names, for example because the upstream deleted the corresponding object, has to be deleted. An entity that is in both is compared, through the `upstream` in its `tag.json`, with the current state of the upstream, and has to be redone when any of these holds: the `upstream` is missing or invalid; the names of the upstream entities recorded in the snapshot differ from the ones listed in the expected names; the node name in the record is not the current upstream node; the epoch in the record is not the epoch of this run; the hash in the record is empty, or differs from the hash of the current body and user tag of the upstream entity; this entity's own `tag.json` cannot be read or is not a JSON object. After the upstream comparison passes, an operator that declares `fingerprint.depend` also checks the hashes of the dependency files, as the section "Fingerprints" below describes. An entity that passes both is kept as it is, and the function is not called for it in this run. `fingerprint.record` takes no part in this comparison.

#### Fingerprints

The upstream snapshot only covers "the body and user tag of the upstream entity". If an operator also reads external files that the upstream entity does not carry, for example a `.sql` file next to a table definition, `fingerprint` is how such dependencies are declared.

`fingerprint` in `props.json` or in the node `config` is an object with at most two sections, `record` and `depend`. Each section is an object whose keys are path templates; the values written in the configuration are not used. The `fingerprint` stored in the entity tag uses the same keys, and the values are the sha256 of the bytes of each file. This key belongs to the user tag, so it is part of the body hash.

The templates are filled with `{name}`, `{staging}`, and the string parameters of the operator. `{name}` is the entity name and always wins over a parameter of the same name. `{staging}` is the `.staging` directory of the job; a string parameter of the same name overrides it. A relative path is resolved from the job root. `record` is rendered after the tag has been filled, so it can still use the string fields of the tag, and a parameter overrides a tag field of the same name. `depend` is rendered before the function runs, so it can only use `{name}`, `{staging}`, and parameters.

`record` names the files this operator writes itself, or the files a source points at. A map, reduce, or fanout records them after `transform_props` and before the snapshot; a source records them after `emit` has handed over the body and the tag, and still only when `start_from_scratch` is set. A change in these hashes does not redo this operator. After the write, the file must exist, or the stage fails with `FatalError`. When the function left no body but `record` is declared, the runner sets the body to a single newline, so that the hash of an empty body is not a hash that never matches. A body the function set is left as it is.

`depend` names the files this operator reads that the upstream entity does not carry. It is rendered before the clearing and compared with the hashes recorded in the tag: a different set of keys, or any different hash, redoes that entity. After a successful write the hashes are updated, so the next comparison sees the files of this run. When a file does not exist or a placeholder has no value, the stage stops with `FatalError` before the clearing, so existing entities are not deleted.

A source that declares `depend`, or an apply that declares `fingerprint`, is rejected at assembly with `JobValidationError`. A source does no comparison before it runs, and an apply has no entity of its own.

#### Clearing and reserving

After the comparison and before any function is called, the runner tidies the directory of the whole stage in one pass: it first deletes all the entity directories that have to be deleted and all the entity directories that have to be redone, and then creates for every entity that has to be created or redone a directory that holds only an empty `tag.json` as a placeholder. This means that as soon as the stage starts executing, every entity that has to be redone has already lost its old body. If the stage fails halfway, the entities that have not been reached yet stay in the state of holding only an empty `tag.json`; their `tag.json` has no `upstream`, so on the next run they are recognized as unfinished and processed again.

#### Filling and writing

For each entity that is waiting, the runner first calls the `transform_data` method of the function to fill in the body, then calls the `transform_props` method to fill in the tag. The body the function fills in has to be a string and the tag has to be a dictionary (that is, a JSON object), otherwise the entity fails with `FatalError`.

When the function has finished, the runner takes care of `global_prop` and `upstream` in the tag. If the tag of the upstream entity has an object named `global_prop`, the runner merges it into the `global_prop` of the target entity's tag; if the target entity already wrote a key of the same name, the value the target wrote wins. For a reduce node there are many upstream entities taking part in the merge, and the runner merges them one by one in the order of the entity names, so the values in a later entity overwrite the ones in an earlier one. The point of this mechanism is that data put into `global_prop` can travel from the start of the job to the end, and it is not lost even if some function in between does not copy the upstream tag over.

`upstream` is always reset, and a leftover `current` is dropped. The upstream entity is handed to the downstream function, and the function often copies the whole upstream tag over, which already contains the upstream's own `upstream`. The runner does not keep that: the `upstream` of the target becomes a live snapshot of the direct upstream entities at that moment (that one record when there is one upstream, and a list of those records when there is none or several). This record has four fields: `operator` is the upstream node name, `name` is the upstream entity name, `epoch` is the epoch of this run, and `hash` is the sha256 of the upstream entity's body together with its user tag. A source node has no upstream and writes no `upstream`.

Finally, the runner writes the entity directory in a fixed order: first `data`, then `tag.json`. Each file is first written to a `.tmp` temporary file in the same directory and only then replaces the real file name, so a file is never left half written. `tag.json` is written last precisely so that the entity only counts as finished once both the body and the snapshot are in place. If an old `upstream.json` is left in the directory, it is deleted after the write.

Every stage prints one progress bar on standard error, with the node name as its title. For a map, fanout, or reduce the total is the number of entities expected in this stretch, and the ones that passed the comparison and are skipped in this round are counted in as well. For an apply the total is the number of upstream entities of this call. A source advances it record by record in `emit` and does not know the total at the start. A parallel map or fanout shares this one progress bar.

### Parallelism and retry

A map or fanout node can process entities with several threads at the same time to shorten the total run time. The concrete method is: the runner cuts the list of entities waiting to be processed into several contiguous slices; the number of slices does not exceed the `parallelism` parameter of the node, and does not exceed the number of entities waiting. If only one slice is cut, they are processed one by one in the current thread; if several slices are cut, each slice gets a worker thread, and each thread processes its own slice in order. These threads share the operator and the parameters of the current process. A reduce node has only one output entity, and a source node works in a different way, so neither of the two is sliced.

The worker threads are started through the `ThreadPoolExecutor` of the Python standard library and do not start another process, so the code that starts the job does not have to be under `if __name__ == "__main__":` for parallelism, and `config` does not have to be picklable.

During a parallel run, if one entity of a slice finally fails, the entities behind it in that slice are not processed, but the other slices run to the end, and the exception is only raised after all the slices have finished. Therefore, after a parallel run fails, there may be more finished entities on disk than you expected.

The processing of each entity is retried according to the `retry` parameter of the node. If the function raises a `FatalError`, it means there is a problem that retrying cannot solve, such as a missing configuration or a wrong template, and then there is no retry and the stage fails at once. If it raises another kind of exception, such as an external command returning an error, the runner waits a while and tries again, waiting `backoff_seconds` times the number of attempts so far seconds, until the total number of attempts reaches `max_attempts`. An entity that has successfully written the `upstream` in `tag.json` stays in the directory; when you run the same job with the same epoch again, those entities pass the comparison and are skipped, and the runner only processes the remaining ones.

### The stage of a source node

A source node has no upstream, so it does not list expected names and does not take part in the comparison above. Whether it produces entities again depends only on whether this call to `execute` passed `start_from_scratch=True`.

If it was not passed, the source node does not call the function and does not change the existing entities; it only makes sure the output directory and the marker file exist, and the downstream nodes read the entities it left the last time. Note that if the very first run on a brand-new epoch does not pass this flag, the source node's directory is empty and the downstream sees an empty upstream: a map or fanout node does nothing at all, and a reduce node produces a result from empty input.

If it was passed, the runner calls the `emit` method of the function, reads the records it hands over one by one, and writes each one as an entity as it arrives. The entity name of each record has to follow the naming rules, the same name must not appear twice, the body has to be a string, and the tag has to be a dictionary. When it writes, the runner overwrites the `data` and `tag.json` in the entity directory directly and deletes a possible leftover `upstream.json`. A source writes no `upstream`. After all the records have been written, the entities of this epoch that were not handed over this time are deleted, so that the entities in the source node's directory match the external data exactly. The `retry` parameter of a source node only applies to the single action of writing one record to disk; if the `emit` method itself raises an exception, for example because an input file is not valid UTF-8 text, that exception is not retried, and the old entities that have not been handed over yet are not deleted either. The directory only becomes consistent again when the next run with `start_from_scratch=True` finishes successfully.

### Decisions on a later run

The table below gathers the cases described above and shows what happens to each entity when the same epoch runs again.

<!-- figure:rerun:start -->
<figure class="figure" id="fig-rerun">
<svg role="img" aria-labelledby="rerun-title rerun-desc" viewBox="0 0 900 640" width="100%" style="max-width:900px">
  <title id="rerun-title">How an entity is judged on a re-run</title>
  <desc>An entity that is expected but missing is created; one that exists but is not expected is deleted; when both exist, the entity is kept if its upstream snapshot and its depend fingerprint agree, and reprocessed otherwise.</desc>
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
  <rect x="208" y="158" width="26.85" height="16" rx="2" fill="#f6f1e8"/>
  <text x="208" y="170" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="start">yes</text>
  <rect x="208" y="278" width="26.85" height="16" rx="2" fill="#f6f1e8"/>
  <text x="208" y="290" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="start">yes</text>
  <rect x="449.05" y="96" width="21.9" height="16" rx="2" fill="#f6f1e8"/>
  <text x="460" y="108" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">no</text>
  <rect x="449.05" y="216" width="21.9" height="16" rx="2" fill="#f6f1e8"/>
  <text x="460" y="228" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">no</text>
  <rect x="449.05" y="352" width="21.9" height="16" rx="2" fill="#f6f1e8"/>
  <text x="460" y="364" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">no</text>
  <rect x="298" y="444" width="26.85" height="16" rx="2" fill="#f6f1e8"/>
  <text x="298" y="456" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="start">yes</text>
  <rect x="118" y="484" width="106.05" height="16" rx="2" fill="#f6f1e8"/>
  <text x="118" y="496" fill="#9a3412" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="start">depend file missing</text>
  <rect x="40" y="88" width="340" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="88" width="340" height="64" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="124" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">is it in the expected list?</text>
  <rect x="40" y="208" width="340" height="64" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="208" width="340" height="64" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="244" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">does it already exist on disk?</text>
  <rect x="40" y="328" width="340" height="96" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="328" width="340" height="96" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="374" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">snapshot matches and depend matches?</text>
  <text x="210" y="391" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">name, node, epoch and hash must agree</text>
  <rect x="560" y="92" width="300" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="92" width="300" height="56" rx="6" fill="rgba(154,52,18,0.08)" stroke="#9a3412" stroke-width="1"/>
  <text x="710" y="124" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">delete the entity directory</text>
  <rect x="560" y="212" width="300" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="212" width="300" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="710" y="244" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">create · call the function</text>
  <rect x="560" y="348" width="300" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="348" width="300" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="710" y="380" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">clear and reprocess</text>
  <rect x="560" y="440" width="300" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="440" width="300" height="56" rx="6" fill="rgba(29,104,66,0.08)" stroke="#1d6842" stroke-width="1"/>
  <text x="710" y="472" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">keep · no function call</text>
  <rect x="560" y="512" width="300" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="512" width="300" height="56" rx="6" fill="rgba(154,52,18,0.08)" stroke="#9a3412" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="710" y="544" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">FatalError · nothing is cleared</text>
  <text x="40" y="596" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">An empty expected list means no comparison at all: map and fanout with no upstream, and apply nodes.</text>
  <text x="40" y="614" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">A reduce node with no upstream compares anyway, and the function receives an empty list.</text>
</svg>
<figcaption><span class="fig-label">Figure 3</span> Judging on a re-run: three questions decide whether an entity is kept, reprocessed, created or deleted.</figcaption>
</figure>
<!-- figure:rerun:end -->

| Case | What happens to the entity |
| --- | --- |
| In the expected names, not in the directory | Created, and the function is called |
| In the directory, not in the expected names | The whole entity directory is deleted |
| In both, the upstream snapshot matches the current upstream, and `depend` matches or was not declared | Kept, the function is not called |
| In both, no upstream snapshot, an invalid upstream snapshot, or an invalid `tag.json` | Cleared and processed again |
| In both, the upstream entity name, node name, epoch, or entity hash differs | Cleared and processed again |
| In both, the upstream matches, but a key or hash of `fingerprint.depend` differs | Cleared and processed again |
| `depend` is declared, but the file does not exist or the template placeholder has no value | Stops with `FatalError`, without clearing |
| A map or fanout node whose upstream has no entity at all | No comparison, the directory stays as it is |
| A reduce node whose upstream has no entity at all | Compared as usual, the function receives an empty list |
| An apply node | Entities are not compared. The function is called for every entity of the current upstream; an empty upstream calls only `finish` |
| A source node, without `start_from_scratch=True` | The function is not called, the entities stay as they are |

### Common situations when running again

From this table you can derive a few rules that come up in daily use.

#### The last run stopped halfway

The entities in the failed stretch whose upstream snapshot was already written stay; only the entities with an empty `tag.json` and no snapshot are redone; the downstream of the failed node never started last time and runs from the beginning now. The non-source nodes before the failed node pass the comparison as long as their upstream did not change, and their functions are not called again.

#### An upstream entity changed

When the body or user tag of an upstream entity changes, the downstream entities that depend on it are redone. A redone entity that writes the same body and user tag as last time passes the comparison of its own downstream, so the redo stops there; otherwise it continues down the graph. For a reduce, a change to the body or user tag of any upstream entity, and an upstream entity appearing or disappearing, redoes that one output. Without `start_from_scratch` you can also edit the `data` or `tag.json` in an already written upstream entity directory directly, and the downstream is redone on the next run.

#### Upstream entities appeared or disappeared

An upstream entity that appears shows up as a creation in a map downstream, and an upstream entity that disappears shows up as a deletion. The one exception is an upstream with no entity left at all: the expected names of a map or fanout are then empty, the downstream directory stays as it is, and it is not emptied because of that.

#### The operator itself changed

When the template, the parameters, the function code, or an external tool changed while the upstream entities did not, the upstream snapshot still matches and the old result is kept. To make the new logic take effect, delete the `<epoch>/` directory of that node, or some of the entity directories in it, or use another epoch. Deleting only the `upstream` from the `tag.json` of an entity also makes it redo, and keeps the directory available for inspection until the redo starts.

#### A source that does not regenerate

Without `start_from_scratch=True`, a change to the source files does not reach the entities of the source, and the downstream naturally does not see it either. Only when it is passed does the source reread its input, and only then does the change start propagating from the root of the graph.

### The directories one run leaves behind

After a run finishes, the output root looks like this:

<!-- figure:layout:start -->
<figure class="figure" id="fig-layout">
<svg role="img" aria-labelledby="layout-title layout-desc" viewBox="0 0 900 500" width="100%" style="max-width:900px">
  <title id="layout-title">What a run leaves on disk</title>
  <desc>Under the output root there is .staging and one directory per node; a node directory is layered by epoch, and each entity directory holds a data file and a tag.json.</desc>
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
  <text x="150" y="66" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;output root&gt;/</text>
  <rect x="40" y="124" width="180" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="124" width="180" height="44" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="130" y="150" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">.staging/</text>
  <rect x="360" y="124" width="180" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="360" y="124" width="180" height="44" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="450" y="150" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;node name&gt;/</text>
  <rect x="40" y="208" width="180" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="208" width="180" height="44" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="130" y="234" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;file name&gt;</text>
  <rect x="320" y="208" width="160" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="320" y="208" width="160" height="44" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="400" y="234" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;epoch&gt;/</text>
  <rect x="560" y="208" width="200" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="560" y="208" width="200" height="44" rx="6" fill="#fffdf8" stroke="#6f685c" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="660" y="234" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;another epoch&gt;/</text>
  <rect x="280" y="292" width="160" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="280" y="292" width="160" height="44" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="360" y="318" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">&lt;entity name&gt;/</text>
  <rect x="200" y="376" width="120" height="40" rx="6" fill="#f6f1e8"/>
  <rect x="200" y="376" width="120" height="40" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="260" y="394" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">data</text>
  <text x="260" y="411" fill="#5e584e" font-size="9" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">the body</text>
  <rect x="380" y="376" width="130" height="40" rx="6" fill="#f6f1e8"/>
  <rect x="380" y="376" width="130" height="40" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="445" y="394" fill="#1c1915" font-size="12" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">tag.json</text>
  <text x="445" y="411" fill="#5e584e" font-size="9" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">the tag</text>
  <text x="236" y="150" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">the whole job's output</text>
  <text x="236" y="234" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">holds the upstream body</text>
  <text x="560" y="276" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">an old epoch stays put</text>
  <text x="525" y="400" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">carries the upstream snapshot</text>
  <text x="40" y="446" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">The epoch is an argument to execute; every node in a run shares it.</text>
  <text x="40" y="466" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">.staging belongs to no node and is not an epoch layer.</text>
</svg>
<figcaption><span class="fig-label">Figure 4</span> What a run leaves on disk: node directories are layered by epoch, and an entity directory holds data and tag.json.</figcaption>
</figure>
<!-- figure:layout:end -->

```text
<output root>/
  .staging/                 overall job output, written by the apply function `Output`
    <file name>             the body of an upstream entity
  <node name>/
    <epoch>/
      <entity name>/
        data
        tag.json            includes the upstream snapshot when the entity has an upstream
    <another epoch>/
      ...
```

`.staging` is the overall output of the job, not an epoch directory of entities for some node.

The epoch is the name the caller passes to `execute`, and also the name of the subdirectory level the entities live in. Within one run, the output of every node uses this epoch, and the epoch recorded in the snapshots is it as well. Another epoch means another set of subdirectories: a new epoch starts from empty directories, the entities of the old epoch stay where they are, and the runner neither reads nor cleans them. When the epoch recorded in a snapshot differs from the current one, the entity has to be redone.

The runner does not check the epoch name and joins it into the path as it is. A name such as `2026/10` creates two directory levels, so pass a single directory name, for example a date or a version number.

## 4. Fingerprints and hashes

### The three kinds of hash in docorder

Deciding whether a result can still be used comes down to comparing hashes. There are three kinds of hash in docorder, and each one answers a different question:

| Hash | What it hashes | Where it is kept | What it decides |
| --- | --- | --- | --- |
| The hash inside the upstream snapshot | The body of the upstream entity together with its user tag | In the `upstream` of the downstream entity's `tag.json` | Whether the upstream result changed |
| `fingerprint.depend` | The external files the operator reads that the upstream entity does not carry | In the `fingerprint` of this entity's `tag.json` | Whether those external files changed |
| `fingerprint.record` | The external files the operator writes itself | In the `fingerprint` of this entity's `tag.json` | Nothing; it is bookkeeping only |

The first one is chapter 3. This chapter covers the other two and how the three make one decision.

### The hash inside the upstream snapshot

Chapter 2 said that `upstream` records a snapshot of the direct upstream entity. A record has four fields: `operator` is the upstream node name, `name` is the upstream entity name, `epoch` is the epoch of this run, and `hash` is the sha256 of the body of the upstream entity together with its user tag.

The algorithm is simple: the body of the upstream entity and its user tag are put into one JSON object, and the sha256 of that JSON is taken. Two details are worth remembering.

First, what goes into the hash is the "user tag", that is, the `tag.json` with the `upstream` and `current` keys removed. `upstream` has to be excluded, otherwise the hash would contain itself and would never settle; `current` is a leftover key from an earlier version and is excluded as well. Every other key of the user tag takes part, so every field the function writes into the tag is counted.

Second, an empty body hashes to an empty string. An empty body means the content of that entity was never written, so it cannot match any earlier result. When the runner sees an empty hash, it judges the entity as not matching.

### Declaring a fingerprint

The upstream snapshot only covers "the body and user tag of the upstream entity". Some operators read other files: the `.sql` file next to a table definition, a list of root words, an intermediate file an upstream step wrote. The content of those files is not in the upstream entity, so the upstream snapshot cannot see them change.

The `fingerprint` object in `props.json` is there for that case. It is an object with at most two sections:

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

`record` and `depend` are both objects. Their keys are path templates, and the values do not matter at all: docorder only reads the keys, and the value is only there as a placeholder.

The two sections have fixed roles:

- `record` lists the files this operator writes itself, or the files a source points at. After the entity is written, the runner hashes those files and records the result in this entity's `tag.json`.
- `depend` lists the files this operator reads that the upstream entity does not carry. During the comparison the runner hashes those files and compares them with the values recorded in the entity.

`record` is bookkeeping only and takes no part in the "does it have to be redone" decision. Changing a file listed in `record` does not make this operator redo itself; it only records the state of the file as it was seen, for downstream steps and for troubleshooting. What actually decides a redo is `depend`.

### How the two checks make one decision

For an entity of a non-source node to stay, two things have to hold at the same time: the upstream snapshot matches the current state of the upstream, and the hash of every file listed in `depend` matches the one recorded before. If either fails, the entity is redone. When both hold, the entity is kept as it is and the function is not called.

<!-- figure:hashes:start -->
<figure class="figure" id="fig-hashes">
<svg role="img" aria-labelledby="hashes-title hashes-desc" viewBox="0 0 900 640" width="100%" style="max-width:900px">
  <title id="hashes-title">How the two hashes decide an entity</title>
  <desc>An entity stays when the upstream snapshot matches the current upstream and every file declared in depend has the hash recorded before; if either check fails the entity is redone. record is bookkeeping and takes no part in the decision.</desc>
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
  <rect x="286.575" y="404" width="26.85" height="16" rx="2" fill="#f6f1e8"/>
  <text x="300" y="416" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">yes</text>
  <rect x="579.05" y="404" width="21.9" height="16" rx="2" fill="#f6f1e8"/>
  <text x="590" y="416" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">no</text>
  <rect x="40" y="56" width="340" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="56" width="340" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="82" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">the upstream body and user tag</text>
  <text x="210" y="99" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">a changed body no longer matches</text>
  <rect x="105" y="148" width="210" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="105" y="148" width="210" height="44" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="174" fill="#1c1915" font-size="13" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">sha256</text>
  <rect x="40" y="228" width="340" height="68" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="228" width="340" height="68" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="210" y="260" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">compare with the hash in the snapshot</text>
  <text x="210" y="277" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">the hash of the upstream body and user tag</text>
  <rect x="520" y="56" width="340" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="520" y="56" width="340" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="690" y="82" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">the external files named in depend</text>
  <text x="690" y="99" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">files the upstream entity does not carry</text>
  <rect x="585" y="148" width="210" height="44" rx="6" fill="#f6f1e8"/>
  <rect x="585" y="148" width="210" height="44" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="690" y="174" fill="#1c1915" font-size="13" font-weight="600" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">sha256</text>
  <rect x="520" y="228" width="340" height="68" rx="6" fill="#f6f1e8"/>
  <rect x="520" y="228" width="340" height="68" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="690" y="260" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">compare with fingerprint.depend in tag.json</text>
  <text x="690" y="277" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">a different key set or hash means a redo</text>
  <rect x="300" y="344" width="300" height="60" rx="6" fill="#f6f1e8"/>
  <rect x="300" y="344" width="300" height="60" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="378" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">do both match?</text>
  <rect x="80" y="452" width="280" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="80" y="452" width="280" height="56" rx="6" fill="rgba(29,104,66,0.08)" stroke="#1d6842" stroke-width="1"/>
  <text x="220" y="484" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">keep · no function call</text>
  <rect x="540" y="452" width="280" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="540" y="452" width="280" height="56" rx="6" fill="rgba(154,52,18,0.08)" stroke="#9a3412" stroke-width="1"/>
  <text x="680" y="484" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">redo · clear and reprocess</text>
  <rect x="40" y="548" width="820" height="56" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="548" width="820" height="56" rx="6" fill="#fffdf8" stroke="#1c1915" stroke-width="1"/>
  <text x="450" y="574" fill="#1c1915" font-size="13" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">fingerprint.record is bookkeeping only</text>
  <text x="450" y="591" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">it goes into tag.json, so it is part of this entity's own hash</text>
</svg>
<figcaption><span class="fig-label">Figure 7</span> How the two hashes make one decision: the entity is kept only when the upstream snapshot and depend both match.</figcaption>
</figure>
<!-- figure:hashes:end -->

`depend` has a knock-on effect. The `fingerprint` lives in `tag.json`, and the user tag part of `tag.json` goes into the hash of the upstream snapshot. So when a file in `depend` changes, this operator redoes itself and its new hash changes with it; the downstream step sees that the upstream changed and redoes itself as well. That is how a change travels outwards from the middle of the graph.

### Path templates and placeholders

Placeholders in a template are written as `{name}`, and these are the values they can take:

| Placeholder | Value |
| --- | --- |
| `{name}` | The name of the current entity. It always wins over a parameter of the same name |
| `{staging}` | The `.staging` directory of the job. A string parameter of the same name overrides it |
| `{parameter}` | A string parameter of the operator, that is, `props.json` without the reserved keys, after the node's `config` has overridden it |
| `{tag field}` | Only `record` can use it: a string field of the operator tag. A parameter of the same name overrides the tag field |

One piece of text may use several placeholders. A placeholder that cannot be filled makes that section fail with `FatalError`: the file does not exist, or the placeholder has no value. A relative path is resolved from the job root; an absolute path is used as it is.

`record` and `depend` are rendered at different moments, and that decides which values they can use:

- `depend` is rendered before the function runs, so it can only use `{name}`, `{staging}` and parameters. At that point the entity has not been written yet and its tag is empty.
- `record` is rendered after the tag has been filled, so besides the values above it can also use the string fields of the tag.

### The order of things in one run

Putting all of this into one stage:

1. Compare. The runner reads the existing entities, compares the upstream snapshot of each one and then the file hashes of `depend`, and sorts them into four groups: create, redo, keep, delete.
2. Clear. The directories that have to go are removed, and every entity that has to be created or redone gets a placeholder directory holding an empty `tag.json`.
3. Before the run. The paths of `depend` are rendered and the files are hashed. When a file is missing the stage stops with `FatalError` here, before the clearing, so the entities that already exist are not deleted.
4. Call the function. `transform_data` fills the body and `transform_props` fills the tag.
5. Account. The paths of `record` are rendered and the files are hashed, and the result goes into the `fingerprint` of `tag.json`. The files have to exist at this point, or the stage fails with `FatalError`.
6. Write. `data` is written first, then `tag.json`.

A source node is different: it has no upstream, so it neither compares nor lists expected names. It only runs when `execute` is called with `start_from_scratch=True`, and it accounts after `emit` has handed over the body and the tag.

### Declarations that are refused

Some declarations are refused during assembly, and the job never starts:

- A source cannot declare `depend`. A source does no comparison before it runs, so it has no use for that hash.
- An apply cannot declare `fingerprint` at all. An apply writes no entity, so it has nowhere to keep the hash.

Both fail with `JobValidationError`.

### An empty body

When the function leaves no body but the operator declares `record`, the runner writes a single newline as the body.

The reason is in the algorithm: an empty body hashes to an empty string, and an empty string never equals the hash recorded last time, so the entity would be judged as needing a redo on every run. A newline gives the body some content, the hash settles, and the comparison means something. A body the function wrote itself is left as it is.

### A node config replaces the whole fingerprint

The `fingerprint` in `props.json` and the `fingerprint` in a node's `config` are the same key, and the node's `config` replaces it as a whole rather than merging with it:

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

The code above drops every fingerprint key the operator home declared in `props.json` instead of adding one more to them. When the home declares three sections of fingerprint, the node's `config` has to write all three.

### Troubleshooting

The fingerprint is kept in the entity's `tag.json`, and looks like this:

```json
{
  "fingerprint": {
    "depend": {
      "{staging}/raw_root.csv": "3a7bd3e2360a3d29eea436fcfb7e44c735d117c42d1c1835420b6b9942dd4f1b"
    }
  }
}
```

The key is the template, not the rendered path. To find out which file a template points at this time, replace the placeholders with their actual values and look.

When an entity is redone on every run, check in this order:

1. Is the `hash` inside `upstream` an empty string? An empty hash means the upstream entity has no body.
2. Is the `epoch` the epoch of this run? An entity from another epoch is redone.
3. Is the set of keys under `fingerprint.depend` the same as the one declared now? One key too many or too few is enough to redo.
4. Does the hash under the key match the current content of the file?
5. Does a key under `fingerprint` use the wrong template, so that it points at a different file every time?

## 5. Use cases

docorder is at its best with this kind of task: a batch of objects that are independent of each other, each of which has to go through a few processing steps, where some of those steps are slow, expensive, or prone to failure. In such tasks docorder can guarantee that only the failed part is redone after a failure, and only the affected part is redone after the input changes. Below are several typical job graphs; they all need nothing more than the functions that ship with docorder, or very little code of your own.

### Batch prompt generation and a model call

This is the most typical use of docorder. The first step of the job is a source node that reads a directory and turns every subdirectory that follows the entity convention into an entity. The second step is a map node that uses `TemplateToPrompt` and applies the template to each entity to produce a prompt. The third step is a map node that uses `PromptToLLM` and hands each prompt to a command line model tool; whatever the tool prints on standard output, or writes itself into the `data` of the target entity, becomes the body of this step. Finally you can add a reduce node that uses `TemplateToLLM` to collect all the answers into one list. The node that calls the model usually needs a `retry` configuration, so that an occasional API error is retried automatically, and a `parallelism` to control how many requests are in flight at the same time. If a few objects still fail after several retries, fix the problem and run the same epoch again: docorder only redoes those few objects, and the objects that already have an answer are not sent to the model again. The example project in chapter 10 is built in this shape.

### Generating configuration files from structured data

If the body of an upstream entity is a JSON object, for example the field definitions of a table or the description of a service, you can first use a map node with `JinjaToJsonnet` to treat every key of the JSON object as a template variable and render a jsonnet program, then use a map node with `JsonnetToPrompt` to compile it with the locally installed `jsonnet` program and get the final JSON or text. jsonnet is a language made for generating JSON configuration; it supports variables, functions, and list comprehensions, and is more flexible than writing JSON by hand. This combination suits generating configuration files of a uniform format from a batch of table definitions or service descriptions.

### Running a command line tool for each entity

A map node with `Command` runs an external command once for each entity. The arguments of the command can refer to the tag, the body, and the output directory of the entity, and the result of the command can be what it prints on standard output or what it writes to a file on disk. This function starts the command directly, without a shell, so spaces and special characters in the arguments are not interpreted again by a shell. It suits calling code formatters, format converters, or scripts of your own team in bulk.

### Gathering and splitting

A reduce node merges a batch of entities into one entity, which suits results that have to combine all the objects, such as an index, a table of contents, or a statistical report. The built-in `TemplateToLLM` can render the whole upstream batch into one prompt for the model and write the reply as that one output entity. A fanout node splits one entity into several, which suits cutting a long document into paragraphs or chapters and then handling them separately in later steps. Fanout has no built-in function; you write it yourself as described in chapter 9, and it usually takes a dozen lines of code.

### Cases that do not fit

Some tasks do not suit docorder. If a step has to read the results of two different upstream nodes at the same time and wants the entity to be redone whenever either of them changes, the current version cannot express such a dependency. If you need to distribute the work across several machines, or want the downstream to start on an object as soon as the upstream has finished it, docorder cannot do that either. It is equally unsuitable when the content of the objects is binary data such as images or audio, because the body can only be text. And if there are only a few objects, every step is fast, and running everything again from the start after a failure costs nothing, then writing an ordinary Python script is simpler.

## 6. Configuration

This chapter gathers everything that has to be configured when you use docorder: how docorder finds the operator homes, what every key in `props.json` means, the arguments of creating a job and adding a node, the arguments of the run function `execute`, and which configuration the functions and the templates read.

### Letting docorder find the operator homes

docorder looks for operator homes through the environment variable `DOCORDER_HOMES`. Its value is one or more directories, separated by the same separator as the system environment variable `PATH`: a colon `:` on macOS and Linux, and a semicolon `;` on Windows. When it looks, docorder searches the directories in the order they are listed, and the earlier ones win; once a home is found the search stops.

An operator home can sit directly in one of the listed directories, or in a category subdirectory of one of them, but not deeper than that. Category subdirectories help you organize many operator homes by purpose, and those whose names start with `.` or `_` are skipped. A directory is recognized as an operator home as soon as it contains a `props.json` file; the name of the operator home is the name of that directory, and that is the name you use to refer to it when you add a node.

```text
homes/                        DOCORDER_HOMES points here
  sources/                    category subdirectory, optional
    table_source/             operator home named table_source
      props.json
  render/
    table_prompt/             operator home named table_prompt
      props.json
      lib/table.jinja
```

docorder looks for the operator home at the moment `add_operator_node` adds the node, so the environment variable has to be set before the job is built. When no operator home of the given name is found, a `FileNotFoundError` is raised, and the message lists all the directories that were searched, which makes it easy to troubleshoot. The simplest approach is to set the environment variable in the start script with `os.environ["DOCORDER_HOMES"] = ...`; the parallel threads are in the same process and read the same environment variable.

### props.json

`props.json` is a JSON object. The table below lists the keys that docorder itself interprets; every other key is passed to the function as a parameter. The last column of the table says whether the value of the key can be overridden in the job, and how.

| Key | Type and default | Meaning | Can it be overridden in the job |
| --- | --- | --- | --- |
| `type` | Required | The operator type, one of `source`, `map`, `reduce`, `fanout`, `apply` | No |
| `class` | Required | The function class, written as `module path:ClassName`; written as `primary:ClassName` it means the class in the `primary.py` file of the operator home | No |
| `parallelism` | Integer, default 1 | The maximum number of threads a map or fanout node uses at the same time | With the `parallelism` argument of `add_operator_node` |
| `retry.max_attempts` | Integer, default 1 | The maximum number of attempts per entity, not less than 1; the default of 1 means no retry | With the `retry` argument of `add_operator_node` |
| `retry.backoff_seconds` | Number, default 0 | The base number of seconds to wait before each retry; the actual wait is `backoff_seconds × attempts so far` seconds | The same |
| `output` | String, default `result` | Only effective for reduce nodes, and it names the single output entity | With the node's `config` |
| `fingerprint` | Object | Declares which external files this operator depends on, in the two sections `record` and `depend`; see the section "Fingerprints" in chapter 3 | With the node's `config` |
| Other keys | Any JSON value | Function parameters, such as `template` and `directory` | With the node's `config` |

`retry` is written as a nested object, for example `"retry": {"max_attempts": 3, "backoff_seconds": 5}`, which means each entity is tried at most three times, waiting 5 seconds after the first failure and 10 seconds after the second. If `props.json` is not a JSON object, `class` has no colon, or `type` is not one of the five above, `add_operator_node` fails with a `JobValidationError`.

### Job and node

`Job(name, root)` creates a job, where `name` is the job name and `root` is the output root. An absolute path is recommended for the output root, so that the results are written to the same place no matter which directory the script is started from. Nodes are added to the job with this method:

```python
job.add_operator_node(
    name,                 # node name, also the subdirectory name under the output root
    operator_home,        # name of the operator home, looked up in the directories listed by DOCORDER_HOMES
    upstream=None,        # upstream node name; a source node leaves it empty, every other node must set it, and it can only be one string
    config=None,          # a dict that overrides the function parameters of the operator home
    parallelism=None,     # overrides the parallelism in props.json
    retry=None,           # overrides the retry in props.json, written as RetryPolicy(max_attempts=..., backoff_seconds=...)
)
```

`RetryPolicy` has to be imported from `docorder.utils.retry`. There are a few things to keep in mind when you use this method: `upstream` can only be one string, and a list or a tuple is rejected, which corresponds to the limit that every node has exactly one upstream; if you add a node with the same name twice, the second one replaces the first without an error, so make sure the node names differ; the node name is joined into the output path without any check, so use a simple name made of letters, digits, hyphens, or underscores.

When a node is constructed, the `config` that was passed in is applied over the function parameters of the operator home and written into `props`. On a shared key the value in `config` wins, and the `class` in `config` is ignored, so you cannot swap the function through `config`. After construction the node no longer keeps `config`, and the parameters are read from `props` from then on. When the job starts running, the runner constructs an operator for every node and lifts the public fields of the node onto the operator. After that the name, the parameters, the output path, and the upstream are all read from the operator and never from the node again. One thing is easy to confuse: putting `parallelism` or `retry` into `config` does not change the parallelism or the retry policy of the node, they only become ordinary function parameters; to change these two scheduling parameters in a job you have to use the same-named arguments of `add_operator_node`.

### execute

```python
from docorder.core.runner import execute

execute(job, epoch, start_from_scratch=False)
```

The `epoch` is used directly as one directory level, and docorder does not check its content, so use a simple name such as a date or a version number; a name with a slash like `2026/10` creates two directory levels. `start_from_scratch=True` asks the source nodes to call the function and produce the entities again; without it, the source nodes keep the entities they left the last time. On the first run with a new epoch you normally need to pass this flag, or the source node's directory is empty and the whole job has no input.

### What a function reads and what a template reads

The same set of parameters is handed to you in two forms: one for the code of the function to read, and one for the template to read. Both contain exactly the same parameters and both follow the rule that the node's `config` overrides `props.json`. The only difference is that the one the template reads has a few more pieces of runtime information filled in by the runner.

The code of a function reads the parameters through `self.environment.operator_props`. Its content is what is left of `props.json` after removing the keys `type`, `class`, `parallelism`, `retry`, and `home`, with the same-named keys of the node's `config` applied over it. The function uses these parameters to decide how it runs, for example `TemplateToPrompt` reads `template` from here to know which template file to use. A template reads `self.environment.template_env`, which holds `operator`, `job`, and `entity`.

A template reads the operator information through a variable named `operator`. It is based on the parameters the function reads, that is, the parameters of `props.json` after the node's `config` has overridden them; on top of that the runner fills in a few pieces of information about this run, namely `name`, `home`, `function_class`, `type`, and `operator_home`, which override the parameters of the same name. The meaning of each is in the variable table in chapter 8. So after you override `template` in the node's `config`, the template file that is actually used and the value that `{{ operator.template }}` shows in the template both change; a key that is only in the node's `config` and not in `props.json` can be read in the template the same way, as `operator.<key>`. The pieces the runner fills in are the only exception: even if you write `name` in `config`, the template still reads the node name. `parallelism` and `retry` are reserved keys of `props.json` and are not passed down as function parameters, so `operator` does not have them; the epoch of this run is in `job.epoch`, not in `operator`.

### Environment variables

| Variable | Read by | Meaning |
| --- | --- | --- |
| `DOCORDER_HOMES` | `add_operator_node` | The list of directories in which operator homes are looked for |
| `DOCORDER_LLM` | `PromptToLLM` | The model tool used when a node has no `tool` parameter; the value is a tool name or the path of a tool definition file |

## 7. Operator types and the built-in functions

### The five operator types

The five operator types differ in how the input entities correspond to the output entities, and where the result of the job is written. The table below compares them from several angles. The "function base class" column is the class that the function of such an operator has to inherit, and the "built-in functions" column lists the functions that ship with docorder and can be used directly in `props.json`.

<!-- figure:operators:start -->
<figure class="figure" id="fig-operators">
<svg role="img" aria-labelledby="operators-title operators-desc" viewBox="0 0 900 540" width="100%" style="max-width:900px">
  <title id="operators-title">The five operator types</title>
  <desc>source produces entities from external data; map turns one upstream entity into one entity of the same name; reduce merges every upstream entity into one; fanout splits one upstream entity into several; apply only calls the function and produces no entity.</desc>
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
  <text x="140" y="28" fill="#6f685c" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">upstream entities</text>
  <text x="410" y="28" fill="#6f685c" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">operator</text>
  <text x="700" y="28" fill="#6f685c" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">output entities</text>
  <rect x="70" y="52" width="140" height="48" rx="6" fill="#f6f1e8"/>
  <rect x="70" y="52" width="140" height="48" rx="6" fill="rgba(27,71,68,0.08)" stroke="#1b4744" stroke-width="1"/>
  <text x="140" y="80" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">external data</text>
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
  <text x="700" y="416" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">writes no entity</text>
  <path d="M 227.0 412.0 L 272 412.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <path d="M 548 412.0 L 620 412.0" fill="none" stroke="#5e584e" stroke-width="1" marker-end="url(#operators-arrow)"/>
  <rect x="240.75" y="388" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="249.5" y="400" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">N</text>
  <rect x="575.25" y="388" width="17.5" height="16" rx="2" fill="#f6f1e8"/>
  <text x="584" y="400" fill="#6f685c" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">0</text>
  <text x="40" y="470" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">Entity names: source comes from emit, map matches the upstream,</text>
  <text x="40" y="490" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">reduce uses the output argument, fanout comes from output_names,</text>
  <text x="40" y="510" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">apply writes no entity and can have no downstream.</text>
</svg>
<figcaption><span class="fig-label">Figure 5</span> The five operator types: the number over each arrow counts entities, and apply is the only type that produces none.</figcaption>
</figure>
<!-- figure:operators:end -->

| Type | How the input corresponds to the output | Where the name of the output entity comes from | Can it run in parallel | Function base class | Built-in functions |
| --- | --- | --- | --- | --- | --- |
| source | No upstream, produces entities from external data | Every record the `emit` method hands over | No | `SourceFunction` | `DirectorySource`, `FilteredDirectorySource`, `FileHashSource` |
| map | One upstream entity gives one output entity | The same name as the upstream entity | Yes | `MapFunction` | `TemplateToPrompt`, `JinjaToJsonnet`, `JsonnetToPrompt`, `Command`, `PromptToLLM`, `EntityTemplateToLLM` |
| reduce | All upstream entities give one output entity | The parameter `output`, default `result` | No | `ReduceFunction` | `TemplateToLLM` |
| fanout | One upstream entity gives several output entities | The return value of the `output_names` method | Yes | `FanoutFunction` | None |
| apply | The function is called once per upstream entity and produces no entity | None | No | `ApplyFunction` | `Output` |

The class that `class` names in `props.json` has to be a subclass of the base class of the `type`. For example, when `type` is `map`, `class` can only be `MapFunction` or a subclass of it, and writing a function of type source fails at assembly with an error. The five rendering map functions that ship with docorder all inherit from `RenderedMap`, which is a subclass of `MapFunction` and provides the three-step shape of "read, render, generate the tag". Chapter 8 introduces it. `EntityTemplateToLLM` is also a map, but it does not go through those three steps.

### The source operator

A source operator sits at the start of the job graph and turns external data into the first batch of entities. As chapter 3 said, a source node only runs its function to reread the external data when `execute` is called with `start_from_scratch=True`.

#### DirectorySource

The full name of `DirectorySource` is `docorder.functions.impl.directory_source:DirectorySource`. It collects the subdirectories of a directory that are already shaped like entities into entities. It only handles the direct subdirectories of that directory and does not go deeper. The name of the subdirectory is the entity name; the subdirectory has to hold `data` and `tag.json`, the body comes from `data`, and the tag comes from `tag.json`. Ordinary files, subdirectories missing one of the two files, and subdirectories whose names start with `.` or `_` are all skipped.

| Parameter | Required | Meaning |
| --- | --- | --- |
| `directory` | Required | The input directory to read; a relative path is resolved from the operator home |

The following situations cause a failure. If a `data` is not valid UTF-8 text, or a `tag.json` is not a JSON object, the stage fails and is not retried. If the directory named by `directory` does not exist, the stage fails with `FatalError`.

The input data usually belongs to the concrete project and not to the operator, so the input directory is generally not put in the operator home; instead you pass an absolute path through `config` when you add the node:

```python
job.add_operator_node("tables", "table_source", config={"directory": str(ROOT / "data" / "tables")})
```

If you need to change part of the behaviour of `DirectorySource`, you can write a subclass and override one or more of these three methods: `extract_tag(name, content, tag)` decides the tag of each entity directory, where `name` is the directory name, `content` is the text of `data`, and `tag` is the `tag.json` that was read; `include(path)` decides whether an entity directory is collected into a record, and returning `True` keeps it; `generate(directory)` replaces the whole process of "producing records from a directory". The `TableSource` in chapter 10 is an example that overrides `extract_tag`.

#### FilteredDirectorySource

The full name of `FilteredDirectorySource` is `docorder.functions.impl.directory_source:FilteredDirectorySource`. On top of `DirectorySource` it adds a `filter` parameter, which selects the wanted entities by the ending of the entity directory name and by the size of the `data` file. Every other behaviour is exactly the same as in `DirectorySource`.

| Parameter | Required | Meaning |
| --- | --- | --- |
| `directory` | Required | The same as in `DirectorySource` |
| `filter.disabled_suffix` | Optional | A string or a list of strings; an entity directory whose name ends with one of them is excluded |
| `filter.enabled_suffix` | Optional | A string or a list of strings; once it is set, only entities whose directory name ends with one of them are kept |
| `filter.min_size` | Optional | A non-negative integer, the lower bound of the size of the `data` file in bytes; a size equal to the bound is kept |
| `filter.max_size` | Optional | A non-negative integer, the upper bound of the size of the `data` file in bytes; a size equal to the bound is kept |

For every entity directory the checks run in this order: first whether it matches `disabled_suffix`, and if it does it is excluded; then whether `enabled_suffix` is set, and if it is set but the directory name does not match, it is excluded as well; finally whether the size of the `data` file is within the range. If `filter` is not an object, one of the suffixes is an empty string, a size is not a non-negative integer, or `min_size` is greater than `max_size`, the stage fails with `FatalError`.

The configuration below only reads the entities under `inputs/` in the operator home whose `data` is at most 64 KB:

```json
{
  "type": "source",
  "class": "docorder.functions.impl.directory_source:FilteredDirectorySource",
  "directory": "inputs",
  "filter": { "max_size": 65536 }
}
```

#### FileHashSource

The full name of `FileHashSource` is `docorder.functions.impl.directory_source:FileHashSource`. On top of `DirectorySource` it adds a `paths` parameter, which writes the absolute paths of a set of files into the tag of the entity. The body is still the original `data` of the input directory, and the file hashes are not computed by this function.

| Parameter | Required | Meaning |
| --- | --- | --- |
| `directory` | Required | The same as in `DirectorySource` |
| `paths` | Required | An object whose keys are the field names written into the tag and whose values are path templates; what is written into the tag is the resolved absolute path |

The values of `paths` are path templates that use `{name}` placeholders. You can fill them with a string from the tag of the entity, or with a string from the operator parameters, and on a shared name the operator parameter overrides the tag. A relative path is resolved from the operator home. When the file does not exist, a placeholder has no value, or `paths` is not an object, the stage fails with `FatalError`.

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

The values inside `fingerprint.record` are not used; only its keys are templates. The `{name}` placeholders in the template can be filled with `{name}` (the entity name), `{staging}` (the `.staging` directory of the job), the string fields of the tag, and the string values of the operator parameters, and on a shared name a parameter overrides the tag. A relative path is resolved from the job root. After the runner hands over the records, it records the sha256 of the files in the tag of the entity, and uses it to tell whether the source files changed; see the section "Fingerprints" in this chapter. A source node can only declare `record`, not `depend`.

### The map operator

A map operator produces one same-named output entity for each upstream entity, and it is the most common kind of operator. The five rendering map functions that ship with docorder all inherit from `RenderedMap`; which variables they can use in a template or in the arguments of a command is explained in chapter 8. `EntityTemplateToLLM` uses a separate Jinja template that holds only paths to call the LLM.

#### TemplateToPrompt

The full name of `TemplateToPrompt` is `docorder.functions.impl.template_to_prompt:TemplateToPrompt`. It renders every entity with a Jinja template from the operator home, and the rendered text is the body of the output entity; the tag of the output entity is a copy of the tag of the upstream entity.

| Parameter | Required | Meaning |
| --- | --- | --- |
| `template` | Required | The path of the template file relative to the operator home; this path must not point outside the operator home |

This function renders the template with Jinja in strict mode: if the template refers to a variable that does not exist, the render fails outright instead of quietly replacing it with an empty string, so that a typo in the template is found early. A syntax error in the template and a missing variable both fail with `FatalError` and are not retried, because however often you try the result is the same.

```json
{
  "type": "map",
  "class": "docorder.functions.impl.template_to_prompt:TemplateToPrompt",
  "template": "lib/note.jinja"
}
```

If the content of `lib/note.jinja` is `Note: {{ entity.source_data }}` and the body of the upstream entity is `hello`, then the body of the output entity is `Note: hello`. The `entity.source_data` here is a built-in template variable of docorder, and it stands for the body of the upstream entity.

#### JinjaToJsonnet

The full name of `JinjaToJsonnet` is `docorder.functions.impl.jinja_to_jsonnet:JinjaToJsonnet`. It requires the body of the upstream entity to be a JSON object, treats every key of that object as a variable of the Jinja template, renders the template in the operator home, and the rendered result is a jsonnet program that becomes the body of the output entity. The tag it produces is an empty object, but the runner still merges the upstream `global_prop` into it as usual.

| Parameter | Required | Meaning |
| --- | --- | --- |
| `template` | Required | The path of the template file relative to the operator home |
| `variables` | Optional | A JSON object that gives default values for the template variables; a key of the same name in the upstream body overrides the value here |

In the template, writing `{{ table }}` inserts the value of the variable as plain text; writing `{{ columns | jsonnet }}` converts the value of the variable into a literal that jsonnet understands, through the `jsonnet` filter, for example a string gets quotes and a list or an object is written in the matching syntax. A filter is a piece of Jinja syntax that hands a value to a function with the pipe `|`. If the upstream body is empty, is not valid JSON, is not a JSON object, `variables` is not an object, the template has an error, or the rendered result is all whitespace, the stage fails with `FatalError`.

Here is an example of a template:

```text
{
  table: {{ table | jsonnet }},
  owner: {{ owner | jsonnet }},
  columns: [c.name for c in {{ columns | jsonnet }}],
  column_count: std.length(self.columns),
}
```

Suppose the body of the upstream entity is `{"table": "orders", "columns": [...]}`, where `columns` lists three fields, and the `variables` parameter is `{"owner": "data-team"}`. This template renders a jsonnet program, which is then compiled by the `JsonnetToPrompt` described in the next section, and the result is JSON like `{"column_count": 3, "columns": ["order_id", "user_id", "amount"], "owner": "data-team", "table": "orders"}`.

If you need to customize its behaviour, write a subclass: overriding the `template_text()` method lets the code provide the template content directly instead of reading it from a file; overriding the `generate_props` method lets you extract information from the rendered result and use it as the tag of the output entity.

#### JsonnetToPrompt

The full name of `JsonnetToPrompt` is `docorder.functions.impl.jsonnet_to_prompt:JsonnetToPrompt`. It takes the body of the upstream entity as a jsonnet program and compiles it with the command `jsonnet -`, passing the program on standard input; what the compiler prints on standard output is the body of the output entity, and the tag of the output entity is a copy of the upstream tag. This function has no parameters of its own, but it requires `jsonnet` to be installed on the machine and to be on the `PATH`.

If the `jsonnet` command cannot be found, the stage fails with `FatalError`; if the compilation returns a non-zero exit code, an ordinary exception is raised and retried according to the `retry` parameter of the node. If the jsonnet program uses `import` to pull in other files, the paths are resolved exactly as they are written in the program; in the template of `JinjaToJsonnet` you can get the absolute path of the operator home with `{{ home }}`, and build the full path of a file in the operator home from it.

#### Command

The full name of `Command` is `docorder.functions.impl.command:Command`. It runs an external command once for each entity, and the command is started directly, without a shell.

| Parameter | Required | Meaning |
| --- | --- | --- |
| `argv` | Required | A list whose first item is the command and whose other items are its arguments; every `{name}` placeholder in an item is replaced with the matching value |
| `cwd` | Optional | The working directory of the command; the placeholders in it are not replaced |
| `output_file` | Optional | The result file the command writes; the placeholders in it are replaced; a relative path is relative to the current directory of the Python process that runs the script |
| `capture` | Optional | Where the body comes from: `file`, `stdout`, or `none`; the default is `file` when `output_file` is set and `stdout` otherwise |

When `capture` is `file`, the content of `output_file` is read as the body after the command finishes; when it is `stdout`, what the command printed on standard output is the body; when it is `none`, the body is an empty string, which suits the cases where only the side effects of the command matter. The tag of the output entity is a copy of the upstream tag plus a `command` key, which holds the full command line after the placeholders were replaced; when `output_file` is set, there is also an `output_file` key, which holds the replaced file path.

```json
{
  "type": "map",
  "class": "docorder.functions.impl.command:Command",
  "argv": ["cp", "{entity.source_data_path}", "{entity.output}/copy.json"],
  "output_file": "{entity.output}/copy.json"
}
```

In this example, `{entity.source_data_path}` is replaced with the path of the body file of the upstream entity, and `{entity.output}` is replaced with the directory of the entity being written. The command copies the source file into this entity directory, and then `Command` reads the copied file as the body. Because the command does not go through a shell, you cannot use a pipe `|` or a redirection `>` directly in the arguments; if you really need one, write it explicitly as `["sh", "-c", "..."]`, but then note that the values substituted into the command line are interpreted by the shell, and if those values come from untrusted input they may cause a command injection.

The following situations fail with `FatalError` and are not retried: the command cannot be found; `argv` is empty; the value of `capture` is not recognized; `capture` is `file` but `output_file` is not set; a placeholder refers to a name that does not exist. The following situations raise an ordinary exception and are retried according to `retry`: the command returns a non-zero exit code; `capture` is `file` and the command did not write `output_file`.

#### PromptToLLM

The full name of `PromptToLLM` is `docorder.functions.impl.prompt_to_llm:PromptToLLM`. It takes the body of the upstream entity as a prompt and hands it to a model tool that runs as a command line program. After the tool returns, a `data` file that is already in the directory of the target entity is the body: it has to be non-empty UTF-8 text, and once the check passes it is not rewritten, only `tag.json` is added. Without that file, what the tool printed on standard output is the body. The tag of the output entity is a copy of the upstream tag. If a `data` file exists before the call starts, it is deleted first. docorder ships no preset configuration for any model tool; the tool has to be defined by you.

| Parameter | Required | Meaning |
| --- | --- | --- |
| `workspace` | Required | An existing directory, used as the working directory of the model tool process |
| `tool` | Optional | The tool to use: a tool name, the path of a tool definition file, or a tool definition object written inline; when it is not set, the environment variable `DOCORDER_LLM` is read |

When `tool` is a string, docorder first looks for a `tools/<name>.json` file in the operator home, and if that file does not exist, reads the string as a path to a file. A tool definition is a JSON object with the following fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `run` | Required | A non-empty list of strings, the command and its arguments; the `{workspace}` in it is replaced with the working directory |
| `prompt` | Optional | How the prompt is passed: `stdin` (the default) passes it on standard input, `arg` appends it as the last argument of the command |
| `name` | Optional | The name of the tool, which appears in error messages so that it is easy to recognize |

```json
{ "name": "my-llm", "run": ["my-llm-cli", "--cwd", "{workspace}"], "prompt": "stdin" }
```

The `my-llm-cli` above is only a placeholder name; in real use, replace it with the command line model tool you actually use. The following situations fail with `FatalError`: `workspace` is not set or the directory it names does not exist; the tool cannot be found; the format of the tool definition is wrong; the executable of the tool is not on the `PATH`. When the tool returns a non-zero exit code, an ordinary exception is raised and retried according to `retry`. Because a model API fails now and then because of rate limiting or network problems, an operator that uses `PromptToLLM` should usually configure `retry` in `props.json`.

#### EntityTemplateToLLM

The full name of `EntityTemplateToLLM` is `docorder.functions.impl.template_to_llm:EntityTemplateToLLM`. It renders one Jinja template per upstream entity, hands the rendered text to the model tool, and writes the reply as the body of that entity. It does not go through the three steps of `RenderedMap`; one call produces the body and the tag at the same time.

| Parameter | Required | Meaning |
| --- | --- | --- |
| `template` | Required | The path of the template file relative to the operator home |
| `workspace` | Required | An existing directory, used as the working directory of the model tool process |
| `tool` | Optional | The same as in `PromptToLLM` |
| `header` | Optional | The header line of the reply from which the body is taken; the meaning is the same as in `TemplateToLLM` |
| `tag_template` | Optional | A piece of Jinja whose rendered result is the tag of the entity |

The template sees `source`, which has the three fields `name`, `path`, and `tag`. `path` is the path of the `data` file of the upstream entity. The template can also call `staging(name)`, which gives the path of one file that already exists in the `.staging` directory of the job. The template does not get the content of the files; write the path in the prompt and let the model read it.

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

When the template refers to a variable that does not exist, the tool cannot be found, the tool definition is invalid, or the `header` has no matching line in the reply, the stage fails with `FatalError`; a non-zero exit code from the tool is retried according to `retry`.

### The reduce operator

A reduce operator merges all the entities the upstream has in this epoch into one output entity, whose name is decided by the parameter `output`, `result` when it is not set. The function receives the list of upstream entities sorted by entity name, and that one target entity. Because this output depends on all the upstream entities, a change to the body of any upstream entity, a new entity, or a deleted entity makes this output be computed again.

The built-in function is `docorder.functions.impl.template_to_llm:TemplateToLLM`. It renders all the upstream entities into one Jinja template, hands the rendered result to the model tool, and writes the reply as the body of that one output entity. The template sees `sources`, a list in the order the reduce received them, each item with `name`, `path`, and `tag`; `path` is the path of the `data` file of that entity. The template can also call `staging(name)`, which gives the path of one file that already exists in the `.staging` directory of the job. When `header` has a value, the body starts at that header line of the reply; `tag_template` is an optional piece of Jinja whose rendered result is the tag of the entity; `min_sources` and `max_sources` bound the number of upstream entities.

Other reduce transforms can be written by you; chapter 9 shows how and gives examples.

### The fanout operator

A fanout operator splits each upstream entity into several output entities. Which output entities it splits into is decided by the `output_names(source)` method of the function: it takes one upstream entity and returns a list of output entity names, and by default it returns only the name of the upstream entity itself. Across the whole stage, the names that all upstream entities split into have to be different from each other, or the stage fails with `OperatorValidationError`. The `output_names` method is called in the main process and may be called more than once in one run, so its result should depend only on the upstream entity passed in, and it should not have side effects such as writing files. docorder ships no function of the fanout type; chapter 9 gives an example.

### The apply operator

An apply operator calls the `apply` method of the function once for each entity the upstream has in this epoch, and then calls `finish` once. Both methods have to return `None`. It writes no entities, and no node in the job graph can name it as its upstream; it must itself have an upstream. When the upstream is empty, `apply` is not called but `finish` still is.

The built-in function is `docorder.functions.impl.output:Output`. It is called by the apply operator and writes the body of every entity as one file in `.staging` at the job root, as the overall output of the job. The parameter `directory` selects another path, and a relative path is resolved from the operator home. The file name is decided by `rename(entity)`, and by default it is the entity name; the parameter `filename` sets a fixed name, and a subclass overrides this method to name each entity. The return value has to be a single file name. Two entities that get the same file name make the stage fail with `FatalError`. The files this function wrote last time and does not produce this time are deleted in `finish`.

### Failure and retry

The table below summarizes which exception each kind of failure raises, and whether that exception is retried according to the `retry` parameter of the node.

| Case | Exception | Retried according to `retry` |
| --- | --- | --- |
| A cyclic dependency in the job graph, an upstream node that does not exist, conflicting output directories | `JobValidationError` | Not applicable, it fails before the execution starts |
| The function class cannot be found, or is not a subclass of the matching base class | `OperatorValidationError` | Not applicable, it fails before the execution starts |
| The operator home cannot be found | `FileNotFoundError` | Not applicable, it fails while the job is built |
| A missing configuration, a wrong template, a missing template variable, a wrong input format | `FatalError` | No |
| An external command, jsonnet, or a model tool returns a non-zero exit code | `DocorderError` | Yes |
| Any other exception raised by a function | The original exception | Yes |

All these exception classes are defined in `docorder.utils.errors`, where `DocorderError` is the common parent of `JobValidationError`, `OperatorValidationError`, and `FatalError`.

#### How each built-in function fails

`FatalError` means that the configuration or the input itself is wrong and another attempt will not help, so the stage fails at once. Every other exception, including a non-zero status from an external process, is tried again after waiting `backoff_seconds × attempts so far` seconds, until `max_attempts` is used up. To decide whether an error should be retried, compare it with the table below.

| function | Fails at once, no retry | Retried according to `retry` |
| --- | --- | --- |
| `DirectorySource`, `FilteredDirectorySource`, `FileHashSource` | missing `directory`, directory does not exist, malformed `filter`, malformed `paths`, a placeholder with no value, a path that is not a file, `data` that is not UTF-8, `tag.json` that is not an object | None |
| `TemplateToPrompt` | `template` missing, template file not in the home, template refers to a variable that does not exist | None |
| `JinjaToJsonnet` | `template` missing, upstream body empty or not a JSON object, render is only whitespace | None |
| `JsonnetToPrompt` | `jsonnet` not found | the compiler exits with a non-zero status |
| `Command` | `argv` missing, first command not found, a brace variable that does not exist, an invalid `capture` value | the process exits with a non-zero status, the command did not write `output_file` |
| `PromptToLLM` | `workspace` missing or not a directory, tool not found, invalid tool definition, first command not found | the process exits with a non-zero status, the written `data` is empty, not UTF-8, or not a file |
| `TemplateToLLM`, `EntityTemplateToLLM` | `template` missing, `workspace` missing or not a directory, a bad `header` / `tag_template`, the template refers to a missing variable, `staging` is given a bad file name or the file is missing, the reply has no `header`, tool not found, invalid tool definition, first command not found. `TemplateToLLM` also fails at once when the source count is wrong | the process exits with a non-zero status |
| `Output` | `directory` is not a non-empty string, `filename` is not a non-empty string, `rename` returns an invalid file name, two entities produce the same file name | a transient error while writing a `.staging` file |

## 8. Rendering functions and template variables

This chapter explains which data the map functions that ship with docorder can use when they render a template or substitute the arguments of a command, and how to add new template variables when the built-in data is not enough.

### The three steps of RenderedMap

The full name of `RenderedMap` is `docorder.functions.rendered_map:RenderedMap`. It is a subclass of `MapFunction` and splits the processing of one entity into three steps that follow one another. The first step is `read_source`, which reads the upstream entity and by default returns the body of the upstream entity. The second step is `apply_render`, which turns what the first step read into the body of the output entity; this is an abstract method that every subclass has to implement, for example `TemplateToPrompt` renders the template here and `Command` runs the command here. The third step is `generate_props`, which generates the tag of the output entity from the result of the second step, and by default it is a copy of the tag of the upstream entity. All three steps receive the same object named `Environment`, which is called the rendering environment; it gathers all the data that can be used while rendering.

An ordinary `MapFunction` has to implement the two methods `transform_data` and `transform_props` separately, and the runner calls them one after the other. `RenderedMap` already implements those two methods for its subclasses, and it guarantees that the three steps above run only once for the same upstream entity and target entity, so that the body and the tag both come from the same execution. Therefore a slow call, such as an external command or a model, happens only once per entity.

### The rendering environment

The rendering environment is `environment.template_env`, a nested dictionary that both the template and the command read.

```text
template_env
  operator                        the function parameters, plus this run's name and home
  job                             name, epoch
  entity                          the entity being rendered
    source_name, source_data, source_tag, source_data_path
    target_name, target_data_path, output
```

`TemplateToPrompt` hands this dictionary to Jinja. `Command` substitutes dotted paths such as `{operator.home}` and `{entity.output}`. `JinjaToJsonnet` uses it as well and additionally puts `home` at the top level. The tag of the entity is in `entity.source_tag`, and is no longer lifted to the top level.

### Built-in template variables

The table below lists the variables that the template of `TemplateToPrompt` and the placeholders of `Command` can use. Jinja writes them as `{{ operator.name }}`, `Command` writes them as `{operator.home}`.

<!-- figure:variables:start -->
<figure class="figure" id="fig-variables">
<svg role="img" aria-labelledby="variables-title variables-desc" viewBox="0 0 900 560" width="100%" style="max-width:900px">
  <title id="variables-title">The built-in template variables</title>
  <desc>The top level of template_env holds exactly three names: operator, job and entity. operator carries the function arguments overridden by config plus a few values filled in by the runner, job carries the job name and the epoch of this run, and entity is split between the upstream entity and the one being written.</desc>
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
  <text x="450" y="87" fill="#5e584e" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace" text-anchor="middle">templates read {{…}}, Command reads {…}</text>
  <rect x="30" y="156" width="270" height="176" rx="6" fill="#f6f1e8"/>
  <rect x="30" y="156" width="270" height="176" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="44" y="179" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">operator</text>
  <text x="44" y="201" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">name   home   function_class</text>
  <text x="44" y="219" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">type   operator_home</text>
  <text x="44" y="245" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">Function arguments: props.json without</text>
  <text x="44" y="263" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">the reserved keys, then overridden by config</text>
  <text x="44" y="281" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">e.g. template · directory</text>
  <rect x="320" y="156" width="180" height="176" rx="6" fill="#f6f1e8"/>
  <rect x="320" y="156" width="180" height="176" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="334" y="179" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">job</text>
  <text x="334" y="201" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">name</text>
  <text x="334" y="219" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">epoch</text>
  <text x="334" y="245" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">The job's name and the</text>
  <text x="334" y="263" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">epoch of this run</text>
  <rect x="520" y="156" width="350" height="176" rx="6" fill="#f6f1e8"/>
  <rect x="520" y="156" width="350" height="176" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="534" y="179" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">entity</text>
  <text x="534" y="201" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source_name    source_data</text>
  <text x="534" y="219" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source_tag     source_data_path</text>
  <text x="534" y="237" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">target_name    target_data_path</text>
  <text x="534" y="255" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">output</text>
  <text x="534" y="281" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">The first four describe the upstream</text>
  <text x="534" y="299" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">entity, the last three the one being written</text>
  <rect x="30" y="396" width="270" height="84" rx="6" fill="#f6f1e8"/>
  <rect x="30" y="396" width="270" height="84" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="44" y="419" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">where the arguments come from</text>
  <text x="44" y="441" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">props.json + 节点 config</text>
  <text x="44" y="459" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">runner adds name, home and type</text>
  <rect x="320" y="396" width="180" height="84" rx="6" fill="#f6f1e8"/>
  <rect x="320" y="396" width="180" height="84" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="334" y="419" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">where the job comes from</text>
  <text x="334" y="441" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">execute(job, epoch)</text>
  <text x="334" y="459" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">the two arguments of the call</text>
  <rect x="520" y="396" width="350" height="84" rx="6" fill="#f6f1e8"/>
  <rect x="520" y="396" width="350" height="84" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="534" y="419" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">where the entities come from</text>
  <text x="534" y="441" fill="#1c1915" font-size="10" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">the upstream entity + the one being written</text>
  <text x="534" y="459" fill="#5e584e" font-size="10" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">entity.source_tag is the upstream tag.json</text>
  <text x="40" y="516" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">JinjaToJsonnet differs at the top level: the upstream JSON keys, the variables argument, plus operator, job, entity and home.</text>
</svg>
<figcaption><span class="fig-label">Figure 6</span> The built-in template variables: three names at the top level, each with its own origin.</figcaption>
</figure>
<!-- figure:variables:end -->

| Variable | Content |
| --- | --- |
| `operator.name` | The name of the current node |
| `operator.home` | The absolute path of the current operator home |
| `operator.<parameter name>` | The parameters of the function, for example `operator.template` |
| `job.name`, `job.epoch` | The job name and the epoch of this run |
| `entity.source_name`, `entity.source_data`, `entity.source_tag`, `entity.source_data_path` | The upstream entity |
| `entity.target_name`, `entity.target_data_path`, `entity.output` | The entity being written |

The different rendering functions use these variables in different ways, and the following sections explain them one by one.

`TemplateToPrompt` renders the template with Jinja, so it can use the whole Jinja syntax, for example `{% for column in entity.source_tag.columns %} ... {% endfor %}` to walk a list, or `{{ entity.source_name | upper }}` to turn the text into upper case. As chapter 7 said, it uses strict mode, so referring to a variable that does not exist fails.

`Command` does not use Jinja; it only recognizes placeholders of the form `{name}`. A name can walk into nested objects with dots, for example `{entity.source_tag.global_prop.project}` means the `project` key inside the `global_prop` object of the upstream tag. A placeholder name can only consist of letters, digits, underscores, and dots, and the dictionary it resolves is the same as the one the template uses, that is `template_env`, so only the three top-level names `operator`, `job`, and `entity` are available. `Command` substitutes every item of `argv` and `output_file`, but not `cwd`. When a placeholder refers to a name that does not exist, the stage fails with `FatalError`.

`JinjaToJsonnet` also uses Jinja, but the top-level variables are different: the top level holds the keys of the JSON object in the upstream body and the keys of the `variables` parameter, plus the four keys `operator`, `job`, `entity`, and `home`, where `home` is `operator.home`. The keys of the upstream tag are not at the top level and have to be reached as `entity.source_tag.<key>`. If the upstream JSON happens to have a key named `operator`, `job`, `entity`, or `home`, it is overridden by these four built-in keys. It also provides the extra `jsonnet` filter.

`JsonnetToPrompt` renders no template at all. `PromptToLLM` does not render a prompt either; it substitutes only one placeholder, `{workspace}`, in the `run` of the tool definition.

### Adding a template variable

When the built-in variables do not meet your needs, you can add new ones in the six ways below. They are listed in the order of how much you have to change, and you should usually prefer the ones earlier in the list.

#### Add a parameter in props.json or in the node config

Every key of the function parameters that is not a reserved key appears in `operator`. For example, if you write `"audience": "business analyst"` in `props.json`, the template can refer to it with `{{ operator.audience }}`, and `Command` can refer to it with `{operator.audience}`. The same key can also be given when you add the node through `config`, overriding the default in `props.json`, for example `config={"audience": "data engineer"}`, and the template then reads `data engineer`. This method suits data that does not change: written into `props.json` it suits "the same template takes a different value in a different operator home"; written into the node's `config` it suits "the same operator home takes a different value in a different job or node".

#### Let the upstream write data into tag.json

Every key of the tag of an upstream entity appears under `entity.source_tag` in the downstream template, so you can let the upstream step write the data you need into its `tag.json`. If the upstream is a source node, you can write a subclass of `DirectorySource` and override the `extract_tag` method to put the fields parsed out of the file content into the tag, and the downstream template can then refer to those fields. The `TableSource` in chapter 10, for example, parses a JSON table definition into the three keys `table`, `description`, and `columns`, so the downstream template can write `{% for column in entity.source_tag.columns %}` directly.

#### Produce new keys with generate_props

If the upstream is itself a rendering map node, you can override its `generate_props` method and add new keys to a copy of the upstream tag, and then the template of its downstream can read those new keys. The example below counts the words in the upstream body, uses that number as the body, and records it in the `words` key of the tag:

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

Downstream of this node, the template can write `{{ entity.source_tag.words }}`. The `carried_tag()` here returns a copy of the upstream tag, and changing the copy does not affect the upstream entity itself.

#### Pass data across several steps with global_prop

The `global_prop` object in the tag is merged by the runner into every downstream entity automatically, even when the tag produced by some function in between does not contain it, for example the tag produced by `JinjaToJsonnet` is an empty object and it is not lost either. This method suits data that is needed "from the start of the job, possibly at every step after it", for example a project name or a batch number. Writing `"global_prop": {"project": "orders domain"}` into the tag of a source node lets the template of any downstream node refer to it with `{{ entity.source_tag.global_prop.project }}`, and `Command` writes it as `{entity.source_tag.global_prop.project}`.

#### Use the upstream JSON and the variables parameter of JinjaToJsonnet

For `JinjaToJsonnet`, every key of the JSON object in the upstream body is a top-level variable, and the `variables` parameter provides default values for them. So to add a new variable you can let the upstream write one more key in the JSON, or add an entry to `variables` in `props.json` or in the node's `config`. `variables` is an ordinary function parameter, so the node's `config` can override it.

#### Inherit a rendering function and override apply_render

If the value you need can only be computed while rendering, for example the date of the day, the number of lines of the body, or data that has to be looked up somewhere else, you can write a subclass of `TemplateToPrompt` and override the `apply_render` method: first call `environment.template_env` to get all the built-in variables, then add the new keys to it, and then hand it to the `render` method provided by the parent class to finish the render.

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

Put this class into the `primary.py` file of the operator home, write `"class": "primary:DatedPrompt"` and `"template": "lib/p.jinja"` in `props.json`, and the template can use `{{ today }}` and `{{ line_count }}`, and the original built-in variables still work as before. The `source` in the method is the upstream body returned by `read_source`, and `self.artifact.read_text` reads a file from the operator home, which chapter 9 introduces. Note that the values injected while rendering are not recorded in the upstream snapshot: for example, when the date changes, the entities that are already done are not processed again because of it.

For `JinjaToJsonnet` the approach is similar: write a subclass and override the `read_source` method, and add the new keys to the dictionary it returns, because the keys of that dictionary are the top-level variables of the template.

### Which value wins when names collide

When variables from different sources share a name, the value that takes effect is decided by these rules. In `entity`, the names `source_name`, `source_data`, `source_tag`, `source_data_path`, `target_name`, `target_data_path`, and `output` are fixed, and a key of the same name in the upstream tag does not appear here; it only exists in `entity.source_tag`. In `operator`, the parameters in the node's `config` first override the parameters of the same name in `props.json`, and then the runner fills in `name`, `home`, `function_class`, `type`, and `operator_home`, and these keys override the ones before them. `class`, `parallelism`, `retry`, `type`, and `home` are reserved keys of `props.json` and are not passed down as function parameters. In `JinjaToJsonnet`, the keys of the upstream JSON override the keys of the same name in `variables`, and the four built-in keys `operator`, `job`, `entity`, and `home` override the keys of the same name in the upstream JSON.

## 9. Writing your own function

When the functions that ship with docorder do not meet your needs, you can write your own. The basic way to write a function is: define a Python class that inherits one of the base classes docorder provides and implement the few methods the base class specifies; then point the `class` key of the operator home's `props.json` at that class. This chapter explains in turn which base class to choose, which objects you can use in the methods, which conventions you must follow, where the code file goes, and it gives a complete example and a way to test it for every operator type. All the example code in this chapter has actually been run and verified.

### Choosing a base class

The table below lists the base class to inherit by "what you want to do", together with the methods you must implement and the ones you may override. A "must implement" method is an abstract method of the base class, that is, a method the base class only declares and does not implement; if a subclass does not implement them, the assembly phase fails with an `OperatorValidationError`. A "may override" method already has a default implementation in the base class and only has to be rewritten when you want to change the default behaviour.

| What you want to do | `type` | Base class to inherit | Must implement | May override |
| --- | --- | --- | --- | --- |
| Produce entities from any external data | source | `docorder.functions.source_function:SourceFunction` | `emit()` | None |
| Produce entities from a directory, but need to change the tag or select files | source | `DirectorySource` or `FilteredDirectorySource` | None | `extract_tag(name, content, tag)`, `include(path)`, `generate(directory)` |
| Transform entities one by one, the body and the tag can be computed separately | map | `docorder.functions.map_function:MapFunction` | `transform_data(source, target)`, `transform_props(source, target)` | None |
| Transform entities one by one, the tag depends on the result of the transform | map | `docorder.functions.rendered_map:RenderedMap` | `apply_render(source, source_entity, environment)` | `read_source`, `generate_props` |
| Add features to one of the rendering functions that ship with docorder | map | A built-in class such as `TemplateToPrompt` | None | `apply_render`, `generate_props`, and so on |
| Merge all entities into one | reduce | `docorder.functions.reduce_function:ReduceFunction` | `transform_data(sources, target)`, `transform_props(sources, target)` | None |
| Split one entity into several | fanout | `docorder.functions.fanout_function:FanoutFunction` | `transform_data(source, target)`, `transform_props(source, target)` | `output_names(source)` |
| Do one operation per upstream entity that produces no data | apply | `docorder.functions.apply_function:ApplyFunction` | `apply(entity)`, optionally `finish()` | None |

The `emit` method of `SourceFunction` should be written as a generator, that is, it uses `yield` inside the method to hand over the results one by one, each time one `SourceRecord(name, data, tag)` object, whose three arguments are the entity name, the body, and the tag. `SourceRecord` is defined in `docorder.functions.source_function` as well.

### What a function can use

Inside the methods of a function, the following attributes are reachable through `self`:

| Attribute | Content |
| --- | --- |
| `self.operator` | The operator that is running. `name`, `props`, `output_path`, `operator_home`, and `upstream` are on the operator; do not go through the node again |
| `self.environment` | Built by the operator. `operator_props` are the function parameters; `template_env` holds the `operator` / `job` / `entity` of the template |
| `self.artifact` | Read-only access to the operator home: `home` is the path of the operator home; `path(rel)` resolves a relative path into a full path inside the operator home; `exists(rel)` tells whether a file exists in the operator home; `read_text(rel)` reads a file from the operator home. None of the paths passed in may point outside the operator home |
| `self.operator_name` | The name of the current node |
| `self.epoch` | The epoch of this run |

The upstream entity and the target entity passed to the methods are `Entity` objects, and they offer the following members:

| Member | Content |
| --- | --- |
| `name` | The name of the entity |
| `directory` | The path of the entity directory |
| `read_text()` | Reads the body of the entity; if there is no `data` file, it returns an empty string |
| `tag` | The tag of the entity, a dictionary |
| `carried_tag()` | Returns a shallow copy of the tag, to be handed to the downstream |
| `staging_data` | The body the target entity is waiting to write; the function assigns it in `transform_data` |

### Rules you must follow

`transform_data` has to assign a string to `target.staging_data`, and `transform_props` has to assign a dictionary to `target.tag`, otherwise the entity fails with `FatalError`. When the target directory already has a `data` file, you may leave `staging_data` unset; the runner keeps that file and writes only `tag.json`. If you want to change the upstream tag, call `carried_tag()` first to get a copy and change the copy, and do not change the `tag` of the upstream entity directly. `carried_tag()` returns a shallow copy, that is, only the outermost level is copied and the lists and dictionaries nested inside are still shared with the upstream, so copy them yourself before you change nested content.

A function does not need to write `data` and `tag.json` itself, and should not; the runner writes them. A function does not need to create a thread pool or implement retry logic either; parallelism and retry are controlled by the `parallelism` and `retry` parameters of the node.

When an error occurs in a function, you should tell two kinds of failure apart. The first is a problem that retrying cannot solve, such as a missing required configuration or a wrong input format; then you should raise `docorder.utils.errors.FatalError`, so that the stage stops at once and no time is wasted on retries. The second is a problem that may recover on its own, such as a network error, an external service that is temporarily unavailable, or an external process that fails now and then; then you should raise another kind of exception and leave it to the `retry` mechanism.

The runner creates a new function object for every attempt at every entity, so do not keep state that has to be shared across entities in the attributes of the object. During a parallel run the function runs in a worker thread and shares the same memory as the operator.

A function may write helper files in `target.directory`, the directory of the target entity, for example `Command` writes the output file of the command there. These helper files are cleared together with the entity directory when the entity is redone or deleted.

Anything a function reads that is not part of the upstream entity, for example a template in the operator home, the result file of another node, or data returned by an external service, is not recorded in the upstream snapshot, and when it changes the runner does not automatically redo the entities that are already done.

### Where the code goes

There are two ways to put the code of a function.

The first way is to put it in the `primary.py` file of the operator home itself and write `"class": "primary:ClassName"` in `props.json`. This is the simplest way: the code stays with the configuration and the templates in the operator home, and copying the home carries the code along. An operator home can only have one `primary.py`, but that file can define several classes. Note that `primary.py` is loaded directly by file path, and the directory of the operator home is not on Python's module search path `sys.path`, so `primary.py` cannot use `import` to pull in other Python files of the same operator home; it can of course import docorder and other installed packages.

The second way is to put it in a Python package of your own project and write `"class": "package.module:ClassName"` in `props.json`. This suits the case where several operator homes have to share the same code, or where the code of a function is long enough to be worth splitting into several modules. The package has to be importable by Python, for example already installed in the same virtual environment, or sitting next to the start script. Parallel execution happens in the same process and uses the same import.

### Example: a custom source

The source function below produces entities from a JSON Lines file. JSON Lines is a text format with one JSON object per line, and it is often used to hold a batch of records. This function produces one entity for every line of the file:

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

The matching `props.json`:

```json
{ "type": "source", "class": "primary:JsonLinesSource", "file": "items.jsonl" }
```

This function reads the file path from the parameter `file`, and a relative path is resolved from the operator home; when the parameter is missing it raises `FatalError`, because that is a configuration problem that retrying cannot solve. The `id` field of each line of `items.jsonl` becomes the name of the entity, the whole JSON line becomes the body of the entity, and the `kind` field is recorded in the tag. The `id` of each line has to follow the entity naming rules and must not repeat, otherwise the stage fails with `OperatorValidationError`.

### Example: map

The map function below turns the upstream body into upper case and adds a flag to the tag:

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

The matching `props.json`:

```json
{ "type": "map", "class": "primary:Uppercase" }
```

The runner calls `transform_data` first and `transform_props` second, and the two are separate calls. If both methods need the same intermediate result, in particular the result of one slow external call, then inheriting `MapFunction` directly is not a good fit, because that call may then happen twice; in that case inherit `RenderedMap` instead, which guarantees that each entity is computed only once.

### Example: based on RenderedMap

The `WordCount` from the section "Produce new keys with generate_props" in chapter 8 is a complete `RenderedMap` subclass: `apply_render` returns the body of the output entity, and `generate_props` adds the `words` key to a copy of the upstream tag as the tag of the output entity. If you need to read something else before the transform, for example to parse the upstream body into JSON, you can override the `read_source` method; its return value is passed to `apply_render` as the first argument `source`.

### Example: reduce

The reduce function below joins the bodies of all the upstream entities with a separator into one entity:

```python
from docorder.functions.reduce_function import ReduceFunction


class JoinBodies(ReduceFunction):
    def transform_data(self, sources, target):
        separator = self.environment.operator_props.get("separator", "\n")
        target.staging_data = separator.join(entity.read_text() for entity in sources)

    def transform_props(self, sources, target):
        target.tag = {"count": len(sources), "names": [entity.name for entity in sources]}
```

The matching `props.json`:

```json
{ "type": "reduce", "class": "primary:JoinBodies", "output": "all", "separator": "\n---\n" }
```

The name of the output entity is decided by the `output` parameter, which is `all` here; `separator` is a parameter this function defines itself and reads through `self.environment.operator_props`. The `sources` passed in is the list of upstream entities sorted by entity name; if the upstream has no entity at all, `sources` is an empty list and the function is still called once, so the code has to handle the empty list correctly.

### Example: fanout

The fanout function below splits each upstream entity by line, and every line becomes a new entity:

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

The matching `props.json`:

```json
{ "type": "fanout", "class": "primary:SplitLines" }
```

If the body of the upstream entity `notes` has three lines, this function produces three entities, `notes-0`, `notes-1`, and `notes-2`. Since the names of all the output entities of a stage have to be different from each other, the name of the upstream entity is put in front as a prefix here, so that the names split out of different upstream entities do not collide. `output_names` has to return a list; `transform_data` takes the index out of the name of the target entity and uses that line as the body.

### Testing a function

The most direct way to test a function is to build a small job with only a few nodes in a temporary directory, run it, and check the content of the output files. The pytest test case below checks the `TableIndex` from chapter 10: it copies the `homes/` directory of the project into the temporary directory `tmp_path` that pytest provides, sets the `DOCORDER_HOMES` environment variable with pytest's `monkeypatch` fixture (which restores it after the test), writes one input file, runs the source and the reduce node, and finally checks whether the collected result contains this table.

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
        json.dumps({"table": "orders", "description": "one row per order", "columns": []}),
        encoding="utf-8",
    )
    monkeypatch.setenv("DOCORDER_HOMES", str(homes))

    job = Job("test", tmp_path / "runs")
    job.add_operator_node("tables", "table_source", config={"directory": str(data)})
    job.add_operator_node("index", "table_index", upstream="tables")
    execute(job, "t", start_from_scratch=True)

    index = (tmp_path / "runs" / "index" / "t" / "index" / "data").read_text(encoding="utf-8")
    assert "- orders: one row per order" in index
```

None of the nodes in this test sets `parallelism`, so everything runs in the current process, and the exception message and the call stack are both easy to read, which also makes it convenient to set breakpoints. The `PROJECT` in the code assumes that this test file sits in the `tests/` directory of the project, so `parents[1]` is the project root.

## 10. Using docorder in your own project

This chapter uses one complete example to show all the steps of using docorder in your own project. Suppose the project is called `my-docs` and holds a batch of data table definitions described in JSON files, and that you want to produce a prompt for each table, hand it to a command line model tool, and have it write a description of that table, and finally collect all the tables into one list. The job has four nodes, in turn a source, a map, a map, and a reduce, and it uses two functions that ship with docorder and two functions you write yourself. All the files and commands in this chapter have actually been run and verified.

### Step 1: install docorder

docorder has not been published to PyPI, so you cannot install it with `pip install docorder`; you have to build the package from the source repository first. The commands below clone the repository and build the package with uv. uv is a tool for Python packages and projects; its website explains how to install it.

```bash
git clone https://github.com/jixie-wish/docorder.git
cd docorder
uv build
```

After the build, the `dist/` directory of the repository holds a file named `docorder-0.1.0-py3-none-any.whl`, which is the standard Python package format. Next create your own project and install this package into it:

```bash
mkdir my-docs && cd my-docs
uv init --bare
uv add /path/to/docorder/dist/docorder-0.1.0-py3-none-any.whl
```

`uv init --bare` only generates a minimal `pyproject.toml`, the configuration file of a Python project, in the current directory; `uv add` creates the virtual environment of the project, installs docorder into it, and records this dependency in `pyproject.toml`. The `/path/to/docorder` in the commands has to be replaced with the location where you actually cloned the repository.

If you modify the code of docorder itself while you use it, you can use `uv add --editable /path/to/docorder` instead; docorder installed this way points straight at the source directory, so a change to the source takes effect at once, with no rebuild and reinstall. If you do not use uv, you can also run `pip install /path/to/docorder-0.1.0-py3-none-any.whl` in your own virtual environment. docorder requires Python 3.10 or newer, and its dependencies jinja2, python-dotenv, pyyaml, and tqdm are installed along with it.

### Step 2: plan the directories

Before you start writing files, plan the directory structure of the project. This is what the example project looks like when it is finished:

```text
my-docs/
  pyproject.toml
  run.py                          start script: builds the job and runs it
  data/
    tables/                       input data, one entity directory per table
      orders/
        data                      the table definition, the body
        tag.json                  the tag of the table
      users/
        data
        tag.json
  homes/                          DOCORDER_HOMES points here
    sources/
      table_source/               source operator: reads data/tables
        props.json
        primary.py                a function you wrote yourself: TableSource
    render/
      table_prompt/               map operator: renders the prompt
        props.json
        lib/table.jinja
    llm/
      ask_llm/                    map operator: calls the model tool
        props.json
        tools/echo.json
    summary/
      table_index/                reduce operator: collects the table list
        props.json
        primary.py                a function you wrote yourself: TableIndex
  workspace/                      working directory of the model tool, created by run.py
  runs/                           output root, not under version control
```

Every part of this structure has its own job. The input data lives in `data/`, belongs to the project itself, and is read by the source node; docorder does not modify any file in it. The operators live in `homes/`, sorted into a few category subdirectories, one directory per operator home, and the functions you write yourself live in the `primary.py` file of their own operator home. All the run results are written to `runs/`, which is fully managed by docorder and can be deleted and regenerated at any time. `run.py` is the only entry point of the whole job; it sets `DOCORDER_HOMES`, builds the job, and starts the run.

### Step 3: prepare the input data

`DirectorySource` reads the subdirectories that are already shaped like entities: each subdirectory is one table, the directory name is the entity name, and it has to hold the two files `data` and `tag.json`. The structure under `data/tables/` is therefore:

```text
data/tables/
  orders/
    data                          the table definition, the body
    tag.json                      the tag of the table
  users/
    data
    tag.json
```

The content of `data/tables/orders/data` is the definition of this table:

```json
{
  "table": "orders",
  "description": "one row per order",
  "columns": [
    {"name": "order_id", "type": "bigint", "comment": "order id"},
    {"name": "user_id", "type": "bigint", "comment": "the user who placed the order"},
    {"name": "amount", "type": "decimal(10,2)", "comment": "order amount"}
  ]
}
```

The content of `data/tables/orders/tag.json` is the tag of this table; at the very least, write an empty object:

```json
{}
```

The structure of `users` is the same as that of `orders`, only it describes the users table, with the two fields `user_id` and `city`. The entity name is the directory name itself, so the directory name has to follow the entity naming rules: not empty, no `/` or `\`, and not starting with `.` or `_`. Ordinary files in this directory, for example a README, are not entities and are not read.

### Step 4: write the operator homes

#### table_source: read the table definitions

This operator reads the entity directories in `data/tables/` and parses the fields out of the body into the tag of the entity, for the templates downstream to use.

The content of `homes/sources/table_source/props.json` is:

```json
{
  "type": "source",
  "class": "primary:TableSource",
  "project": "orders domain"
}
```

The content of `homes/sources/table_source/primary.py` is:

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

`TableSource` inherits `FilteredDirectorySource`, so the behaviour of "reading entity directories" is taken over from the parent class. This example configures no `filter`, so the filtering rules of the parent class do not apply and every entity directory under `data/tables/` is collected into a record. It overrides only the `extract_tag` method: it first takes the `tag.json` from the input directory, then parses the JSON of `data` and adds the three fields `table`, `description`, and `columns`; if the body is not valid JSON, it raises `FatalError`, because such an error cannot be solved by retrying. Finally it puts the custom parameter `project` from `props.json` into `global_prop`, so that the project name travels all the way through the runner to the final reduce node. You may have noticed that there is no `directory` parameter in `props.json`, because the input directory belongs to the project and not to the operator; it is passed in by `run.py` through the node's `config`, so that this operator home can be copied unchanged into other projects.

#### table_prompt: render the prompt

This operator uses the `TemplateToPrompt` that ships with docorder directly and needs no code at all; you only have to prepare `props.json` and the template file.

The content of `homes/render/table_prompt/props.json` is:

```json
{
  "type": "map",
  "class": "docorder.functions.impl.template_to_prompt:TemplateToPrompt",
  "template": "lib/table.jinja",
  "audience": "business analyst"
}
```

The content of `homes/render/table_prompt/lib/table.jinja` is:

```text
Write a short description of the {{ entity.source_tag.table }} table for {{ operator.audience }}.

Project: {{ entity.source_tag.global_prop.project }}
Purpose: {{ entity.source_tag.description }}

| Column | Type | Meaning |
| --- | --- | --- |
{% for column in entity.source_tag.columns -%}
| {{ column.name }} | {{ column.type }} | {{ column.comment }} |
{% endfor %}
```

The variables used in the template come from three different places. `entity.source_tag.table`, `entity.source_tag.description`, and `entity.source_tag.columns` come from the tag of the upstream entity, that is, the fields `TableSource` parsed; `entity.source_tag.global_prop.project` also comes from the upstream tag, from its `global_prop`; `operator.audience` comes from the custom parameter `audience` in the `props.json` of this operator home. The `{% for column in entity.source_tag.columns -%}` in the template walks the list of columns and writes one table row per column; the minus sign in `-%}` removes the newline after that tag, so that no blank line is left between the rows of the table.

#### ask_llm: call the model tool

This operator uses the `PromptToLLM` that ships with docorder and hands the prompt produced by the previous step to the model tool.

The content of `homes/llm/ask_llm/props.json` is:

```json
{
  "type": "map",
  "class": "docorder.functions.impl.prompt_to_llm:PromptToLLM",
  "tool": "echo",
  "retry": { "max_attempts": 3, "backoff_seconds": 5 }
}
```

The content of `homes/llm/ask_llm/tools/echo.json` is:

```json
{
  "name": "echo",
  "run": ["cat"],
  "prompt": "stdin"
}
```

The value `echo` of the `tool` parameter makes `PromptToLLM` read `tools/echo.json` from this operator home. This tool definition uses the system command `cat` and prints the prompt it received on standard input unchanged; it is only there so that this example can run completely without depending on any real model service. In real use you have to create another tool definition file in the `tools/` directory, replace its `run` with the command line model tool you actually use, and change the `tool` in `props.json` to the name of that new tool. The `retry` configuration means each entity is tried at most three times, which is very useful for a model API that fails now and then. The `workspace` parameter that `PromptToLLM` requires is passed in by `run.py` through the node's `config` as well.

#### table_index: collect the table list

This operator is a reduce function you write yourself; it collects the information of all the tables into one table list in Markdown format.

The content of `homes/summary/table_index/props.json` is:

```json
{
  "type": "reduce",
  "class": "primary:TableIndex",
  "output": "index",
  "title": "Table list"
}
```

The content of `homes/summary/table_index/primary.py` is:

```python
from docorder.functions.reduce_function import ReduceFunction


class TableIndex(ReduceFunction):
    def transform_data(self, sources, target):
        lines = [f"# {self.environment.operator_props.get('title', 'Table list')}", ""]
        for entity in sources:
            lines.append(f"- {entity.tag.get('table', entity.name)}: {entity.tag.get('description', '')}")
        target.staging_data = "\n".join(lines) + "\n"

    def transform_props(self, sources, target):
        target.tag = {"tables": [entity.name for entity in sources]}
```

The upstream of this reduce node is the `ask_llm` node. Because `TemplateToPrompt` and `PromptToLLM` both copy the tag of the upstream over unchanged, the `table` and `description` that `TableSource` parsed at the very beginning have been carried all the way here, so `TableIndex` can read them straight from the `tag` of every upstream entity. `title` is a parameter this function defines itself, used as the title of the list. The name of the output entity is decided by the `output` parameter, which is `index`.

### Step 5: write the start script

The content of `run.py` is:

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
    parser = argparse.ArgumentParser(description="generate descriptions for the tables under data/tables")
    parser.add_argument("epoch", help="the epoch of this run, for example 2026-10-16")
    parser.add_argument("--scratch", action="store_true", help="make the source reread data/tables")
    args = parser.parse_args()

    homes = [str(ROOT / "homes"), os.environ.get("DOCORDER_HOMES", "")]
    os.environ["DOCORDER_HOMES"] = os.pathsep.join(path for path in homes if path)
    (ROOT / "workspace").mkdir(exist_ok=True)

    execute(build_job(), args.epoch, start_from_scratch=args.scratch)
    print((ROOT / "runs" / "index" / args.epoch / "index" / "data").read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
```

There are a few things worth saying about this script. The `build_job` function builds a job with four nodes: the `tables` node uses the `table_source` operator and passes the input directory through `config`; the `prompts` node has `tables` as its upstream, uses the `table_prompt` operator, and sets `parallelism=2`, which allows at most two threads to render at the same time; the `answers` node has `prompts` as its upstream, uses the `ask_llm` operator, and passes the working directory of the model tool through `config`; the `index` node has `answers` as its upstream and uses the `table_index` operator.

The `main` function parses the command line arguments with the Python standard library `argparse`: the first argument is the epoch, and the optional `--scratch` switch decides whether `start_from_scratch=True` is passed. The code that sets `DOCORDER_HOMES` has to come before the call to `build_job()`, because the operator homes are looked up when the nodes are added; here the project's own `homes/` is put first, so that the operator homes of the project win over the ones of the same name already in the environment, while the directories that were already in the environment variable are kept. `os.pathsep` is the path separator of the current system, so this works on macOS, Linux, and Windows alike. Every path in the script is computed from `ROOT`, the directory the script is in, so the result is the same no matter which directory you run it from.

The paths that belong to the project, that is the input directory and the working directory, are passed in through the node's `config`, and the operator homes contain no project-specific path at all, so these operator homes can be copied unchanged into other projects. The `parallelism=2` of the `prompts` node renders with two threads in the current process; it does not start another subprocess.

### Step 6: run it and look at the result

On the first run with a new epoch you need to add `--scratch`, so that the source node reads the input data:

```bash
uv run python run.py 2026-10-16 --scratch
```

After the run finishes, the script prints the result of the reduce node:

```text
# Table list

- orders: one row per order
- users: registered users
```

At this point the structure of the `runs/` directory is as follows; every node has a directory named after the node, and the `2026-10-16/` inside it is the epoch directory:

```text
runs/
  tables/   2026-10-16/{orders,users}/  data, tag.json
  prompts/  2026-10-16/{orders,users}/  data, tag.json
  answers/  2026-10-16/{orders,users}/  data, tag.json
  index/    2026-10-16/index/           data, tag.json
```

Open `runs/prompts/2026-10-16/orders/data` and you can see the rendered prompt, with every variable of the template replaced by its actual value:

```text
Write a short description of the orders table for business analyst.

Project: orders domain
Purpose: one row per order

| Column | Type | Meaning |
| --- | --- | --- |
| order_id | bigint | order id |
| user_id | bigint | the user who placed the order |
| amount | decimal(10,2) | order amount |
```

Now open `runs/index/2026-10-16/index/tag.json` and you can see that besides the `tables` that `TableIndex` wrote, there is also the `global_prop` that travelled down from the source node, even though `TableIndex` never copied it itself. The runner also wrote an `upstream` key, which records the snapshot of every upstream entity that took part in this collection; it is left out here for brevity:

```json
{
  "global_prop": {
    "project": "orders domain"
  },
  "tables": [
    "orders",
    "users"
  ]
}
```

### Step 7: run again after a change

Once the project is in use, the input data, the templates, and the code keep changing. Different changes need different ways of running again, and they all follow the rules in the section "Decisions on a later run" in chapter 3.

If a run failed halfway, for example because the model tool still reported an error after using up all its retries, fix the problem that caused the failure first and then run the same epoch again, without `--scratch`: `uv run python run.py 2026-10-16`. The entities that are already done are kept because the comparison passes, and docorder only redoes the failed entities and the downstream entities affected by them.

If the input data changed, that is, if you added, changed, or deleted an entity directory under `data/tables/`, you have to add `--scratch` when you run again, or the source node will not reread the directory. After that, only the tables whose body really changed are processed again along the job graph, the new tables are created, the deleted tables are removed from every downstream node, and the reduce node regenerates the table list because its upstream changed. For example, after adding a `payments/` entity directory and running again with `--scratch`, the table list has one more line, `payments`; if you forget `--scratch`, the source node does not read the new directory and the table list does not change at all.

If you changed the template, a parameter in `props.json`, or the code of the function, docorder does not notice the change, and you have to delete the epoch directory of the affected node before you run again. For example, after changing `table.jinja`, run `rm -rf runs/prompts/2026-10-16` to delete the result of the prompt node, and then run `uv run python run.py 2026-10-16`: the `prompts` node renders all the prompts again, and because the content of the prompts changed, the two nodes `answers` and `index` are processed again as well. If you only want some entities to be processed again, delete only the matching entity directories, for example `runs/prompts/2026-10-16/orders`.

If you want to keep all the current results and run everything again from scratch, use a new epoch, for example `uv run python run.py 2026-10-17 --scratch`. The directories of the old epoch are not cleaned up automatically; delete them by hand when they are no longer needed.

### Version control

The `data/`, `homes/`, `run.py`, `pyproject.toml`, and `uv.lock` (the dependency lock file uv generates) of the project should all be under version control. `runs/` and `workspace/` are files produced at run time and should go into `.gitignore` so that they are not committed:

```text
runs/
workspace/
```

Also, do not put credentials such as access tokens or passwords into `props.json` or into a tool definition file, because these files are committed to the repository together with the project. The credentials a model tool needs should be put in environment variables and read by the tool itself.

## 11. A data governance case study

### Where the case lives in the repository

`examples/data-governance/` holds three runnable jobs, all of them real data governance work:

| Directory | What the job does | Size |
| --- | --- | --- |
| `documentation/` | Renders table definitions into prompts and hands them to a model to write descriptions | The smallest one; this is what `make quality` runs |
| `dbt_model/` | Generates dbt models (SQL and YAML) from table documentation | Medium; needs an external model tool |
| `semantic_layer/` | Builds a root catalogue, assigns roots to models, and fills in member attributes | The most complete one, and the one this chapter covers |

The code of each job is in its own `job.py`, and the operator homes live under `.op_home/`. Chapter 10 showed how to build a job from scratch; this chapter looks at a job that is already built, and that is considerably more involved than the tutorial.

### The problem

The warehouse holds several hundred Hive tables, each described by a dbt model. The yml of a model lists its metrics: the metric name, its description, and how it is aggregated. A model called `fct_refund` has a metric such as `refund_amount`, while another model may have `gmv_refunded`.

The question data governance has to answer is: are these metrics talking about the same thing? If they are, they should share one name, one definition, and one set of aliases, so that an analyst writing SQL does not have to guess what "refund amount" is called downstream.

Doing this by hand means reading several hundred yml files, keeping a catalogue of roots, and then filling in an assignment for every metric of every model. It is a lot of work, and it has to be redone whenever a model changes.

This case uses four jobs in sequence, each handing its result to the next one:

<!-- figure:pipeline:start -->
<figure class="figure" id="fig-pipeline">
<svg role="img" aria-labelledby="pipeline-title pipeline-desc" viewBox="0 0 900 500" width="100%" style="max-width:900px">
  <title id="pipeline-title">The four jobs of the data governance case</title>
  <desc>Four jobs in sequence: build the root catalogue, correct it, assign roots to the models and fill in the member attributes. Each job writes its result into .staging, where the next job reads it.</desc>
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
  <rect x="549.15" y="68" width="41.7" height="16" rx="2" fill="#f6f1e8"/>
  <text x="570" y="80" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">writes</text>
  <rect x="549.15" y="176" width="41.7" height="16" rx="2" fill="#f6f1e8"/>
  <text x="570" y="188" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">writes</text>
  <rect x="549.15" y="284" width="41.7" height="16" rx="2" fill="#f6f1e8"/>
  <text x="570" y="296" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">writes</text>
  <rect x="549.15" y="392" width="41.7" height="16" rx="2" fill="#f6f1e8"/>
  <text x="570" y="404" fill="#6f685c" font-size="9" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif" text-anchor="middle">writes</text>
  <rect x="40" y="48" width="500" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="48" width="500" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="54" y="71" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">raw_root job：build the root catalogue</text>
  <text x="54" y="93" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source → librarian → taxonomist_root → publish</text>
  <rect x="40" y="156" width="500" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="156" width="500" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="54" y="179" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">refine_root job：correct the root catalogue</text>
  <text x="54" y="201" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source → optimizer_root → merge_root → publish_final</text>
  <rect x="40" y="264" width="500" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="264" width="500" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="54" y="287" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">root_assigner job：assign roots to the models</text>
  <text x="54" y="309" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source_assign → root_assigner → reduce_assigner → publish_assigner</text>
  <text x="54" y="327" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">→ extract_root → taxonomist_member → combine_root_member → publish_root_member</text>
  <rect x="40" y="372" width="500" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="40" y="372" width="500" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="54" y="395" fill="#1c1915" font-size="12" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">member_attribute job：fill in the member attributes</text>
  <text x="54" y="417" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">source_member → assign_member → combine_assign_member → publish_assign_member</text>
  <rect x="600" y="48" width="260" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="600" y="48" width="260" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="614" y="71" fill="#1c1915" font-size="11" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">raw_root.csv</text>
  <text x="614" y="93" fill="#5e584e" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">the first draft of the catalogue</text>
  <rect x="600" y="156" width="260" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="600" y="156" width="260" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="614" y="179" fill="#1c1915" font-size="11" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">final_root.csv</text>
  <text x="614" y="201" fill="#5e584e" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">the final catalogue</text>
  <rect x="600" y="264" width="260" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="600" y="264" width="260" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="614" y="287" fill="#1c1915" font-size="11" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">root_assign.json</text>
  <text x="614" y="309" fill="#5e584e" font-size="9.5" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">the assignment table</text>
  <text x="614" y="327" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">root_member.csv</text>
  <rect x="600" y="372" width="260" height="88" rx="6" fill="#f6f1e8"/>
  <rect x="600" y="372" width="260" height="88" rx="6" fill="#fffdf8" stroke="#d8d0c1" stroke-width="1"/>
  <text x="614" y="395" fill="#1c1915" font-size="11" font-weight="600" font-family="'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif">member attributes</text>
  <text x="614" y="417" fill="#1c1915" font-size="9.5" font-family="'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace">root_member_assign.json</text>
</svg>
<figcaption><span class="fig-label">Figure 8</span> The four jobs of the case: each result lands in .staging and the next job reads it.</figcaption>
</figure>
<!-- figure:pipeline:end -->

### The first job: building the root catalogue

| Node | Type | What it does |
| --- | --- | --- |
| `source` | source | Reads the one-input-per-model directory `.input/` and produces entities |
| `librarian` | map | Reads the yml of the model, extracts the metric list, and writes it as JSON |
| `taxonomist_root` | reduce | Renders the JSON of every model into one prompt, calls the model once, and gets the root catalogue |
| `publish` | apply | Writes the root catalogue to `.staging/raw_root.csv` |

The `source` uses the built-in `FileHashSource`. Every child directory of `.input/` is one entity, and its `tag.json` names the database and the table:

```json
{
  "db": "core_data",
  "table": "fct_refund"
}
```

The `paths` of `FileHashSource` turn those two fields into the absolute path of the model files and write them into the tag of the entity:

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

`{model_home}` is a string parameter of the operator that points at the directory holding the model files. `librarian` reads the yml at that absolute path and parses the metric list out of it. It is an ordinary map function that only extends `MapFunction` and never calls a model, so it is fast.

`taxonomist_root` is a reduce: it renders the JSON of every upstream entity into one prompt, calls the model once, and gets a CSV back. The first line is the header:

```text
root_id|root_zh|kind|definition|not_a|aliases
product_click_count|商品点击次数|count|Count of product click events, one per user, ...|已归因点击次数, 未归因点击次数|how many product clicks, ...
```

Every line is one root: an English ID, a Chinese name, a kind (`count`, `rate`, `amount`, `score`, `duration`), a definition, a note about what it is definitely not, and the aliases.

`publish` is an apply. The built-in `Output` writes that entity to `.staging/raw_root.csv`. An apply writes no entity, it only calls the function, so it has no downstream.

### The second job: correcting the root catalogue

A first draft of a root catalogue is rarely perfect: the definition is off, an alias is missing, or two roots are really the same thing. This job has the model propose corrections for each model, and then folds the proposals into the catalogue.

| Node | Type | What it does |
| --- | --- | --- |
| `source` | source | The same node the first job uses |
| `optimizer_root` | map | One model call per model; it edits `raw_root_patch_log.csv` only when the catalogue does not fit |
| `merge_root` | reduce | One model call that folds that file into the catalogue |
| `publish_final` | apply | Writes `.staging/final_root.csv` |

The operator home of `optimizer_root` declares two sections of fingerprint:

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

The `depend` points at `.staging/raw_root.csv`, which is what the first job produced. When the catalogue changes, every entity of this operator is redone; when neither the model definitions nor the catalogue changed, not one of them is redone and not a cent is spent on the model.

The `record` names `.staging/raw_root_patch_log.csv`. The prompt tells the model to change that file from `raw_root.csv`: create it when it is missing, edit it in place when it exists, and leave a row untouched when the catalogue already fits.

`merge_root` reads both files directly. Its `depend` lists `.staging/raw_root.csv` and `.staging/raw_root_patch_log.csv`, so a change to either file makes it run again.

### The third job: assigning roots to models

With a final catalogue in hand, the next step is to find the root of every metric of every model.

| Node | Type | What it does |
| --- | --- | --- |
| `source_assign` | source | A source of its own, with a different node name from the `source` of the first job |
| `root_assigner` | map | One model call per model, deciding which roots the metrics of that model belong to |
| `reduce_assigner` | reduce | Combines the assignments of every model into one JSON |
| `publish_assigner` | apply | Writes `.staging/root_assign.json` |
| `extract_root` | fanout | Splits the assignment JSON by root, one entity per root |
| `taxonomist_member` | map | One model call per root, writing the member list of that root |
| `combine_root_member` | reduce | Joins the member lists of every root into one CSV |
| `publish_root_member` | apply | Writes `.staging/root_member.csv` |

`source_assign` declares a `record` that covers both the model files and the catalogue:

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

The `catalog` here points at `.staging/final_root.csv`, so when the catalogue changes this source writes a new hash into the entity and the downstream follows.

Note that the `fingerprint` in the node's `config` replaces the one of the operator home as a whole, which is why the two entries of the home are written out again above. Chapter 4, "Fingerprints and hashes", describes that rule.

`extract_root` is the only fanout in this case. Its `output_names` reads the root IDs out of the assignment JSON and skips `unassigned`:

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

There is one upstream entity, the assignment JSON, and the output is one entity per root. How many entities a fanout produces has nothing to do with how many entities it has upstream, and that is exactly why it exists. The input in this repository produces fourteen root entities.

### The fourth job: filling in member attributes

The last job adds descriptions to the members of every root. Its shape is the simplest of the four: `source_member`, `assign_member`, `combine_assign_member` and `publish_assign_member`, a source, a map, a reduce and an apply.

### The mechanisms this case uses

| Mechanism | Where it shows up |
| --- | --- |
| The five operator types | source, map, reduce, fanout and apply are all used |
| `fingerprint.record` | Records the model files, the catalogue and the intermediate products |
| `fingerprint.depend` | Carries a change of the catalogue downstream |
| `.staging` | Passes data from one job to the next |
| `retry` | Retries a failed model call |

### How to run it

```bash
cd examples/data-governance/semantic_layer
uv run python job.py                   # build the root catalogue
uv run python job.py refine            # correct the root catalogue
uv run python job.py assign            # assign roots to the models
uv run python job.py member_attribute  # fill in the member attributes
```

The `.env` of the project holds nothing but `DOCORDER_HOMES`, which points at the `.op_home` of this directory. The location of the model files is given by the environment variable `SEMANTIC_LAYER_MODELS`, the input directory by `SEMANTIC_LAYER_INPUT`. The model tool is chosen with `DOCORDER_LLM`; without it the default tool configured in the script is used.

These jobs need a model tool installed on the machine and model files to read, so they are not run in CI. CI runs the smallest job, the one under `documentation/`.

## 12. Best practices

This chapter is not about the mechanisms of docorder but about how to use it so that it stays reliable. The earlier chapters explain "what it does"; this chapter explains "how you should organize your project and your jobs". These conventions are not enforced, but each of them corresponds to a pitfall that has actually been hit.

### Decide first whether the task suits docorder

The core assumption of docorder is that the objects being processed share one shape, can be put on disk, can be processed again, and that processing one of them costs more than reading it from disk. It is therefore good at things like "generate a description for each of a batch of tables", "cut a summary out of each of a batch of documents", and "render one artifact for each of a batch of configurations".

If your task does not have that shape, do not force it. Typical counterexamples:

- A one-off task, where a script that runs once is enough. Building a whole set of directories and operators so that you can resume it later is extra cost.
- There are few objects but every step of each one is heavy. The directories, snapshots, and comparisons of docorder bring a fixed amount of complexity.
- A one-off aggregation that needs a global view. A reduce can do it, but it can only hand the whole upstream batch to one call, and when the input is too large it is better to write a script.

Check it against the "Use cases" in chapter 5 first, and then decide whether to use it.

### Directories and naming

**Prepare the input directories in the shape of entities.** `DirectorySource` only recognizes the shape of "a subdirectory that holds `data` or `tag.json`". When the input is a scatter of ordinary files, write a source that organizes them into entity directories instead of changing the way `DirectorySource` reads.

**Keep entity names well behaved.** Non-empty, no `/` and no `\`, and not starting with `.` or `_`. The name becomes a directory name directly, and it also ends up in templates and in command line arguments. Names with spaces, Chinese characters, or shell special characters do work, but they make troubleshooting painful, so stick to lower case letters, digits, and underscores.

**Use a single directory level for the epoch.** The epoch is joined into the path directly, and `2026/10` creates two directory levels. Use a single-level name such as `2026-10-16` or `v3`. It is a version marker, not a time path.

**Keep the output root stable.** A job always writes to one output root, so that an interrupted run can pick up the progress when it is run again. A temporary directory or a path with a random number in it makes resuming impossible.

**Do not commit the output directory.** It holds the progress and the artifacts, not the source. Add the output root (`runs/` and the like) to `.gitignore`. If the input data of a job comes from real business data, do not commit that either.

### Incremental runs and idempotence

This is where docorder is easiest to get wrong.

**Use the same epoch for the same piece of work.** Resuming means running the same epoch once more. Changing the epoch means starting over, and everything computed before is wasted. An epoch means "a version of this batch of data", not "the identifier of one run".

**Explicitly invalidate old results when you change the logic.** When the template, the parameters, the function code, or an external tool changes while the upstream entities stay the same, the upstream snapshot still matches and the old result is kept as it is. Then either delete the epoch directory of that node, or delete only the entity directories that have to be redone, or use another epoch. docorder does not judge for you that "the code changed".

**Pass `--scratch` when you change the input.** The `start_from_scratch=True` of a source node is the switch through which the input data enters the job. Without it, a change to the source files does not reach the entities of the source, and the downstream naturally does not see it either.

**Do not edit upstream entity directories by hand.** Editing an already written `data` or `tag.json` directly makes the downstream that depends on it redo, which is useful while debugging, but treating it as the normal workflow makes "who is upstream" untraceable. Change the source instead.

**Do not let the body be empty.** When the upstream body is an empty string, its hash is empty every time and never matches the snapshot, so the entities that depend on it are redone on every run. A model call is not cheap, so that means paying for it again on every run. When you really cannot get any content, write a placeholder.

**Make the job script repeatable.** Running the same epoch twice should give the same result, not an error or an accumulation. Pass the epoch into the script as an argument instead of hard-coding it.

### Organizing the operator homes

**Name a home after its role, not after the project.** Names like `table_source`, `ask_llm`, and `render_prompt` can be reused across projects; `my_project_table_source` can only be used by one project. The differences between projects are passed in through the node's `config`.

**Keep the static files in the home and the code in `primary.py`.** Pure files such as templates and tool definitions go straight into the home directory; when you need code, use `class: "primary:ClassName"` and put the code in the `primary.py` of the home.

**Pass the differences with `config`, the common parts with the home.** The custom keys of `props.json` are the default parameters of this home, and the node's `config` overrides the keys of the same name. When one home serves several projects, every project-specific value should go through `config`.

**The order of `DOCORDER_HOMES` is the priority.** The earlier directories are searched first, and a home of the same name in an earlier directory wins. This is very handy while debugging locally: put your own home directory first, and a broken home there does not affect anyone else.

**Set the environment variables before you build the job.** The lookup of a home happens at the moment `add_operator_node` is called.

### Error handling

**Use `FatalError` for configuration errors.** A missing parameter, a wrong template, a wrong input format, and problems like these give the same result however often you retry, so they should fail at once. Raising an ordinary exception in a function triggers a retry and wastes time on a call that is bound to fail.

**Use an ordinary exception for the failure of an external process.** A model API that times out or an external command that returns a non-zero status is worth retrying. Functions such as `PromptToLLM` already make this distinction; you only have to keep the same judgement when you wrap your own function.

**Give the node that calls the model a `retry` and a `parallelism`.** The default degree of parallelism is often too aggressive for an external API, and it easily triggers rate limiting. Get it working with a small degree of parallelism first, and then raise it to the quota of the API.

**A failed entity leaves the scene behind.** A failed entity leaves a directory that holds only an empty `tag.json` and no `data`, with no `upstream` snapshot. After you fix the problem and run the same epoch again, it is redone, and the entities that succeeded before are not done again. So while troubleshooting you can go straight to that directory.

### Calling a model

**Pick the right function.** One result per object in a batch, use `EntityTemplateToLLM` (map); one summary for the whole batch, use `TemplateToLLM` (reduce); the upstream is already a prompt, use `PromptToLLM` directly.

**Prefer to put the call on a map.** The granularity of a map is one entity, so a failure affects one object and the cost of resuming is the lowest. The granularity of a reduce is the whole batch, so one failure means the whole batch starts over.

**Use `tag_template` to keep the metadata.** Besides the body that the model returns, let the function write the structured result into the tag as well, and the later steps do not have to parse the body again.

**Use `header` to constrain the output format.** Give `PromptToLLM` a `header`, and the table in the reply of the model can be cut out reliably and used as the body, so the downstream does not have to deal with the small talk the model may have added.

**Write the input of the model as a path, not as content.** The templates of `EntityTemplateToLLM` and `TemplateToLLM` can get the path of the upstream `data` file; letting the model read it itself saves tokens compared to stuffing a large piece of content into the prompt, and is also less likely to overflow.

**Use `fingerprint.depend` to track external files.** When a result depends on a file that is not in the upstream entity, for example the `.sql` next to a table definition, declare it with `depend`, and the matching entities are only redone when the file changes.

### Common anti-patterns

| Anti-pattern | Problem | Better approach |
| --- | --- | --- |
| One subprocess per object, each processed on its own | You lose the batching, the retry, and the ability to resume | Use a map operator and let the runner schedule it |
| Writing your own retry or thread pool inside a function | It duplicates the mechanisms of the runner and the failure semantics differ | Raise an ordinary exception and let the runner retry, and control the concurrency with `parallelism` |
| Creating a job or calling `execute` inside a function | There is nowhere to keep the progress, and resuming stops working | A function handles one entity; the job is built by the script |
| Putting large blocks of data into the tag | The hash of the snapshot grows with the data and the comparison gets slower | Keep only identifiers and paths in the tag; the body goes into a file |
| Using a new epoch for every run | Everything is computed from scratch every time | Fix the epoch, and control the scope of the redo with directory cleanup |
| Changing the template without cleaning up the old results | The old results are kept as they are and it looks like "it did not take effect" | Delete the epoch directory of that node, or use another epoch |
| Putting unrelated entities in one epoch | One failing entity drags the whole batch down, and several jobs interfere with each other | One output root per job, one batch of data per epoch |

## Appendix A: The built-in functions

| Class | How to write `class` | `type` | Parameters |
| --- | --- | --- | --- |
| `DirectorySource` | `docorder.functions.impl.directory_source:DirectorySource` | source | `directory` |
| `FilteredDirectorySource` | `docorder.functions.impl.directory_source:FilteredDirectorySource` | source | `directory`, `filter` |
| `FileHashSource` | `docorder.functions.impl.directory_source:FileHashSource` | source | `directory`, `paths`, `fingerprint` |
| `TemplateToPrompt` | `docorder.functions.impl.template_to_prompt:TemplateToPrompt` | map | `template` |
| `JinjaToJsonnet` | `docorder.functions.impl.jinja_to_jsonnet:JinjaToJsonnet` | map | `template`, `variables` |
| `JsonnetToPrompt` | `docorder.functions.impl.jsonnet_to_prompt:JsonnetToPrompt` | map | None |
| `Command` | `docorder.functions.impl.command:Command` | map | `argv`, `cwd`, `output_file`, `capture` |
| `PromptToLLM` | `docorder.functions.impl.prompt_to_llm:PromptToLLM` | map | `workspace`, `tool` |
| `EntityTemplateToLLM` | `docorder.functions.impl.template_to_llm:EntityTemplateToLLM` | map | `template`, `workspace`, `tool`, `header`, `tag_template` |
| `TemplateToLLM` | `docorder.functions.impl.template_to_llm:TemplateToLLM` | reduce | `template`, `workspace`, `tool`, `header`, `tag_template`, `min_sources`, `max_sources` |
| `Output` | `docorder.functions.impl.output:Output` | apply | `directory`, `filename` |

The base classes and the helper classes used when writing a function are defined in the following modules: `SourceFunction` and `SourceRecord` are in `docorder.functions.source_function`, `MapFunction` is in `docorder.functions.map_function`, `RenderedMap` is in `docorder.functions.rendered_map`, `ReduceFunction` is in `docorder.functions.reduce_function`, `FanoutFunction` is in `docorder.functions.fanout_function`, and `ApplyFunction` is in `docorder.functions.apply_function`. `Artifact` is in `docorder.core.artifact`, and `Environment` is in `docorder.core.environment`. The exception classes `DocorderError`, `JobValidationError`, `OperatorValidationError`, and `FatalError` are all in `docorder.utils.errors`, and the retry policy `RetryPolicy` is in `docorder.utils.retry`.

## Appendix B: Implementation index

| Path | Responsibility |
| --- | --- |
| `src/docorder/core/artifact.py` | The entry point for the read-only files of an operator home |
| `src/docorder/core/entity.py` | Checks the entity name, reads and writes entity directories, computes and compares the upstream snapshot |
| `src/docorder/core/storage.py` | Manages the entities of one epoch directory, and creating, clearing, and deleting them |
| `src/docorder/core/operator.py` | Interprets `props.json`, represents a node, lists the expected names, executes the five operator types, and slices the parallel work |
| `src/docorder/core/job.py` | Building, checking, and topologically sorting the job graph |
| `src/docorder/core/runner.py` | Assembles the job, executes the stages one by one, and manages the output directory marker |
| `src/docorder/core/epoch_diff.py` | Compares the entities of two runs and reports how many were added, changed, and deleted |
| `src/docorder/core/external_hash.py` | The `record` and `depend` of `fingerprint`: renders the path templates and computes the file hashes |
| `src/docorder/core/environment.py` | The rendering environment: `operator_props` and `template_env` |
| `src/docorder/functions/` | The function base classes; the built-in implementations are in `functions/impl/` |
| `src/docorder/utils/paths.py` | Resolves `DOCORDER_HOMES` and looks up the operator homes |
| `src/docorder/utils/modules.py` | Loads a function class written as `primary:ClassName` or `module:ClassName` |
| `src/docorder/utils/llm_tool.py` | The model tool: reads the tool presets from the home and starts the external process |
| `src/docorder/utils/retry.py` | The retry policy, and how it applies to one entity call |
| `src/docorder/utils/progress.py` | The progress display of one stage |
| `src/docorder/utils/errors.py` | `DocorderError` and its subclasses |
| `src/docorder/cli/` | The `docorder status` command: shows the epochs in an output directory |
| `tests/test_contract.py` | The contract tests for the behaviour above |

## Appendix C: Related documents

- [README](../README.en.md): installation, a quick start, and troubleshooting common problems.
- [glossary.en.md](../glossary.en.md): the glossary of terms.
- [CONTRIBUTING.en.md](../CONTRIBUTING.en.md): the development conventions and the requirements for a commit.
- [The documentation home page](index.en.html): the overview, the core concepts, the model, the quick start, running the same epoch again, and the entry points to every chapter of this guide.
- [The Jinja template documentation](https://jinja.palletsprojects.com/en/stable/templates/): the template syntax used by `TemplateToPrompt` and `JinjaToJsonnet`.
- [Jsonnet](https://jsonnet.org/): the configuration language that `JsonnetToPrompt` compiles.
- [concurrent.futures.ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor): the thread pool used when map and fanout nodes run in parallel.
