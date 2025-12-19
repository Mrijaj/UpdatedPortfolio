document.addEventListener('DOMContentLoaded', () => {

    // ===========================
    // 1. DARK MODE LOGIC
    // ===========================
    const themeIcon = document.getElementById('theme-icon');
    const body = document.body;
    const currentTheme = localStorage.getItem('theme');

    if (currentTheme === 'dark') {
        body.classList.add('dark-mode');
        if (themeIcon) {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
    }

    if (themeIcon) {
        themeIcon.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            if (body.classList.contains('dark-mode')) {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
                localStorage.setItem('theme', 'dark');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
                localStorage.setItem('theme', 'light');
            }
        });
    }

    // ===========================
    // 2. CHATBOT LOGIC
    // ===========================
    const chatToggleBtn = document.getElementById('chat-toggle-btn');
    const chatBox = document.getElementById('chat-box');
    const chatCloseBtn = document.getElementById('chat-close-btn');
    const minimizeBtn = document.getElementById('chat-minimize-btn');
    const clearBtn = document.getElementById('chat-clear-btn');
    const sendBtn = document.getElementById('send-btn');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');

    // --- HELPER: GET TIME GREETING ---
    function getTimeBasedGreeting() {
        const hour = new Date().getHours();
        if (hour < 12) return "Good Morning";
        if (hour < 18) return "Good Afternoon";
        return "Good Evening";
    }

    // --- A. LOAD STATE ON PAGE LOAD ---
    const savedState = localStorage.getItem('chatState');

    if (savedState === 'open') {
        chatBox.classList.remove('hidden');
        chatBox.classList.remove('minimized');
    } else if (savedState === 'minimized') {
        chatBox.classList.remove('hidden');
        chatBox.classList.add('minimized');
    } else {
        chatBox.classList.add('hidden');
    }

    const savedHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];

    if (savedHistory.length > 0) {
        chatMessages.innerHTML = '';
        savedHistory.forEach(msg => {
            addMessageToUI(msg.text, msg.type);
        });
    } else {
        resetChat();
    }

    // --- B. SAVE HELPERS ---
    function saveChatState(state) {
        localStorage.setItem('chatState', state);
    }

    function saveMessageHistory(text, type) {
        const history = JSON.parse(localStorage.getItem('chatHistory')) || [];
        history.push({ text: text, type: type });
        localStorage.setItem('chatHistory', JSON.stringify(history));
    }

    function resetChat() {
        const timeGreeting = getTimeBasedGreeting();
        const welcomeText = `${timeGreeting}! I am Elia, Ijaj's AI assistant. Ask me anything!`;
        addMessageToUI(welcomeText, 'bot-message');
        saveMessageHistory(welcomeText, 'bot-message');
    }

    // --- C. EVENT LISTENERS ---
    if (chatToggleBtn) {
        chatToggleBtn.addEventListener('click', () => {
            chatBox.classList.toggle('hidden');
            if (chatBox.classList.contains('hidden')) {
                saveChatState('hidden');
            } else {
                chatBox.classList.remove('minimized');
                saveChatState('open');
                if (window.innerWidth > 768 && userInput) {
                    setTimeout(() => userInput.focus(), 100);
                }
            }
        });
    }

    if (chatCloseBtn) {
        chatCloseBtn.addEventListener('click', () => {
            chatBox.classList.add('hidden');
            saveChatState('hidden');
        });
    }

    if (minimizeBtn) {
        minimizeBtn.addEventListener('click', () => {
            chatBox.classList.toggle('minimized');
            saveChatState(chatBox.classList.contains('minimized') ? 'minimized' : 'open');
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            localStorage.removeItem('chatHistory');
            chatMessages.innerHTML = '';
            resetChat();
        });
    }

    // --- D. TYPING INDICATOR LOGIC ---
    function showTypingIndicator() {
        const typingContainer = document.createElement('div');
        typingContainer.id = 'elia-typing';
        typingContainer.classList.add('message-container', 'bot-container');

        typingContainer.innerHTML = `
            <img src="https://cdn-icons-png.flaticon.com/512/4140/4140047.png" class="chat-avatar" alt="Elia">
            <div class="message bot-message typing-dots">
                <span></span><span></span><span></span>
            </div>
        `;
        chatMessages.appendChild(typingContainer);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('elia-typing');
        if (indicator) indicator.remove();
    }

    // --- E. SENDING MESSAGES ---
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === "") return;

        addMessageToUI(message, 'user-message');
        saveMessageHistory(message, 'user-message');
        userInput.value = '';

        // Show typing indicator while waiting for response
        showTypingIndicator();

        fetch('/get_response', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();
            addMessageToUI(data.response, 'bot-message');
            saveMessageHistory(data.response, 'bot-message');
        })
        .catch(error => {
            console.error('Error:', error);
            removeTypingIndicator();
            const errorMsg = "Sorry, connection error.";
            addMessageToUI(errorMsg, 'bot-message');
            saveMessageHistory(errorMsg, 'bot-message');
        });
    }

    function addMessageToUI(text, className) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message-container');

        if (className === 'bot-message') {
            messageContainer.classList.add('bot-container');
            const avatarImg = document.createElement('img');
            // Lady avatar URL
            avatarImg.src = 'https://cdn-icons-png.flaticon.com/512/4140/4140047.png';
            avatarImg.alt = 'Elia Avatar';
            avatarImg.classList.add('chat-avatar');
            messageContainer.appendChild(avatarImg);
        } else {
            messageContainer.classList.add('user-container');
        }

        const messageBubble = document.createElement('div');
        messageBubble.classList.add('message', className);
        messageBubble.textContent = text;

        messageContainer.appendChild(messageBubble);
        chatMessages.appendChild(messageContainer);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);

    if (userInput) {
        userInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') sendMessage();
        });
    }
});