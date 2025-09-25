import traceback
import pandas as pd

from utils.state import GraphState
from utils.utils import (
    get_reference_extractor,
    get_entity_detector,
    get_coder,
    get_planner,
    get_debugger,
    get_row_finder,
    extract_python_code,
    execute_code,
    extract_references,
    detect_entity,
    exact_search,
    fuzzy_search,
    similarity_search
)

from sentence_transformers import SentenceTransformer

MAX_NUM_ITERATIONS = 10
DATASET_PATHS = {1: "data/buildings_1740.csv", 2: "data/buildings_1808.csv", 3: "data/landmarks.csv"}

def extract_entities(state):
    """extracts the References and the Entities from the question"""
    question = state['question']

    # Initialize LLMs
    reference_extractor = get_reference_extractor(state['llm'])
    entity_detector = get_entity_detector(state['llm'])

    references = reference_extractor.invoke({"question": question})
    references = extract_references(references)

    encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    clean_references = []
    clean_entities = []
    for reference in references:
        if len(reference) != 3:
            continue
        
        # detect an entity
        is_entity = entity_detector.invoke({"question": question, "reference": reference})
        is_entity = detect_entity(is_entity)

        try:
            # get reference info
            reference_name = reference[0].lower()
            reference_column = reference[1].lower()
            reference_dataset = reference[2]

            # get the column values from the dataset
            dataset = pd.read_csv(DATASET_PATHS[int(reference_dataset)])

            if not is_entity:
                # if not an entity, consider as a reference
                if reference_column in dataset.columns:
                    clean_references.append({
                        reference_name: {
                            'dataset': DATASET_PATHS[int(reference_dataset)],
                            'column': reference_column
                        }
                    })
                else:
                    continue
            else:
                dataset = dataset[dataset[reference_column].notna()]
                column_values = dataset[reference_column].unique()

                # get exact matching
                matches = exact_search(reference_name, column_values)
            
                # fuzzy search
                if len(matches) == 0:
                    matches = fuzzy_search(reference_name, column_values)
            
                # similarity search
                threshold = 0.9
                while len(matches) == 0 and threshold >= 0.5:
                    matches = similarity_search(reference_name, column_values, encoder, threshold=threshold)
                    threshold -= 0.05
            
                # skip this entity if not matches are found with at least 50% of similarity
                if len(matches) == 0:
                    continue
                
                clean_entities.append({
                    reference_name: {
                        'dataset': DATASET_PATHS[int(reference_dataset)],
                        'column': reference_column,
                        'matches': matches
                    }
                })
        except:
            continue

    return {"references": clean_references, "entities": clean_entities}

def create_plan(state):
    """creates a plan to answer the question"""
    question = state['question']
    entities = state['entities']
    references = state['references']
    answer_format = state['answer_format']

    # create the plan
    planner = get_planner(state['llm'])
    plan = planner.invoke({
            "question": question, 
            "entities": entities, 
            "references": references, 
            "answer_format": answer_format
        })

    return {"plan": plan}

def write_code(state):
    """writes / debugs a code following the given plan / error message"""
    question = state['question']
    entities = state['entities']
    references = state['references']
    answer_format = state['answer_format']
    plan = state['plan']
    num_steps = state['num_steps']
    error_message = state['error_message']

    # Generate or Debug the code
    if error_message:
        code = state['code']
        debugger = get_debugger(state['llm'])
        code = debugger.invoke({
                "question": question, 
                "entities": entities, 
                "references": references, 
                "plan": plan, 
                "code": f"```python\n{code}\n```", 
                "error_message": error_message,
                "answer_format": answer_format
            })
    else:
        coder = get_coder(state['llm'])
        code = coder.invoke({
                "question": question, 
                "plan": plan,
                "answer_format": answer_format
            })

    # extract the code block
    code_block = extract_python_code(code)

    num_steps += 1
    
    return {"code": code_block, "num_steps": num_steps}

def execute(state):
    """executes the given code"""
    code = state['code']

    # execute the code
    try:
        output = execute_code(code)
    except Exception:
        error_message = traceback.format_exc()
        error_message = error_message.split('exec(code, combined_namespace)')[-1]

        return {"error_message": error_message, 'code_output': None}

    return {"error_message": None, "code_output": output}

def check_output(state: GraphState):
    """determines whether to finish."""
    error_message = state["error_message"]
    num_steps = state["num_steps"]

    if error_message or num_steps == MAX_NUM_ITERATIONS:
        return "end"
    else:
        return "debug"
    
def get_num_rows(state):
    """creates a plan to answer the question"""
    question = state['question']
    code = state['code']
    code_output = state['code_output']

    # create the plan
    row_finder = get_row_finder(state['llm'])
    code_row = row_finder.invoke({
            "question": question, 
            "code": code, 
            "code_output": code_output, 
        })
    try:
        code_row = extract_python_code(code_row)
        num_rows = execute_code(code_row)
    except Exception:
        num_rows = None

    return {"num_rows": num_rows}