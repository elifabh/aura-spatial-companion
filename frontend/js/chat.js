/**
 * Aura Chat Module
 * Manages the chat bottom sheet messages, typing indicator, and API calls.
 * Supports streaming responses (SSE) for ChatGPT-like typing effect.
 */

const AuraChat = (() => {
    const messagesContainer = () => document.getElementById('chat-messages');
    let typingEl = null;

    function createMessage(content, type = 'aura') {
        const msg = document.createElement('div');
        msg.className = `msg msg-${type}`;

        const avatar = document.createElement('div');
        avatar.className = 'msg-avatar';
        if (type === 'aura') {
            avatar.innerHTML = '<img src="/assets/icons/icon-512.png" alt="Aura">';
        } else {
            avatar.textContent = '👤';
        }

        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';

        // Check for memory indicators
        const isFromMemory = content.includes('Memory Insight') || 
                             content.includes('previous scan') || 
                             content.includes('last time') ||
                             content.includes('I remember') ||
                             content.includes('previously');

        // Simple markdown rendering
        const formatted = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/• /g, '&bull; ');

        let badgeHtml = '';
        if (isFromMemory && type === 'aura') {
            badgeHtml = '<div class="memory-badge">🧠 From memory</div>';
        }

        bubble.innerHTML = `${badgeHtml}<p>${formatted}</p>`;

        msg.appendChild(avatar);
        msg.appendChild(bubble);

        return msg;
    }

    function createStreamMessage() {
        /** Create an empty Aura message bubble for streaming tokens into. */
        const msg = document.createElement('div');
        msg.className = 'msg msg-aura';

        const avatar = document.createElement('div');
        avatar.className = 'msg-avatar';
        avatar.innerHTML = '<img src="/assets/icons/icon-512.png" alt="Aura">';

        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';
        bubble.innerHTML = '<p></p>';

        msg.appendChild(avatar);
        msg.appendChild(bubble);

        return { msg, textEl: bubble.querySelector('p') };
    }

    function addAuraMessage(content) {
        const container = messagesContainer();
        container.appendChild(createMessage(content, 'aura'));
        container.scrollTop = container.scrollHeight;
    }

    function addUserMessage(content) {
        const container = messagesContainer();
        container.appendChild(createMessage(content, 'user'));
        container.scrollTop = container.scrollHeight;
    }

    function showTyping() {
        if (typingEl) return;
        const container = messagesContainer();
        typingEl = document.createElement('div');
        typingEl.className = 'msg msg-aura';
        typingEl.id = 'typing-indicator';
        typingEl.innerHTML = `
            <div class="msg-avatar"><img src="/assets/icons/icon-512.png" alt="Aura"></div>
            <div class="msg-bubble">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        container.appendChild(typingEl);
        container.scrollTop = container.scrollHeight;
    }

    function hideTyping() {
        if (typingEl) {
            typingEl.remove();
            typingEl = null;
        }
    }

    function formatMarkdown(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/• /g, '&bull; ');
    }

    async function sendMessage(text) {
        if (!text.trim()) return;

        addUserMessage(text);
        showTyping();

        try {
            // Try streaming first (ChatGPT-like effect)
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, user_id: 'default' }),
            });

            if (!response.ok) throw new Error('Stream failed');

            hideTyping();

            // Create empty bubble and stream tokens into it
            const container = messagesContainer();
            const { msg, textEl } = createStreamMessage();
            container.appendChild(msg);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const token = line.slice(6);
                        if (token === '[DONE]') break;
                        if (token.startsWith('[ERROR:')) {
                            throw new Error(token);
                        }
                        fullText += token;
                        textEl.innerHTML = formatMarkdown(fullText);
                        container.scrollTop = container.scrollHeight;
                    }
                }
            }

            // Final format pass for memory badges
            if (fullText.includes('Memory Insight') || fullText.includes('I remember')) {
                const badge = document.createElement('div');
                badge.className = 'memory-badge';
                badge.textContent = '🧠 From memory';
                textEl.parentElement.insertBefore(badge, textEl);
            }

        } catch {
            hideTyping();
            // Fallback to standard endpoint
            try {
                const response = await AuraAPI.sendMessage(text);
                addAuraMessage(response.reply);
            } catch {
                addAuraMessage(
                    "I'm having trouble connecting right now. " +
                    "Make sure **Ollama** is running with Gemma 4 and try again."
                );
            }
        }
    }

    return { addAuraMessage, addUserMessage, showTyping, hideTyping, sendMessage };
})();

