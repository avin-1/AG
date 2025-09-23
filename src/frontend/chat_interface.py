import streamlit as st
import requests
from src.utils.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="FloatChat - ARGO Data Explorer",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 FloatChat - ARGO Ocean Data Assistant")
st.markdown("**AI-Powered Conversational Interface for ARGO Ocean Data Discovery**")
st.markdown("Ask questions about ARGO float data using natural language! This system specializes in Indian Ocean ARGO data analysis.")

# Example queries from the problem statement
st.subheader("💡 Example Queries")
example_queries = [
    "Show me salinity profiles near the equator in March 2023",
    "Compare BGC parameters in the Arabian Sea for the last 6 months", 
    "What are the nearest ARGO floats to this location?",
    "What ARGO floats are available in the Indian Ocean?",
    "Show me temperature profiles from different floats",
    "Find floats operating in the Bay of Bengal region"
]

col1, col2 = st.columns(2)
for i, query in enumerate(example_queries):
    with col1 if i % 2 == 0 else col2:
        if st.button(f"💬 {query}", key=f"example_{query}"):
            st.session_state.user_input = query

st.divider()

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about ARGO data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        response = requests.post("http://localhost:8000/chat", json={"text": prompt}).json()
        with st.chat_message("assistant"):
            st.markdown(response["response"])
        st.session_state.messages.append({"role": "assistant", "content": response["response"]})
    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"Error connecting to API: {e}")
            st.info("Make sure the API server is running: `python src/api/main.py`")

# Sidebar with additional info
with st.sidebar:
    st.header("📊 Quick Stats")
    st.info("""
    **Current Dataset:**
    - Indian Ocean ARGO floats
    - Temperature, Salinity, Pressure data
    - Interactive visualizations available
    """)
    
    st.header("🔗 Navigation")
    if st.button("📈 Go to Dashboard"):
        st.switch_page("pages/dashboard.py")
    
    st.header("ℹ️ About FloatChat")
    st.markdown("""
    FloatChat is an AI-powered system that:
    - Processes ARGO NetCDF data
    - Provides natural language querying
    - Offers interactive visualizations
    - Supports data export capabilities
    
    **Built for:** Ministry of Earth Sciences (MoES)
    **Organization:** INCOIS
    """)