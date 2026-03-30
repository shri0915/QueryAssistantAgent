#!/usr/bin/env python3
"""
Simple MCP Server for Database Operations
This provides an MCP interface to SQL Server database
"""
import asyncio
import os
import json
from typing import Any
import pyodbc
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Create the MCP server
app = Server("database-mcp-server")

# Database connection
db_connection = None
connection_string = None

def get_connection():
    """Get or create database connection"""
    global db_connection, connection_string
    
    if connection_string is None:
        connection_string = os.getenv("DATABASE_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("DATABASE_CONNECTION_STRING environment variable not set")
    
    if db_connection is None:
        try:
            db_connection = pyodbc.connect(connection_string, timeout=10)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {str(e)}")
    
    return db_connection

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="execute_query",
            description="Execute a SQL query against the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_schema",
            description="Get database schema information",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="test_connection",
            description="Test the database connection",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "execute_query":
            query = arguments.get("query")
            if not query:
                return [TextContent(type="text", text=json.dumps({"error": "No query provided"}))]
            
            conn = get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute(query)
                
                # Check if it's a SELECT query
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = []
                    for row in cursor.fetchall():
                        rows.append([str(val) if val is not None else None for val in row])
                    
                    result = {
                        "success": True,
                        "columns": columns,
                        "rows": rows,
                        "rowCount": len(rows)
                    }
                else:
                    # For INSERT/UPDATE/DELETE
                    conn.commit()
                    result = {
                        "success": True,
                        "rowsAffected": cursor.rowcount
                    }
                
                return [TextContent(type="text", text=json.dumps(result))]
                
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({
                    "success": False,
                    "error": str(e)
                }))]
            finally:
                cursor.close()
        
        elif name == "get_schema":
            conn = get_connection()
            cursor = conn.cursor()
            
            try:
                # Get all tables
                cursor.execute("""
                    SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """)
                
                tables = []
                for row in cursor.fetchall():
                    schema, table_name, table_type = row
                    tables.append({
                        "schema": schema,
                        "name": table_name,
                        "type": table_type
                    })
                
                result = {
                    "success": True,
                    "database": conn.getinfo(pyodbc.SQL_DATABASE_NAME),
                    "tables": tables
                }
                
                return [TextContent(type="text", text=json.dumps(result))]
                
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({
                    "success": False,
                    "error": str(e)
                }))]
            finally:
                cursor.close()
        
        elif name == "test_connection":
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT DB_NAME(), @@VERSION")
                row = cursor.fetchone()
                db_name = row[0]
                version = row[1]
                cursor.close()
                
                result = {
                    "success": True,
                    "connected": True,
                    "database": db_name,
                    "version": version
                }
                
                return [TextContent(type="text", text=json.dumps(result))]
                
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({
                    "success": False,
                    "connected": False,
                    "error": str(e)
                }))]
        
        else:
            return [TextContent(type="text", text=json.dumps({
                "error": f"Unknown tool: {name}"
            }))]
    
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "error": str(e)
        }))]

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
