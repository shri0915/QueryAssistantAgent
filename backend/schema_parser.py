"""
Schema Parser for handling database schema files
"""
import re
from typing import Optional


class SchemaParser:
    @staticmethod
    def parse_schema(content: str, filename: str) -> str:
        """
        Parse and clean schema content from uploaded file
        
        Args:
            content: Raw file content
            filename: Name of the uploaded file
            
        Returns:
            Cleaned and formatted schema string
        """
        # Detect file type and parse accordingly
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext in ['sql', 'ddl']:
            return SchemaParser._parse_sql_schema(content)
        elif file_ext in ['txt', 'md']:
            return SchemaParser._parse_text_schema(content)
        else:
            # Try to auto-detect
            if 'CREATE TABLE' in content.upper() or 'CREATE DATABASE' in content.upper():
                return SchemaParser._parse_sql_schema(content)
            else:
                return SchemaParser._parse_text_schema(content)
    
    @staticmethod
    def _parse_sql_schema(content: str) -> str:
        """Parse SQL DDL schema"""
        # Remove comments
        content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Clean up whitespace
        content = re.sub(r'\n\s*\n', '\n', content)
        content = content.strip()
        
        return content
    
    @staticmethod
    def _parse_text_schema(content: str) -> str:
        """Parse text-based schema description"""
        # Just clean up the text
        content = content.strip()
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content
    
    @staticmethod
    def extract_table_names(schema: str) -> list:
        """Extract table names from schema"""
        # Look for CREATE TABLE statements
        table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?'
        tables = re.findall(table_pattern, schema, re.IGNORECASE)
        
        if tables:
            return list(set(tables))
        
        # If no SQL found, try to extract from text descriptions
        # Look for patterns like "Table: users" or "users table"
        table_pattern = r'(?:Table:\s*|table\s+)(\w+)'
        tables = re.findall(table_pattern, schema, re.IGNORECASE)
        
        return list(set(tables)) if tables else []
    
    @staticmethod
    def validate_schema(schema: str) -> tuple[bool, Optional[str]]:
        """
        Validate if schema content is usable
        
        Returns:
            (is_valid, error_message)
        """
        if not schema or len(schema.strip()) < 10:
            return False, "Schema content is too short or empty"
        
        # Check if it contains at least some database-related keywords
        keywords = ['table', 'column', 'field', 'create', 'database', 'schema', 'primary', 'foreign', 'key']
        has_keywords = any(keyword in schema.lower() for keyword in keywords)
        
        if not has_keywords:
            return False, "Schema does not appear to contain database structure information"
        
        return True, None
