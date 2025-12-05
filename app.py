import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import json

from agent import app

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Financial Analyst AI", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #1E1E1E; border-right: 1px solid #2c2c2c; }
    [data-testid="stChatMessage"] { border-radius: 10px; padding: 16px; margin-bottom: 12px; border: 1px solid transparent; }
    [data-testid="stChatMessage"]:has(span[data-testid="chat-avatar-assistant"]) { background-color: #262626; border-color: #3c3c3c; }
    [data-testid="stChatMessage"]:has(span[data-testid="chat-avatar-user"]) { background-color: #303030; }
    [data-testid="stChatInput"] { background-color: #1E1E1E; border-top: 1px solid #2c2c2c; }
    .stButton>button { border-radius: 8px; border: 1px solid #4CAF50; background-color: transparent; color: #4CAF50; margin-right: 5px; }
    .stButton>button:hover { background-color: #4CAF50; color: white; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("📈 Financial Analyst AI")
    st.markdown("An AI assistant for investment research. Ask for a stock price, a full analysis, or compare multiple stocks.")
    st.markdown("---")
    st.markdown("### Example Prompts:")
    st.markdown("- *Analyze HP* (will trigger clarification)")
    st.markdown("- *What is the price of MSFT?*")
    st.markdown("- *Compare AAPL and GOOG*")

# --- MAIN CHAT INTERFACE ---

if "messages" not in st.session_state:
    st.session_state.messages = [AIMessage(content="Hello! I'm your Financial Analyst AI. How can I assist you today?")]

# Display chat messages and handle clarification UI
for message in st.session_state.messages:
    if isinstance(message, AIMessage) and message.tool_calls:
        tool_call = message.tool_calls[0]
        if tool_call['name'] == 'request_user_clarification':
            args = tool_call['args']
            with st.chat_message("assistant"):
                st.markdown(args['question'])
                if args.get('options'):
                    cols = st.columns(len(args['options']))
                    for i, option in enumerate(args['options']):
                        if cols[i].button(option, key=f"option_{i}"):
                            st.session_state.clarification_response = option
                            st.rerun()
    else:
        with st.chat_message(message.type):
            st.markdown(message.content)

# Handle user input (from chat box or clarification buttons)
user_input = st.chat_input("Ask about a stock...")

if st.session_state.get("clarification_response"):
    user_input = st.session_state.pop("clarification_response")
    last_user_message = next(m for m in reversed(st.session_state.messages) if isinstance(m, HumanMessage))
    prompt = f"Original query was: '{last_user_message.content}'. The user clarified with: '{user_input}'."
else:
    prompt = user_input

if prompt:
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        # --- THIS IS THE UPDATED, MORE FORCEFUL PROMPT ---
        final_prompt = (
            f"User query: '{prompt}'. \n\n"
            "You are an expert financial analyst. Your primary goal is to be accurate and never guess. "
            "Your first and most important step is to determine if a company name is ambiguous. "
            "For example, if the user says 'Ford', you must recognize that this could mean the ticker 'F' (Ford Motor Company) or 'FORD' (Forward Industries, Inc.). "
            "In this situation, or any similar situation with an ambiguous name, your ONLY allowed action is to call the `request_user_clarification` tool. "
            "You must provide the user with the options you have found. For the 'Ford' example, your tool call should be `request_user_clarification(question='I found multiple tickers for \"Ford\". Which did you mean?', options=['F (Ford Motor Company)', 'FORD (Forward Industries, Inc.)'])`. "
            "DO NOT proceed with any other tool if there is ambiguity. "
            "Only after the ticker is unambiguous should you select the correct data tool (`get_current_stock_price`, `get_full_stock_analysis`, etc.) and synthesize the report."
        )
        
        inputs = {"messages": [HumanMessage(content=final_prompt)]}
        
        final_response_message = AIMessage(content="")
        for output in app.stream(inputs):
            if "agent" in output:
                for message in output["agent"]["messages"]:
                    final_response_message = message

        st.session_state.messages.append(final_response_message)
        st.rerun()

