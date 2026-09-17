# HugeGraph-Ai Quick Start (Beta)

LLMS 索引： [llms.txt](/versions/1.3/cn/llms.txt)

---

### 1 HugeGraph-Ai 概述
hugegraph-ai 旨在探索 HugeGraph 与人工智能（AI）的融合，包括与大模型结合的应用，与图机器学习组件的集成等，为开发者在项目中利用 HugeGraph 的 AI 能力提供全面支持。

### 2 环境要求
- python 3.8+
- hugegraph 1.0.0+ 

### 3 准备工作
- 启动 HugeGraph 数据库，你可以通过 Docker 来实现。请参考这个[链接](https://hub.docker.com/r/hugegraph/hugegraph)获取指引。
- 启动 gradio 交互式 demo，你可以通过以下命令启动，启动后打开 [http://127.0.0.1:8001](http://127.0.0.1:8001)
```bash
# ${PROJECT_ROOT_DIR} 为 hugegraph-ai 的根目录，需要自行配置
export PYTHONPATH=${PROJECT_ROOT_DIR}/hugegraph-llm/src:${PROJECT_ROOT_DIR}/hugegraph-python-client/src
python3 ./hugegraph-llm/src/hugegraph_llm/utils/gradio_demo.py
```
- 配置 HugeGraph 数据库连接信息和 LLM 模型信息，可以通过两种方式配置：
  1. 配置 `./hugegraph-llm/src/config/config.ini` 文件
  2. 在 gradio 中，分别完成 LLM 和 HugeGraph 的配置后，点击 `Initialize configs`，将返回初始化后的完整配置文件。如图所示:
  ![gradio配置](/versions/1.3/docs/images/gradio-config.png)
- 离线下载 NLTK stopwords 
```bash
python3 ./hugegraph_llm/operators/common_op/nltk_helper.py
```


### 4 使用说明
#### 4.1 通过 LLM 在 HugeGraph 中构建知识图谱
##### 4.1.1 通过 gradio 交互式界面构建知识图谱
- 参数说明：
  - Text: 输入的文本。 
  - Schema：接受以下两种类型的文本： 
    - 用户定义的 JSON 格式模式。 
    - 指定 HugeGraph 图实例的名称，它将自动提取图的模式。
  - Disambiguate word sense：是否进行词义消除歧义。 
  - Commit to hugegraph：是否将构建的知识图谱提交到 HugeGraph 服务器

![gradio配置](/versions/1.3/docs/images/gradio-kg.png)

##### 4.1.2 通过代码构建知识图谱
- 完整代码
```python
from hugegraph_llm.llms.init_llm import LLMs
from hugegraph_llm.operators.kg_construction_task import KgBuilder

llm = LLMs().get_llm()
builder = KgBuilder(llm)
(
    builder
    .import_schema(from_hugegraph="test_graph").print_result()
    .extract_triples(TEXT).print_result()
    .disambiguate_word_sense().print_result()
    .commit_to_hugegraph()
    .run()
)
```
- 时序图
![gradio配置](/versions/1.3/docs/images/kg-uml.png)


1. 初始化: 初始化 LLMs 实例，获取 LLM，然后创建图谱构建的任务实例 `KgBuilder`，KgBuilder 中定义了多个 operator，用户可以根据需求自由组合达到目的 。（tip: `print_result()` 可以在控制台打印每一步输出的结果，不影响整体执行逻辑）

```python
llm = LLMs().get_llm()
builder = KgBuilder(llm)
```
2. 导入 Schema：使用 `import_schema` 方法导入, 支持三种模式：
    - 从 HugeGraph 实例导入，指定 HugeGraph 图实例的名称，它将自动提取图的模式。
    - 从用户定义的模式导入，接受用户定义的 JSON 格式模式。
    - 从提取结果导入（即将发布）
```python
# Import schema from a HugeGraph instance
builder.import_schema(from_hugegraph="test_graph").print_result()
# Import schema from user-defined schema
builder.import_schema(from_user_defined="xxx").print_result()
# Import schema from an extraction result
builder.import_schema(from_extraction="xxx").print_result()
```
3. 提取三元组：使用 `extract_triples` 方法从文本中提取三元组。

```python
TEXT = "Meet Sarah, a 30-year-old attorney, and her roommate, James, whom she's shared a home with since 2010."
builder.extract_triples(TEXT).print_result()
```
4. 消除词义歧义：使用 `disambiguate_word_sense` 方法消除词义歧义。

```python
builder.disambiguate_word_sense().print_result()
```
5. 提交到 HugeGraph：使用 `commit_to_hugegraph` 方法提交构建的知识图谱到 HugeGraph 实例。

```python
builder.commit_to_hugegraph().print_result()
```

6. 运行：使用 `run` 方法执行上述操作。
```python
builder.run()
```

#### 4.2 基于 HugeGraph 的检索增强生成（RAG）
##### 4.1.1 通过 gradio 交互问答
1. 首先点击 `Initialize HugeGraph test data` 按钮，初始化 HugeGraph 数据。
  ![gradio配置](/versions/1.3/docs/images/gradio-rag-1.png)
2. 然后点击 `Retrieval augmented generation` 按钮，生成问题的答案。
   ![gradio配置](/versions/1.3/docs/images/gradio-rag-2.png)

##### 4.1.2 通过代码构建 Graph RAG
- 完整代码
```python
graph_rag = GraphRAG()
result = (
    graph_rag.extract_keyword(text="Tell me about Al Pacino.").print_result()
    .query_graph_for_rag(
        max_deep=2,
        max_items=30
    ).print_result()
    .synthesize_answer().print_result()
    .run(verbose=True)
)
```
1. extract_keyword: 提取关键词, 并进行近义词扩展
```python
graph_rag.extract_keyword(text="Tell me about Al Pacino.").print_result()
```
2. query_graph_for_rag: 从 HugeGraph 中检索对应的关键词，及其多度的关联关系
   - max_deep: hugegraph 检索的最大深度
   - max_items: hugegraph 最大返回结果数
```python
graph_rag.query_graph_for_rag(
    max_deep=2,
    max_items=30
).print_result()
```
3. synthesize_answer: 针对提问，汇总结果，组织语言回答问题。
```python
graph_rag.synthesize_answer().print_result()
```
4. run: 执行上述操作。
```python
graph_rag.run(verbose=True)
```
