from fastapi import APIRouter, status, Depends
from fastapi.params import Depends
from fastapi_pagination import Page, Params
from typing import Annotated
from app.core.dependency import SessionDep
from app.message.services import MessageService
from app.message.schema import MessageSchema, MessageResponse
from app.auth.dependency import AccessTokenBearer

message_services = MessageService()
message_router = APIRouter()


@message_router.get("/", response_model=Page[MessageResponse], dependencies=[Depends(AccessTokenBearer())])
async def get_all_messages(session: SessionDep, _params: Annotated[Params, Depends()]):
    messages = await message_services.get_messages(session)
    return messages


@message_router.get("/{chat_id}", response_model=MessageResponse, dependencies=[Depends(AccessTokenBearer())])
async def get_message_item(message_id: str, session: SessionDep):
    chat = await message_services.get_message_id(message_id, session)
    return chat


@message_router.delete("/{chat_id}", status_code=204, dependencies=[Depends(AccessTokenBearer())])
async def message_delete(message_id: str, session: SessionDep):
    deleted_chat = await message_services.delete_message(message_id=message_id, session=session)
    return deleted_chat
