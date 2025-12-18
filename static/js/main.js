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
    // 2. TERMINAL TOAST LOGIC
    // ===========================
    const logoLink = document.querySelector('.logo');
    const toast = document.getElementById("terminal-toast");

    if (logoLink && toast) {
        logoLink.addEventListener('click', function(e) {
            e.preventDefault();
            const targetUrl = this.href;
            toast.classList.add("show");
            setTimeout(function() {
                toast.classList.remove("show");
                window.location.href = targetUrl;
            }, 1200);
        });
    }

    // ===========================
    // 3. PERSISTENT CHATBOT LOGIC
    // ===========================
    const chatToggleBtn = document.getElementById('chat-toggle-btn');
    const chatBox = document.getElementById('chat-box');
    const chatCloseBtn = document.getElementById('chat-close-btn');
    const minimizeBtn = document.getElementById('chat-minimize-btn');
    const clearBtn = document.getElementById('chat-clear-btn'); // <--- NEW
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
    // 1. Load UI State
    const savedState = localStorage.getItem('chatState');

    if (savedState === 'open') {
        chatBox.classList.remove('hidden');
        chatBox.classList.remove('minimized');
    } else if (savedState === 'minimized') {
        chatBox.classList.remove('hidden');
        chatBox.classList.add('minimized');
        if(minimizeBtn) minimizeBtn.querySelector('i').classList.replace('fa-minus', 'fa-plus');
    } else {
        chatBox.classList.add('hidden');
    }

    // 2. Load Message History OR Create Welcome Message
    const savedHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];

    if (savedHistory.length > 0) {
        // History exists: Load it
        chatMessages.innerHTML = '';
        savedHistory.forEach(msg => {
            addMessageToUI(msg.text, msg.type);
        });
    } else {
        // No History: Create Dynamic Welcome Message
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
            chatBox.classList.remove('hidden');
            chatBox.classList.remove('minimized');
            saveChatState('open');
            if(minimizeBtn) minimizeBtn.querySelector('i').classList.replace('fa-plus', 'fa-minus');
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
            const icon = minimizeBtn.querySelector('i');
            if (chatBox.classList.contains('minimized')) {
                icon.classList.replace('fa-minus', 'fa-plus');
                saveChatState('minimized');
            } else {
                icon.classList.replace('fa-plus', 'fa-minus');
                saveChatState('open');
            }
        });
    }

    // NEW: CLEAR BUTTON LOGIC
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            // 1. Wipe Storage
            localStorage.removeItem('chatHistory');
            // 2. Wipe UI
            chatMessages.innerHTML = '';
            // 3. Reset with Greeting
            resetChat();
        });
    }

    function sendMessage() {
        const message = userInput.value.trim();
        if (message === "") return;

        addMessageToUI(message, 'user-message');
        saveMessageHistory(message, 'user-message');
        userInput.value = '';

        fetch('/get_response', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            addMessageToUI(data.response, 'bot-message');
            saveMessageHistory(data.response, 'bot-message');
        })
        .catch(error => {
            console.error('Error:', error);
            const errorMsg = "Sorry, connection error.";
            addMessageToUI(errorMsg, 'bot-message');
            saveMessageHistory(errorMsg, 'bot-message');
        });
    }

    function addMessageToUI(text, className) {
        const div = document.createElement('div');
        div.classList.add('message', className);
        div.textContent = text;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);

    if (userInput) {
        userInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') sendMessage();
        });
    }
});