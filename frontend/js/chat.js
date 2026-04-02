/**
 * Aura Chat Module
 * Manages the chat interface, messages, and typing indicators.
 */

const AuraChat = (() => {
    const messagesContainer = () => document.getElementById('messages');
    let typingEl = null;

    function addMessage(content, type = 'aura') {
        const container = messagesContainer();
        const msg = document.createElement('div');
        msg.className = `message ${type}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = type === 'aura' ? '✦' : '👤';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Simple markdown-like rendering
        const formatted = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/• /g, '&bull; ');

        contentDiv.innerHTML = `<p>${formatted}</p>`;

        msg.appendChild(avatar);
        msg.appendChild(contentDiv);
        container.appendChild(msg);

        // Scroll to bottom
        const chatArea = document.getElementById('chat-area');
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function addAuraMessage(content) {
        addMessage(content, 'aura');
    }

    function addUserMessage(content) {
        addMessage(content, 'user');
    }

    function showTyping() {
        if (typingEl) return;
        const container = messagesContainer();
        typingEl = document.createElement('div');
        typingEl.className = 'message aura-message';
        typingEl.innerHTML = `
            <div class="message-avatar">✦</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        container.appendChild(typingEl);

        const chatArea = document.getElementById('chat-area');
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function hideTyping() {
        if (typingEl) {
            typingEl.remove();
            typingEl = null;
        }
    }

    async function sendMessage(text) {
        if (!text.trim()) return;

        addUserMessage(text);
        showTyping();

        try {
            const response = await AuraAPI.sendMessage(text);
            hideTyping();
            addAuraMessage(response.reply);
        } catch (error) {
            hideTyping();
            addAuraMessage(
                "I'm having trouble connecting to my brain right now. " +
                "Please make sure Ollama is running and try again."
            );
        }
    }

    return { addMessage, addAuraMessage, addUserMessage, showTyping, hideTyping, sendMessage };
})();
