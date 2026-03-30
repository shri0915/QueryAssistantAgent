"""
FastAPI Backend for Query Assistant Agent
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv
import uvicorn
from pathlib import Path

from llm_service import LLMService
from schema_parser import SchemaParser
from dab_service import get_dab_service

# Load environment variables
load_dotenv()

app = FastAPI(title="Query Assistant Agent")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()
schema_parser = SchemaParser()
dab_service = get_dab_service()

# Frontend directory path
frontend_dir = Path(__file__).parent.parent / "frontend"

# In-memory storage for schema and conversation history
# In production, use a proper database
storage = {
    "schema": None,
    "schema_filename": None,
    "conversations": {}  # session_id -> conversation history
}

# Pydantic models
class ChatRequest(BaseModel):
    question: str
    model: str = "openai"  # "openai" or "gemini"
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    query: str
    explanation: Optional[str] = None
    tables_used: Optional[List[str]] = None
    confidence: Optional[str] = None
    model_used: str
    success: bool
    error: Optional[str] = None

class SchemaInfo(BaseModel):
    filename: Optional[str]
    has_schema: bool
    table_count: int
    tables: List[str]

class ModelAvailability(BaseModel):
    openai: bool
    gemini: bool
    openai_model: Optional[str] = None
    gemini_model: Optional[str] = None

class ExecuteQueryRequest(BaseModel):
    sql: str
    session_id: Optional[str] = "default"

class ExecuteQueryResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    row_count: Optional[int] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None

class DatabaseConnectionStatus(BaseModel):
    connected: bool
    message: str


# Mount static files for frontend
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/")
async def read_root():
    """Serve the frontend HTML"""
    frontend_path = frontend_dir / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "Query Assistant Agent API is running"}


@app.get("/styles.css")
async def get_styles():
    """Serve CSS file"""
    css_path = frontend_dir / "styles.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return {"error": "CSS file not found"}


@app.get("/script.js")
async def get_script():
    """Serve JavaScript file"""
    js_path = frontend_dir / "script.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    return {"error": "JavaScript file not found"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "openai_configured": llm_service.is_openai_available(),
        "gemini_configured": llm_service.is_gemini_available()
    }


@app.get("/api/models", response_model=ModelAvailability)
async def get_available_models():
    """Get available AI models"""
    return ModelAvailability(
        openai=llm_service.is_openai_available(),
        gemini=llm_service.is_gemini_available(),
        openai_model=llm_service.openai_model,
        gemini_model=llm_service.gemini_model_name
    )


@app.post("/api/upload-schema")
async def upload_schema(file: UploadFile = File(...)):
    """Upload and parse database schema file"""
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Parse schema
        parsed_schema = schema_parser.parse_schema(text_content, file.filename)
        
        # Validate schema
        is_valid, error_msg = schema_parser.validate_schema(parsed_schema)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Store schema
        storage["schema"] = parsed_schema
        storage["schema_filename"] = file.filename
        storage["conversations"] = {}  # Reset conversations when new schema is uploaded
        
        # Extract table info
        tables = schema_parser.extract_table_names(parsed_schema)
        
        return {
            "success": True,
            "filename": file.filename,
            "table_count": len(tables),
            "tables": tables,
            "message": f"Schema uploaded successfully. Found {len(tables)} tables."
        }
    
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be a text file (UTF-8 encoded)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing schema: {str(e)}")


@app.get("/api/schema-info", response_model=SchemaInfo)
async def get_schema_info():
    """Get current schema information"""
    has_schema = storage["schema"] is not None
    tables = []
    
    if has_schema:
        tables = schema_parser.extract_table_names(storage["schema"])
    
    return SchemaInfo(
        filename=storage["schema_filename"],
        has_schema=has_schema,
        table_count=len(tables),
        tables=tables
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process natural language question and return SQL query"""
    try:
        # Check if schema is uploaded
        if not storage["schema"]:
            raise HTTPException(
                status_code=400, 
                detail="Please upload a database schema first"
            )
        
        # Check if selected model is available
        if request.model == "openai" and not llm_service.is_openai_available():
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in .env file"
            )
        
        if request.model == "gemini" and not llm_service.is_gemini_available():
            raise HTTPException(
                status_code=400,
                detail="Gemini API key not configured. Please set GEMINI_API_KEY in .env file"
            )
        
        # Get or create conversation history
        session_id = request.session_id or "default"
        if session_id not in storage["conversations"]:
            storage["conversations"][session_id] = []
        
        conversation_history = storage["conversations"][session_id]
        
        # Generate SQL query
        response_data = await llm_service.generate_query(
            question=request.question,
            schema=storage["schema"],
            model=request.model,
            conversation_history=conversation_history
        )
        
        # Extract SQL and metadata
        sql_query = response_data.get("sql", "")
        explanation = response_data.get("explanation", "")
        tables_used = response_data.get("tables_used", [])
        confidence = response_data.get("confidence", "medium")
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": request.question})
        conversation_history.append({"role": "assistant", "content": sql_query})
        
        # Keep only last 10 messages to prevent context from growing too large
        if len(conversation_history) > 10:
            storage["conversations"][session_id] = conversation_history[-10:]
        
        return ChatResponse(
            query=sql_query,
            explanation=explanation,
            tables_used=tables_used,
            confidence=confidence,
            model_used=request.model,
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return ChatResponse(
            query="",
            model_used=request.model,
            success=False,
            error=str(e)
        )


@app.delete("/api/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session"""
    if session_id in storage["conversations"]:
        del storage["conversations"][session_id]
    return {"success": True, "message": "Conversation history cleared"}


@app.delete("/api/schema")
async def delete_schema():
    """Delete current schema"""
    storage["schema"] = None
    storage["schema_filename"] = None
    storage["conversations"] = {}
    return {"success": True, "message": "Schema deleted"}


@app.get("/api/database/test-connection", response_model=DatabaseConnectionStatus)
async def test_database_connection():
    """Test connection to the database via DAB MCP server"""
    try:
        success, message = await dab_service.test_connection()
        return DatabaseConnectionStatus(connected=success, message=message)
    except Exception as e:
        return DatabaseConnectionStatus(
            connected=False, 
            message=f"Connection test failed: {str(e)}"
        )


@app.post("/api/database/execute", response_model=ExecuteQueryResponse)
async def execute_query(request: ExecuteQueryRequest):
    """Execute SQL query against the database via DAB MCP server"""
    import time
    
    try:
        # Check if query is provided
        if not request.sql or not request.sql.strip():
            raise HTTPException(status_code=400, detail="SQL query is required")
        
        # Start timing
        start_time = time.time()
        
        # Execute the query
        success, result = await dab_service.execute_query(request.sql)
        
        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        if not success:
            return ExecuteQueryResponse(
                success=False,
                error=str(result),
                execution_time_ms=execution_time
            )
        
        # Determine row count if possible
        row_count = None
        if isinstance(result, dict):
            if "data" in result and isinstance(result["data"], list):
                row_count = len(result["data"])
            elif "rows" in result:
                row_count = len(result["rows"]) if isinstance(result["rows"], list) else None
        elif isinstance(result, list):
            row_count = len(result)
        
        return ExecuteQueryResponse(
            success=True,
            data=result,
            row_count=row_count,
            execution_time_ms=round(execution_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ExecuteQueryResponse(
            success=False,
            error=f"Query execution failed: {str(e)}"
        )


@app.get("/api/database/schema")
async def get_database_schema():
    """Get schema information from the database via DAB MCP server"""
    try:
        success, schema_info = await dab_service.get_schema_info()
        
        if not success:
            return {"success": False, "error": str(schema_info)}
        
        return {"success": True, "schema": schema_info}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get schema: {str(e)}"}


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║         Query Assistant Agent - Server Starting          ║
╚══════════════════════════════════════════════════════════╝

Server: http://{host}:{port}
API Docs: http://{host}:{port}/docs

OpenAI: {'✓ Configured' if llm_service.is_openai_available() else '✗ Not configured'}
Gemini: {'✓ Configured' if llm_service.is_gemini_available() else '✗ Not configured'}
DAB MCP: Ready (test connection via API)

""")
    
    uvicorn.run(app, host=host, port=port)
