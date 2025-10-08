from uuid import UUID

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc, delete
from fastapi.responses import JSONResponse

from app.core.model import Message
from fastapi_pagination.ext.sqlmodel import apaginate
from app.message.schema import MessageSchema, MessageResponse


class MessageService:
    async def get_messages(self, session:AsyncSession):
        statement = select(Message).order_by(desc(Message.created_at))
        return await apaginate(session, statement)

    async def get_message_from_chat_id(self, chat_id: str, session:AsyncSession):
        statement = select(Message).where(Message.chat_id == UUID(chat_id))
        return await apaginate(session, statement)

    async def create_message(self, message: MessageSchema, session:AsyncSession):
        data_dict = message.model_dump()
        new_message = Message(**data_dict)
        session.add(new_message)
        await session.commit()
        return new_message