# Query Assistant Agent

A powerful chat agent that understands database schemas, converts natural language questions into SQL queries, and executes them against your database using Azure Data API Builder MCP. Supports OpenAI, Google Gemini, and local LLMs.

## Features

- 📊 Upload database schema files (SQL, ERD diagrams, text descriptions)
- 🤖 Choose between OpenAI, Google Gemini, or a local LLM
- 💬 Ask questions in plain English
- 🔍 Get SQL queries as responses
- ▶️ **Execute queries directly against your database**
- 📊 **View results in a formatted table**
- 📝 Maintain conversation context
- 🔒 Built-in SQL safety validation (read-only queries)

## Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Database Drivers (Automatic)

The required drivers are installed automatically with pip:
- **pyodbc** - for SQL Server and Azure SQL
- **psycopg2** - for PostgreSQL
- **mysql-connector-python** - for MySQL

```bash
pip install -r requirements.txt
```

### 3. (Optional) Install Azure Data API Builder for MCP Mode

**Note:** Direct connection mode (default) works without this. Install DAB only if you plan to use MCP protocol.

```bash
# Install as .NET global tool
dotnet tool install -g Microsoft.DataApiBuilder

# Verify installation
dab --version
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# AI Model API Keys (configure at least one)
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Local LLM (optional, for Ollama-compatible servers)
LOCAL_LLM_URL=http://localhost:11434/api/chat
LOCAL_LLM_MODEL=gemma3:4b
LOCAL_LLM_TIMEOUT_SECONDS=60

# Database Connection (required for query execution)
DATABASE_CONNECTION_STRING=your_database_connection_string

# DAB MCP Configuration (optional, defaults provided)
DAB_CONFIG_PATH=./dab-config.json
DAB_SERVER_COMMAND=npx
DAB_SERVER_ARGS=@azure/data-api-builder-mcp
```

**Database Connection String Examples:**

- **SQL Server (Local with Windows Auth):**
  ```
  Server=localhost;Database=mydb;Trusted_Connection=True;TrustServerCertificate=True
  ```

- **SQL Server (with username/password):**
  ```
  Server=localhost;Database=mydb;User Id=sa;Password=yourpassword;TrustServerCertificate=True
  ```

- **Azure SQL Database:**
  ```
  Server=myserver.database.windows.net;Database=mydb;User Id=username;Password=yourpassword;Encrypt=True
  ```

- **PostgreSQL:**
  ```
  Host=localhost;Port=5432;Database=mydb;Username=postgres;Password=yourpassword
  ```
  
  **Or PostgreSQL connection URI:**
  ```
  postgresql://username:password@localhost:5432/mydb
  ```

- **MySQL:**
  ```
  server=localhost;port=3306;database=mydb;user=root;password=yourpassword
  ```

**MCP Mode Configuration:**

Set `USE_MCP=true` to enable MCP protocol (requires DAB MCP server support):

**MCP Mode Configuration:**

Set `USE_MCP=true` to enable MCP protocol (requires DAB MCP server support):

```env
USE_MCP=true
DAB_CONFIG_PATH=./dab-config.json
```

**For now, use direct connection mode (default):**

```env
USE_MCP=false
DATABASE_CONNECTION_STRING=your_connection_string
```

### 4. Configure Data API Builder (Optional - for MCP Mode)

**Note:** This step is optional. The system works with direct database connections by default.

When MCP protocol support is available, create `dab-config.json`:

```bash
cp dab-config.json.example dab-config.json
```

Edit `dab-config.json` to match your database type and entities. Example for SQL Server:

```json
{
  "$schema": "https://github.com/Azure/data-api-builder/releases/latest/download/dab.draft.schema.json",
  "data-source": {
    "database-type": "mssql",
    "connection-string": "@env('DATABASE_CONNECTION_STRING')",
    "options": {
      "set-session-context": false
    }
  },
  "runtime": {
    "rest": {
      "enabled": true,
      "path": "/api"
    },
    "graphql": {
      "enabled": false
    },
    "host": {
      "mode": "development",
      "cors": {
        "origins": ["*"]
      }
    }
  },
  "entities": {}
}
```

**Supported database types in DAB:** `mssql`, `postgresql`, `mysql`, `cosmosdb_nosql`

For more details, see the [Azure Data API Builder documentation](https://learn.microsoft.com/azure/data-api-builder/).

### 5. Run the Application

```bash
python backend/main.py
```

### 6. Access the Application

Open your browser to `http://localhost:8000`

## Usage

### Basic Workflow

1. **Upload Schema** - Upload your database schema file (SQL DDL, text description, or diagram)
2. **Select AI Model** - Choose your preferred AI model (OpenAI, Gemini, or Local)
3. **Ask Questions** - Type questions about your database in natural language
4. **Get SQL Queries** - Receive generated SQL queries with explanations
5. **Execute Queries** - Click the "▶ Execute" button to run queries against your database
6. **View Results** - See formatted results in a table with execution time

### Query Execution

Once you've configured the database connection:

1. Ask a question like "Show me all customers"
2. The AI generates a SQL query
3. Click the **"▶ Execute"** button next to the query
4. View results directly in the chat interface

**Note:** Only SELECT queries can be executed for safety. INSERT, UPDATE, DELETE, and other write operations are blocked.

## Example Questions

- "Show me all customers who made purchases last month"
- "What's the total revenue by product category?"
- "Find the top 10 products by sales"
- "List all orders with their customer details"
- "How many active users do we have?"
- "What's the average order value?"

## API Endpoints

### Schema Management
- `POST /api/upload-schema` - Upload database schema file
- `GET /api/schema-info` - Get current schema information
- `DELETE /api/schema` - Delete current schema

### Query Generation
- `POST /api/chat` - Send a question and get SQL query
- `DELETE /api/conversation/{session_id}` - Clear conversation history

### Database Operations (New!)
- `GET /api/database/test-connection` - Test database connection via DAB MCP
- `POST /api/database/execute` - Execute SQL query against the database
- `GET /api/database/schema` - Get schema information from the database

### System
- `GET /api/health` - Health check
- `GET /api/models` - Get available AI models
- `GET /` - Serve frontend application

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (HTML/JS/CSS)  │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│   FastAPI       │
│   Backend       │
├─────────────────┤
│ • LLM Service   │◄─── OpenAI / Gemini
│ • DB Service    │◄─── MCP Protocol (when enabled)
│               or│     ↓ Direct Connection (default)
│ • Schema Parser │
└────────┬────────┘
         │
         ├─── MCP Mode ───┐
         │                │
         │         ┌──────▼──────┐
         │         │    Azure    │
         │         │   Data API  │
         │         │   Builder   │
         │         └──────┬──────┘
         │                │
         └─── Direct ─────┤
              Mode        │
                          │
                ┌─────────▼─────────┐
                │    Database       │
                │ • SQL Server      │
                │ • PostgreSQL      │
                │ • MySQL           │
                │ • Azure SQL       │
                └───────────────────┘
```

### Hybrid Architecture Benefits

1. **Direct Connection (Default)**
   - Simpler setup, works immediately
   - Native drivers for SQL Server, PostgreSQL, MySQL
   - No additional services required
   - Perfect for local development

2. **MCP Protocol (Future-Ready)**
   - Set `USE_MCP=true` when DAB MCP support is available
   - Unified abstraction for all database types
   - Works with cloud databases (Azure SQL, etc.)
   - Supports advanced features via Data API Builder

### Supported Databases

- **SQL Server** (2016+) - via pyodbc
- **Azure SQL Database** - via pyodbc
- **PostgreSQL** (9.6+) - via psycopg2
- **MySQL** (5.7+) - via mysql-connector-python

## Troubleshooting

### Database Connection Issues

**Error: "Failed to connect to database"**
- Verify your `DATABASE_CONNECTION_STRING` in `.env` is correct
- Ensure database server is running and accessible
- Check firewall rules allow connections
- For Azure SQL: ensure your IP is whitelisted
- For PostgreSQL/MySQL: verify port is correct (5432/3306)

**Test your connection string outside the app:**
```bash
# SQL Server (using sqlcmd)
sqlcmd -S localhost -d master -E

# PostgreSQL
psql -h localhost -U postgres -d mydb

# MySQL
mysql -h localhost -u root -p
```

**Database driver issues:**
- Ensure required drivers are installed: `pip install -r requirements.txt`
- For SQL Server on Linux/Mac: install ODBC driver (see [Microsoft docs](https://learn.microsoft.com/sql/connect/odbc/))
- Check database permissions for your connection user

### AI Model Issues

**Error: "OpenAI API key not configured"**
- Set `OPENAI_API_KEY` in your `.env` file
- Restart the server after updating environment variables

**Error: "Model not chat-capable"**
- Use a chat model like `gpt-4o-mini` or `gpt-4.1-mini`
- Set `OPENAI_MODEL` in `.env` to override the default

### MCP Mode Issues (Advanced)

**MCP mode is future-ready but currently uses direct connections by default.**

When DAB MCP server support becomes available:
- Set `USE_MCP=true` in `.env`
- Ensure `dab-config.json` is properly configured
- Install DAB: `dotnet tool install -g Microsoft.DataApiBuilder`

## Security Features

- ✅ **Read-only enforcement**: Only SELECT queries are executed
- ✅ **Keyword filtering**: Blocks INSERT, UPDATE, DELETE, DROP, etc.
- ✅ **LLM validation**: Queries are reviewed by AI before execution
- ✅ **Retry mechanism**: Failed queries are regenerated with safety feedback
- ✅ **Multi-database support**: SQL Server, PostgreSQL, MySQL, Azure SQL
- ✅ **MCP-ready architecture**: Easy switch to MCP protocol when available
- ✅ **Direct connections**: Simple setup with native database drivers

## Technologies

- **Backend**: FastAPI (Python)
- **Frontend*Drivers**: pyodbc, psycopg2, mysql-connector-python
- **Database Access**: Direct connection (default) or MCP protocol (future)
- **Protocol**: Model Context Protocol (MCP) - ready for future integration
- **Database Access**: Azure Data API Builder MCP Server
- **Protocol**: Model Context Protocol (MCP)
