// Configuration
const API_BASE_URL = 'http://localhost:5001';

// State
let currentSessionId = null;
let currentFile = null;

// DOM Elements
const uploadSection = document.getElementById('uploadSection');
const chatSection = document.getElementById('chatSection');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const uploadArea = document.getElementById('uploadArea');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const removeBtn = document.getElementById('removeBtn');
const processBtn = document.getElementById('processBtn');
const uploadLoading = document.getElementById('uploadLoading');
const currentDocName = document.getElementById('currentDocName');
const newDocBtn = document.getElementById('newDocBtn');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const sendIcon = document.getElementById('sendIcon');
const btnSpinner = document.getElementById('btnSpinner');
const suggestedQuestions = document.querySelectorAll('.suggestion-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkServerHealth();
});

// Setup Event Listeners
function setupEventListeners() {
    // Upload button
    uploadBtn.addEventListener('click', () => fileInput.click());
    
    // File input
    fileInput.addEventListener('change', handleFileSelect);
    
    // Remove file
    removeBtn.addEventListener('click', removeFile);
    
    // Process button
    processBtn.addEventListener('click', uploadDocument);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // New document button
    newDocBtn.addEventListener('click', resetToUpload);
    
    // Chat input
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Send button
    sendBtn.addEventListener('click', sendMessage);
    
    // Suggested questions
    suggestedQuestions.forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.textContent;
            sendMessage();
        });
    });
}

// Check server health
async function checkServerHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) {
            showError('Cannot connect to server. Please ensure the backend is running.');
        }
    } catch (error) {
        showError('Cannot connect to server. Please ensure the backend is running on port 5000.');
    }
}

// File handling
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
        currentFile = file;
        displayFileInfo(file);
    } else {
        showError('Please select a valid PDF file.');
    }
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
        currentFile = file;
        fileInput.files = e.dataTransfer.files;
        displayFileInfo(file);
    } else {
        showError('Please select a valid PDF file.');
    }
}

function displayFileInfo(file) {
    fileName.textContent = file.name;
    fileInfo.style.display = 'flex';
    processBtn.style.display = 'block';
}

function removeFile() {
    currentFile = null;
    fileInput.value = '';
    fileInfo.style.display = 'none';
    processBtn.style.display = 'none';
}

// Upload document
async function uploadDocument() {
    if (!currentFile) {
        showError('Please select a file first.');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', currentFile);
    
    // Show loading
    uploadLoading.style.display = 'block';
    processBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentSessionId = data.session_id;
            currentDocName.textContent = data.filename;
            showChatSection();
        } else {
            showError(data.error || 'Failed to upload document.');
        }
    } catch (error) {
        showError('Error uploading document: ' + error.message);
    } finally {
        uploadLoading.style.display = 'none';
        processBtn.disabled = false;
    }
}

// Chat functions
async function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message) return;
    if (!currentSessionId) {
        showError('Please upload a document first.');
        return;
    }
    
    // Clear input
    chatInput.value = '';
    
    // Add user message
    addMessage(message, 'user');
    
    // Disable input while processing
    setInputState(false);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addMessage(data.response, 'ai');
        } else {
            addMessage('Error: ' + (data.error || 'Failed to get response.'), 'ai');
        }
    } catch (error) {
        addMessage('Error: ' + error.message, 'ai');
    } finally {
        setInputState(true);
        chatInput.focus();
    }
}

function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setInputState(enabled) {
    chatInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
    
    if (enabled) {
        sendIcon.style.display = 'inline';
        btnSpinner.style.display = 'none';
    } else {
        sendIcon.style.display = 'none';
        btnSpinner.style.display = 'block';
    }
}

// UI transitions
function showChatSection() {
    uploadSection.style.display = 'none';
    chatSection.style.display = 'flex';
}

function resetToUpload() {
    // Clear session
    if (currentSessionId) {
        clearSession(currentSessionId);
    }
    
    currentSessionId = null;
    currentFile = null;
    
    // Reset UI
    chatSection.style.display = 'none';
    uploadSection.style.display = 'block';
    
    // Clear chat
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <p>👋 Hello! Your document has been uploaded successfully.</p>
            <p>You can now ask me questions about the content. Try asking:</p>
            <ul>
                <li>What is the total budget mentioned in this document?</li>
                <li>When is the project deadline?</li>
                <li>Who are the key stakeholders?</li>
                <li>What are the next steps outlined?</li>
            </ul>
        </div>
    `;
    
    // Reset file input
    removeFile();
}

// Clear session
async function clearSession(sessionId) {
    try {
        await fetch(`${API_BASE_URL}/clear/${sessionId}`, {
            method: 'DELETE'
        });
    } catch (error) {
        console.error('Error clearing session:', error);
    }
}

// Error handling
function showError(message) {
    alert(message);
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (currentSessionId) {
        clearSession(currentSessionId);
    }
});