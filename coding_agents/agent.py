from langgraph.graph import StateGraph, END
from utils.nodes import extract_entities, create_plan, write_code, execute, check_output, get_num_rows
from utils.state import GraphState

# Define workflow
workflow = StateGraph(GraphState)

# Define the nodes 
workflow.add_node("extract_entities", extract_entities)
workflow.add_node("create_plan", create_plan)
workflow.add_node("write_code", write_code)
workflow.add_node("execute", execute)
workflow.add_node("get_num_rows", get_num_rows)

# Build graph
workflow.set_entry_point("extract_entities")
workflow.add_edge("extract_entities", "create_plan")
workflow.add_edge("create_plan", "write_code")
workflow.add_edge("write_code", "execute")
workflow.add_conditional_edges(
    "execute",
    check_output,
    {
        "debug": "write_code",
        "end": "get_num_rows",
    },
)
workflow.add_edge("get_num_rows", END)
graph = workflow.compile()