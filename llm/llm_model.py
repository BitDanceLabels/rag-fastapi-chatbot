from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from pathlib import Path

# --- Load vector store và retriever ---
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "embedding" / "chroma_langchain_db"


embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

vector_store = Chroma(
    persist_directory=str(DB_PATH),
    embedding_function=embedding,
    collection_name="customer-service",
)
retriever = vector_store.as_retriever(
    search_type="mmr", search_kwargs={"k": 2, "fetch_k": 10}
)

# --- Ollama LLM ---
llm = ChatOllama(
    model="deepseek-r1:8b",
    temperature=0.01,
    num_predict=1024,
    validate_model_on_init=True,
)

# --- Prompt template ---
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Bạn là trợ lý ảo. "
            "Nhiệm vụ tóm tắt thông tin và trả lời cho khách hàng.",
        ),
        (
            "system",
            "Câu hỏi của khách hàng: {question}\n\n"
            "Thông tin tìm thấy trong cơ sở dữ liệu:\n{context}\n\n",
        ),
    ]
)

# # --- Truy vấn ---
# question = "Giới thiệu về Quatest 3"
# docs = retriever.invoke(question)
# # for doc in docs:
# #     print(f"{doc.id}: {doc.page_content}\n")
#
# # Lấy nội dung từ các chunk
# contents = [doc.page_content for doc in docs]
# context = "\n".join(contents)
#
## --- Kết nối LLM và prompt ---
chain = prompt | llm
# ai_msg = chain.invoke(
#     {
#         "question": question,
#         "context": context,
#     }
# )

# for chunk in chain.stream(
#     {
#         "question": question,
#         "context": context,
#     }
# ):
#     print(chunk.content, end="", flush=True)

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit", "bye"]:
        print("\nAI: bye bye")
        break

    print("AI: ", end="", flush=True)
    question = user_input.strip()

    docs = retriever.invoke(question)
    contents = [doc.page_content for doc in docs]
    context = "\n".join(contents)

    for chunk in chain.stream(
        {
            "question": question,
            "context": context,
        }
    ):
        print(chunk.content, end="", flush=True)
    print("\n")
