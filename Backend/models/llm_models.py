
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# ── Symptom extractor — strict and precise 
extractor_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.2,
    api_key=os.getenv("OPENAI_API_KEY")
)

# ── Conversation model — warm and natural 
chat_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# ── Embeddings model — for semantic similarity search 
embeddings_model = OpenAIEmbeddings(
    api_key=os.getenv("OPENAI_API_KEY")
)