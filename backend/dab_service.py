"""
Database Service with MCP support via Azure Data API Builder
Supports multiple database types: SQL Server, PostgreSQL, MySQL
Uses direct database drivers as fallback when MCP is not available
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Try to import MCP SDK
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

# Database drivers - imported as needed
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    pyodbc = None

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    mysql = None


class DABService:
    """Service for database operations via MCP or direct connection"""
    
    def __init__(self):
        # MCP configuration
        self.use_mcp = os.getenv("USE_MCP", "false").lower() == "true"
        self.mcp_session: Optional[ClientSession] = None
        self.dab_command = "dab"  # Data API Builder CLI command
        
        # Direct connection fallback
        self.connection = None
        self.connection_string = os.getenv("DATABASE_CONNECTION_STRING", "")
        self.db_type = self._detect_db_type()
        
        self._is_connected = False
    
    def _detect_db_type(self) -> str:
        """Detect database type from connection string"""
        conn_str = self.connection_string.lower()
        if "server=" in conn_str or "data source=" in conn_str or "trusted_connection" in conn_str:
            return "mssql"
        elif ("host=" in conn_str or "postgresql://" in conn_str) and ("port=5432" in conn_str or "postgres" in conn_str):
            return "postgresql"
        elif ("host=" in conn_str or "mysql://" in conn_str) and ("port=3306" in conn_str or "mysql" in conn_str):
            return "mysql"
        return "mssql"  # default
    
    async def connect(self) -> bool:
        """
        Connect to the database (via MCP or direct connection)
        Returns True if connection successful, False otherwise
        """
        if self._is_connected:
            return True
        
        # Try MCP connection first if enabled
        if self.use_mcp and MCP_AVAILABLE:
            return await self._connect_mcp()
        
        # Fallback to direct connection
        return await self._connect_direct()
    
    async def _connect_mcp(self) -> bool:
        """Connect via MCP protocol with Python MCP server"""
        try:
            # Get Python executable path
            import sys
            python_exe = sys.executable
            
            # Path to our MCP server
            mcp_server_path = Path(__file__).parent / "mcp_db_server.py"
            
            if not mcp_server_path.exists():
                print(f"MCP server not found at {mcp_server_path}, falling back to direct connection")
                return await self._connect_direct()
            
            # Configure MCP server to run our Python database server
            server_params = StdioServerParameters(
                command=python_exe,
                args=[str(mcp_server_path)],
                env={**os.environ.copy()}
            )
            
            print(f"Starting MCP server: {python_exe} {mcp_server_path}")
            
            # stdio_client returns a context manager, need to use it properly
            stdio = stdio_client(server_params)
            read, write = await stdio.__aenter__()
            self.mcp_session = ClientSession(read, write)
            await self.mcp_session.initialize()
            
            print("MCP server initialized successfully")
            
            # Test the connection
            result = await self.mcp_session.call_tool("test_connection", {})
            if result and len(result.content) > 0:
                import json
                response = json.loads(result.content[0].text)
                if response.get("connected"):
                    print(f"MCP: Connected to database '{response.get('database')}'")
                    self._is_connected = True
                    return True
            
            print("MCP connection test failed, falling back to direct connection")
            return await self._connect_direct()
            
        except Exception as e:
            print(f"MCP connection failed: {str(e)}, falling back to direct connection")
            return await self._connect_direct()
    
    async def _connect_direct(self) -> bool:
        """Direct database connection using appropriate driver"""
        if self.connection:
            try:
                if self.db_type == "mssql":
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                elif self.db_type == "postgresql":
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                elif self.db_type == "mysql":
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                return True
            except:
                self.connection = None
        
        try:
            if self.db_type == "mssql":
                if not PYODBC_AVAILABLE:
                    return False
                self.connection = pyodbc.connect(self.connection_string, timeout=10)
            
            elif self.db_type == "postgresql":
                if not PSYCOPG2_AVAILABLE:
                    return False
                # Parse PostgreSQL connection string
                self.connection = psycopg2.connect(self.connection_string)
            
            elif self.db_type == "mysql":
                if not MYSQL_AVAILABLE:
                    return False
                # Parse MySQL connection string (format: host=x;database=y;user=z;password=w)
                params = {}
                for part in self.connection_string.split(';'):
                    if '=' in part:
                        key, value = part.split('=', 1)
                        key = key.strip().lower()
                        if key == 'server' or key == 'host':
                            params['host'] = value.strip()
                        elif key == 'database':
                            params['database'] = value.strip()
                        elif key == 'user' or key == 'uid':
                            params['user'] = value.strip()
                        elif key == 'password' or key == 'pwd':
                            params['password'] = value.strip()
                        elif key == 'port':
                            params['port'] = int(value.strip())
                
                self.connection = mysql.connector.connect(**params)
            
            self._is_connected = True
            return True
            
        except Exception as e:
            print(f"Failed to connect to {self.db_type} database: {str(e)}")
            self._is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the database"""
        if self.mcp_session:
            self.mcp_session = None
        
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
        
        self._is_connected = False
    
    async def execute_query(self, sql: str) -> Tuple[bool, Any]:
        """
        Execute a SQL query
        
        Args:
            sql: The SQL query to execute
            
        Returns:
            Tuple of (success: bool, result: Any)
        """
        if not self._is_connected:
            connected = await self.connect()
            if not connected:
                return False, "Not connected to database. Please check your configuration."
        
        # Use MCP if available
        if self.use_mcp and self.mcp_session:
            return await self._execute_query_mcp(sql)
        
        # Fallback to direct execution
        return await self._execute_query_direct(sql)
    
    async def _execute_query_mcp(self, sql: str) -> Tuple[bool, Any]:
        """Execute query via MCP protocol"""
        try:
            tools = await self.mcp_session.list_tools()
            execute_tool = None
            
            for tool in tools.tools:
                if "query" in tool.name.lower() or "execute" in tool.name.lower():
                    execute_tool = tool
                    break
            
            if not execute_tool:
                # Fallback to direct connection
                return await self._execute_query_direct(sql)
            
            result = await self.mcp_session.call_tool(
                name=execute_tool.name,
                arguments={"sql": sql, "query": sql}
            )
            
            if hasattr(result, 'content') and result.content:
                content = result.content[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    return True, data
            
            return True, {"data": str(result)}
            
        except Exception as e:
            print(f"MCP query execution failed: {str(e)}, falling back to direct")
            return await self._execute_query_direct(sql)
    
    async def _execute_query_direct(self, sql: str) -> Tuple[bool, Any]:
        """Execute query directly via database driver"""
    async def _execute_query_direct(self, sql: str) -> Tuple[bool, Any]:
        """Execute query directly via database driver"""
        if not self.connection:
            return False, "Database connection not available"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)
            
            # Check if query returns results
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    row_dict = {}
                    for i, column_name in enumerate(columns):
                        value = row[i]
                        if value is None:
                            row_dict[column_name] = None
                        elif isinstance(value, (bytes, bytearray)):
                            row_dict[column_name] = value.hex()
                        elif hasattr(value, 'isoformat'):  # datetime objects
                            row_dict[column_name] = value.isoformat()
                        else:
                            row_dict[column_name] = value
                    results.append(row_dict)
                
                cursor.close()
                
                # Commit for PostgreSQL and MySQL (they don't auto-commit SELECTs in some cases)
                if self.db_type in ["postgresql", "mysql"]:
                    self.connection.commit()
                
                return True, {"data": results, "rowCount": len(results), "columns": columns}
            else:
                rowcount = cursor.rowcount
                cursor.close()
                
                if self.db_type in ["postgresql", "mysql"]:
                    self.connection.commit()
                
                return True, {"message": "Query executed successfully", "rowsAffected": rowcount}
            
        except Exception as e:
            # Rollback on error
            if self.db_type in ["postgresql", "mysql"]:
                try:
                    self.connection.rollback()
                except:
                    pass
            
            error_msg = str(e)
            if hasattr(e, 'args') and len(e.args) > 1:
                error_msg = e.args[1] if isinstance(e.args[1], str) else str(e.args[1])
            return False, f"Database error: {error_msg}"
    
    async def get_schema_info(self) -> Tuple[bool, Any]:
        """
        Get database schema information
        
        Returns:
            Tuple of (success: bool, schema_info: Any)
        """
        if not self._is_connected:
            connected = await self.connect()
            if not connected:
                return False, "Not connected to database"
        
        try:
            cursor = self.connection.cursor()
            
            # Get list of tables
            query = """
            SELECT 
                TABLE_SCHEMA,
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            
            cursor.execute(query)
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "schema": row[0],
                    "name": row[1],
                    "type": row[2],
                    "fullName": f"{row[0]}.{row[1]}"
                })
            
            cursor.close()
            return True, {"tables": tables, "tableCount": len(tables)}
            
        except Exception as e:
            return False, f"Error getting schema info: {str(e)}"
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test the database connection"""
        try:
            connected = await self.connect()
            if not connected:
                return False, "Failed to connect to database. Please check your configuration."
            
            # Test with a simple query
            if self.use_mcp and self.mcp_session:
                return True, "Connected successfully via MCP protocol"
            
            # Direct connection test
            if PYODBC_AVAILABLE and self.connection:
                cursor = self.connection.cursor()
                cursor.execute("SELECT @@VERSION as Version, DB_NAME() as CurrentDatabase")
                row = cursor.fetchone()
                version = row[0] if row else "Unknown"
                database = row[1] if row else "Unknown"
                cursor.close()
                
                version_short = version.split('\n')[0] if version else "Unknown"
                return True, f"Connected to '{database}'. Server: {version_short}"
            
            return True, "Connected successfully"
            
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def is_connected(self) -> bool:
        """Check if currently connected to database"""
        return self._is_connected


# Singleton instance
_dab_service_instance = None


def get_dab_service() -> DABService:
    """Get or create the DAB service singleton instance"""
    global _dab_service_instance
    if _dab_service_instance is None:
        _dab_service_instance = DABService()
    return _dab_service_instance
