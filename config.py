from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# MODEL_NAME = "qwen3.5:2b"

# llm = init_chat_model(
#   model="gemini-3.1-flash-lite",
#   model_provider="google_genai",
#   temperature=0,
#   reasoning_effort="medium",
# )

# worker llm
llm = ChatGoogleGenerativeAI(
  model="gemini-3.1-flash-lite",
  temperature=0,
  reasoning_effort="minimal",
)
# non-worker json llm
json_llm = ChatGoogleGenerativeAI(
  model="gemini-3.1-flash-lite",
  temperature=0,
  response_mime_type="application/json",
  reasoning_effort="medium",
)

# json_llm = init_chat_model(
#   model="gemini-3.1-flash-lite",
#   model_provider="google_genai",
#   temperature=0,
#   response_mime_type="application/json",
#   reasoning_effort="minimal",
# )

