import streamlit as st
import requests
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document  # REMOVED BaseRetriever import
from typing import List

# 🔐 API keys directly here
SERPER_API_KEY = "my_k1" 
OPENWEATHER_API_KEY = "my_key"

# 🧠 Load Ollama LLM
llm = Ollama(model="granite3-dense:2b")


# 🔍 Simple Serper function
def search_serper(query: str, api_key: str) -> str:
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    data = {"q": query}
    try:
        res = requests.post("https://google.serper.dev/search", headers=headers, json=data, timeout=10)
        res.raise_for_status()
        results = res.json()
        return "\n\n".join([r.get("snippet", "") for r in results.get("organic", [])])
    except requests.exceptions.RequestException as e:
        st.error(f"Search API error: {e}")
        return ""

# ✅ FIXED: Custom Retriever (no BaseRetriever)
from langchain.schema import Document, BaseRetriever
from typing import List

class SerperRetriever(BaseRetriever):
    api_key: str  # Declare this as a field

    def get_relevant_documents(self, query: str) -> List[Document]:
        content = search_serper(query, self.api_key)
        return [Document(page_content=content)] if content else []

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        return self.get_relevant_documents(query)


# 🔗 RAG chain constructor
def build_rag_chain(category: str):
    retriever = SerperRetriever(api_key=SERPER_API_KEY)
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=f"""
You are a helpful assistant specialized in {category}.
Use the following context to answer the question.

Context:
{{context}}

Question: {{question}}

Answer:"""
    )

    memory_key = f"{category.lower().replace(' ', '_')}_chat_history"
    if memory_key not in st.session_state:
        st.session_state[memory_key] = ConversationBufferMemory(
            return_messages=True, memory_key="chat_history"
        )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=st.session_state[memory_key],
        combine_docs_chain_kwargs={"prompt": prompt}
    )
    return chain, memory_key

# 🌦️ Weather UI
def show_weather():
    st.subheader("🌦️ Weather Dashboard")
    city = st.text_input("Enter city name", "Hyderabad")
    if st.button("Get Weather"):
        if not city:
            st.warning("Please enter a city name")
            return

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            data = res.json()

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"### {data['name']}, {data['sys']['country']}")
                st.metric("🌡️ Temperature", f"{data['main']['temp']}°C")
                st.metric("☁️ Weather", data['weather'][0]['description'].title())
            with col2:
                st.metric("💧 Humidity", f"{data['main']['humidity']}%")
                st.metric("🌬️ Wind Speed", f"{data['wind']['speed']} m/s")
        except requests.exceptions.RequestException as e:
            st.error(f"Weather API error: {str(e)}")

# 💬 Chat History Display
def display_chat_history(memory_key: str):
    if memory_key in st.session_state:
        st.markdown("### 💬 Chat History")
        for msg in st.session_state[memory_key].chat_memory.messages:
            if msg.type == "human":
                st.markdown(f"**🧑 You**: {msg.content}")
            else:
                st.markdown(f"**🤖 Assistant**: {msg.content}")

# 🧠 Streamlit app entry
def main():
    st.set_page_config(page_title="Multi-Assistant RAG Bot", layout="wide")
    st.title("🧠 Multi-Domain RAG Assistant (IBM Granite + Serper + Weather)")

    tab1, tab2, tab3 = st.tabs([
        "💊 Medical Assistant",
        "🌾 Agriculture Assistant",
        "🌤️ Weather Dashboard"
    ])

    with tab1:
        st.header("Medical Assistance")
        query = st.chat_input("Ask a medical-related question...", key="med_input")
        if query:
            chain, memory_key = build_rag_chain("Medical Assistance")
            with st.spinner("Thinking..."):
                response = chain.run(query)
            st.session_state[memory_key].chat_memory.add_user_message(query)
            st.session_state[memory_key].chat_memory.add_ai_message(response)
            st.chat_message("user").write(query)
            st.chat_message("assistant").write(response)
        display_chat_history("medical_assistance_chat_history")

    with tab2:
        st.header("Agricultural Assistance")
        query = st.chat_input("Ask a farming or crop-related question...", key="agri_input")
        if query:
            chain, memory_key = build_rag_chain("Agricultural Assistance")
            with st.spinner("Thinking..."):
                response = chain.run(query)
            st.session_state[memory_key].chat_memory.add_user_message(query)
            st.session_state[memory_key].chat_memory.add_ai_message(response)
            st.chat_message("user").write(query)
            st.chat_message("assistant").write(response)
        display_chat_history("agricultural_assistance_chat_history")

    with tab3:
        show_weather()

# 🚀 Run app
if __name__ == "__main__":
    main()
