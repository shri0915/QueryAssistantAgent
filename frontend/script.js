// API base URL
const API_BASE = window.location.origin;

// Session ID for conversation context
const SESSION_ID = 'default';

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    checkModelAvailability();
    loadSchemaInfo();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Schema file upload
    document.getElementById('schemaFile').addEventListener('change', handleSchemaUpload);
    
    // Enter key to send message
    document.getElementById('questionInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuestion();
        }
    });
}

// Store model names globally so chat messages can reference them
let modelNames = { openai: 'OpenAI', gemini: 'Gemini', local: 'Local LLM' };

// Check which AI models are available
async function checkModelAvailability() {
    try {
        const response = await fetch(`${API_BASE}/api/models`);
        const data = await response.json();
        
        // Store model names from backend
        if (data.openai_model) modelNames.openai = data.openai_model;
        if (data.gemini_model) modelNames.gemini = data.gemini_model;
        if (data.local_model) modelNames.local = data.local_model;
        
        // Update labels with actual model names
        document.getElementById('openaiModelName').textContent = `OpenAI (${modelNames.openai})`;
        document.getElementById('geminiModelName').textContent = `Gemini (${modelNames.gemini})`;
        document.getElementById('localModelName').textContent = `Local (${modelNames.local})`;
        
        // Update OpenAI status
        const openaiStatus = document.getElementById('openaiStatus');
        const openaiRadio = document.getElementById('modelOpenAI');
        if (data.openai) {
            openaiStatus.textContent = '✓';
            openaiStatus.style.color = 'var(--success-color)';
        } else {
            openaiStatus.textContent = '✗';
            openaiStatus.style.color = 'var(--error-color)';
            openaiRadio.disabled = true;
        }
        
        // Update Gemini status
        const geminiStatus = document.getElementById('geminiStatus');
        const geminiRadio = document.getElementById('modelGemini');
        if (data.gemini) {
            geminiStatus.textContent = '✓';
            geminiStatus.style.color = 'var(--success-color)';
        } else {
            geminiStatus.textContent = '✗';
            geminiStatus.style.color = 'var(--error-color)';
            geminiRadio.disabled = true;
        }

        // Update Local LLM status
        const localStatus = document.getElementById('localStatus');
        const localRadio = document.getElementById('modelLocal');
        if (data.local) {
            localStatus.textContent = '✓';
            localStatus.style.color = 'var(--success-color)';
        } else {
            localStatus.textContent = '✗';
            localStatus.style.color = 'var(--error-color)';
            localRadio.disabled = true;
        }
        
        // Choose first available model if currently selected one is unavailable
        const selectedRadio = document.querySelector('input[name="model"]:checked');
        if (selectedRadio && selectedRadio.disabled) {
            if (data.openai) {
                openaiRadio.checked = true;
            } else if (data.gemini) {
                geminiRadio.checked = true;
            } else if (data.local) {
                localRadio.checked = true;
            }
        }
        
        // If none are available, show warning
        if (!data.openai && !data.gemini && !data.local) {
            showNotification('No AI models available. Configure API keys or start a local LLM server.', 'error');
        }
    } catch (error) {
        console.error('Error checking model availability:', error);
    }
}

// Load current schema info
async function loadSchemaInfo() {
    try {
        const response = await fetch(`${API_BASE}/api/schema-info`);
        const data = await response.json();
        
        if (data.has_schema) {
            updateSchemaStatus(data);
            enableChat();
        }
    } catch (error) {
        console.error('Error loading schema info:', error);
    }
}

// Handle schema file upload
async function handleSchemaUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    showNotification('Uploading schema...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/api/upload-schema`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const data = await response.json();
        updateSchemaStatus(data);
        enableChat();
        showNotification(data.message, 'success');
        
        // Clear chat when new schema is uploaded
        clearChat();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
    
    // Reset file input
    event.target.value = '';
}

// Update schema status display
function updateSchemaStatus(data) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    const schemaInfo = document.getElementById('schemaInfo');
    const deleteBtn = document.getElementById('deleteSchemaBtn');
    
    statusDot.className = 'status-dot status-success';
    statusText.textContent = 'Schema loaded';
    
    document.getElementById('schemaFilename').textContent = data.filename;
    document.getElementById('tableCount').textContent = data.table_count;
    
    const tableList = document.getElementById('tableList');
    tableList.innerHTML = '';
    data.tables.forEach(table => {
        const tag = document.createElement('span');
        tag.className = 'table-tag';
        tag.textContent = table;
        tableList.appendChild(tag);
    });
    
    schemaInfo.style.display = 'block';
    deleteBtn.disabled = false;
}

// Enable chat input
function enableChat() {
    document.getElementById('questionInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;
}

// Disable chat input
function disableChat() {
    document.getElementById('questionInput').disabled = true;
    document.getElementById('sendBtn').disabled = true;
}

// Delete schema
async function deleteSchema() {
    if (!confirm('Are you sure you want to delete the current schema?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/schema`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Reset UI
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.querySelector('.status-text');
            const schemaInfo = document.getElementById('schemaInfo');
            const deleteBtn = document.getElementById('deleteSchemaBtn');
            
            statusDot.className = 'status-dot status-empty';
            statusText.textContent = 'No schema uploaded';
            schemaInfo.style.display = 'none';
            deleteBtn.disabled = true;
            
            disableChat();
            clearChat();
            showNotification('Schema deleted', 'success');
        }
    } catch (error) {
        showNotification('Error deleting schema', 'error');
    }
}

// Send question to API
async function sendQuestion() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    
    if (!question) return;
    
    // Get selected model
    const selectedModel = document.querySelector('input[name="model"]:checked').value;
    
    // Add user message to chat
    addMessage('user', question);
    
    // Clear input
    input.value = '';
    
    // Show loading indicator
    const loadingId = addLoadingMessage();
    
    // Disable input while processing
    disableChat();
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                model: selectedModel,
                session_id: SESSION_ID
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }
        
        const data = await response.json();
        
        // Remove loading indicator
        removeMessage(loadingId);
        
        if (data.success) {
            addMessage('assistant', data, selectedModel);
        } else {
            addMessage('error', data.error || 'Failed to generate query');
        }
    } catch (error) {
        // Remove loading indicator
        removeMessage(loadingId);
        addMessage('error', error.message);
    } finally {
        enableChat();
        input.focus();
    }
}

// Add message to chat
function addMessage(type, content, model = null) {
    const messagesContainer = document.getElementById('chatMessages');
    
    // Remove welcome message if it exists
    const welcomeMessage = messagesContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.id = `msg-${Date.now()}`;
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="message-icon user-icon">👤</div>
            <div class="message-content">
                <div class="message-text">${escapeHtml(content)}</div>
            </div>
        `;
    } else if (type === 'assistant') {
        // content is now the full response data object
        const sqlQuery = content.query || content;
        const explanation = content.explanation;
        const tablesUsed = content.tables_used;
        const confidence = content.confidence;
        
        let metadataHtml = '';
        if (explanation || tablesUsed || confidence) {
            metadataHtml = '<div class="query-metadata">';
            
            if (explanation) {
                metadataHtml += `<div class="metadata-item"><strong>Explanation:</strong> ${escapeHtml(explanation)}</div>`;
            }
            
            if (tablesUsed && tablesUsed.length > 0) {
                const tablesList = tablesUsed.map(t => `<span class="table-tag">${escapeHtml(t)}</span>`).join(' ');
                metadataHtml += `<div class="metadata-item"><strong>Tables:</strong> ${tablesList}</div>`;
            }
            
            if (confidence) {
                const confidenceClass = confidence === 'high' ? 'confidence-high' : 
                                       confidence === 'low' ? 'confidence-low' : 'confidence-medium';
                metadataHtml += `<div class="metadata-item"><strong>Confidence:</strong> <span class="${confidenceClass}">${escapeHtml(confidence)}</span></div>`;
            }
            
            metadataHtml += '</div>';
        }
        
        messageDiv.innerHTML = `
            <div class="message-icon assistant-icon">🤖</div>
            <div class="message-content">
                <div class="message-meta">
                    <span>Generated SQL Query</span>
                    ${model ? `<span>• ${modelNames[model] || model}</span>` : ''}
                </div>
                ${metadataHtml}
                <div class="sql-query" data-sql="${escapeHtml(sqlQuery).replace(/"/g, '&quot;')}">
                    <div class="sql-query-header">
                        <span>SQL</span>
                        <button class="copy-btn" onclick="copyToClipboard(this)">Copy</button>
                        <button class="execute-btn" onclick="executeQuery(this)">▶ Execute</button>
                    </div>
                    <div class="sql-code">${formatSQL(escapeHtml(sqlQuery))}</div>
                    <div class="query-results" style="display: none;"></div>
                </div>
            </div>
        `;
    } else if (type === 'error') {
        messageDiv.innerHTML = `
            <div class="message-icon assistant-icon">⚠️</div>
            <div class="message-content">
                <div class="error-message">${escapeHtml(content)}</div>
            </div>
        `;
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return messageDiv.id;
}

// Add loading message
function addLoadingMessage() {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.id = `loading-${Date.now()}`;
    
    messageDiv.innerHTML = `
        <div class="message-icon assistant-icon">🤖</div>
        <div class="message-content">
            <div class="loading">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return messageDiv.id;
}

// Remove message by ID
function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// Clear chat
function clearChat() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <h2>👋 Welcome!</h2>
            <p>Upload a database schema to get started. Then ask questions about your data in plain English, and I'll generate SQL queries for you.</p>
            <div class="example-questions">
                <p><strong>Example questions:</strong></p>
                <div class="example-chip" onclick="askExample(this)">Show me all customers</div>
                <div class="example-chip" onclick="askExample(this)">What's the total revenue?</div>
                <div class="example-chip" onclick="askExample(this)">List orders from last month</div>
                <div class="example-chip" onclick="askExample(this)">Find top 10 products by sales</div>
            </div>
        </div>
    `;
}

// Ask example question
function askExample(element) {
    const question = element.textContent;
    const input = document.getElementById('questionInput');
    input.value = question;
    input.focus();
}

// Execute SQL query against the database
async function executeQuery(button) {
    // Get the SQL from the data attribute
    const sqlContainer = button.closest('.sql-query');
    const sql = sqlContainer.getAttribute('data-sql');
    
    // Decode HTML entities
    const textarea = document.createElement('textarea');
    textarea.innerHTML = sql;
    const decodedSql = textarea.value;
    
    const resultsContainer = sqlContainer.querySelector('.query-results');
    const originalText = button.textContent;
    
    // Show loading state
    button.textContent = '⏳ Executing...';
    button.disabled = true;
    resultsContainer.style.display = 'block';
    resultsContainer.decodedSnnerHTML = '<div class="loading"><div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div></div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/database/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sql: sql,
                session_id: SESSION_ID
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayQueryResults(resultsContainer, data);
            button.textContent = '✓ Executed';
            button.style.background = 'var(--success-color)';
            
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = '';
                button.disabled = false;
            }, 2000);
        } else {
            resultsContainer.innerHTML = `
                <div class="error-message">
                    <strong>Execution Error:</strong> ${escapeHtml(data.error || 'Unknown error')}
                </div>
            `;
            button.textContent = originalText;
            button.disabled = false;
        }
    } catch (error) {
        resultsContainer.innerHTML = `
            <div class="error-message">
                <strong>Request Error:</strong> ${escapeHtml(error.message)}
            </div>
        `;
        button.textContent = originalText;
        button.disabled = false;
    }
}

// Display query results in a table
function displayQueryResults(container, data) {
    let html = '';
    
    // Show execution time if available
    if (data.execution_time_ms !== null && data.execution_time_ms !== undefined) {
        html += `<div class="results-meta">Executed in ${data.execution_time_ms}ms`;
        if (data.row_count !== null && data.row_count !== undefined) {
            html += ` • ${data.row_count} row${data.row_count !== 1 ? 's' : ''}`;
        }
        html += '</div>';
    }
    
    // Extract rows from various response formats
    let rows = [];
    if (data.data) {
        if (Array.isArray(data.data)) {
            rows = data.data;
        } else if (data.data.data && Array.isArray(data.data.data)) {
            rows = data.data.data;
        } else if (data.data.rows && Array.isArray(data.data.rows)) {
            rows = data.data.rows;
        } else if (typeof data.data === 'object') {
            // If it's a single object, wrap it in an array
            rows = [data.data];
        }
    }
    
    if (rows.length === 0) {
        html += '<div class="no-results">Query executed successfully. No rows returned.</div>';
    } else {
        // Get column names from first row
        const columns = Object.keys(rows[0]);
        
        html += '<div class="results-table-container"><table class="results-table">';
        
        // Table header
        html += '<thead><tr>';
        columns.forEach(col => {
            html += `<th>${escapeHtml(col)}</th>`;
        });
        html += '</tr></thead>';
        
        // Table body (limit to first 100 rows for display)
        html += '<tbody>';
        const displayRows = rows.slice(0, 100);
        displayRows.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const value = row[col];
                const displayValue = value === null || value === undefined ? 
                    '<span class="null-value">NULL</span>' : 
                    escapeHtml(String(value));
                html += `<td>${displayValue}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody>';
        html += '</table></div>';
        
        if (rows.length > 100) {
            html += `<div class="results-note">Showing first 100 of ${rows.length} rows</div>`;
        }
    }
    
    container.innerHTML = html;
}

// Copy SQL to clipboard
function copyToClipboard(button) {
    const sqlCode = button.closest('.sql-query').querySelector('.sql-code');
    const text = sqlCode.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.style.background = 'var(--success-color)';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    });
}

// Format SQL for display
function formatSQL(sql) {
    // Basic SQL formatting
    const keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 
                     'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET', 'INSERT', 'UPDATE', 
                     'DELETE', 'CREATE', 'ALTER', 'DROP', 'AND', 'OR', 'ON', 'AS'];
    
    let formatted = sql;
    keywords.forEach(keyword => {
        const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
        formatted = formatted.replace(regex, `<span style="color: #60a5fa;">${keyword}</span>`);
    });
    
    return formatted;
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? 'var(--success-color)' : type === 'error' ? 'var(--error-color)' : 'var(--primary-color)'};
        color: white;
        border-radius: 8px;
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add CSS animation for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
