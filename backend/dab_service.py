"""
DAB (Data API Builder) MCP Service for database operations
Uses Azure Data API Builder MCP server to execute queries
"""
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class DABService:
    """Service for interacting with Azure Data API Builder via MCP"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.dab_config_path = os.getenv("DAB_CONFIG_PATH", "./dab-config.json")
        self.dab_server_command = os.getenv("DAB_SERVER_COMMAND", "npx")
        self.dab_server_args = os.getenv("DAB_SERVER_ARGS", "@azure/data-api-builder-mcp").split()
        self._is_connected = False
    
    async def connect(self) -> bool:
        """
        Connect to the DAB MCP server
        Returns True if connection successful, False otherwise
        """
        if self._is_connected and self.session:
            return True
        
        try:
            # Configure the MCP server parameters
            server_params = StdioServerParameters(
                command=self.dab_server_command,
                args=self.dab_server_args,
                env={
                    **os.environ.copy(),
                    "DAB_CONFIG": self.dab_config_path
                }
            )
            
            # Create stdio client connection
            self.read, self.write = await stdio_client(server_params)
            self.session = ClientSession(self.read, self.write)
            
            # Initialize the session
            await self.session.initialize()
            
            self._is_connected = True
            return True
            
        except Exception as e:
            print(f"Failed to connect to DAB MCP server: {str(e)}")
            self._is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the DAB MCP server"""
        if self.session:
            # MCP sessions are typically managed by context managers
            # In this case, we'll just mark as disconnected
            self._is_connected = False
            self.session = None
    
    async def execute_query(self, sql: str) -> Tuple[bool, Any]:
        """
        Execute a SQL query via DAB MCP server
        
        Args:
            sql: The SQL query to execute
            
        Returns:
            Tuple of (success: bool, result: Any)
            - If success=True, result contains the query results
            - If success=False, result contains the error message
        """
        if not self._is_connected:
            connected = await self.connect()
            if not connected:
                return False, "Not connected to database. Please check DAB MCP server configuration."
        
        try:
            # List available tools from the MCP server
            tools_response = await self.session.list_tools()
            
            # Find the execute-query tool (DAB MCP provides this)
            execute_tool = None
            for tool in tools_response.tools:
                if tool.name == "execute-query" or "query" in tool.name.lower():
                    execute_tool = tool
                    break
            
            if not execute_tool:
                return False, "DAB MCP server does not provide query execution tool"
            
            # Call the tool to execute the query
            result = await self.session.call_tool(
                name=execute_tool.name,
                arguments={"query": sql}
            )
            
            # Parse the result
            if result.isError:
                return False, f"Query execution error: {result.content}"
            
            # Extract data from result
            query_result = self._parse_tool_result(result)
            return True, query_result
            
        except Exception as e:
            return False, f"Error executing query: {str(e)}"
    
    def _parse_tool_result(self, result) -> Dict[str, Any]:
        """Parse the MCP tool result into a structured format"""
        try:
            # MCP tool results come back as content blocks
            if hasattr(result, 'content') and len(result.content) > 0:
                content = result.content[0]
                
                # If it's text content, try to parse as JSON
                if hasattr(content, 'text'):
                    try:
                        return json.loads(content.text)
                    except json.JSONDecodeError:
                        return {"raw": content.text}
                
                # Return the content as-is
                return {"data": content}
            
            return {"data": str(result)}
            
        except Exception as e:
            return {"error": f"Failed to parse result: {str(e)}"}
    
    async def get_schema_info(self) -> Tuple[bool, Any]:
        """
        Get database schema information from DAB MCP server
        
        Returns:
            Tuple of (success: bool, schema_info: Any)
        """
        if not self._is_connected:
            connected = await self.connect()
            if not connected:
                return False, "Not connected to database"
        
        try:
            # List available resources from the MCP server
            resources_response = await self.session.list_resources()
            
            # DAB MCP exposes database schema as resources
            schema_resources = []
            for resource in resources_response.resources:
                if "schema" in resource.name.lower() or "table" in resource.name.lower():
                    schema_resources.append({
                        "name": resource.name,
                        "uri": resource.uri,
                        "description": getattr(resource, 'description', '')
                    })
            
            return True, {"resources": schema_resources}
            
        except Exception as e:
            return False, f"Error getting schema info: {str(e)}"
    
    async def test_connection(self) -> Tuple[bool, str]:
        """
        Test the connection to DAB MCP server
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            connected = await self.connect()
            if not connected:
                return False, "Failed to connect to DAB MCP server"
            
            # Try to list tools as a connection test
            tools_response = await self.session.list_tools()
            tool_count = len(tools_response.tools)
            
            return True, f"Connected successfully. Found {tool_count} available tools."
            
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def is_connected(self) -> bool:
        """Check if currently connected to DAB MCP server"""
        return self._is_connected


# Singleton instance
_dab_service_instance = None


def get_dab_service() -> DABService:
    """Get or create the DAB service singleton instance"""
    global _dab_service_instance
    if _dab_service_instance is None:
        _dab_service_instance = DABService()
    return _dab_service_instance
