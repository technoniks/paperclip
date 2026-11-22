from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

MODEL_NAME = "qwen3.5:2b"

llm = init_chat_model(
  model="gemini-3.1-flash-lite",
  model_provider="google_genai",
  temperature=0,
  reasoning_effort="minimal",
)

json_llm = init_chat_model(
  model="gemini-3.1-flash-lite",
  model_provider="google_genai",
  temperature=0,
  response_mime_type="application/json",
  reasoning_effort="minimal",
)

# print(json_llm.invoke({"message": "Hello, world!"}))
