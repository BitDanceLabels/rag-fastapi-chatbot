from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from app.chat_message_history.services import SimpleRedisHistory
from app.embedding_search.services import SearchService
from app.config import Config

search_service = SearchService(db=Config.PSYCOPG_CONNECT, vector_table="item")
simple_redis_history = SimpleRedisHistory(session_id="session-1", redis_url="redis://localhost:6379")

messages = simple_redis_history.get_message(limit=2)
tuples = [(m.type, m.content) for m in messages]
print(tuples)


llm = ChatOllama(
    model="model_name",
    temperature=0.01,
    num_predict=512,
    validate_model_on_init=True,
)


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

prompt.invoke(
    {
        "history": tuples,
        "question": "now multiply that by 4",
    }
)
print(prompt)