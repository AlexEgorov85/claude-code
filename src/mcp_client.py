"""MCP (Model Context Protocol) Client implementation."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, AsyncIterator, Union
from enum import Enum
import json
import asyncio


class MCPServerStatus(str, Enum):
    """Status of an MCP server connection."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPResource:
    """An MCP resource."""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


@dataclass
class MCPPrompt:
    """An MCP prompt."""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments or []
        }


@dataclass
class MCPTool:
    """An MCP tool from a server."""
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class MCPMessage:
    """A message in MCP protocol."""
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int] = None
    
    def to_json(self) -> str:
        msg = {"jsonrpc": "2.0", "method": self.method}
        if self.params:
            msg["params"] = self.params
        if self.result is not None:
            msg["result"] = self.result
        if self.error is not None:
            msg["error"] = self.error
        if self.id is not None:
            msg["id"] = self.id
        return json.dumps(msg)
    
    @classmethod
    def from_json(cls, data: str) -> 'MCPMessage':
        obj = json.loads(data)
        return cls(
            method=obj.get("method", ""),
            params=obj.get("params", {}),
            result=obj.get("result"),
            error=obj.get("error"),
            id=obj.get("id")
        )


class BaseMCPServer(ABC):
    """Abstract base class for MCP servers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the server."""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[MCPResource]:
        """List available resources."""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> str:
        """Read a resource by URI."""
        pass
    
    @abstractmethod
    async def list_prompts(self) -> List[MCPPrompt]:
        """List available prompts."""
        pass
    
    @abstractmethod
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Get a prompt by name."""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        """List available tools."""
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool."""
        pass
    
    @property
    @abstractmethod
    def status(self) -> MCPServerStatus:
        """Current connection status."""
        pass


class StdioMCPServer(BaseMCPServer):
    """MCP server connected via stdio (subprocess)."""
    
    def __init__(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self._name = name
        self._command = command
        self._args = args
        self._env = env
        self._process: Optional[asyncio.subprocess.Process] = None
        self._status = MCPServerStatus.DISCONNECTED
        self._message_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._read_task: Optional[asyncio.Task] = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def status(self) -> MCPServerStatus:
        return self._status
    
    async def connect(self) -> None:
        """Start the MCP server process and initialize."""
        try:
            self._status = MCPServerStatus.CONNECTING
            
            self._process = await asyncio.create_subprocess_exec(
                self._command,
                *self._args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._env
            )
            
            # Start reading responses
            self._read_task = asyncio.create_task(self._read_loop())
            
            # Send initialize request
            await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "claude-code-python",
                    "version": "1.0.0"
                }
            })
            
            # Send initialized notification
            await self._send_notification("notifications/initialized")
            
            self._status = MCPServerStatus.CONNECTED
        except Exception as e:
            self._status = MCPServerStatus.ERROR
            raise RuntimeError(f"Failed to connect to MCP server: {str(e)}")
    
    async def disconnect(self) -> None:
        """Stop the MCP server process."""
        self._status = MCPServerStatus.DISCONNECTED
        
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
        
        self._process = None
        self._read_task = None
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Any:
        """Send a JSON-RPC request."""
        self._message_id += 1
        msg_id = self._message_id
        
        future = asyncio.Future()
        self._pending_requests[msg_id] = future
        
        msg = MCPMessage(method=method, params=params or {}, id=msg_id)
        await self._send_message(msg)
        
        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            del self._pending_requests[msg_id]
            raise
    
    async def _send_notification(self, method: str, params: Dict[str, Any] = None) -> None:
        """Send a JSON-RPC notification."""
        msg = MCPMessage(method=method, params=params or {})
        await self._send_message(msg)
    
    async def _send_message(self, msg: MCPMessage) -> None:
        """Send a message to the server."""
        if not self._process or not self._process.stdin:
            raise RuntimeError("Not connected")
        
        data = msg.to_json() + "\n"
        self._process.stdin.write(data.encode('utf-8'))
        await self._process.stdin.drain()
    
    async def _read_loop(self) -> None:
        """Read responses from the server."""
        if not self._process or not self._process.stdout:
            return
        
        buffer = ""
        while True:
            try:
                chunk = await self._process.stdout.read(4096)
                if not chunk:
                    break
                
                buffer += chunk.decode('utf-8')
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        await self._handle_message(line)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error reading from MCP server: {e}")
                break
    
    async def _handle_message(self, data: str) -> None:
        """Handle an incoming message."""
        try:
            msg = MCPMessage.from_json(data)
            
            if msg.id is not None:
                # This is a response
                if msg.id in self._pending_requests:
                    future = self._pending_requests.pop(msg.id)
                    if msg.error:
                        future.set_exception(Exception(msg.error.get("message", "Unknown error")))
                    else:
                        future.set_result(msg.result)
        except Exception as e:
            print(f"Error handling MCP message: {e}")
    
    async def list_resources(self) -> List[MCPResource]:
        """List available resources."""
        result = await self._send_request("resources/list")
        return [
            MCPResource(
                uri=r["uri"],
                name=r["name"],
                description=r.get("description"),
                mime_type=r.get("mimeType")
            )
            for r in result.get("resources", [])
        ]
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource by URI."""
        result = await self._send_request("resources/read", {"uri": uri})
        contents = result.get("contents", [])
        if contents:
            return contents[0].get("text", "")
        return ""
    
    async def list_prompts(self) -> List[MCPPrompt]:
        """List available prompts."""
        result = await self._send_request("prompts/list")
        return [
            MCPPrompt(
                name=p["name"],
                description=p.get("description"),
                arguments=p.get("arguments")
            )
            for p in result.get("prompts", [])
        ]
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Get a prompt by name."""
        result = await self._send_request("prompts/get", {
            "name": name,
            "arguments": arguments or {}
        })
        messages = result.get("messages", [])
        if messages:
            return messages[0].get("content", {}).get("text", "")
        return ""
    
    async def list_tools(self) -> List[MCPTool]:
        """List available tools."""
        result = await self._send_request("tools/list")
        return [
            MCPTool(
                name=t["name"],
                description=t.get("description"),
                input_schema=t.get("inputSchema", {})
            )
            for t in result.get("tools", [])
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool."""
        result = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        return result.get("content")


class HTTPMCPServer(BaseMCPServer):
    """MCP server connected via HTTP/SSE."""
    
    def __init__(self, name: str, url: str, headers: Optional[Dict[str, str]] = None):
        self._name = name
        self._url = url
        self._headers = headers or {}
        self._status = MCPServerStatus.DISCONNECTED
        self._session = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def status(self) -> MCPServerStatus:
        return self._status
    
    async def connect(self) -> None:
        """Connect to the HTTP MCP server."""
        try:
            self._status = MCPServerStatus.CONNECTING
            
            import aiohttp
            self._session = aiohttp.ClientSession(headers=self._headers)
            
            # Initialize
            async with self._session.post(
                f"{self._url}/initialize",
                json={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "claude-code-python",
                        "version": "1.0.0"
                    }
                }
            ) as resp:
                await resp.json()
            
            self._status = MCPServerStatus.CONNECTED
        except Exception as e:
            self._status = MCPServerStatus.ERROR
            raise RuntimeError(f"Failed to connect to HTTP MCP server: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from the server."""
        self._status = MCPServerStatus.DISCONNECTED
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _request(self, method: str, params: Dict[str, Any] = None) -> Any:
        """Make an HTTP request."""
        if not self._session:
            raise RuntimeError("Not connected")
        
        async with self._session.post(
            f"{self._url}/{method}",
            json=params or {}
        ) as resp:
            result = await resp.json()
            return result
    
    async def list_resources(self) -> List[MCPResource]:
        result = await self._request("resources/list")
        return [
            MCPResource(uri=r["uri"], name=r["name"])
            for r in result.get("resources", [])
        ]
    
    async def read_resource(self, uri: str) -> str:
        result = await self._request("resources/read", {"uri": uri})
        contents = result.get("contents", [])
        return contents[0].get("text", "") if contents else ""
    
    async def list_prompts(self) -> List[MCPPrompt]:
        result = await self._request("prompts/list")
        return [
            MCPPrompt(name=p["name"], description=p.get("description"))
            for p in result.get("prompts", [])
        ]
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        result = await self._request("prompts/get", {"name": name, "arguments": arguments or {}})
        messages = result.get("messages", [])
        return messages[0].get("content", {}).get("text", "") if messages else ""
    
    async def list_tools(self) -> List[MCPTool]:
        result = await self._request("tools/list")
        return [
            MCPTool(name=t["name"], description=t.get("description"), input_schema=t.get("inputSchema", {}))
            for t in result.get("tools", [])
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        result = await self._request("tools/call", {"name": name, "arguments": arguments})
        return result.get("content")


class MCPClient:
    """Client for managing multiple MCP servers."""
    
    def __init__(self):
        self._servers: Dict[str, BaseMCPServer] = {}
    
    def add_server(self, server: BaseMCPServer) -> None:
        """Add an MCP server."""
        self._servers[server.name] = server
    
    def remove_server(self, name: str) -> bool:
        """Remove an MCP server."""
        if name in self._servers:
            del self._servers[name]
            return True
        return False
    
    def get_server(self, name: str) -> Optional[BaseMCPServer]:
        """Get a server by name."""
        return self._servers.get(name)
    
    def get_all_servers(self) -> List[BaseMCPServer]:
        """Get all servers."""
        return list(self._servers.values())
    
    async def connect_all(self) -> None:
        """Connect to all servers."""
        await asyncio.gather(*[s.connect() for s in self._servers.values()], return_exceptions=True)
    
    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        await asyncio.gather(*[s.disconnect() for s in self._servers.values()], return_exceptions=True)
    
    async def list_all_resources(self) -> List[MCPResource]:
        """List resources from all servers."""
        results = await asyncio.gather(
            *[s.list_resources() for s in self._servers.values()],
            return_exceptions=True
        )
        resources = []
        for result in results:
            if isinstance(result, list):
                resources.extend(result)
        return resources
    
    async def list_all_tools(self) -> List[MCPTool]:
        """List tools from all servers."""
        results = await asyncio.gather(
            *[s.list_tools() for s in self._servers.values()],
            return_exceptions=True
        )
        tools = []
        for result in results:
            if isinstance(result, list):
                tools.extend(result)
        return tools
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on a specific server."""
        server = self.get_server(server_name)
        if not server:
            raise ValueError(f"Unknown server: {server_name}")
        return await server.call_tool(tool_name, arguments)
