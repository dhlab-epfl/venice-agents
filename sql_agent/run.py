from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

from langchain_community.utilities import SQLDatabase
import pandas as pd
import numpy as np

import warnings
warnings.filterwarnings('ignore')

from utils import *

import os
HF_TOKEN = os.getenv("HF_TOKEN")

from huggingface_hub import login
login(token=HF_TOKEN)

# hyperparameters
NUM_BEAMS = 4
MAX_NEW_TOKENS = 256

def get_db():
    # database
    db = SQLDatabase.from_uri("sqlite:///./data/catastici.db")
    return db

def get_model(model_name: str = 'seeklhy/codes-7b'):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        device_map = "auto", 
        torch_dtype = torch.float16
    )

    # update eos token id of the tokenizer and the model to support early stop SQL generation
    token_ids_of_example_sql = tokenizer("SELECT * FROM tables ;")["input_ids"]
    if token_ids_of_example_sql[-1] == tokenizer.eos_token_id:
        new_eos_token_id = token_ids_of_example_sql[-2]
    else:
        new_eos_token_id = token_ids_of_example_sql[-1]
    model.config.eos_token_id = new_eos_token_id
    tokenizer.eos_token_id = new_eos_token_id
    
    # max tokens
    max_tokens = 6144 if "15" in model_name else 8192        
    
    return model, tokenizer, max_tokens

def get_generate_model(model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype = torch.float16
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model, tokenizer

def prepare_prompt(
    question: str,
    db: SQLDatabase,
    few_n: int
):
    # get the original questions
    demonstration = pd.read_csv("data/demonstration.csv")

    # similarity model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Compute embedding for both lists
    q_embedding = model.encode(question, convert_to_tensor=True)
    d_embeddings = model.encode(demonstration['question'].tolist(), convert_to_tensor=True)

    # Compute cosine-similarities
    cosine_scores = util.cos_sim(q_embedding, d_embeddings)
    top_n_idx = np.argsort(cosine_scores.squeeze().tolist())[::-1][:few_n]
    
    # prepare the prompt
    few_shot = '\n\n'.join([get_prompt().format(matched_contents=get_matched_contents(question=demonstration.iloc[idx]['question'], db=db),question=demonstration.iloc[idx]['question']) + demonstration.iloc[idx]['query'] for idx in top_n_idx])
    in_prompt = few_shot + '\n\n' + get_prompt().format(matched_contents=get_matched_contents(question=question, db=db), question=question)

    return in_prompt

def prepare_input_ids_and_attention_mask(
    tokenizer: AutoTokenizer,
    input_seq: str, 
    max_input_length: int, 
    device: torch.device
):
    input_ids = tokenizer(input_seq , truncation = False)["input_ids"]

    if len(input_ids) <= max_input_length:
        input_ids = input_ids
        attention_mask = [1] * len(input_ids)
    else:
        if tokenizer.name_or_path == "THUDM/codegeex2-6b":
            input_ids = [64790, 64792] + input_ids[-(max_input_length-2):]
        else:
            input_ids = [tokenizer.bos_token_id] + input_ids[-(max_input_length-1):]

        attention_mask = [1] * max_input_length
    
    return {
        "input_ids": torch.tensor([input_ids]).to(device), # torch.int64
        "attention_mask": torch.tensor([attention_mask]).to(device) # torch.int64
    }
    
def text2sql_func(
    model: AutoModelForCausalLM, 
    tokenizer: AutoTokenizer, 
    text2sql_input_seq: str, 
    max_tokens: int
):
    inputs = prepare_input_ids_and_attention_mask(
        tokenizer, 
        text2sql_input_seq, 
        max_tokens - MAX_NEW_TOKENS,
        model.device
    )

    input_length = inputs["input_ids"].shape[1]

    with torch.no_grad():
        generate_ids = model.generate(
            **inputs,
            max_new_tokens = MAX_NEW_TOKENS,
            num_beams = NUM_BEAMS,
            num_return_sequences = NUM_BEAMS,
            use_cache = True,
            pad_token_id = tokenizer.eos_token_id,
            eos_token_id = tokenizer.eos_token_id
        )

    generated_sqls = post_process(tokenizer.batch_decode(generate_ids[:, input_length:], skip_special_tokens = True, clean_up_tokenization_spaces = False))
    
    return generated_sqls     

def generate_query(
    question: str, 
    db: SQLDatabase,
    model: AutoModelForCausalLM, 
    tokenizer: AutoTokenizer, 
    max_tokens: int,
    few_n: int = 5
):
    # get prompt
    in_prompt = prepare_prompt(question=question, db=db, few_n=few_n)
   
    # generate sql query
    generated_sqls = text2sql_func(model=model, tokenizer=tokenizer, text2sql_input_seq=in_prompt, max_tokens=max_tokens)
    generated_answers = [check_sql_executability(query=generated_sql, db=db) for generated_sql in generated_sqls]
    final_answer = get_majority_vote(generated_answers, num_beams=NUM_BEAMS)
    final_sql = generated_sqls[generated_answers.index(final_answer)]
    
    return final_answer, final_sql 

def generate_answer(
    question: str,
    answer: str, 
    sql: str, 
    model: AutoModelForCausalLM, 
    tokenizer: AutoTokenizer,
    instruct_token: str='[/INST]'
):
    prompt = f"""You are a historian specialized in Venice 1740.
You are given a question, an SQL query to answer the question, and the answer of the question extracted from the database.
Using the SQL query, and the extracted answer, generate an answer in Natural Language to the question.

The question is based on the following Database:
CREATE TABLE [catastici]
(
    [Property_ID] INT, -- Primary key. Unique ID of each property
    [Owner_ID] INT, -- Unique ID of each owner of the property
    [Owner_First_Name] NVARCHAR(30), -- First name of the owner of the property
    [Owner_Family_Name] NVARCHAR(30), -- Family name of the owner of the property
    [Property_Type] NVARCHAR(100), -- Specific type of the property given in Italian
    [Rent_Income] INT, -- Rent price of the property that the owner receives as income, given in Venice ancient gold coin ducats
    [Property_Location] NVARCHAR(100) -- Ancient approximate toponym of the property given in Italian
);

Don't mention anything about the database. Just answer the question.
If the extracted answer contains an error message, reply with "I don't know".

### Question
{question}

### SQL query
{sql}

### Extracted answer
{answer}

### Answer
"""
    message = [
        {"role": "user", "content": prompt}
    ]

    input_ids = tokenizer.apply_chat_template(message, return_tensors="pt")
    attention_mask = torch.ones_like(input_ids)

    input_ids = input_ids.to("cuda")
    attention_mask = attention_mask.to("cuda")
    model.to("cuda")
    
    generated_ids = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=1000, 
        do_sample=True, 
        pad_token_id=tokenizer.eos_token_id
    )
    decoded = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    return decoded.split(instruct_token)[1].strip()


def run(
    verbose: bool = True,
    answer_in_nl: bool = False
):
    assert answer_in_nl or verbose; "Set at least one of 'verbose' or 'answer_in_nl' to True."

    # get model
    model, tokenizer, max_tokens = get_model()
    
    # get generation model
    if answer_in_nl:
        generate_model, generate_tokenizer = get_generate_model()
    
    # get db
    db = get_db()

    while True:
        question = input("Question: ").lower()
        if question.lower() == 'exit':
            break
        
        # get the sql and the answer
        answer, sql = generate_query(question, db=db, model=model, tokenizer=tokenizer, max_tokens=max_tokens)
        
        # print the output
        if verbose:
            print('-'*20)
            print('Generated SQL:')
            print(sql)
            print('-'*20)
            print('Predicted Answer:')
            print(answer)
            print('-'*20)
        if answer_in_nl:
            text_answer = generate_answer(question=question, answer=answer, sql=sql, model=generate_model, tokenizer=generate_tokenizer)
            print("Answer:")
            print(text_answer)
            print('-'*20)
            

if __name__ == "__main__":
    from jsonargparse import CLI
    
    CLI(run)