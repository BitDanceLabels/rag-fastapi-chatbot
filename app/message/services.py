from uuid import UUID

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from sympy.integrals.meijerint_doc import category

from app.core.model import Message
from fastapi_pagination.ext.sqlmodel import apaginate
from app.message.schema import MessageSchema



class MessageService:
    async def get_message(self, session:AsyncSession):
        statement = select(Message).order_by(desc(Message.created_at))
        return await apaginate(session, statement)

    async def get_message_id(self, message_id: str, session:AsyncSession):
        message_uuid = UUID(message_id)
        result = await session.get(Message.message_id == message_uuid)
        if not result:
            raise HTTPException(status_code=404, detail="Message not found")
        return result

    async def create_message(self, message: MessageSchema, session:AsyncSession):
        data_dict = message.model_dump()
        new_message = Message(**data_dict)
        session.add(new_message)
        await session.commit()
        return new_message

    async def update_message(self, message_id: str, data_update: MessageSchema, session:AsyncSession):
        message = await session.get(Message.category, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        for key, value in data_update.items():
                setattr(message, key, value)
        await session.commit()
        return category

    async def delete_message(self, message_id: str, session:AsyncSession):
        message = await session.get(Message.category, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        await session.delete(message)
        await session.commit()
        return None