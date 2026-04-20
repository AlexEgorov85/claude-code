"""Comprehensive test suite for the agent core components."""
import asyncio
import pytest
from typing import List, Dict, Any


# ==================== LLM Client Tests ====================

class TestLLMClient:
    """Tests for LLM client components."""
    
    @pytest.mark.asyncio
    async def test_mock_llm_chat(self):
        """Test mock LLM client chat functionality."""
        from src.llm_clients import MockLLMClient
        from src.llm_client import LLMResponse, FinishReason, LLMMessage, MessageRole
        
        expected_response = LLMResponse(
            content="Hello, I'm a mock response",
            finish_reason=FinishReason.STOP
        )
        
        client = MockLLMClient(responses=[expected_response])
        messages = [LLMMessage(role=MessageRole.USER, content="Test message")]
        
        response = await client.chat(messages)
        
        assert response.content == "Hello, I'm a mock response"
        assert response.finish_reason == FinishReason.STOP
        assert client.call_count == 1
    
    @pytest.mark.asyncio
    async def test_mock_llm_stream(self):
        """Test mock LLM client streaming."""
        from src.llm_clients import MockLLMClient
        from src.llm_client import LLMResponse, FinishReason, LLMMessage, MessageRole
        
        expected_response = LLMResponse(
            content="Streaming response",
            finish_reason=FinishReason.STOP
        )
        
        client = MockLLMClient(responses=[expected_response])
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        chunks = []
        async for chunk in client.chat_stream(messages):
            chunks.append(chunk)
        
        assert len(chunks) >= 2  # At least content and finish chunks
        assert any(c.content == "Streaming response" for c in chunks)
        assert any(c.is_complete for c in chunks)
    
    @pytest.mark.asyncio
    async def test_token_estimation(self):
        """Test token estimation."""
        from src.llm_clients import MockLLMClient
        from src.llm_client import LLMMessage, MessageRole
        
        client = MockLLMClient()
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello world"),
            LLMMessage(role=MessageRole.ASSISTANT, content="Hi there")
        ]
        
        tokens = await client.estimate_tokens(messages)
        assert tokens > 0


# ==================== Cost Tracker Tests ====================

class TestCostTracker:
    """Tests for cost tracking."""
    
    def test_record_usage(self):
        """Test recording token usage."""
        from src.llm_client import CostTracker
        
        tracker = CostTracker()
        usage = {"input_tokens": 100, "output_tokens": 50}
        
        session_usage = tracker.record_usage("session1", usage)
        
        assert session_usage.input_tokens == 100
        assert session_usage.output_tokens == 50
        assert session_usage.total_tokens == 150
    
    def test_cost_calculation(self):
        """Test cost calculation."""
        from src.llm_client import CostTracker
        
        tracker = CostTracker()
        tracker.record_usage("session1", {"input_tokens": 1000000, "output_tokens": 500000})
        
        cost = tracker.get_session_cost("session1")
        assert cost > 0
    
    def test_multiple_sessions(self):
        """Test tracking multiple sessions."""
        from src.llm_client import CostTracker
        
        tracker = CostTracker()
        tracker.record_usage("session1", {"input_tokens": 100, "output_tokens": 50})
        tracker.record_usage("session2", {"input_tokens": 200, "output_tokens": 100})
        
        assert tracker.get_session_cost("session1") < tracker.get_session_cost("session2")
        assert tracker.get_total_cost() > 0
    
    def test_reset(self):
        """Test resetting usage."""
        from src.llm_client import CostTracker
        
        tracker = CostTracker()
        tracker.record_usage("session1", {"input_tokens": 100, "output_tokens": 50})
        tracker.reset_session("session1")
        
        assert tracker.get_session_cost("session1") == 0


# ==================== Tool Tests ====================

class TestTools:
    """Tests for tools system."""
    
    @pytest.mark.asyncio
    async def test_read_file_tool(self):
        """Test read file tool."""
        from src.tools import ReadFileTool
        import tempfile
        import os
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content\nLine 2")
            temp_path = f.name
        
        try:
            tool = ReadFileTool()
            result = await tool.execute(path=temp_path)
            
            assert "Test content" in result
            assert "Line 2" in result
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_write_file_tool(self):
        """Test write file tool."""
        from src.tools import WriteFileTool
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "test.txt")
        
        try:
            tool = WriteFileTool()
            result = await tool.execute(path=temp_path, content="Test write content")
            
            assert "Successfully wrote" in result
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
            assert content == "Test write content"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            os.rmdir(temp_dir)
    
    @pytest.mark.asyncio
    async def test_bash_tool(self):
        """Test bash tool."""
        from src.tools import BashTool
        
        tool = BashTool()
        result = await tool.execute(command="echo 'Hello World'")
        
        assert result["exit_code"] == 0
        assert "Hello World" in result["stdout"]
    
    @pytest.mark.asyncio
    async def test_list_dir_tool(self):
        """Test list directory tool."""
        from src.tools import ListDirTool
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp()
        
        # Create some files
        open(os.path.join(temp_dir, "file1.txt"), 'w').close()
        open(os.path.join(temp_dir, "file2.txt"), 'w').close()
        os.mkdir(os.path.join(temp_dir, "subdir"))
        
        try:
            tool = ListDirTool()
            result = await tool.execute(path=temp_dir)
            
            assert len(result) >= 3
            names = [item["name"] for item in result]
            assert "file1.txt" in names
            assert "file2.txt" in names
            assert "subdir" in names
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_tool_registry(self):
        """Test tool registry."""
        from src.tools import ToolRegistry, ReadFileTool
        
        registry = ToolRegistry()
        
        # Check default tools are registered
        assert registry.get("read_file") is not None
        assert registry.get("write_file") is not None
        assert registry.get("bash") is not None
        
        # Get definitions
        definitions = registry.get_definitions_dict()
        assert len(definitions) >= 5
        
        # Execute a tool
        result = await registry.execute("read_file", "call_1", {"path": "/nonexistent"})
        assert not result.success
        assert "error" in result.error.lower() or "not found" in result.error.lower()


# ==================== History Manager Tests ====================

class TestHistoryManager:
    """Tests for history management."""
    
    def test_add_entry(self):
        """Test adding entries to history."""
        from src.history import HistoryManager
        
        manager = HistoryManager("test_session")
        entry = manager.add_entry("user", content="Hello")
        
        assert entry.role == "user"
        assert entry.content == "Hello"
        assert manager.message_count == 1
    
    def test_get_entries(self):
        """Test retrieving entries."""
        from src.history import HistoryManager
        
        manager = HistoryManager("test_session")
        manager.add_entry("user", content="Hello")
        manager.add_entry("assistant", content="Hi there")
        manager.add_entry("user", content="How are you?")
        
        all_entries = manager.get_all()
        assert len(all_entries) == 3
        
        last_two = manager.get_last_n(2)
        assert len(last_two) == 2
        assert last_two[0].content == "Hi there"
    
    def test_token_estimation(self):
        """Test token estimation for history."""
        from src.history import HistoryManager
        
        manager = HistoryManager("test_session")
        manager.add_entry("user", content="Hello world " * 10)
        
        tokens = manager.estimate_tokens()
        assert tokens > 0
    
    def test_clear_history(self):
        """Test clearing history."""
        from src.history import HistoryManager
        
        manager = HistoryManager("test_session")
        manager.add_entry("user", content="Hello")
        manager.clear()
        
        assert manager.message_count == 0
    
    @pytest.mark.asyncio
    async def test_save_and_load(self, tmp_path):
        """Test saving and loading history."""
        from src.history import HistoryManager
        
        # Create and save
        manager1 = HistoryManager("test_session", str(tmp_path))
        manager1.add_entry("user", content="Hello")
        manager1.add_entry("assistant", content="Hi")
        await manager1.save()
        
        # Load
        manager2 = await HistoryManager.load("test_session", str(tmp_path))
        
        assert manager2.message_count == 2
        assert manager2.get_last_n(1)[0].content == "Hi"
    
    @pytest.mark.asyncio
    async def test_compact_history(self):
        """Test history compaction."""
        from src.history import HistoryManager
        
        manager = HistoryManager("test_session")
        
        # Add many entries
        for i in range(10):
            manager.add_entry("user", content=f"Message {i}")
            manager.add_entry("assistant", content=f"Response {i}")
        
        # Compact keeping last 3
        summary = await manager.compact(keep_last_n=3)
        
        assert summary is not None
        assert summary.message_count > 0
        assert manager.message_count == 3


# ==================== MCP Client Tests ====================

class TestMCPClient:
    """Tests for MCP client."""
    
    def test_mcp_server_creation(self):
        """Test creating MCP server instances."""
        from src.mcp_client import StdioMCPServer, HTTPMCPServer, MCPServerStatus
        
        stdio_server = StdioMCPServer("test", "echo", [])
        assert stdio_server.name == "test"
        assert stdio_server.status == MCPServerStatus.DISCONNECTED
        
        http_server = HTTPMCPServer("http_test", "http://localhost:8080")
        assert http_server.name == "http_test"
    
    def test_mcp_client_management(self):
        """Test MCP client server management."""
        from src.mcp_client import MCPClient, StdioMCPServer
        
        client = MCPClient()
        server = StdioMCPServer("test", "echo", [])
        
        client.add_server(server)
        assert client.get_server("test") == server
        assert len(client.get_all_servers()) == 1
        
        client.remove_server("test")
        assert client.get_server("test") is None


# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests for the agent system."""
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test a complete conversation flow with mock LLM."""
        from src.llm_clients import MockLLMClient
        from src.llm_client import LLMResponse, FinishReason, LLMMessage, MessageRole, ToolCall
        from src.tools import ToolRegistry
        from src.history import HistoryManager
        
        # Setup
        llm = MockLLMClient(responses=[
            LLMResponse(
                content=None,
                tool_calls=[ToolCall(id="call_1", name="bash", arguments={"command": "echo hello"})],
                finish_reason=FinishReason.TOOL_CALLS
            ),
            LLMResponse(
                content="The command output is: hello",
                finish_reason=FinishReason.STOP
            )
        ])
        
        tool_registry = ToolRegistry()
        history = HistoryManager("integration_test")
        
        # Simulate conversation
        user_message = "Run echo hello"
        history.add_entry("user", content=user_message)
        
        # First LLM call - should return tool call
        messages = history.to_messages_for_llm(include_summary=False)
        response1 = await llm.chat(messages)
        
        assert response1.has_tool_calls
        assert len(response1.tool_calls) == 1
        
        # Execute tool
        tool_call = response1.tool_calls[0]
        tool_result = await tool_registry.execute(
            tool_call.name,
            tool_call.id,
            tool_call.arguments
        )
        
        # Add tool result to history
        history.add_entry(
            "assistant",
            tool_calls=[tool_call.to_dict()]
        )
        history.add_entry(
            "user",
            content=tool_result.to_content(),
            tool_call_id=tool_call.id
        )
        
        # Second LLM call - should return final response
        messages = history.to_messages_for_llm(include_summary=False)
        response2 = await llm.chat(messages)
        
        assert response2.content is not None
        history.add_entry("assistant", content=response2.content)
        
        # Verify history
        assert history.message_count >= 4


def run_tests():
    """Run all tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
