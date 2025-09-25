from typing import TypedDict
from langchain_openai import ChatOpenAI

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        entities: matched values of the entities
        plan: analysis plan
        code: code
        error_message: error message
        error: flag for error
        num_steps: number of steps
        code_output: output of the code
    """
    llm: ChatOpenAI
    question : str
    entities : dict
    references: dict
    answer_format: str
    plan : str
    code : str
    error_message: str
    num_steps : int
    code_output: str
    num_rows: int