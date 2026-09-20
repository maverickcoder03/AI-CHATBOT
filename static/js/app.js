/**
 * Nova AI — Frontend Application Logic
 * Implements real-time SSE streaming, session history, voice STT/TTS,
 * markdown parsing, syntax highlighting, and export capabilities.
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- Application State ---
    const state = {
        currentSessionId: null,
        isStreaming: false,
        activeModel: localStorage.getItem('nova_model') || 'nova-general',
        systemPrompt: localStorage.getItem('nova_system_prompt') || '',
        theme: localStorage.getItem('nova_theme') || 'dark',
        sessions: [],
        recognition: null,
        isRecording: false,
        speechSynthesis: window.speechSynthesis || null,
        currentUtterance: null
    };

    // --- DOM Elements ---
    const elements = {
        sidebar: document.getElementById('sidebar'),
        toggleSidebarBtn: document.getElementById('toggleSidebarBtn'),
        closeSidebarBtn: document.getElementById('closeSidebarBtn'),
        newChatBtn: document.getElementById('newChatBtn'),
        searchChatsInput: document.getElementById('searchChatsInput'),
        sessionsList: document.getElementById('sessionsList'),
        themeToggleBtn: document.getElementById('themeToggleBtn'),
        settingsBtn: document.getElementById('settingsBtn'),
        clearAllBtn: document.getElementById('clearAllBtn'),
        currentChatTitle: document.getElementById('currentChatTitle'),
        activeModelName: document.getElementById('activeModelName'),
        exportBtn: document.getElementById('exportBtn'),
        exportMenu: document.getElementById('exportMenu'),
        exportMarkdownBtn: document.getElementById('exportMarkdownBtn'),
        exportJsonBtn: document.getElementById('exportJsonBtn'),
        messagesViewport: document.getElementById('messagesViewport'),
        welcomeContainer: document.getElementById('welcomeContainer'),
        messagesList: document.getElementById('messagesList'),
        scrollBottomBtn: document.getElementById('scrollBottomBtn'),
        messageInput: document.getElementById('messageInput'),
        sendBtn: document.getElementById('sendBtn'),
        voiceInputBtn: document.getElementById('voiceInputBtn'),
        statusIndicator: document.getElementById('statusIndicator'),
        settingsModal: document.getElementById('settingsModal'),
        closeSettingsBtn: document.getElementById('closeSettingsBtn'),
        modelSelect: document.getElementById('modelSelect'),
        systemPromptInput: document.getElementById('systemPromptInput'),
        saveSettingsBtn: document.getElementById('saveSettingsBtn'),
        resetSettingsBtn: document.getElementById('resetSettingsBtn'),
        toastContainer: document.getElementById('toastContainer')
    };

    // --- Marked.js Custom Renderer for Code Highlighting ---
    if (typeof marked !== 'undefined') {
        const renderer = new marked.Renderer();
        renderer.code = function(code, language) {
            const lang = language || 'text';
            const validLang = hljs.getLanguage(lang) ? lang : 'plaintext';
            const highlighted = hljs.highlight(code, { language: validLang }).value;
            
            return `
                <div class="code-block-container">
                    <div class="code-block-header">
                        <span>${lang}</span>
                        <button class="copy-code-btn" data-code="${encodeURIComponent(code)}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                            <span>Copy</span>
                        </button>
                    </div>
                    <pre><code class="hljs ${validLang}">${highlighted}</code></pre>
                </div>
            `;
        };
        marked.setOptions({ renderer, breaks: true, gfm: true });
    }

    // --- Initialize Application ---
    function init() {
        applyTheme(state.theme);
        initSpeechRecognition();
        fetchModels();
        loadSessions().then(() => {
            if (state.sessions.length > 0) {
                selectSession(state.sessions[0].id);
            } else {
                startNewChat();
            }
        });
        bindEvents();
    }

    // --- Theme Management ---
    function applyTheme(theme) {
        state.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('nova_theme', theme);

        const darkIcon = elements.themeToggleBtn.querySelector('.dark-icon');
        const lightIcon = elements.themeToggleBtn.querySelector('.light-icon');
        if (theme === 'dark') {
            darkIcon.style.display = 'inline-flex';
            lightIcon.style.display = 'none';
        } else {
            darkIcon.style.display = 'none';
            lightIcon.style.display = 'inline-flex';
        }
    }

    // --- Model Configuration ---
    async function fetchModels() {
        try {
            const res = await fetch('/api/models');
            const data = await res.json();
            if (data.models && elements.modelSelect) {
                elements.modelSelect.innerHTML = data.models.map(m => `
                    <option value="${m.id}" ${m.id === state.activeModel ? 'selected' : ''}>
                        ${m.name}
                    </option>
                `).join('');
            }
            updateActiveModelBadge();
        } catch (err) {
            console.error('Failed to fetch models:', err);
        }
    }

    function updateActiveModelBadge() {
        const option = elements.modelSelect ? elements.modelSelect.querySelector(`option[value="${state.activeModel}"]`) : null;
        elements.activeModelName.textContent = option ? option.textContent.trim() : state.activeModel;
    }

    // --- Sessions Management ---
    async function loadSessions() {
        try {
            const res = await fetch('/api/sessions');
            const data = await res.json();
            state.sessions = data.sessions || [];
            renderSessionsList();
        } catch (err) {
            console.error('Failed to load sessions:', err);
            elements.sessionsList.innerHTML = '<div class="sessions-loading">Could not load chats.</div>';
        }
    }

    function renderSessionsList(filterText = '') {
        const filtered = state.sessions.filter(s => 
            s.title.toLowerCase().includes(filterText.toLowerCase())
        );

        if (filtered.length === 0) {
            elements.sessionsList.innerHTML = `<div class="sessions-loading">${filterText ? 'No matching chats found.' : 'No conversations yet.'}</div>`;
            return;
        }

        elements.sessionsList.innerHTML = filtered.map(s => `
            <div class="session-item ${s.id === state.currentSessionId ? 'active' : ''}" data-id="${s.id}">
                <div class="session-item-title">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    <span>${escapeHtml(s.title)}</span>
                </div>
                <div class="session-item-actions">
                    <button class="action-icon-btn rename-session-btn" title="Rename" data-id="${s.id}">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                    </button>
                    <button class="action-icon-btn danger delete-session-btn" title="Delete" data-id="${s.id}">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            </div>
        `).join('');

        // Bind item events
        elements.sessionsList.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.session-item-actions')) return;
                selectSession(item.dataset.id);
            });
        });

        elements.sessionsList.querySelectorAll('.rename-session-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                promptRenameSession(btn.dataset.id);
            });
        });

        elements.sessionsList.querySelectorAll('.delete-session-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteSession(btn.dataset.id);
            });
        });
    }

    async function selectSession(sessionId) {
        if (state.isStreaming) return;
        state.currentSessionId = sessionId;
        renderSessionsList(elements.searchChatsInput.value);

        try {
            const res = await fetch(`/api/sessions/${sessionId}`);
            if (!res.ok) throw new Error('Session not found');
            const data = await res.json();
            
            elements.currentChatTitle.textContent = data.session.title;
            elements.welcomeContainer.style.display = data.messages.length === 0 ? 'flex' : 'none';
            elements.messagesList.innerHTML = '';

            data.messages.forEach(msg => {
                appendMessageBubble(msg.role, msg.content, false);
            });

            scrollToBottom();
        } catch (err) {
            console.error('Failed to load session history:', err);
            showToast('Error loading conversation history', 'danger');
        }
    }

    async function startNewChat() {
        if (state.isStreaming) return;
        try {
            const res = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: 'New Conversation' })
            });
            const data = await res.json();
            state.currentSessionId = data.session_id;
            elements.currentChatTitle.textContent = 'New Conversation';
            elements.messagesList.innerHTML = '';
            elements.welcomeContainer.style.display = 'flex';
            await loadSessions();
            elements.messageInput.focus();
        } catch (err) {
            console.error('Failed to create new chat:', err);
            showToast('Failed to start a new chat', 'danger');
        }
    }

    async function deleteSession(sessionId) {
        if (!confirm('Are you sure you want to delete this conversation?')) return;
        try {
            await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
            showToast('Conversation deleted');
            if (state.currentSessionId === sessionId) {
                state.currentSessionId = null;
                await loadSessions();
                if (state.sessions.length > 0) {
                    selectSession(state.sessions[0].id);
                } else {
                    startNewChat();
                }
            } else {
                await loadSessions();
            }
        } catch (err) {
            showToast('Failed to delete conversation', 'danger');
        }
    }

    async function promptRenameSession(sessionId) {
        const session = state.sessions.find(s => s.id === sessionId);
        const newTitle = prompt('Rename conversation:', session ? session.title : '');
        if (newTitle && newTitle.trim()) {
            try {
                await fetch(`/api/sessions/${sessionId}/rename`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: newTitle.trim() })
                });
                if (state.currentSessionId === sessionId) {
                    elements.currentChatTitle.textContent = newTitle.trim();
                }
                await loadSessions();
                showToast('Conversation renamed');
            } catch (err) {
                showToast('Failed to rename conversation', 'danger');
            }
        }
    }

    // --- Message Rendering & Bubbles ---
    function appendMessageBubble(role, content = '', isStreaming = false) {
        elements.welcomeContainer.style.display = 'none';

        const row = document.createElement('div');
        row.className = `message-row ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' 
            ? '<span>You</span>' 
            : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`;

        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        if (isStreaming) {
            bubble.innerHTML = `<span class="typing-indicator"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></span>`;
        } else {
            bubble.innerHTML = formatMessageContent(content);
        }

        contentWrapper.appendChild(bubble);

        // Add action toolbar for assistant messages
        if (role === 'assistant' && !isStreaming) {
            contentWrapper.appendChild(createMessageActions(content));
        }

        row.appendChild(avatar);
        row.appendChild(contentWrapper);
        elements.messagesList.appendChild(row);

        attachCodeCopyListeners(bubble);
        scrollToBottom();
        return { row, bubble, contentWrapper };
    }

    function formatMessageContent(text) {
        if (!text) return '';
        if (typeof marked !== 'undefined') {
            return marked.parse(text);
        }
        return escapeHtml(text).replace(/\n/g, '<br>');
    }

    function createMessageActions(content) {
        const actions = document.createElement('div');
        actions.className = 'message-actions';

        // Copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-action-btn';
        copyBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy`;
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(content);
            copyBtn.innerHTML = `✓ Copied!`;
            setTimeout(() => {
                copyBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy`;
            }, 2000);
        };

        // Text-to-speech button
        const speakBtn = document.createElement('button');
        speakBtn.className = 'message-action-btn';
        speakBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg> Read Aloud`;
        speakBtn.onclick = () => speakText(content);

        actions.appendChild(copyBtn);
        actions.appendChild(speakBtn);
        return actions;
    }

    function attachCodeCopyListeners(container) {
        container.querySelectorAll('.copy-code-btn').forEach(btn => {
            btn.onclick = () => {
                const code = decodeURIComponent(btn.dataset.code);
                navigator.clipboard.writeText(code);
                const originalText = btn.querySelector('span').textContent;
                btn.querySelector('span').textContent = 'Copied!';
                setTimeout(() => {
                    btn.querySelector('span').textContent = originalText;
                }, 2000);
            };
        });
    }

    // --- Streaming Chat Submission (SSE) ---
    async function handleSendMessage() {
        const text = elements.messageInput.value.trim();
        if (!text || state.isStreaming) return;

        elements.messageInput.value = '';
        adjustTextareaHeight();
        
        // Append user message
        appendMessageBubble('user', text, false);

        // Prepare streaming bubble for assistant
        state.isStreaming = true;
        setSendingState(true);
        const { bubble, contentWrapper } = appendMessageBubble('assistant', '', true);

        let accumulatedReply = '';

        try {
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: state.currentSessionId,
                    message: text,
                    model: state.activeModel,
                    system_prompt: state.systemPrompt
                })
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // Keep incomplete chunk in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.session_id && !state.currentSessionId) {
                                state.currentSessionId = data.session_id;
                            }
                            if (data.chunk) {
                                accumulatedReply += data.chunk;
                                bubble.innerHTML = formatMessageContent(accumulatedReply) + '<span class="streaming-cursor"></span>';
                                attachCodeCopyListeners(bubble);
                                scrollToBottom();
                            }
                            if (data.done) {
                                bubble.innerHTML = formatMessageContent(data.full_response || accumulatedReply);
                                contentWrapper.appendChild(createMessageActions(data.full_response || accumulatedReply));
                                attachCodeCopyListeners(bubble);
                            }
                            if (data.error) {
                                bubble.innerHTML = `<span style="color:var(--danger)">⚠️ Error: ${escapeHtml(data.error)}</span>`;
                            }
                        } catch (err) {
                            console.error('Error parsing SSE event:', err);
                        }
                    }
                }
            }

            await loadSessions();
        } catch (err) {
            console.error('Streaming request failed:', err);
            bubble.innerHTML = `<span style="color:var(--danger)">⚠️ Failed to connect to AI server. Please verify your connection.</span>`;
        } finally {
            state.isStreaming = false;
            setSendingState(false);
            scrollToBottom();
        }
    }

    function setSendingState(isSending) {
        elements.sendBtn.disabled = isSending;
        elements.statusIndicator.textContent = isSending ? '⚡ Streaming...' : '● Ready';
        elements.statusIndicator.style.color = isSending ? 'var(--accent-color)' : 'var(--success)';
    }

    // --- Voice Input (Speech-to-Text) ---
    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            elements.voiceInputBtn.style.display = 'none';
            return;
        }

        state.recognition = new SpeechRecognition();
        state.recognition.continuous = false;
        state.recognition.interimResults = true;
        state.recognition.lang = 'en-US';

        state.recognition.onstart = () => {
            state.isRecording = true;
            elements.voiceInputBtn.classList.add('recording');
            showToast('Listening... Speak now');
        };

        state.recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                transcript += event.results[i][0].transcript;
            }
            elements.messageInput.value = transcript;
            adjustTextareaHeight();
        };

        state.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            showToast(`Voice error: ${event.error}`, 'danger');
            stopRecording();
        };

        state.recognition.onend = () => {
            stopRecording();
        };
    }

    function toggleRecording() {
        if (!state.recognition) return;
        if (state.isRecording) {
            state.recognition.stop();
        } else {
            state.recognition.start();
        }
    }

    function stopRecording() {
        state.isRecording = false;
        elements.voiceInputBtn.classList.remove('recording');
    }

    // --- Text-to-Speech (TTS) ---
    function speakText(text) {
        if (!state.speechSynthesis) {
            showToast('Text-to-speech not supported by your browser', 'danger');
            return;
        }

        if (state.speechSynthesis.speaking) {
            state.speechSynthesis.cancel();
            return;
        }

        // Strip markdown before speaking
        const cleanText = text.replace(/```[\s\S]*?```/g, 'Code block omitted.')
                              .replace(/`([^`]+)`/g, '$1')
                              .replace(/[*_#]/g, '');

        state.currentUtterance = new SpeechSynthesisUtterance(cleanText);
        state.currentUtterance.rate = 1.0;
        state.speechSynthesis.speak(state.currentUtterance);
        showToast('Reading response aloud...');
    }

    // --- Export Capabilities ---
    async function exportChat(format) {
        if (!state.currentSessionId) {
            showToast('No active conversation to export', 'warning');
            return;
        }

        try {
            const res = await fetch(`/api/sessions/${state.currentSessionId}`);
            const data = await res.json();
            const session = data.session;
            const messages = data.messages;

            let fileContent = '';
            let fileName = `${session.title.replace(/[^a-zA-Z0-9]/g, '_')}_chat.${format === 'json' ? 'json' : 'md'}`;
            let mimeType = format === 'json' ? 'application/json' : 'text/markdown';

            if (format === 'json') {
                fileContent = JSON.stringify({ session, messages }, null, 2);
            } else {
                fileContent = `# ${session.title}\n*Exported on ${new Date().toLocaleString()}*\n\n---\n\n`;
                messages.forEach(m => {
                    fileContent += `### ${m.role === 'user' ? '👤 You' : '🤖 Nova AI'} (${m.created_at})\n\n${m.content}\n\n---\n\n`;
                });
            }

            const blob = new Blob([fileContent], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = fileName;
            a.click();
            URL.revokeObjectURL(url);
            showToast(`Exported as ${format.toUpperCase()}`);
            elements.exportMenu.classList.remove('show');
        } catch (err) {
            showToast('Export failed', 'danger');
        }
    }

    // --- Event Listeners ---
    function bindEvents() {
        // Toggle Sidebar
        elements.toggleSidebarBtn.onclick = () => {
            elements.sidebar.classList.toggle('collapsed');
            elements.sidebar.classList.toggle('open');
        };
        elements.closeSidebarBtn.onclick = () => {
            elements.sidebar.classList.remove('open');
        };

        // New Chat
        elements.newChatBtn.onclick = startNewChat;

        // Search chats
        elements.searchChatsInput.oninput = (e) => {
            renderSessionsList(e.target.value);
        };

        // Theme Toggle
        elements.themeToggleBtn.onclick = () => {
            applyTheme(state.theme === 'dark' ? 'light' : 'dark');
        };

        // Clear All
        elements.clearAllBtn.onclick = async () => {
            if (!confirm('Are you sure you want to clear ALL conversation history?')) return;
            await fetch('/api/clear', { method: 'POST' });
            showToast('All conversations cleared');
            startNewChat();
        };

        // Voice Input
        elements.voiceInputBtn.onclick = toggleRecording;

        // Send message
        elements.sendBtn.onclick = handleSendMessage;
        elements.messageInput.onkeydown = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        };

        // Auto-expand textarea
        elements.messageInput.oninput = adjustTextareaHeight;

        // Suggestion Cards
        document.querySelectorAll('.suggestion-card').forEach(card => {
            card.onclick = () => {
                elements.messageInput.value = card.dataset.prompt;
                adjustTextareaHeight();
                handleSendMessage();
            };
        });

        // Export dropdown
        elements.exportBtn.onclick = (e) => {
            e.stopPropagation();
            elements.exportMenu.classList.toggle('show');
        };
        document.onclick = (e) => {
            if (!e.target.closest('.dropdown')) {
                elements.exportMenu.classList.remove('show');
            }
        };
        elements.exportMarkdownBtn.onclick = () => exportChat('md');
        elements.exportJsonBtn.onclick = () => exportChat('json');

        // Settings Modal
        elements.settingsBtn.onclick = () => {
            elements.systemPromptInput.value = state.systemPrompt;
            elements.modelSelect.value = state.activeModel;
            elements.settingsModal.classList.add('show');
        };
        elements.closeSettingsBtn.onclick = () => {
            elements.settingsModal.classList.remove('show');
        };
        elements.settingsModal.onclick = (e) => {
            if (e.target === elements.settingsModal) elements.settingsModal.classList.remove('show');
        };

        elements.saveSettingsBtn.onclick = () => {
            state.activeModel = elements.modelSelect.value;
            state.systemPrompt = elements.systemPromptInput.value.trim();
            localStorage.setItem('nova_model', state.activeModel);
            localStorage.setItem('nova_system_prompt', state.systemPrompt);
            updateActiveModelBadge();
            elements.settingsModal.classList.remove('show');
            showToast('Settings saved successfully');
        };

        elements.resetSettingsBtn.onclick = () => {
            state.systemPrompt = '';
            elements.systemPromptInput.value = '';
            localStorage.removeItem('nova_system_prompt');
            showToast('Settings reset to default');
        };

        // Scroll button
        elements.messagesViewport.onscroll = () => {
            const isNearBottom = elements.messagesViewport.scrollHeight - elements.messagesViewport.scrollTop - elements.messagesViewport.clientHeight < 120;
            elements.scrollBottomBtn.style.display = isNearBottom ? 'none' : 'flex';
        };
        elements.scrollBottomBtn.onclick = scrollToBottom;

        // Global Shortcuts (Ctrl+K for new chat)
        window.onkeydown = (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                startNewChat();
            }
        };
    }

    // --- Helpers ---
    function adjustTextareaHeight() {
        elements.messageInput.style.height = 'auto';
        elements.messageInput.style.height = `${Math.min(elements.messageInput.scrollHeight, 160)}px`;
    }

    function scrollToBottom() {
        elements.messagesViewport.scrollTo({
            top: elements.messagesViewport.scrollHeight,
            behavior: 'smooth'
        });
    }

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        elements.toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Start App
    init();
});
