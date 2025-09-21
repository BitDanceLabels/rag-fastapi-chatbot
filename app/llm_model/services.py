from langchain_ollama import ChatOllama
from app.prompt_template import generate_prompt_with_context

llm = ChatOllama(
    model="deepseek-r1:8b",
    temperature=0.01,
    num_predict=1024,
    validate_model_on_init=True,
)

question = ""
prompt = generate_prompt_with_context(user_question=question, k=3)

# --- Streaming ---
for chunk in llm.stream(prompt):
    print(chunk.content, end="", flush=True)

