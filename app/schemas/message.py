# app/schemas/message.py
from pydantic import BaseModel

class Message(BaseModel):
    message: str