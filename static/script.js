let currentThreadId = localStorage.getItem('lume_current_thread_id');

const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const historyList = document.getElementById('history-list');
const archiveChatBtn = document.getElementById('archive-chat-btn');

// Delete Modal Elements
let pendingDeleteTarget = null;
let pendingDeleteType = null;
const deleteModal = document.getElementById('delete-modal');
const deleteVerifyInput = document.getElementById('delete-verify-input');
const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
const deleteTargetNameDisplay = document.getElementById('delete-target-name');
const deleteEntityType = document.getElementById('delete-entity-type');

const previewModal = document.getElementById('preview-modal');
const pdfViewer = document.getElementById('pdf-viewer');
const docxViewer = document.getElementById('docx-viewer');
const closePreviewBtn = document.getElementById('close-preview-btn');
const downloadPreviewBtn = document.getElementById('download-preview-btn');
let currentPreviewUrl = null;

async function openPreview(url, name) {
    currentPreviewUrl = url;
    pdfViewer.classList.add('hidden');
    docxViewer.classList.add('hidden');
    pdfViewer.src = '';
    docxViewer.innerHTML = '';

    downloadPreviewBtn.href = url;
    downloadPreviewBtn.setAttribute('download', name);

    if (url.endsWith('.pdf')) {
        pdfViewer.src = url;
        pdfViewer.classList.remove('hidden');
    } else if (url.endsWith('.docx')) {
        docxViewer.classList.remove('hidden');
        try {
            const response = await fetch(url);
            const arrayBuffer = await response.arrayBuffer();
            await docx.renderAsync(arrayBuffer, docxViewer);
        } catch (e) {
            console.error("Error rendering DOCX", e);
            docxViewer.innerHTML = `<div style="color:white; padding: 2rem;">Error loading DOCX preview. Please download the file to view it.</div>`;
        }
    }

    previewModal.classList.remove('hidden');
}

async function loadChatHistory() {
    try {
        const res = await fetch('/api/chats');
        const data = await res.json();
        historyList.innerHTML = '';

        if (data.threads) {
            data.threads.forEach(t => {
                const threadDate = new Date(t.created_at || Date.now()).toLocaleDateString();
                const div = document.createElement('div');
                div.className = `history-item ${t.id === currentThreadId ? 'active' : ''}`;
                div.innerHTML = `
                    <div class="history-info" onclick="selectThread('${t.id}')">
                        <div class="history-date">${threadDate}</div>
                        <div class="history-title">
                            ${t.archived ? '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px; opacity: 0.7;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0110 0v4"></path></svg>' : ''}
                            ${t.title}
                        </div>
                    </div>
                    <button class="delete-thread-btn" onclick="event.stopPropagation(); deleteThread('${t.id}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6"/></svg>
                    </button>
                `;
                historyList.appendChild(div);
            });
        }
    } catch (e) {
        console.error("Error loading chat history", e);
    }
}

function toggleInputStatus(disabled) {
    userInput.disabled = disabled;
    sendBtn.disabled = disabled;
    archiveChatBtn.disabled = disabled;
    if (disabled) {
        userInput.placeholder = "This chat is archived and read-only.";
        archiveChatBtn.style.opacity = "0.5";
        archiveChatBtn.style.cursor = "not-allowed";
        archiveChatBtn.textContent = "Archived";
    } else {
        userInput.placeholder = "Enter command...";
        archiveChatBtn.style.opacity = "1";
        archiveChatBtn.style.cursor = "pointer";
        archiveChatBtn.textContent = "Archive Chat";
        userInput.focus();
    }
}

async function selectThread(id) {
    currentThreadId = id;
    localStorage.setItem('lume_current_thread_id', id);
    loadChatHistory(); // Update active state in UI

    try {
        const res = await fetch(`/api/chats/${id}`);
        const data = await res.json();

        chatWindow.innerHTML = '';

        if (data.thread && data.thread.messages) {
            data.thread.messages.forEach(msg => {
                const type = msg.role === 'assistant' ? 'bot' : 'user';
                appendMessage(type, msg.content, true); // skip animation
            });
            chatWindow.scrollTop = chatWindow.scrollHeight;

            // Lock/Unlock input based on archival state
            toggleInputStatus(!!data.thread.archived);
        }
    } catch (e) {
        console.error("Error loading thread", e);
    }
}

async function deleteThread(id) {
    if (!confirm("Are you sure you want to delete this conversation?")) return;

    try {
        const res = await fetch(`/api/chats/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.status === 'success') {
            if (currentThreadId === id) {
                newChatBtn.click();
            } else {
                loadChatHistory();
            }
        }
    } catch (e) {
        console.error("Error deleting thread", e);
    }
}

newChatBtn.addEventListener('click', () => {
    currentThreadId = null;
    localStorage.removeItem('lume_current_thread_id');
    chatWindow.innerHTML = '';

    toggleInputStatus(false);

    // Hide progress bar just in case
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) progressContainer.classList.add('hidden');

    loadChatHistory();
    appendMessage('bot', 'Welcome. I am LUME. Your business intelligence is loaded and ready. How shall we operate today?');
});

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    userInput.value = '';
    appendMessage('user', message);

    // Show Progress Bar
    const progressContainer = document.getElementById('progress-container');
    const progressFill = document.getElementById('progress-fill');
    const progressPercent = document.getElementById('progress-percent');

    progressContainer.classList.remove('hidden');
    progressFill.style.transition = 'width 4s cubic-bezier(0.1, 0.5, 0.3, 1)';
    progressFill.style.width = '90%';

    let pct = 0;
    progressPercent.textContent = "0%";
    const pctInterval = setInterval(() => {
        if (pct < 88) {
            pct += Math.random() * 15;
            if (pct > 88) pct = 88;
            progressPercent.textContent = `${Math.floor(pct)}%`;
        }
    }, 400);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, thread_id: currentThreadId })
        });
        const data = await response.json();

        // Complete Progress
        clearInterval(pctInterval);
        progressPercent.textContent = '100%';
        progressFill.style.transition = 'width 0.3s ease-out';
        progressFill.style.width = '100%';
        setTimeout(() => {
            progressContainer.classList.add('hidden');
            progressFill.style.width = '0%';
            progressPercent.textContent = '0%';
        }, 600);

        // Result Handling
        let botReply = data.reply;
        const attachments = data.attachments || [];

        // Update currentThreadId if this was a new chat
        if (data.thread_id && !currentThreadId) {
            currentThreadId = data.thread_id;
            localStorage.setItem('lume_current_thread_id', currentThreadId);
        }

        const deleteModalMatch = botReply.match(/\[ACTION:DELETE_MODAL:(.+?)\]/);
        if (deleteModalMatch) {
            try {
                const modalData = JSON.parse(deleteModalMatch[1]);
                pendingDeleteTarget = modalData.name;
                pendingDeleteType = modalData.type;

                botReply = botReply.replace(deleteModalMatch[0], '').trim();

                deleteTargetNameDisplay.textContent = pendingDeleteTarget;
                deleteEntityType.textContent = pendingDeleteType;
                deleteVerifyInput.value = '';
                confirmDeleteBtn.disabled = true;
                deleteModal.classList.remove('hidden');
            } catch (e) {
                console.error("Failed to parse DELETE_MODAL data", e);
            }
        }

        appendMessage('bot', botReply, false, attachments);
        loadChatHistory();

    } catch (err) {
        console.error("Chat error:", err);
        appendMessage('bot', "System error. Intelligence link severed. Reconnecting...");
    }
}

function quickCommand(cmd) {
    userInput.value = cmd;
    sendMessage();
}

function appendMessage(role, text, skipAnimation = false, attachments = []) {
    const card = document.createElement('div');
    card.className = `editorial-card ${role}-card`;

    const textContent = document.createElement('div');
    textContent.className = 'message-content';
    textContent.innerHTML = formatMarkdown(text);

    card.appendChild(textContent);
    chatWindow.appendChild(card);

    // Render attachments if any
    if (attachments && attachments.length > 0) {
        const attachContainer = document.createElement('div');
        attachContainer.className = 'attachment-container';

        attachments.forEach(file => {
            const thumb = document.createElement('div');
            thumb.className = 'file-thumbnail';
            thumb.innerHTML = `
                <div class="file-icon-wrapper">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                </div>
                <div class="file-info">
                    <span class="file-name">${file.name}</span>
                    <span class="file-meta">${file.type.toUpperCase()} • View</span>
                </div>
                <div class="file-actions">
                    <button class="thumb-btn view-btn">Quick View</button>
                    <a href="${file.url}" download class="thumb-btn">Download</a>
                </div>
            `;

            thumb.addEventListener('click', () => openPreview(file.url, file.name));
            thumb.querySelector('.view-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                openPreview(file.url, file.name);
            });

            attachContainer.appendChild(thumb);
        });
        card.appendChild(attachContainer);
    }

    chatWindow.scrollTop = chatWindow.scrollHeight;

    if (!skipAnimation && window.gsap) {
        gsap.from(card, { duration: 0.5, y: 20, opacity: 0, ease: "power2.out" });
    }
}

function formatMarkdown(text) {
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" class="chat-link" target="_blank">$1</a>')
        .replace(/### (.*?)\n/g, '<h3 style="font-family: var(--headline-serif); margin:1rem 0 0.5rem 0;">$1</h3>')
        .replace(/^- (.*?)$/gm, '<li style="margin-left: 1.5rem; list-style-type: disc;">$1</li>')
        .replace(/\n/g, '<br>');
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// Archive Chat Event Listener
archiveChatBtn.addEventListener('click', async () => {
    if (!currentThreadId) {
        appendMessage('bot', "No active chat to archive.");
        return;
    }

    const clientName = prompt("Enter the Exact Client Name to archive this chat memory under:");
    if (!clientName) return;

    // Get the client ID from the backend.
    archiveChatBtn.disabled = true;
    archiveChatBtn.textContent = "Archiving...";

    try {
        const response = await fetch(`/api/chats/${currentThreadId}/archive`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ client_id: clientName }) // Backend now resolves name to ID
        });

        const data = await response.json();
        if (data.status === 'success') {
            const ext = data.extraction;
            let summaryHtml = `### ✅ Chat Archived & Memory Updated\n\n`;
            summaryHtml += `**Summary:** ${ext.summary}\n\n`;

            if (ext.memory) summaryHtml += `**New Memory:** ${ext.memory}\n\n`;

            const prefs = Object.entries(ext.preferences);
            if (prefs.length > 0) {
                summaryHtml += `**Updated Preferences:**\n`;
                prefs.forEach(([k, v]) => {
                    summaryHtml += `- ${k}: ${v}\n`;
                });
            }

            appendMessage('bot', summaryHtml);
            toggleInputStatus(true);
            loadChatHistory(); // Update 'archived' state icons if implemented
        } else {
            appendMessage('bot', `❌ Archival Failed: ${data.message}`);
        }
    } catch (err) {
        console.error("Error archiving chat:", err);
        appendMessage('bot', "❌ System error while archiving chat.");
    } finally {
        if (!currentThreadId || !archiveChatBtn.disabled) {
            archiveChatBtn.disabled = false;
            archiveChatBtn.textContent = "Archive Chat";
        }
    }
});

// Modal Event Listeners
deleteVerifyInput.addEventListener('input', (e) => {
    if (e.target.value === pendingDeleteTarget) {
        confirmDeleteBtn.disabled = false;
        confirmDeleteBtn.classList.add('hover:bg-red-500/30');
    } else {
        confirmDeleteBtn.disabled = true;
        confirmDeleteBtn.classList.remove('hover:bg-red-500/30');
    }
});

cancelDeleteBtn.addEventListener('click', () => {
    deleteModal.classList.add('hidden');
    pendingDeleteTarget = null;
    appendMessage("bot", `Deletion cancelled.`);
});

confirmDeleteBtn.addEventListener('click', async () => {
    deleteModal.classList.add('hidden');
    appendMessage("bot", `Deleting ${pendingDeleteTarget}...`);

    try {
        const response = await fetch('/api/delete-entity', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                target_name: pendingDeleteTarget,
                entity_type: pendingDeleteType
            })
        });

        const result = await response.json();
        if (result.status === 'success') {
            appendMessage("bot", `✅ ${pendingDeleteTarget} has been permanently deleted.`);
        } else {
            appendMessage("bot", `❌ Deletion failed: ${result.message}`);
        }
    } catch (e) {
        console.error("Error deleting entity", e);
        appendMessage("bot", `❌ System error during deletion.`);
    }
    pendingDeleteTarget = null;
});


// Preview Interceptor (Event Delegation)
chatWindow.addEventListener('click', (e) => {
    const link = e.target.closest('.chat-link');
    if (link) {
        const url = link.getAttribute('href');
        if (url.endsWith('.pdf') || url.endsWith('.docx')) {
            e.preventDefault();
            const fileName = url.split('/').pop();
            openPreview(url, fileName);
        }
    }
});

const sendToClientBtn = document.getElementById('send-to-client-btn');

sendToClientBtn.addEventListener('click', async () => {
    if (!currentPreviewUrl) {
        alert("No document selected for sending.");
        return;
    }

    sendToClientBtn.disabled = true;
    sendToClientBtn.textContent = "Sending...";

    try {
        const response = await fetch('/api/send-document', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_url: currentPreviewUrl })
        });
        const data = await response.json();

        if (data.status === 'success') {
            appendMessage('bot', `✅ ${data.message}`);
            previewModal.classList.add('hidden');
            pdfViewer.src = '';
        } else {
            appendMessage('bot', `❌ ${data.message}`);
        }
    } catch (err) {
        console.error("Error sending document:", err);
        appendMessage('bot', "❌ System error while sending document.");
    } finally {
        sendToClientBtn.disabled = false;
        sendToClientBtn.textContent = "Send to Client";
    }
});

closePreviewBtn.addEventListener('click', () => {
    previewModal.classList.add('hidden');
    pdfViewer.src = '';
    docxViewer.innerHTML = '';
});

// Close modals on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        previewModal.classList.add('hidden');
        deleteModal.classList.add('hidden');
        pdfViewer.src = '';
        docxViewer.innerHTML = '';
    }
});

window.quickCommand = quickCommand;

document.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
    if (currentThreadId) {
        selectThread(currentThreadId);
    } else {
        appendMessage('bot', 'Welcome. I am LUME. Your business intelligence is loaded and ready. How shall we operate today?');
    }
    userInput.focus();

    // Add Lume-inance if it still exists
    const lumeInance = document.querySelector('.lume-inance');
    if (lumeInance) {
        document.addEventListener('mousemove', (e) => {
            gsap.to(lumeInance, {
                duration: 0.8,
                x: e.clientX - 300,
                y: e.clientY - 300,
                ease: "power2.out"
            });
        });
    }
});
