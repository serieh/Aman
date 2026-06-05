from dotenv import load_dotenv
load_dotenv()
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def test_model(model_name):
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
        vector = embeddings.embed_query("test query")
        print(f"SUCCESS with {model_name}: vector size {len(vector)}")
    except Exception as e:
        print(f"FAILED with {model_name}: {e}")

test_model("models/text-embedding-004")
test_model("text-embedding-004")
