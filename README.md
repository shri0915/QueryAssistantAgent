# Query Assistant Agent

A simple chat agent that understands database schemas and converts natural language questions into SQL queries. Supports both OpenAI and Google Gemini.

## Features

- 📊 Upload database schema files (SQL, ERD diagrams, text descriptions)
- 🤖 Choose between OpenAI GPT or Google Gemini
- 💬 Ask questions in plain English
- 🔍 Get SQL queries as responses
- 📝 Maintain conversation context

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - Copy `.env.example` to `.env`
   - Add your OpenAI and/or Gemini API keys

3. **Run the Application**
   ```bash
   python backend/main.py
   ```

4. **Access the Application**
   - Open your browser to `http://localhost:8000`

## Usage

1. Upload your database schema file (SQL DDL, text description, or diagram)
2. Select your preferred AI model (OpenAI or Gemini)
3. Ask questions about your database in natural language
4. Receive SQL queries that can be executed on your database

## Example Questions

- "Show me all customers who made purchases last month"
- "What's the total revenue by product category?"
- "Find the top 10 products by sales"
- "List all orders with their customer details"

## API Endpoints

- `POST /upload-schema` - Upload database schema file
- `POST /chat` - Send a question and get SQL query
- `GET /` - Serve frontend application

## Technologies

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript
- **AI Models**: OpenAI GPT-4, Google Gemini Pro
