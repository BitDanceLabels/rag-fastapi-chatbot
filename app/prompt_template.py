from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.segmatic_search.services import SearchService
from app.config import Config

PSYCOPG_CONNECT = Config.PSYCOPG_CONNECT
table_name = "item"

search_service = SearchService(db=PSYCOPG_CONNECT, vector_table=table_name)

# Define the prompt template
prompt_template = ChatPromptTemplate(
    [
        (
            "system",
            "Bạn là trợ lý ảo chuyên cung cấp thông tin hỗ trợ khách hàng dựa trên dữ liệu truy vấn.",
        ),
        MessagesPlaceholder("msgs"),
    ]
)


def generate_prompt_with_context(
    user_question: str,
    k: int = 4,
    distance_function: str = str("<=>"),  # as cosine similarity
    hnsw_ef_search: int = 40,
    fetch_k: int = 30,
    lambda_mult: float = 0.7,
):
    # Get query data
    query_result = search_service.mmr_search(
        query=user_question,
        k=k,
        distance_function=distance_function,
        hnsw_ef_search=hnsw_ef_search,
        fetch_k=fetch_k,
        lambda_mult=lambda_mult,
    )

    # Create conversation history with context and user query
    messages_to_pass = [
        AIMessage(content="Tôi có thể giúp gì được cho bạn?"),
        HumanMessage(
            content=f"""
            Dữ liệu truy vấn: {query_result}
            \nCâu hỏi của người dùng: {user_question}
            \nXem dữ liệu truy vấn chọn ngữ cảnh phù hợp và tóm tắt ngữ cảnh
            \nTrả lời cho khách hàng lịch sự chuyên nghiệp 
            \nNếu dữ liệu truy vấn không có thông tin liên quan thì trả lời tôi không biết"""
        ),
    ]

    # Invoke the prompt
    formatted_prompt = prompt_template.invoke({"msgs": messages_to_pass})
    return formatted_prompt


if __name__ == "__main__":
    # # Test the function
    user_question = "phạm vi hoạt động hoặc lịch làm việc của Quatest 3"

    formatted_prompt = generate_prompt_with_context(user_question)
    print(formatted_prompt)
