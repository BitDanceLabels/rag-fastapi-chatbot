from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_ollama import ChatOllama
from app.prompt_template import generate_prompt_with_context
from pydantic import BaseModel
import logging

# Initialize FastAPI app
app = FastAPI(title="Chat API with Streaming")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the language model
llm = ChatOllama(
    model="deepseek-r1:8b",
    temperature=0.01,
    num_predict=1024,
    validate_model_on_init=True,
)

# Request model for the chat endpoint
class ChatRequest(BaseModel):
    question: str


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses based on user question and context.

    Args:
        request: ChatRequest object containing the user question and number of context items (k).

    Returns:
        StreamingResponse with model-generated text.
    """
    try:
        # Generate prompt with context
        prompt = generate_prompt_with_context(
            user_question=request.question
        )
        logger.info(f"Generated prompt: {prompt}")

        # Define a generator function for streaming
        def generate():
            chunk_count = 0
            for chunk in llm.stream(prompt):
                chunk_count += 1
                yield chunk.content

        # Return streaming response
        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")