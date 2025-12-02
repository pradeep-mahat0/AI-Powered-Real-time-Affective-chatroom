// --- DOM Elements ---
const authContainer = document.getElementById('auth-container');
const chatContainer = document.getElementById('chat-container');
const authForm = document.getElementById('auth-form');
const authTitle = document.getElementById('auth-title');
const toggleAuthLink = document.getElementById('toggle-auth');
const authError = document.getElementById('auth-error');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const logoutBtn = document.getElementById('logout-btn');
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-text');
const messagesDiv = document.getElementById('messages');
const moodEmoji = document.getElementById('mood-emoji');
const moodText = document.getElementById('mood-text');
const summaryBtn = document.getElementById('summary-btn');

// --- State Variables ---
let ws;
let isLogin = true;
let currentUser = null;
let moodInterval;
const emotionEmojis = {
    'admiration': '😍', 'amusement': '😄', 'anger': '😠', 'annoyance': '😒', 
    'approval': '👍', 'caring': '🤗', 'confusion': '😕', 'curiosity': '🤔', 
    'desire': '😏', 'disappointment': '😞', 'disapproval': '👎', 'disgust': '🤢', 
    'embarrassment': '😳', 'excitement': '🤩', 'fear': '😨', 'gratitude': '🙏', 
    'grief': '😥', 'joy': '😊', 'love': '❤️', 'nervousness': '😬', 
    'optimism': '🙂', 'pride': '😎', 'realization': '💡', 'relief': '😌', 
    'remorse': '😔', 'sadness': '😢', 'surprise': '😮', 'neutral': '😐',
    'unknown': '💬'
};

// --- Authentication Logic ---
toggleAuthLink.addEventListener('click', (e) => {
    e.preventDefault();
    isLogin = !isLogin;
    authTitle.textContent = isLogin ? 'Login' : 'Sign Up';
    toggleAuthLink.innerHTML = isLogin ? 'Sign up for an account' : 'Login to your account';
    authError.textContent = '';
});

authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = usernameInput.value;
    const password = passwordInput.value;
    const endpoint = isLogin ? '/login' : '/signup';
    
    try {
        authError.textContent = '';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Authentication failed');
        }
        if (isLogin) {
            const data = await response.json();
            // UPDATED: Using sessionStorage to keep login separate for each tab
            sessionStorage.setItem('token', data.access_token);
            await enterChat();
        } else {
            alert('Signup successful! Please log in.');
            isLogin = true;
            authTitle.textContent = 'Login';
            toggleAuthLink.innerHTML = 'Sign up for an account';
        }
    } catch (error) {
        authError.textContent = error.message;
    }
});

logoutBtn.addEventListener('click', () => {
    // UPDATED: Using sessionStorage to keep login separate for each tab
    sessionStorage.removeItem('token');
    currentUser = null;
    if (ws) ws.close();
    if (moodInterval) clearInterval(moodInterval);
    authContainer.style.display = 'flex';
    chatContainer.classList.add('hidden');
});

// --- Chat Logic ---
async function enterChat() {
    // UPDATED: Using sessionStorage to keep login separate for each tab
    const token = sessionStorage.getItem('token');
    if (!token) { logoutBtn.click(); return; }

    try {
         const response = await fetch('/me', { headers: { 'Authorization': `Bearer ${token}` } });
         if (!response.ok) throw new Error('Could not fetch user details.');
         currentUser = await response.json();
    } catch(e) {
        console.error(e); logoutBtn.click(); return;
    }

    authContainer.style.display = 'none';
    chatContainer.classList.remove('hidden');

    await fetchMessageHistory(token);
    await updateMood(token);
    
    moodInterval = setInterval(() => updateMood(token), 5000);
    
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws?token=${token}`);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'chat_message') {
            appendMessage(data);
        } else if (data.type === 'system_alert') {
            appendSystemAlert(data.content);
        } else if (data.type === 'emotion_update') {
            // NEW: Handle the emotion update
            updateMessageEmotion(data.message_id, data.emotion);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        alert("Connection error. Please log in again.");
        logoutBtn.click();
    };
}

// NEW: Function to update an existing message's emoji
function updateMessageEmotion(messageId, emotion) {
    // Find the emoji span for the specific message
    const emojiSpan = document.getElementById(`emoji-${messageId}`);
    
    if (emojiSpan) {
        const newEmoji = emotionEmojis[emotion] || emotionEmojis['unknown'];
        emojiSpan.textContent = newEmoji;
        emojiSpan.title = `Detected emotion: ${emotion}`;
        
        // Optional: Add a subtle pulse animation
        emojiSpan.classList.add('pulse-animation');
        setTimeout(() => {
            emojiSpan.classList.remove('pulse-animation');
        }, 500);
    }
}

async function updateMood(token) {
    try {
        const response = await fetch('/mood', { headers: { 'Authorization': `Bearer ${token}` } });
        if (!response.ok) return;
        const data = await response.json();
        moodEmoji.textContent = emotionEmojis[data.mood] || emotionEmojis['neutral'];
        moodText.textContent = data.mood;
    } catch (error) {
        console.error("Mood fetch error:", error);
    }
}

async function fetchMessageHistory(token) {
    try {
        const response = await fetch('/messages', { headers: { 'Authorization': `Bearer ${token}` } });
        if (!response.ok) throw new Error('Failed to fetch history');
        const history = await response.json();
        messagesDiv.innerHTML = '';
        history.forEach(msg => appendMessage(msg, false));
    } catch (error) { console.error("History fetch error:", error); }
}

messageForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const message = messageInput.value;
    if (message.trim() && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(message);
        messageInput.value = '';
    }
});

function appendSystemAlert(content) {
    const item = document.createElement('div');
    item.className = 'text-center text-sm text-yellow-400 italic py-2 font-semibold';
    item.textContent = `⚠️ ${content}`;
    messagesDiv.appendChild(item);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function appendMessage(msg, animate = true) {
    const isSent = currentUser && msg.username === currentUser.username;
    
    if (msg.username === 'System') {
        const item = document.createElement('div');
        item.className = 'text-center text-sm text-slate-400 italic py-2';
        item.textContent = msg.content;
        messagesDiv.appendChild(item);
    } else {
        const emoji = emotionEmojis[msg.emotion] || emotionEmojis['unknown'];
        const avatarInitial = msg.username ? msg.username.charAt(0).toUpperCase() : '?';
        const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

        const messageWrapper = document.createElement('div');
        messageWrapper.id = `message-${msg.id}`; 
        messageWrapper.className = `flex items-end gap-2 ${isSent ? 'justify-end' : 'justify-start'}`;
        if (animate) messageWrapper.classList.add('fade-in');

        const avatar = `
            <div class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-indigo-500 text-white font-bold text-sm">
                ${avatarInitial}
            </div>
        `;

        const messageBubble = document.createElement('div');
        messageBubble.className = 'max-w-xs md:max-w-md';
        messageBubble.innerHTML = `
            <div class="flex items-center gap-2 ${isSent ? 'justify-end' : ''}">
               <p class="text-sm font-semibold ${isSent ? 'text-indigo-300' : 'text-gray-300'}">${msg.username}</p>
               <p class="text-xs text-slate-400">${timestamp}</p>
            </div>
            <div class="mt-1 flex items-end gap-2 p-3 rounded-lg ${isSent ? 'bg-indigo-600' : 'bg-slate-700'}">
                <p class="text-white break-words"></p>
                <span id="emoji-${msg.id}" class="text-xl" title="Detected emotion: ${msg.emotion}">${emoji}</span>
            </div>
        `;
        messageBubble.querySelector('p.break-words').textContent = msg.content;

        messageWrapper.innerHTML = `
            ${!isSent ? avatar : ''}
            ${isSent ? avatar : ''}
        `;

        // Insert the bubble in the correct place
        if (!isSent) {
            messageWrapper.insertAdjacentElement('beforeend', messageBubble);
        } else {
            messageWrapper.insertAdjacentElement('afterbegin', messageBubble);
        }
        
        messagesDiv.appendChild(messageWrapper);
    }

    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function fetchAndShowSummary() {
    const token = sessionStorage.getItem('token');
    if (!token) return;

    summaryBtn.textContent = 'Generating...';
    summaryBtn.disabled = true;

    try {
        const response = await fetch('/summary', { 
            headers: { 'Authorization': `Bearer ${token}` } 
        });

        if (!response.ok) {
            throw new Error('Failed to fetch summary.');
        }

        const data = await response.json();
        
        // Store the summary in session storage for the next page to access.
        sessionStorage.setItem('chatSummary', data.summary);
        
        // Redirect the browser to the new summary page.
        window.location.href = '/summary-page';

    } catch (error) {
        console.error("Summary fetch error:", error);
        alert("Could not generate a summary at this time.");
        // Restore the button's state only if an error occurs.
        summaryBtn.textContent = 'Get Summary';
        summaryBtn.disabled = false;
    } 
}

// --- Event Listeners and Initial Load ---
summaryBtn.addEventListener('click', fetchAndShowSummary);

document.addEventListener('DOMContentLoaded', () => {
    // UPDATED: Using sessionStorage to keep login separate for each tab
    if (sessionStorage.getItem('token')) {
        enterChat();
    } else {
        authContainer.style.display = 'flex';
    }
});

