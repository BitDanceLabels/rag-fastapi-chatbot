from fastapi import APIRouter
from fastapi.params import Depends
from fastapi_pagination import Page
from app.core.dependency import SessionDep
from app.message.services import MessageService
from app.message.schema import MessageResponse
from app.auth.dependency import AccessTokenBearer

message_services = MessageService()
message_router = APIRouter()


@message_router.get("/", response_model=Page[MessageResponse], dependencies=[Depends(AccessTokenBearer())])
async def get_all_messages(session: SessionDep):
    messages = await message_services.get_messages(session)
    return messages


@message_router.get("/{chat_id}", response_model=Page[MessageResponse], dependencies=[Depends(AccessTokenBearer())])
async def get_message_from_chat_id(chat_id: str, session: SessionDep):
    chat = await message_services.get_message_from_chat_id(chat_id, session)
    return chat
