import re
import sys
import ast
from io import StringIO
import pandas as pd

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate

from rapidfuzz import fuzz
from sentence_transformers import util

from utils.prompts import (
    extract_reference_prompt,
    extract_entity_prompt,
    analysis_system_prompt, 
    python_system_prompt, 
    plan_prompt,
    code_prompt,
    debug_prompt,
    num_row_prompt
)

def execute_code(code):
    global_namespace = globals().copy()
    local_namespace = locals().copy()
    combined_namespace = {**global_namespace, **local_namespace}
    
    # Redirect stdout to capture printed output
    stdout_orig = sys.stdout
    sys.stdout = StringIO()

    try:
        # Execute the code in the combined namespace
        code = code.replace('exit()', 'return')
        exec(code, combined_namespace)

        # Get the captured output
        output = sys.stdout.getvalue()
        return output.strip()
    finally:
        # Restore stdout
        sys.stdout = stdout_orig

def read_questions(questions_path='out/out_matches.csv'):
    questions = pd.read_csv(questions_path)
    return questions

def get_openai_llm(model_name: str = 'gpt-4o-mini', seed: int = 42, do_sample=True, temperature=0, top_p=0): # temperature=0, top_p=0 -> greedy
    if do_sample:
        llm = ChatOpenAI(model_name=model_name, seed=seed)
    else:
        llm = ChatOpenAI(model_name=model_name, temperature=temperature, seed=seed, top_p=top_p)
    
    return llm

def construct_chat_prompt(system_prompt, message):
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=(system_prompt)),
            HumanMessagePromptTemplate.from_template(message),
        ]
    )

    return prompt

def extract_python_code(text):
    if text.count('```') == 1:
        if '```python' in text:
            return text.split('```python')[-1]
        elif '```Python' in text:
            return text.split('```Python')[-1]
        else:
            return text.split('```')[-1]
        
    # Find all code block matches in the text
    pattern = r'```python(.*?)```|```\s*(.*?)```|```Python(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    # Extract the code from matches
    code_blocks = [match[0] if match[0] else match[1] for match in matches]
    code_blocks = [code_block[len('python'):].lstrip() if code_block.lower().startswith('python') else code_block for code_block in code_blocks]
    code = '\n\n'.join(code_blocks).strip()
    
    return code

def get_reference_extractor(llm):

    prompt = construct_chat_prompt(analysis_system_prompt, extract_reference_prompt)
    reference_extractor = prompt | llm | StrOutputParser()

    return reference_extractor

def get_entity_detector(llm):

    prompt = construct_chat_prompt(analysis_system_prompt, extract_entity_prompt)
    entity_extractor = prompt | llm | StrOutputParser()

    return entity_extractor

def get_planner(llm):
    prompt = construct_chat_prompt(analysis_system_prompt, plan_prompt)
    planner = prompt | llm | StrOutputParser()

    return planner

def get_coder(llm):
    prompt = construct_chat_prompt(python_system_prompt, code_prompt)
    coder = prompt | llm | StrOutputParser()

    return coder

def get_debugger(llm):

    prompt = construct_chat_prompt(python_system_prompt, debug_prompt)
    debugger = prompt | llm | StrOutputParser()

    return debugger

def get_row_finder(llm):

    prompt = construct_chat_prompt(python_system_prompt, num_row_prompt)
    debugger = prompt | llm | StrOutputParser()

    return debugger

def wrap_strings(matches):
    return re.sub(r'(\b\w[\w\s]*\b)', r'"\1"', matches)
    
def extract_references(input_string):
    input_string.replace('“', '"').replace('”', '"')

    # Use regular expression to find the pattern
    pattern = r"\[\(.*?\)\]"
    matches = re.search(pattern, input_string, re.DOTALL)

    try:
        if matches:
            matches_str = matches.group(0)
            
            if matches_str.count('"') < 2:
                matches_str = wrap_strings(matches_str)
            
            matches_list = ast.literal_eval(matches_str)
        else:
            matches_list = []
    except:
        matches_list = []

    return matches_list

def detect_entity(text):
    # Use a regular expression to find content between [[ and ]]
    match = re.search(r'\[\[(.*?)\]\]', text)
    if match:
        return bool("true" in match.group(1).lower())
    else:
        return bool("True" in text)
    
def exact_search(query, strings):
    """
    Perform an exact search on a list of strings and return values with a similarity score higher than threshold.
    """
    if query in strings:
        return [query]
    else:
        return []

def fuzzy_search(query, strings, threshold=70):
    """
    Perform a fuzzy similarity search on a list of strings and return values with a similarity score higher than threshold.
    Relies on Levenshtein Distance: Measures the minimum number of single-character edits (insertions, deletions, or substitutions) required to change one word into the other.
    """
    strings_str = strings.astype(str)
    return [string for string in strings_str if fuzz.ratio(string, query) > threshold]

def similarity_search(query, strings, encoder, threshold=0.7):
    """
    Perform a similarity search on a list of strings and return values with a similarity score higher than threshold.
    """
    strings_str = strings.astype(str)

    query_embedding = encoder.encode(query, convert_to_tensor=True)
    strings_embeddings = encoder.encode(strings_str, convert_to_tensor=True)
    
    similarities = util.pytorch_cos_sim(query_embedding, strings_embeddings)[0]
    result = [strings_str[i] for i in range(len(strings_str)) if similarities[i] > threshold]
    
    return result

import re

def extract_content(text):
    match = re.findall(r'\[\[(.*?)\]\]', text)
    if match:
        return match[-1]
    else:
        return None