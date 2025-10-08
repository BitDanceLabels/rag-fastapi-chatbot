from fastapi import APIRouter, Depends
from app.llm_model.services import generate_response
from fastapi.responses import StreamingResponse
from app.core.dependency import SessionDep
from app.auth.dependency import AccessTokenBearer


conversation_router = APIRouter()

@conversation_router.post("/{chat_id}", dependencies=[Depends(AccessTokenBearer())])
async def chat_endpoint(chat_id: str, question: str, session: SessionDep):
    event_stream = await generate_response(query=question, chat_id=chat_id, session=session)
    return StreamingResponse(event_stream(), media_type="text/plain")
