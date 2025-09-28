import redis
import json
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_to_dict, messages_from_dict, HumanMessage, AIMessage

class SimpleRedisHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, redis_url: str):
        self.session_id = session_id
        self.r = redis.Redis.from_url(redis_url, decode_responses=True)

    def add_message(self, message: BaseMessage):
        key = f"history:{self.session_id}"
        msg_dict = messages_to_dict([message])[0]
        # print("Storing message:", msg_dict)  # Debug
        self.r.rpush(key, json.dumps(msg_dict))

    def get_message(self, limit: int | None = None):
        key = f"history:{self.session_id}"
        if limit is None:
            raw = [json.loads(m) for m in self.r.lrange(key, 0, -1)]
        else:
            raw = [json.loads(m) for m in self.r.lrange(key, -limit, -1)]
        # print("Retrieved messages:", raw)  # Debug
        return messages_from_dict(raw)

    @property
    def messages(self):
       return self.get_message()

    def clear(self):
        self.r.delete(f"history:{self.session_id}")

#######Testing#######

# Test the implementation
history = SimpleRedisHistory(session_id="session-1", redis_url="redis://localhost:6379")

# Add messages
history.add_message(HumanMessage(content="Hello, AI!"))
history.add_message(AIMessage(content="Hello, human! How can I assist you today?"))# Retrieve all messages
#
# messages = history.get_message(limit=2)
# for message in messages:
#     print(f"{message.type}: {message.content}")
#
# # Clear the history for the session
# history.clear()
