/**
 * UniUs Chatbot — Frontend Logic
 * Handles splash screen, message sending, receiving, and UI interactions.
 */

const splashScreen = document.getElementById('splash-screen');
const appContainer = document.getElementById('app-container');
const messagesContainer = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');

let isWaiting = false;

// ============ Splash Screen ============
window.addEventListener('load', () => {
    // Show splash for 4 seconds, then morph transition to chat
    setTimeout(() => {
        splashScreen.classList.add('fade-out');
        
        // After splash fades (0.8s transition), show the app
        setTimeout(() => {
            splashScreen.style.display = 'none';
            appContainer.classList.add('visible');
            messageInput.focus();
        }, 800);
    }, 4000);
});

// ============ Auto-resize textarea ============
messageInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// ============ Send on Enter (Shift+Enter for new line) ============
messageInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ============ Send suggested question ============
function sendSuggested(btn) {
    const text = btn.textContent.trim();
    messageInput.value = text;
    sendMessage();
}

// ============ Format time ============
function getTimeString() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// ============ Simple markdown renderer ============
function renderMarkdown(text) {
    if (!text) return '';

    let html = text;

    // Escape HTML special characters first
    html = html.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;');

    // Headers
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Inline code
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Plain URLs
    html = html.replace(/(^|[^"=])(https?:\/\/[^\s<]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');

    // Unordered lists
    html = html.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Paragraphs
    const paragraphs = html.split(/\n\n+/);
    html = paragraphs
        .map(p => {
            p = p.trim();
            if (!p) return '';
            if (p.startsWith('<h') || p.startsWith('<ul') || p.startsWith('<ol')) return p;
            p = p.replace(/\n/g, '<br>');
            return `<p>${p}</p>`;
        })
        .filter(Boolean)
        .join('');

    return html;
}

// ============ Add message to chat ============
function addMessage(content, isUser = false, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'} ${isError ? 'error-message' : ''}`;

    const renderedContent = isUser ? `<p>${escapeHtml(content)}</p>` : renderMarkdown(content);
    const timeStr = getTimeString();

    if (isUser) {
        messageDiv.innerHTML = `
            <div class="message-avatar">👤</div>
            <div class="message-content">
                <div class="message-bubble">${renderedContent}</div>
                <span class="message-time">${timeStr}</span>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <img src="/static/logo.png" alt="UniUs">
            </div>
            <div class="message-content">
                <div class="message-bubble">${renderedContent}</div>
                <span class="message-time">${timeStr}</span>
            </div>
        `;
    }

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============ Typing indicator ============
function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <img src="/static/logo.png" alt="UniUs">
        </div>
        <div class="message-bubble">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
}

// ============ Scroll to bottom ============
function scrollToBottom() {
    requestAnimationFrame(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    });
}

// ============ Send message ============
async function sendMessage() {
    const text = messageInput.value.trim();

    if (!text || isWaiting) return;

    // Add user message
    addMessage(text, true);

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Disable input
    isWaiting = true;
    sendBtn.disabled = true;
    messageInput.disabled = true;

    // Show typing
    showTyping();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });

        hideTyping();

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            addMessage(data.error, false, true);
        } else {
            addMessage(data.response, false);
        }
    } catch (error) {
        hideTyping();
        console.error('Chat error:', error);
        addMessage(
            '😓 Connection error. Please make sure the server is running and try again.',
            false,
            true
        );
    } finally {
        isWaiting = false;
        sendBtn.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    }
}
