from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.auth.dependency import AccessTokenBearer
from app.core.dependency import SessionDep
from app.llm_model.schema import ChatRequest
from app.llm_model.services import generate_response


conversation_router = APIRouter()


@conversation_router.post("/", dependencies=[Depends(AccessTokenBearer())])
async def chat_endpoint(payload: ChatRequest, session: SessionDep):
    event_stream = await generate_response(
        query=payload.question, chat_id=payload.chat_id, session=session
    )
    return StreamingResponse(event_stream(), media_type="text/plain")
