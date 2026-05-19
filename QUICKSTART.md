# Quick Start Guide

## Prerequisites

1. Python 3.8 or higher
2. **Node.js** (for database connectivity) - [Download](https://nodejs.org/)
3. API keys for at least one of:
   - OpenAI API key (for GPT-4)
   - Google Gemini API key
   - Or a local LLM server (Ollama-compatible)
4. **(Optional)** Access to a database (SQL Server, PostgreSQL, or MySQL) for query execution

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys and Database

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file and add your settings:

```env
# AI Model API Keys (required - at least one)
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here

# Local LLM (optional, Ollama-compatible)
LOCAL_LLM_URL=http://localhost:11434/api/chat
LOCAL_LLM_MODEL=gemma3:4b
LOCAL_LLM_TIMEOUT_SECONDS=60

# Database Connection (optional - required only for query execution)
DATABASE_CONNECTION_STRING=Server=localhost;Database=mydb;User Id=sa;Password=yourpass;TrustServerCertificate=True
```

**Note:** If you skip the database configuration, you can still generate SQL queries but won't be able to execute them.

### 2b. Configure Database Connection (Optional)

If you want to execute queries against a real database:

1. Copy the DAB config example:
   ```bash
   cp dab-config.json.example dab-config.json
   ```

2. Edit `dab-config.json` to match your database type (`mssql`, `postgresql`, or `mysql`)

3. Ensure your database is running and accessible

### 3. Run the Application

```bash
cd backend
python main.py
```

The server will start at `http://localhost:8000`

### 4. Open in Browser

Navigate to `http://localhost:8000` in your web browser.

## Usage

### Step 1: Upload Schema

Click "Upload Schema" and select a database schema file:
- SQL DDL files (.sql)
- Text descriptions (.txt, .md)
- Example schemas are provided in the `examples/` folder

### Step 2: Select AI Model

Choose between:
- **OpenAI GPT-4**: More accurate, better at complex queries
- **Google Gemini**: Fast, good for most queries
- **Local LLM**: Runs locally (for example via Ollama)

### Step 3: Ask Questions

Type your questions in plain English, for example:

**E-Commerce Database:**
- "Show me all orders from last month"
- "Find customers who spent more than $1000"
- "What are the top 5 best-selling products?"
- "List all pending orders with customer details"
- "Calculate total revenue by category"

**Library Database:**
- "Show all overdue books"
- "Find members who have borrowed more than 5 books"
- "List the most popular books by loan count"
- "Show all available books in the Science Fiction genre"

### Step 4: Use the Generated SQL

The AI will generate SQL queries that you can:
- **Copy** to clipboard with one click
- **Execute** directly against your database (if configured)
- Modify as needed

To execute a query:
1. Click the **"▶ Execute"** button next to the generated SQL
2. View results in a formatted table
3. See execution time and row count

**Safety Note:** Only SELECT queries can be executed. Write operations (INSERT, UPDATE, DELETE) are automatically blocked.

## Tips

- **Be Specific**: The more details in your question, the better the SQL query
- **Use Context**: The agent remembers previous questions in the conversation
- **Check the Query**: Always review generated queries before running on production databases
- **Test with Examples**: Use the provided example schemas to learn how the system works

## Troubleshooting

### "No AI models configured"
- Make sure you've added at least one API key to the `.env` file or started your local LLM server
- Restart the server after adding API keys

### "Please upload a database schema first"
- You need to upload a schema file before asking questions
- Use one of the example schemas to get started

### "Failed to connect to DAB MCP server" or Execute button not working
- Install Node.js if not already installed: https://nodejs.org/
- Verify your `DATABASE_CONNECTION_STRING` in `.env` is correct
- Ensure your database server is running
- Check that your database user has SELECT permissions
- Test connection using: `curl http://localhost:8000/api/database/test-connection`

### "npx command not found"
- Install Node.js from https://nodejs.org/
- Restart your terminal/command prompt after installation
- Verify with: `node --version` and `npx --version`

## Quick Test

Once everything is set up, try this workflow:

1. Upload `examples/ecommerce_schema.sql` or `examples/library_schema.sql`
2. Ask: "Show me all tables in this database"
3. Click "▶ Execute" if you have a database connected
4. See the SQL query and results!

## What's Next?

- Read the full [README.md](README.md) for detailed setup and features
- Explore the [Azure Data API Builder documentation](https://learn.microsoft.com/azure/data-api-builder/) for advanced database configuration
- Check your database schema and start asking questions!

### Schema Upload Failed
- Ensure the file is a text file (UTF-8 encoded)
- Check that the schema contains database-related keywords
- Try using one of the example schemas first

## Example Workflows

### Workflow 1: Exploring a New Database

1. Upload the database schema
2. Ask: "What tables are in this database?"
3. Ask: "Show me the structure of the orders table"
4. Ask: "How are customers and orders related?"

### Workflow 2: Business Analysis

1. Upload your e-commerce schema
2. Ask: "Calculate total revenue for each month in 2024"
3. Ask: "Which products have the highest profit margins?"
4. Ask: "Show customer lifetime value"

### Workflow 3: Data Quality Checks

1. Upload your schema
2. Ask: "Find customers with invalid email addresses"
3. Ask: "Show orders with no associated customer"
4. Ask: "List products with negative stock quantities"

## API Endpoints

If you want to integrate with other tools:

- `GET /api/health` - Check system status
- `GET /api/models` - Get available AI models
- `POST /api/upload-schema` - Upload database schema
- `GET /api/schema-info` - Get current schema info
- `POST /api/chat` - Send question and get SQL query
- `DELETE /api/schema` - Delete current schema

See full API documentation at `http://localhost:8000/docs`

## Getting API Keys

### OpenAI API Key
1. Visit https://platform.openai.com/
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key

### Google Gemini API Key
1. Visit https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create a new API key
4. Enable the Generative Language API

## Security Notes

- Never commit your `.env` file to version control
- Keep your API keys secure and private
- Review generated SQL queries before running on production databases
- Consider rate limits and costs of API calls
