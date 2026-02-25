# Quick Start Guide

## Prerequisites

1. Python 3.8 or higher
2. API keys for at least one of:
   - OpenAI API key (for GPT-4)
   - Google Gemini API key

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file and add your API keys:

```
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
```

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
- Copy to clipboard with one click
- Run on your actual database
- Modify as needed

## Tips

- **Be Specific**: The more details in your question, the better the SQL query
- **Use Context**: The agent remembers previous questions in the conversation
- **Check the Query**: Always review generated queries before running on production databases
- **Test with Examples**: Use the provided example schemas to learn how the system works

## Troubleshooting

### "No AI models configured"
- Make sure you've added at least one API key to the `.env` file
- Restart the server after adding API keys

### "Please upload a database schema first"
- You need to upload a schema file before asking questions
- Use one of the example schemas to get started

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
