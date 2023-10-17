

# from forge.sdk.workspace import LocalWorkspace
# import os
# wor = LocalWorkspace(".")

# print(wor.list("",""))


# import json
# print(json.dumps(["asdasd","dfsfsdf"]))

#%%
import weaviate


auth_config = weaviate.AuthApiKey(api_key="2wMDJgDrr4dYJQ6pa19qKKbIfMjjQAH7SyAw")  # Replace w/ your Weaviate instance API key

# Instantiate the client with the auth config
client = weaviate.Client(
    url="https://autogpt-cluster-5gdt9cse.weaviate.network",  # Replace w/ your endpoint
    auth_client_secret=auth_config,
    additional_headers={  # (Optional) Any additional headers; e.g. keys for API inference services
    "X-Cohere-Api-Key": "ElLgLL7pk5bazHA3NX9KCmVQrAwjGDWnqaIG93Af",            # Replace with your Cohere key
    # "X-HuggingFace-Api-Key": "YOUR-HUGGINGFACE-API-KEY",  # Replace with your Hugging Face key
    # "X-OpenAI-Api-Key": "YOUR-OPENAI-API-KEY",            # Replace with your OpenAI key
  }
)


client.schema.get()  # Get the schema to test connection


# %%

class_obj = {
    # Class definition
    "class": "JeopardyQuestion",
    "vectorizer": "text2vec-cohere",
    # Property definitions
    "properties": [
        {
            "name": "category",
            "dataType": ["text"],
        },
        {
            "name": "question",
            "dataType": ["text"],
        },
        {
            "name": "answer",
            "dataType": ["text"],
        },
    ],

}
client.schema.delete_class("JeopardyQuestion")
client.schema.create_class(class_obj)

client.schema.get()  # Get the schema to test connection

# %%

import pandas as pd

df = pd.read_csv("jeopardy_questions-350.csv", nrows = 100)
print(df)
# %%
from weaviate.util import generate_uuid5

with client.batch(
    batch_size=200,  # Specify batch size
    num_workers=2,   # Parallelize the process
) as batch:
    for _, row in df.iterrows():
        question_object = {
            "category": row.category,
            "question": row.question,
            "answer": row.answer,
        }
        batch.add_data_object(
            question_object,
            class_name="JeopardyQuestion",
            uuid=generate_uuid5(question_object)
        )
# %%
client.query.aggregate("JeopardyQuestion").with_meta_count().do()

#%%
import json

res = client.query.get("JeopardyQuestion", ["question", "answer", "category"]).with_additional(["id", "vector"]).with_limit(2).do()

print(json.dumps(res, indent=4))
# %%
res = client.query.get(
    "JeopardyQuestion",
    ["question", "answer", "category"])\
    .with_near_text({"concepts": "animals"})\
    .with_limit(5)\
    .do()

print(res)
# %%

import requests

headers = {
    # 'User-agent':
    # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    
}

params = {
  'q': 'minecraft',
'format': 'json',
}

html = requests.get('http://localhost:8899/search', headers=headers, params=params)

print(html.json)
# %%
print(html.json()['results'])
# %%
