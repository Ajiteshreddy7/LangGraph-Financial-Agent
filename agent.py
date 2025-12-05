# agent.py

import os
from dotenv import load_dotenv
import operator
from typing import TypedDict, Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Import the tools from our tools.py file
from tools import tools

# Load environment variables from the .env file
load_dotenv()

# Define the AI model, bound with our single tool
model = ChatOpenAI(temperature=0, streaming=True).bind_tools(tools)

# Define the structure of the agent's state
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]

# Define the conditional edge that decides whether to continue or end
def should_continue(state):
    last_message = state['messages'][-1]
    # If the LLM didn't call a tool, we end the conversation
    if not last_message.tool_calls:
        return "end"
    # Otherwise, we continue to the action node
    return "continue"

# Define the node that calls the AI model
def call_model(state):
    messages = state['messages']
    response = model.invoke(messages)
    return {"messages": [response]}

# Assemble the graph
workflow = StateGraph(AgentState)

# Create the ToolNode (the node that executes our tool)
tool_node = ToolNode(tools)

# Add the nodes to the graph
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

# Set the entry point and edges
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"continue": "action", "end": END},
)
workflow.add_edge("action", "agent")

# Compile the graph into a runnable application
app = workflow.compile()