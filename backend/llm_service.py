"""
LLM Service for handling OpenAI and Gemini API interactions
"""
import os
import re
import json
from typing import Optional, List, Dict, Tuple
from openai import OpenAI
from pydantic import BaseModel, Field

# Try to import Gemini, but make it optional
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


class SQLResponse(BaseModel):
    """Structured response model for SQL query generation"""
    sql: str = Field(..., description="The generated SQL query")
    explanation: str = Field(..., description="Brief explanation of what the query does")
    tables_used: List[str] = Field(default_factory=list, description="List of tables referenced in the query")
    confidence: str = Field(default="high", description="Confidence level: high, medium, or low")


class LLMService:
    MAX_RETRIES = 3

    # SQL keywords that indicate write / destructive operations
    _DANGEROUS_KEYWORDS = re.compile(
        r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|MERGE|'
        r'RENAME|GRANT|REVOKE|EXEC|EXECUTE|CALL|INTO)\b',
        re.IGNORECASE,
    )

    def __init__(self):
        self.openai_client = None
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-5.2-chat-latest")
        self.gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.gemini_model = None
        
        # Initialize OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your_openai_api_key_here":
            self.openai_client = OpenAI(api_key=openai_key)
        
        # Initialize Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if GEMINI_AVAILABLE and gemini_key and gemini_key != "your_gemini_api_key_here":
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel(self.gemini_model_name)
    
    def create_system_prompt(self, schema: str, database_type: str = "mssql") -> str:
        """Create system prompt with database schema and database type"""
        
        # Database-specific syntax notes
        db_syntax = {
            "mssql": "SQL Server (T-SQL) syntax. USE: GETDATE(), TOP n, DATEDIFF(), DATEADD(), LEN(), etc.",
            "postgresql": "PostgreSQL syntax. USE: NOW(), CURRENT_DATE, LIMIT n, DATE_TRUNC(), LENGTH(), etc.",
            "mysql": "MySQL syntax. USE: NOW(), CURDATE(), LIMIT n, DATEDIFF(), DATE_ADD(), LENGTH(), etc."
        }
        
        syntax_note = db_syntax.get(database_type, db_syntax["mssql"])
        
        return f"""You are a SQL query assistant. Your task is to convert natural language questions into SQL queries based on the provided database schema.

Database Type: {database_type.upper()}
Syntax: {syntax_note}

Database Schema:
{schema}

Rules:
1. Only generate valid **SELECT / read-only** SQL queries based on the schema provided
2. **NEVER** generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, or any other write / destructive statement
3. Use proper {database_type.upper()} SQL syntax (NOT other database dialects)
4. Include appropriate JOINs when needed
5. Use clear table and column names from the schema
6. Add comments to explain complex queries
7. If the question cannot be answered with the given schema, explain why

You must respond with a JSON object in this exact format:
{{
  "sql": "your SQL query here",
  "explanation": "brief explanation of what the query does",
  "tables_used": ["table1", "table2"],
  "confidence": "high/medium/low"
}}

Do not include any text outside the JSON object."""

    async def generate_query(
        self, 
        question: str, 
        schema: str, 
        model: str = "openai",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        database_type: str = "mssql"
    ) -> Dict[str, any]:
        """Generate SQL query from natural language question with safety validation and retry.
        
        Returns:
            Dict with keys: sql, explanation, tables_used, confidence
        """
        
        system_prompt = self.create_system_prompt(schema, database_type)
        last_error = ""

        for attempt in range(1, self.MAX_RETRIES + 1):
            # Build the effective question; on retries, include the rejection reason
            effective_question = question
            if last_error:
                effective_question = (
                    f"{question}\n\n"
                    f"⚠️ Your previous response was rejected: {last_error}\n"
                    "Please regenerate a **read-only SELECT** query only."
                )

            if model == "openai":
                response_data = await self._generate_with_openai(effective_question, system_prompt, conversation_history)
            elif model == "gemini":
                response_data = await self._generate_with_gemini(effective_question, system_prompt, conversation_history)
            else:
                raise ValueError(f"Unsupported model: {model}")

            # Extract SQL from structured response
            sql = response_data.get("sql", "")
            
            # --- Validation ---
            is_safe, reason = self._keyword_safety_check(sql)
            if not is_safe:
                last_error = reason
                continue

            is_valid, reason = await self._llm_validate_query(sql, model)
            if not is_valid:
                last_error = reason
                continue

            return response_data  # passed both checks

        raise Exception(
            f"Query generation failed after {self.MAX_RETRIES} attempts. "
            f"Last rejection reason: {last_error}"
        )

    # ---- Validation helpers ------------------------------------------------

    def _keyword_safety_check(self, sql: str) -> Tuple[bool, str]:
        """Fast regex check – reject if any write/destructive keyword is found."""
        # Strip SQL comments before scanning
        stripped = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        stripped = re.sub(r'/\*.*?\*/', '', stripped, flags=re.DOTALL)

        match = self._DANGEROUS_KEYWORDS.search(stripped)
        if match:
            keyword = match.group(0).upper()
            return False, f"Query contains disallowed operation: {keyword}"
        return True, ""

    async def _llm_validate_query(self, sql: str, model: str) -> Tuple[bool, str]:
        """Use the LLM to validate that the SQL is read-only and well-formed."""
        validation_prompt = (
            "You are a SQL security reviewer. Analyse the SQL query below and answer with EXACTLY one line:\n"
            "  SAFE   – if the query is purely read-only (SELECT, WITH, EXPLAIN, SHOW, DESCRIBE) and syntactically reasonable.\n"
            "  UNSAFE: <short reason> – if the query modifies data, schema, or permissions, or is malformed.\n\n"
            f"SQL Query:\n{sql}\n\nVerdict:"
        )

        try:
            if model == "openai":
                result = await self._generate_with_openai(
                    validation_prompt,
                    "You are a SQL security reviewer. Respond with SAFE or UNSAFE: <reason>.",
                    None,
                )
            elif model == "gemini":
                result = await self._generate_with_gemini(
                    validation_prompt,
                    "You are a SQL security reviewer. Respond with SAFE or UNSAFE: <reason>.",
                    None,
                )
            else:
                return True, ""  # fallback: skip LLM validation for unknown model

            verdict = result.strip()
            if verdict.upper().startswith("SAFE"):
                return True, ""
            # Extract reason after "UNSAFE:"
            reason = verdict.split(":", 1)[1].strip() if ":" in verdict else verdict
            return False, f"LLM review rejected query: {reason}"
        except Exception:
            # If the validation call itself fails, allow the query through
            # (the keyword check already passed)
            return True, ""
    
    async def _generate_with_openai(
        self, 
        question: str, 
        system_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, any]:
        """Generate query using OpenAI with structured JSON output"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": question})
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                max_completion_tokens=1000,
                response_format={"type": "json_object"}  # Force JSON output
            )
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                data = json.loads(content)
                # Validate with Pydantic model
                validated = SQLResponse(**data)
                return validated.model_dump()
            except (json.JSONDecodeError, Exception) as parse_error:
                # Fallback: treat as plain SQL
                return {
                    "sql": content,
                    "explanation": "Generated SQL query",
                    "tables_used": [],
                    "confidence": "medium"
                }
        except Exception as e:
            error_msg = str(e)
            if "not a chat model" in error_msg:
                raise Exception(
                    f"OpenAI API error: Selected model '{self.openai_model}' is not chat-capable. "
                    "Set OPENAI_MODEL to a chat model like 'gpt-4o-mini' or 'gpt-4.1-mini'."
                )
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def _generate_with_gemini(
        self, 
        question: str, 
        system_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, any]:
        """Generate query using Gemini with structured JSON output"""
        if not GEMINI_AVAILABLE:
            raise ValueError("Gemini library not installed. Install with: pip install google-generativeai")
        if not self.gemini_model:
            raise ValueError("Gemini API key not configured")
        
        # Combine system prompt with conversation history and question
        full_prompt = system_prompt + "\n\n"
        
        if conversation_history:
            for msg in conversation_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                full_prompt += f"{role}: {msg['content']}\n"
        
        full_prompt += f"\nUser Question: {question}\n\nRespond with JSON only:"
        
        try:
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                    response_mime_type="application/json"  # Force JSON output
                )
            )
            content = response.text.strip()
            
            # Parse JSON response
            try:
                data = json.loads(content)
                # Validate with Pydantic model
                validated = SQLResponse(**data)
                return validated.model_dump()
            except (json.JSONDecodeError, Exception) as parse_error:
                # Fallback: treat as plain SQL
                return {
                    "sql": content,
                    "explanation": "Generated SQL query",
                    "tables_used": [],
                    "confidence": "medium"
                }
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def is_openai_available(self) -> bool:
        """Check if OpenAI is configured and available"""
        return self.openai_client is not None
    
    def is_gemini_available(self) -> bool:
        """Check if Gemini is configured and available"""
        return GEMINI_AVAILABLE and self.gemini_model is not None
