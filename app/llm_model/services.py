from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from sqlmodel.ext.asyncio.session import AsyncSession
from langchain_core.prompts import MessagesPlaceholder
from uuid import UUID
from app.embedding_search.services import SearchService
from app.config import Config
from app.message.services import MessageService
from app.message.schema import MessageSchema
from app.chat_message_history.services import SimpleRedisHistory

search_service = SearchService(db=Config.PSYCOPG_CONNECT, vector_table="embedding")
message_service = MessageService()


llm = ChatOllama(
    model="deepseek-r1:8b",
    temperature=0.01,
    num_predict=1024,
    validate_model_on_init=True,
)


async def generate_response(
    query: str,
    chat_id: str,
    session: AsyncSession,
):
    # Create user message in db
    chat_uuid = UUID(chat_id)
    user_message = await message_service.create_message(
        message=MessageSchema(
            content=query,
            role="user",
            chat_id=chat_uuid,
        ),
        session=session,
    )

    # Create user message in history queue
    history_service = SimpleRedisHistory(
        session_id=str(user_message.chat_id), redis_url=Config.REDIS_URL, ttl=3600
    )
    history_service.add_message(HumanMessage(content=user_message.content))

    contextualize_q_system_prompt = (
        "Bạn nhận được lịch sử trò chuyện cùng với câu hỏi mới nhất của người dùng."
        "nếu câu hỏi này phụ thuộc vào ngữ cảnh trước đó,"
        "hãy viết lại nó thành một câu hỏi độc lập, có thể hiểu được mà không cần tham chiếu đến lịch sử."
        "Không được trả lời câu hỏi, chỉ cần định dạng lại và trả về câu hỏi cuối cùng."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "Câu hỏi:{input}\n\nDữ liệu tham khảo:\n{context}"),
        ]
    )

    # Get history
    messages = history_service.get_messages(
        limit=3  # message of the last three time
    )
    chat_history = [(m.type, m.content) for m in messages]

    # Get context
    context = search_service.mmr_search(query=query)

    # Create chain
    chain = contextualize_q_prompt | llm

    inputs = {
        "chat_history": chat_history,
        "input": query,
        "context": context,
    }

    async def event_stream():
        full_response = ""
        async for chunk in chain.astream(inputs):
            text = chunk.content
            if text:
                full_response += text
                yield text

        # Create user message in db
        bot_message = await message_service.create_message(
            message=MessageSchema(
                content=full_response,
                role="bot",
                chat_id=chat_uuid,
            ),
            session=session,
        )

        # Create bot message in history queue
        history_service.add_message(AIMessage(content=bot_message.content))

    return event_stream

