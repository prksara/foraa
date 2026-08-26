import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from database.models import Conversation, Message

class ConversationManager:
    """Database-backed storage for conversations strictly partitioned by user_id."""

    async def create_conversation(self, db: AsyncSession, user_id: str, title: str = "New Chat") -> Conversation:
        conv = Conversation(title=title, user_id=user_id)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv.messages = []
        return conv

    async def get_conversation(self, db: AsyncSession, conv_id: str, user_id: str) -> Optional[Conversation]:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conv_id)
            .where(Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalars().first()

    async def list_conversations(self, db: AsyncSession, user_id: str) -> List[Conversation]:
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def delete_conversation(self, db: AsyncSession, conv_id: str, user_id: str) -> bool:
        conv = await self.get_conversation(db, conv_id, user_id)
        if conv:
            await db.delete(conv)
            await db.commit()
            return True
        return False

    async def add_message(self, db: AsyncSession, conv_id: str, user_id: str, role: str, content: str) -> Optional[Message]:
        conv = await self.get_conversation(db, conv_id, user_id)
        if not conv:
            return None
            
        msg = Message(
            conversation_id=conv_id,
            role=role,
            content=content
        )
        db.add(msg)
        
        conv.updated_at = datetime.datetime.utcnow()
        
        if len(conv.messages) == 0 and role == "user":
            conv.title = content[:30] + ("..." if len(content) > 30 else "")
            
        await db.commit()
        await db.refresh(msg)
        return msg

# Singleton instance
manager = ConversationManager()
