import langchain_core
import langchain_openai
import langchain_neo4j
import sys

MODELS = [
    "o1-preview",
    "o1",
    "o1-mini",
    "gpt-4o",
]

CYPHER_GENERATION_TEMPLATE = """
Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}

Cypher examples:

# Find applications
MATCH (a:ApplicationService) RETURN a

# Where is configuration for example-application-name?
MATCH ({{name:'example-application-name'}})-[r]-()
WHERE r.`pwrt:inspector:value-ref` IS NOT NULL
RETURN r.`pwrt:inspector:value-ref`

# Find elements who's name similar to example-element-name
MATCH (e) WHERE apoc.text.levenshteinSimilarity(e.name, 'example-element-name')>0.3

# Which applications do produce to example-top-name topic?
MATCH (e)-[:Flow]->({{name:'example-top-name', specialization:'Kafka topic'}})
RETURN DISTINCT e.name

# Which applications do consume from example-top-name topic?
MATCH (e)<-[:Flow]-({{name:'example-top-name', specialization:'Kafka topic'}})
RETURN DISTINCT e.name

# Find S3 elements
MATCH (e{{specialization:'AWS S3 object'}})
RETURN DISTINCT e.name

# Find API elements
MATCH ()--(e{{specialization:'HTTP REST'}})
RETURN DISTINCT e.name

Note:
Terms "application", "microservice", "component" are synonyms.
Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question is:
{question}"""

CYPHER_GENERATION_PROMPT = langchain_core.prompts.prompt.PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)

graph = langchain_neo4j.Neo4jGraph(
    url="bolt://neo4j:7687", username="", password=""
)

chain = langchain_neo4j.GraphCypherQAChain.from_llm(
    langchain_openai.ChatOpenAI(model="o1-preview-2024-09-12"),
    graph=graph,
    top_k=20,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    return_intermediate_steps=True,
    allow_dangerous_requests=True,
)

print("Choose model from the list.")
for i, m in enumerate(MODELS):
    print(f'[{i}] {m}')
model_index = int(input("> "))
if model_index < 0 or model_index >= len(MODELS):
    print(f"Your input was {model_index}. Not in the list.")
    sys.exit()
model = MODELS[model_index]

print(f"Using model {model}.")

print(
    """Ask your questions.
Example: Show me all microservices

(Type quit to exit.)
"""
)
while True:
    query = input("Your question > ")
    if query == "quit":
        break
    result = chain.invoke({"query": query})
    print(f"Intermediate steps: {result['intermediate_steps']}")
    print(f"Final answer: {result['result']}")
    print()
