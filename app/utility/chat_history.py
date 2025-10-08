import redis
import json
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_to_dict, messages_from_dict
import logging
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RedisHistoryLogger")


class SimpleRedisHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, redis_url: str, ttl: Optional[int] = None):
        """
        Initialize Redis-backed chat history.

        Args:
            session_id: Unique identifier for the session
            redis_url: Redis connection URL
            ttl: Optional time-to-live (in seconds) for Redis keys
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")
        if not redis_url:
            raise ValueError("redis_url cannot be empty")

        self.session_id = session_id
        self.ttl = ttl
        try:
            self.r = redis.Redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.r.ping()
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        logger.info(f"Initialized RedisHistory for session_id={session_id}")

    def add_message(self, message: BaseMessage) -> None:
        """
        Add a message to the Redis history.

        Args:
            message: The message to add
        """
        key = f"history:{self.session_id}"
        try:
            msg_dict = messages_to_dict([message])[0]
            self.r.rpush(key, json.dumps(msg_dict))
            if self.ttl:
                self.r.expire(key, self.ttl)
            logger.info(
                f"Stored message in Redis | key={key} | type={message.type} | content={message.content[:50]}"
            )
        except (redis.RedisError, json.JSONEncodeError) as e:
            logger.error(f"Failed to add message: {e}")
            raise

    def get_messages(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """
        Retrieve messages from Redis history.

        Args:
            limit: Optional number of recent messages to retrieve

        Returns:
            List of BaseMessage objects
        """
        key = f"history:{self.session_id}"
        try:
            if limit is None:
                raw = [json.loads(m) for m in self.r.lrange(key, 0, -1)]
            else:
                raw = [json.loads(m) for m in self.r.lrange(key, -limit, -1)]
            return messages_from_dict(raw)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to retrieve messages: {e}")
            return []

    @property
    def messages(self) -> List[BaseMessage]:
        """Get all messages in the history."""
        return self.get_messages()

    def clear(self) -> None:
        """Clear the session history from Redis."""
        try:
            self.r.delete(f"history:{self.session_id}")
            logger.info(f"Cleared history for session_id={self.session_id}")
        except redis.RedisError as e:
            logger.error(f"Failed to clear history: {e}")
            raise