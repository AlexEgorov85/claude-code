"""Enhanced History Management with serialization and compression."""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import json
from pathlib import Path
from datetime import datetime
import hashlib


@dataclass
class HistoryEntry:
    """A single entry in the conversation history."""
    id: str
    role: str  # "user", "assistant", "system"
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "tool_calls": self.tool_calls,
            "tool_call_id": self.tool_call_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryEntry':
        return cls(
            id=data["id"],
            role=data["role"],
            content=data.get("content"),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            metadata=data.get("metadata", {})
        )
    
    def token_estimate(self) -> int:
        """Estimate tokens for this entry."""
        tokens = 0
        if self.content:
            tokens += len(self.content.split()) * 1.3
        if self.tool_calls:
            for tc in self.tool_calls:
                tokens += len(json.dumps(tc).split()) * 1.3
        return int(tokens)


@dataclass
class ConversationSummary:
    """Summary of a conversation for compression."""
    summary: str
    key_points: List[str]
    start_time: datetime
    end_time: datetime
    message_count: int
    tool_calls_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "key_points": self.key_points,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "message_count": self.message_count,
            "tool_calls_count": self.tool_calls_count
        }


class HistoryManager:
    """Manage conversation history with persistence and compression."""
    
    def __init__(self, session_id: str, storage_path: Optional[str] = None):
        self.session_id = session_id
        self.storage_path = Path(storage_path) if storage_path else Path("./history")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._entries: List[HistoryEntry] = []
        self._summary: Optional[ConversationSummary] = None
        self._max_entries_before_compact = 50
        self._auto_compact_enabled = True
    
    @property
    def entries(self) -> List[HistoryEntry]:
        return self._entries.copy()
    
    @property
    def message_count(self) -> int:
        return len(self._entries)
    
    @property
    def summary(self) -> Optional[ConversationSummary]:
        return self._summary
    
    def add_entry(
        self,
        role: str,
        content: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HistoryEntry:
        """Add an entry to history."""
        entry_id = hashlib.md5(
            f"{self.session_id}:{len(self._entries)}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        entry = HistoryEntry(
            id=entry_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            metadata=metadata or {}
        )
        
        self._entries.append(entry)
        
        # Check if auto-compact is needed
        if self._auto_compact_enabled and len(self._entries) >= self._max_entries_before_compact:
            # Trigger compact (caller should handle the actual compaction)
            pass
        
        return entry
    
    def get_last_n(self, n: int) -> List[HistoryEntry]:
        """Get the last n entries."""
        return self._entries[-n:] if n > 0 else []
    
    def get_all(self) -> List[HistoryEntry]:
        """Get all entries."""
        return self._entries.copy()
    
    def clear(self) -> None:
        """Clear all history."""
        self._entries.clear()
        self._summary = None
    
    def estimate_tokens(self) -> int:
        """Estimate total tokens in history."""
        return sum(entry.token_estimate() for entry in self._entries)
    
    async def compact(
        self, 
        llm_client=None, 
        model: str = "claude-sonnet-4-20250514",
        keep_last_n: int = 5
    ) -> ConversationSummary:
        """Compact the history by summarizing old messages."""
        if len(self._entries) <= keep_last_n:
            return self._summary or ConversationSummary(
                summary="",
                key_points=[],
                start_time=self._entries[0].timestamp if self._entries else datetime.now(),
                end_time=self._entries[-1].timestamp if self._entries else datetime.now(),
                message_count=len(self._entries),
                tool_calls_count=sum(1 for e in self._entries if e.tool_calls)
            )
        
        # Get entries to summarize
        entries_to_summarize = self._entries[:-keep_last_n]
        
        # Create summary text
        summary_text = "\n".join([
            f"{e.role}: {e.content or '[tool call]'}"
            for e in entries_to_summarize
            if e.content or e.tool_calls
        ])
        
        # If LLM client is provided, use it for better summarization
        if llm_client:
            try:
                from .llm_client import LLMMessage, MessageRole, LLMConfig
                
                prompt = f"""Summarize the following conversation history into a concise summary and extract key points.

Conversation:
{summary_text}

Provide:
1. A brief summary (2-3 sentences)
2. Key points discussed (bullet points)"""

                response = await llm_client.chat(
                    messages=[LLMMessage(role=MessageRole.USER, content=prompt)],
                    config=LLMConfig(model=model, max_tokens=1000)
                )
                
                summary_content = response.content or ""
                key_points = [line.strip("- ").strip("* ") for line in summary_content.split("\n") if line.strip().startswith(("-", "*"))]
                
                self._summary = ConversationSummary(
                    summary=summary_content,
                    key_points=key_points,
                    start_time=entries_to_summarize[0].timestamp,
                    end_time=entries_to_summarize[-1].timestamp,
                    message_count=len(entries_to_summarize),
                    tool_calls_count=sum(1 for e in entries_to_summarize if e.tool_calls)
                )
            except Exception:
                # Fallback to simple summary
                self._summary = self._create_simple_summary(entries_to_summarize)
        else:
            self._summary = self._create_simple_summary(entries_to_summarize)
        
        # Replace summarized entries with summary entry
        self._entries = self._entries[-keep_last_n:]
        
        return self._summary
    
    def _create_simple_summary(self, entries: List[HistoryEntry]) -> ConversationSummary:
        """Create a simple summary without LLM."""
        key_points = []
        tool_calls_count = 0
        
        for entry in entries:
            if entry.tool_calls:
                tool_calls_count += len(entry.tool_calls)
                for tc in entry.tool_calls:
                    key_points.append(f"Used tool: {tc.get('name', 'unknown')}")
            elif entry.content and len(entry.content) < 200:
                key_points.append(f"{entry.role}: {entry.content[:100]}...")
        
        return ConversationSummary(
            summary=f"Previous conversation with {len(entries)} messages",
            key_points=key_points[:20],  # Limit key points
            start_time=entries[0].timestamp,
            end_time=entries[-1].timestamp,
            message_count=len(entries),
            tool_calls_count=tool_calls_count
        )
    
    def to_messages_for_llm(
        self, 
        include_summary: bool = True,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Convert history to format suitable for LLM API."""
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add summary if available and requested
        if include_summary and self._summary:
            summary_content = (
                f"Previous conversation summary:\n{self._summary.summary}\n\n"
                f"Key points:\n" + "\n".join(f"- {p}" for p in self._summary.key_points)
            )
            messages.append({"role": "system", "content": summary_content})
        
        # Add entries
        for entry in self._entries:
            msg = {"role": entry.role}
            
            if entry.tool_call_id:
                # This is a tool result
                msg["content"] = entry.content
                msg["tool_call_id"] = entry.tool_call_id
            elif entry.tool_calls:
                # This is an assistant message with tool calls
                if entry.content:
                    msg["content"] = entry.content
                msg["tool_calls"] = entry.tool_calls
            else:
                # Regular message
                msg["content"] = entry.content or ""
            
            messages.append(msg)
        
        return messages
    
    async def save(self) -> Path:
        """Save history to file."""
        filepath = self.storage_path / f"{self.session_id}.json"
        
        data = {
            "session_id": self.session_id,
            "summary": self._summary.to_dict() if self._summary else None,
            "entries": [e.to_dict() for e in self._entries]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    @classmethod
    async def load(cls, session_id: str, storage_path: Optional[str] = None) -> 'HistoryManager':
        """Load history from file."""
        manager = cls(session_id, storage_path)
        filepath = manager.storage_path / f"{session_id}.json"
        
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            manager._entries = [HistoryEntry.from_dict(e) for e in data.get("entries", [])]
            
            if data.get("summary"):
                summary_data = data["summary"]
                manager._summary = ConversationSummary(
                    summary=summary_data["summary"],
                    key_points=summary_data["key_points"],
                    start_time=datetime.fromisoformat(summary_data["start_time"]),
                    end_time=datetime.fromisoformat(summary_data["end_time"]),
                    message_count=summary_data["message_count"],
                    tool_calls_count=summary_data["tool_calls_count"]
                )
        
        return manager
    
    def set_auto_compact(self, enabled: bool, threshold: int = 50) -> None:
        """Enable/disable auto-compaction."""
        self._auto_compact_enabled = enabled
        self._max_entries_before_compact = threshold
