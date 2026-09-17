# HugeGraph-Ai Quick Start (Beta)

LLMS index: [llms.txt](/versions/1.3/llms.txt)

---

### 1 HugeGraph-Ai Overview
hugegraph-ai aims to explore the integration of HugeGraph and artificial intelligence (AI), including applications combined with large models, integration with graph machine learning components, etc., to provide comprehensive support for developers to use HugeGraph's AI capabilities in projects.

### 2 Environment Requirements
- python 3.8+
- hugegraph 1.0.0+ 

### 3 Preparation
- Start the HugeGraph database, you can achieve this through Docker. Please refer to this [link](https://hub.docker.com/r/hugegraph/hugegraph) for guidance.
- Start the gradio interactive demo, you can start with the following command, and open [http://127.0.0.1:8001](http://127.0.0.1:8001) after starting

```bash
# ${PROJECT_ROOT_DIR} is the root directory of hugegraph-ai, which needs to be configured by yourself
export PYTHONPATH=${PROJECT_ROOT_DIR}/hugegraph-llm/src:${PROJECT_ROOT_DIR}/hugegraph-python-client/src
python3 ./hugegraph-llm/src/hugegraph_llm/utils/gradio_demo.py
```
- Configure HugeGraph database connection information and LLM information, which can be configured in two ways:
  1. Configure the `./hugegraph-llm/src/config/config.ini` file
  2. In gradio, after completing the configurations for LLM and HugeGraph, click on `Initialize configs`, the complete and initialized configuration file will be outputted.
  ![gradio-config](/versions/1.3/docs/images/gradio-config.png)
- offline download NLTK stopwords
```bash
python3 ./hugegraph_llm/operators/common_op/nltk_helper.py
```

### 4 How to use
#### 4.1 Build a knowledge graph in HugeGraph through LLM
##### 4.1.1 Build a knowledge graph through the gradio interactive interface
- Parameter description:
  - Text: The input text. 
  - Schema: Accepts the following two types of text: 
    - User-defined JSON format schema. 
    - Specify the name of the HugeGraph graph instance, which will automatically extract the schema of the graph.
  - Disambiguate word sense: Whether to disambiguate word sense. 
  - Commit to hugegraph: Whether to submit the constructed knowledge graph to the HugeGraph server

![gradio-config](/versions/1.3/docs/images/gradio-kg.png)

##### 4.1.2 Build a knowledge graph through code
- Complete code
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
- Sequence Diagram
  ![gradio-config](/versions/1.3/docs/images/kg-uml.png)

1. Initialize: Initialize the LLMs instance, get the LLM, and then create a task instance `KgBuilder` for graph construction. `KgBuilder` defines multiple operators, and users can freely combine them according to their needs. (tip: `print_result()` can print the result of each step in the console, without affecting the overall execution logic)

```python
llm = LLMs().get_llm()
builder = KgBuilder(llm)
```
2. Import Schema: Import using the `import_schema` method, which supports three modes:
    - Import from a HugeGraph instance, specify the name of the HugeGraph graph instance, and it will automatically extract the schema of the graph.
    - Import from a user-defined schema, accept user-defined JSON format schema.
    - Import from the extraction result (release soon)

```python
# Import schema from a HugeGraph instance
builder.import_schema(from_hugegraph="test_graph").print_result()
# Import schema from user-defined schema
builder.import_schema(from_user_defined="xxx").print_result()
# Import schema from an extraction result
builder.import_schema(from_extraction="xxx").print_result()
```
3. Extract triples: Use the `extract_triples` method to extract triples from the text.

```python
TEXT = "Meet Sarah, a 30-year-old attorney, and her roommate, James, whom she's shared a home with since 2010."
builder.extract_triples(TEXT).print_result()
```
4. Disambiguate word sense: Use the `disambiguate_word_sense` method to disambiguate word sense.

```python
builder.disambiguate_word_sense().print_result()
```
5. Commit to HugeGraph: Use the `commit_to_hugegraph` method to submit the constructed knowledge graph to the HugeGraph instance.

```python
builder.commit_to_hugegraph().print_result()
```

6. Run: Use the `run` method to execute the above operations.

```python
builder.run()
```

#### 4.2 Retrieval augmented generation (RAG) based on HugeGraph
##### 4.1.1 Interactive Q&A through gradio
1. First click the `Initialize HugeGraph test data` button to initialize the HugeGraph data.
   ![gradio-config](/versions/1.3/docs/images/gradio-rag-1.png)
2. Then click the `Retrieval augmented generation` button to generate the answer to the question.
   ![gradio-config](/versions/1.3/docs/images/gradio-rag-2.png)

##### 4.1.2 Build Graph RAG through code
- code
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
1. extract_keyword: Extract keywords and expand synonyms.

```python
graph_rag.extract_keyword(text="Tell me about Al Pacino.").print_result()
```
2. query_graph_for_rag: Retrieve the corresponding keywords and their multi-degree associated relationships from HugeGraph.
   - max_deep: The maximum depth of hugegraph retrieval.
   - max_items: The maximum number of results returned by hugegraph.

```python
graph_rag.query_graph_for_rag(
    max_deep=2,
    max_items=30
).print_result()
```
3. synthesize_answer: Summarize the results and organize the language to answer the question.
```python
graph_rag.synthesize_answer().print_result()
```
4. run: Execute the above operations.

```python
graph_rag.run(verbose=True)
```
