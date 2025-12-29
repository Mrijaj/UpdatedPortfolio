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
    const chatHeader = document.querySelector('.chat-header'); // Entire header is now handle
    const chatCloseBtn = document.getElementById('chat-close-btn');
    const clearBtn = document.getElementById('chat-clear-btn');
    const expandBtn = document.getElementById('chat-expand-btn');
    const sendBtn = document.getElementById('send-btn');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const eliaPopup = document.getElementById('elia-popup');

    // --- Modal Elements ---
    const confirmModal = document.getElementById('chat-confirm-modal');
    const confirmYes = document.getElementById('confirm-clear-yes');
    const confirmNo = document.getElementById('confirm-clear-no');

    // Track active requests/typing for the "Stop" functionality
    let eliaAbortController = null;

    // --- ELIA AUTO-POPUP LOGIC (REFINED) ---
    if (window.location.pathname === "/" || window.location.pathname.includes("home")) {
        // Wait 3 seconds to show the bubble
        setTimeout(() => {
            if (eliaPopup && chatBox.classList.contains('hidden')) {
                eliaPopup.classList.remove('hidden');

                // TIME LIMIT: Disappear after 7 seconds
                setTimeout(() => {
                    if (eliaPopup) {
                        eliaPopup.style.opacity = '0';
                        eliaPopup.style.transform = 'translateX(20px)'; // Slide back towards the button
                        setTimeout(() => eliaPopup.remove(), 500);
                    }
                }, 7000);
            }
        }, 3000);
    }

    // --- HELPER: GET TIME GREETING ---
    function getTimeBasedGreeting() {
        const hour = new Date().getHours();
        if (hour < 12) return "Good Morning";
        if (hour < 18) return "Good Afternoon";
        return "Good Evening";
    }

    // --- A. SESSION INITIALIZATION ---
    localStorage.removeItem('chatHistory');
    chatMessages.innerHTML = '';

    const savedState = localStorage.getItem('chatState');
    if (savedState === 'open') {
        chatBox.classList.remove('hidden');
    } else {
        chatBox.classList.add('hidden');
    }

    resetChat();

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
            if (eliaPopup) eliaPopup.remove();
            chatBox.classList.toggle('hidden');

            // Toggle Logic: The main button acts as minimize/maximize
            if (chatBox.classList.contains('hidden')) {
                saveChatState('hidden');
            } else {
                saveChatState('open');
                if (window.innerWidth > 768 && userInput) {
                    setTimeout(() => userInput.focus(), 100);
                }
            }
        });
    }

    // --- EXPAND FUNCTIONALITY (Fixed Icons) ---
    if (expandBtn) {
        expandBtn.addEventListener('click', () => {
            chatBox.classList.toggle('expanded');
            const icon = expandBtn.querySelector('i');
            if (chatBox.classList.contains('expanded')) {
                icon.classList.remove('fa-expand');
                icon.classList.add('fa-compress');
                expandBtn.title = "Compress Chat";
            } else {
                icon.classList.remove('fa-compress');
                icon.classList.add('fa-expand');
                expandBtn.title = "Expand Chat";
            }
        });
    }

    if (chatCloseBtn) {
        chatCloseBtn.addEventListener('click', () => {
            chatBox.classList.add('hidden');
            saveChatState('hidden');
        });
    }

    // --- MODAL CLEAR LOGIC ---
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (confirmModal) confirmModal.classList.remove('hidden');
        });
    }

    if (confirmNo) {
        confirmNo.addEventListener('click', () => {
            if (confirmModal) confirmModal.classList.add('hidden');
        });
    }

    if (confirmYes) {
        confirmYes.addEventListener('click', () => {
            localStorage.removeItem('chatHistory');
            chatMessages.innerHTML = '';
            resetChat();
            if (confirmModal) confirmModal.classList.add('hidden');
        });
    }

    // --- DRAG LOGIC (Full Header Handle with Phone Support) ---
    let isDragging = false;
    let xOffset = 0;
    let yOffset = 0;
    let initialX;
    let initialY;

    if (chatHeader) {
        // Desktop Support
        chatHeader.addEventListener('mousedown', dragStart);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', dragEnd);

        // Mobile Support
        chatHeader.addEventListener('touchstart', dragStart, { passive: false });
        document.addEventListener('touchmove', drag, { passive: false });
        document.addEventListener('touchend', dragEnd);
    }

    function dragStart(e) {
        // Prevents dragging if a button inside the header is clicked
        if (e.target.closest('button')) return;

        if (e.type === "touchstart") {
            initialX = e.touches[0].clientX - xOffset;
            initialY = e.touches[0].clientY - yOffset;
        } else {
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;
        }

        isDragging = true;
    }

    function drag(e) {
        if (isDragging) {
            e.preventDefault(); // Prevents background scroll on mobile

            let currentX, currentY;
            if (e.type === "touchmove") {
                currentX = e.touches[0].clientX - initialX;
                currentY = e.touches[0].clientY - initialY;
            } else {
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
            }

            xOffset = currentX;
            yOffset = currentY;
            chatBox.style.transform = `translate3d(${currentX}px, ${currentY}px, 0)`;
        }
    }

    function dragEnd() {
        isDragging = false;
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
        const sendIcon = sendBtn.querySelector('i');
        const headerSpan = document.querySelector('.chat-header span');

        if (eliaAbortController) {
            eliaAbortController.abort();
            eliaAbortController = null;
            removeTypingIndicator();

            const botMessages = chatMessages.querySelectorAll('.bot-message');
            const lastMsg = botMessages[botMessages.length - 1];

            if (lastMsg) {
                lastMsg.classList.add('message-aborted');
                const badge = document.createElement('div');
                badge.className = 'stop-badge';
                badge.innerHTML = '<i class="fas fa-stop-circle"></i> Response stopped';
                lastMsg.appendChild(badge);
            }

            finishAiResponse();
            return;
        }

        const message = userInput.value.trim();
        if (message === "") return;

        userInput.disabled = true;

        if (sendIcon) {
            sendIcon.classList.remove('fa-paper-plane');
            sendIcon.classList.add('fa-stop');
            sendBtn.title = "Stop Response";

            if (headerSpan) headerSpan.classList.add('is-typing');
        }

        addMessageToUI(message, 'user-message');
        saveMessageHistory(message, 'user-message');
        userInput.value = '';

        showTypingIndicator();

        eliaAbortController = new AbortController();

        fetch('/get_response', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message }),
            signal: eliaAbortController.signal
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();
            addMessageToUI(data.response, 'bot-message');
            saveMessageHistory(data.response, 'bot-message');
        })
        .catch(error => {
            if (error.name === 'AbortError') {
                console.log("Response stopped by user.");
            } else {
                console.error('Error:', error);
                removeTypingIndicator();
                addMessageToUI("Sorry, connection error.", 'bot-message');
                finishAiResponse();
            }
        });
    }

    // --- F. TYPEWRITER EFFECT HELPER ---
    function typeWriter(text, element, speed = 25) {
        let i = 0;
        element.textContent = "";

        const startedWithController = !!eliaAbortController;

        function type() {
            if (startedWithController && !eliaAbortController) {
                return;
            }

            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                chatMessages.scrollTop = chatMessages.scrollHeight;
                setTimeout(type, speed);
            } else {
                if (typeof marked !== 'undefined') {
                    element.innerHTML = marked.parse(text);
                }

                addCopyButtons();

                if (typeof Prism !== 'undefined') {
                    Prism.highlightAllUnder(element);
                }

                finishAiResponse();
            }
        }
        type();
    }

    function finishAiResponse() {
        eliaAbortController = null;
        userInput.disabled = false;
        sendBtn.disabled = false;

        const sendIcon = sendBtn.querySelector('i');
        const headerSpan = document.querySelector('.chat-header span');

        if (sendIcon) {
            sendIcon.classList.remove('fa-stop');
            sendIcon.classList.add('fa-paper-plane');
            sendBtn.title = "Send Message";
        }

        if (headerSpan) headerSpan.classList.remove('is-typing');

        userInput.focus();
    }

    function addMessageToUI(text, className, isHistory = false) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message-container');

        if (className === 'bot-message') {
            messageContainer.classList.add('bot-container');
            const avatarImg = document.createElement('img');
            avatarImg.src = 'https://cdn-icons-png.flaticon.com/512/4140/4140047.png';
            avatarImg.alt = 'Elia Avatar';
            avatarImg.classList.add('chat-avatar');
            messageContainer.appendChild(avatarImg);
        } else {
            messageContainer.classList.add('user-container');
        }

        const messageBubble = document.createElement('div');
        messageBubble.classList.add('message', className);

        messageContainer.appendChild(messageBubble);
        chatMessages.appendChild(messageContainer);

        if (className === 'bot-message' && !isHistory) {
            typeWriter(text, messageBubble);
        } else {
            if (typeof marked !== 'undefined') {
                messageBubble.innerHTML = marked.parse(text);
            } else {
                messageBubble.textContent = text;
            }

            addCopyButtons();

            if (typeof Prism !== 'undefined') {
                Prism.highlightAllUnder(messageBubble);
            }
        }

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // --- G. COPY CODE FUNCTIONALITY (With Robust Fallback) ---
    function addCopyButtons() {
        const codeBlocks = chatMessages.querySelectorAll('pre');

        codeBlocks.forEach((codeBlock) => {
            if (codeBlock.querySelector('.copy-code-btn')) return;

            const button = document.createElement('button');
            button.className = 'copy-code-btn';
            button.innerHTML = '<i class="far fa-copy"></i> Copy';
            button.title = "Copy to clipboard";

            button.addEventListener('click', () => {
                const codeElement = codeBlock.querySelector('code');
                const textToCopy = codeElement ? codeElement.innerText : codeBlock.innerText;

                if (navigator.clipboard && window.isSecureContext) {
                    navigator.clipboard.writeText(textToCopy)
                        .then(() => showCopySuccess(button))
                        .catch(err => console.error('Clipboard API failed:', err));
                } else {
                    const textArea = document.createElement("textarea");
                    textArea.value = textToCopy;
                    document.body.appendChild(textArea);
                    textArea.select();
                    try {
                        document.execCommand('copy');
                        showCopySuccess(button);
                    } catch (err) {
                        console.error('Fallback copy failed:', err);
                    }
                    document.body.removeChild(textArea);
                }
            });

            codeBlock.appendChild(button);
        });
    }

    function showCopySuccess(btn) {
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.innerHTML = '<i class="far fa-copy"></i> Copy';
            btn.classList.remove('copied');
        }, 2000);
    }

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);

    if (userInput) {
        userInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') sendMessage();
        });
    }
});