# Query Assistant Agent

A powerful chat agent that understands database schemas, converts natural language questions into SQL queries, and executes them against your database using Azure Data API Builder MCP. Supports both OpenAI and Google Gemini.

## Features

- 📊 Upload database schema files (SQL, ERD diagrams, text descriptions)
- 🤖 Choose between OpenAI GPT or Google Gemini
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

### 2. Install Azure Data API Builder MCP Server

The DAB MCP server enables direct database connectivity. Choose your installation method:

**Option A: Using npx (Recommended, no installation required)**
```bash
# No installation needed - it will be run on-demand
# The server will be started automatically when needed
```

**Option B: Global npm installation**
```bash
npm install -g @azure/data-api-builder-mcp
```

**Note:** You need Node.js installed for either option. [Download Node.js](https://nodejs.org/)

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

# Database Connection (required for query execution)
DATABASE_CONNECTION_STRING=your_database_connection_string

# DAB MCP Configuration (optional, defaults provided)
DAB_CONFIG_PATH=./dab-config.json
DAB_SERVER_COMMAND=npx
DAB_SERVER_ARGS=@azure/data-api-builder-mcp
```

**Database Connection String Examples:**

- **SQL Server:**
  ```
  Server=localhost;Database=mydb;User Id=sa;Password=yourpassword;TrustServerCertificate=True
  ```

- **PostgreSQL:**
  ```
  Host=localhost;Database=mydb;Username=postgres;Password=yourpassword
  ```

- **MySQL:**
  ```
  server=localhost;database=mydb;user=root;password=yourpassword
  ```

### 4. Configure Data API Builder

Create `dab-config.json` from the example:

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

**Supported database types:** `mssql`, `postgresql`, `mysql`, `cosmosdb_nosql`

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
2. **Select AI Model** - Choose your preferred AI model (OpenAI or Gemini)
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
│ • DAB Service   │◄─── MCP Protocol
│ • Schema Parser │
└────────┬────────┘
         │
         │ MCP (Model Context Protocol)
         │
┌────────▼────────┐
│  Azure Data     │
│  API Builder    │
│  MCP Server     │
└────────┬────────┘
         │
         │ Native DB Protocol
         │
┌────────▼────────┐
│   Database      │
│ (SQL/Postgres/  │
│    MySQL)       │
└─────────────────┘
```

## Troubleshooting

### Database Connection Issues

**Error: "Failed to connect to DAB MCP server"**
- Ensure Node.js is installed: `node --version`
- Verify `@azure/data-api-builder-mcp` is accessible
- Check your `DATABASE_CONNECTION_STRING` in `.env`
- Verify database server is running and accessible

**Error: "Query execution error"**
- Ensure your `dab-config.json` is properly configured
- Check database permissions for your connection user
- Verify the database type matches your configuration

### AI Model Issues

**Error: "OpenAI API key not configured"**
- Set `OPENAI_API_KEY` in your `.env` file
- Restart the server after updating environment variables

**Error: "Model not chat-capable"**
- Use a chat model like `gpt-4o-mini` or `gpt-4.1-mini`
- Set `OPENAI_MODEL` in `.env` to override the default

### MCP Server Issues

**Error: "npx command not found"**
- Install Node.js from https://nodejs.org/
- Restart your terminal after installation

**MCP server slow to start**
- First run with `npx` downloads the package (one-time)
- Consider global installation: `npm install -g @azure/data-api-builder-mcp`

## Security Features

- ✅ **Read-only enforcement**: Only SELECT queries are executed
- ✅ **Keyword filtering**: Blocks INSERT, UPDATE, DELETE, DROP, etc.
- ✅ **LLM validation**: Queries are reviewed by AI before execution
- ✅ **Retry mechanism**: Failed queries are regenerated with safety feedback
- ✅ **MCP isolation**: Database access through secure MCP protocol

## Technologies

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript
- **AI Models**: OpenAI GPT, Google Gemini
- **Database Access**: Azure Data API Builder MCP Server
- **Protocol**: Model Context Protocol (MCP)
