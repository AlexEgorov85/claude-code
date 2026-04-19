"""
Менеджер контекста диалога.
Управляет историей сообщений и усечением при превышении лимита токенов.
"""
from typing import List, Optional
from dataclasses import dataclass, field
from llm.client import Message

@dataclass
class ContextManager:
    max_tokens: int = 100000
    messages: List[Message] = field(default_factory=list)

    def add_message(self, role: str, content: str):
        """Добавляет сообщение в историю."""
        self.messages.append(Message(role=role, content=content))

    def get_messages(self) -> List[Message]:
        """Возвращает текущую историю сообщений."""
        return self.messages

    def clear_history(self):
        """Очищает историю (кроме системного промпта, если он хранится отдельно)."""
        self.messages = []

    def trim_to_fit(self, estimated_tokens_per_message: int = 500):
        """
        Усекает историю сообщений, если она превышает лимит токенов.
        Удаляет самые старые сообщения пользователя/ассистента.
        """
        max_messages = self.max_tokens // estimated_tokens_per_message
        
        if len(self.messages) > max_messages:
            # Оставляем только последние N сообщений
            self.messages = self.messages[-max_messages:]
            return True  # Была обрезка
        return False
