let currentThreadId = null;

const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const historyList = document.getElementById('history-list');

// Delete Modal Elements
let pendingDeleteTarget = null;
let pendingDeleteType = null;
const deleteModal = document.getElementById('delete-modal');
const deleteVerifyInput = document.getElementById('delete-verify-input');
const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
const deleteTargetNameDisplay = document.getElementById('delete-target-name');
const deleteEntityType = document.getElementById('delete-entity-type');

async function loadChatHistory() {
    try {
        const res = await fetch('/api/chats');
        const data = await res.json();
        historyList.innerHTML = '';

        if (data.threads) {
            data.threads.forEach(t => {
                const div = document.createElement('div');
                div.className = `history-item ${t.id === currentThreadId ? 'active' : ''}`;
                div.onclick = () => selectThread(t.id);

                const date = new Date(t.updated_at).toLocaleDateString();
                div.innerHTML = `<div class="history-date">${date}</div><div class="history-title">${t.title}</div>`;
                historyList.appendChild(div);
            });
        }
    } catch (e) {
        console.error("Error loading chat history", e);
    }
}

async function selectThread(id) {
    currentThreadId = id;
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
        }
    } catch (e) {
        console.error("Error loading thread", e);
    }
}

newChatBtn.addEventListener('click', () => {
    currentThreadId = null;
    chatWindow.innerHTML = '';
    loadChatHistory();
    appendMessage('bot', 'Welcome. I am LUME. Your business intelligence is loaded and ready. How shall we operate today?');
});

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    userInput.value = '';
    appendMessage('user', message);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, thread_id: currentThreadId })
        });
        const data = await response.json();
        let botReply = data.reply;

        const deleteModalMatch = botReply.match(/\[ACTION:DELETE_MODAL:(.+?)\]/);
        if (deleteModalMatch) {
            try {
                const modalData = JSON.parse(deleteModalMatch[1]);
                pendingDeleteTarget = modalData.name;
                pendingDeleteType = modalData.type;

                // Remove the action block from visible message
                botReply = botReply.replace(deleteModalMatch[0], '').trim();

                // Setup and show modal
                deleteTargetNameDisplay.textContent = pendingDeleteTarget;
                deleteEntityType.textContent = pendingDeleteType;
                deleteVerifyInput.value = '';
                confirmDeleteBtn.disabled = true;
                deleteModal.classList.remove('hidden');
            } catch (e) {
                console.error("Failed to parse DELETE_MODAL data", e);
            }
        }

        appendMessage('bot', botReply);

        // Refresh sidebar so new chat gets a title/date
        loadChatHistory();

    } catch (err) {
        appendMessage('bot', "System error. Intelligence link severed. Reconnecting...");
    }
}

function quickCommand(cmd) {
    userInput.value = cmd;
    sendMessage();
}

function appendMessage(role, text, skipAnimation = false) {
    const card = document.createElement('div');
    card.className = `editorial-card ${role}-card`;

    // We create an interior div for the text to ensure our custom formatting
    // doesn't clobber the card's structure if we later add avatars, etc.
    const textContent = document.createElement('div');
    textContent.className = 'message-content';
    textContent.innerHTML = formatMarkdown(text);

    card.appendChild(textContent);

    chatWindow.appendChild(card);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    if (!skipAnimation && window.gsap) {
        gsap.from(card, { duration: 0.5, y: 20, opacity: 0, ease: "power2.out" });
    }
}

function formatMarkdown(text) {
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/### (.*?)\n/g, '<h3 style="font-family: var(--headline-serif); margin:1rem 0 0.5rem 0;">$1</h3>')
        .replace(/\n/g, '<br>');
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
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

window.quickCommand = quickCommand;

document.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
    if (!currentThreadId) {
        appendMessage('bot', 'Welcome. I am LUME. Your business intelligence is loaded and ready. How shall we operate today?');
    }

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
