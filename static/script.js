const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const lumeInance = document.querySelector('.lume-inance');

// Delete Modal Elements
let pendingDeleteTarget = null;
let pendingDeleteType = null;
const deleteModal = document.getElementById('delete-modal');
const deleteVerifyInput = document.getElementById('delete-verify-input');
const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
const deleteTargetNameDisplay = document.getElementById('delete-target-name');
const deleteEntityType = document.getElementById('delete-entity-type');

// INITIAL ANIMATIONS
gsap.from(".bento-card", {
    duration: 1.2,
    y: 50,
    opacity: 0,
    stagger: 0.2,
    ease: "power4.out"
});

// Lume-inance follow effect
document.addEventListener('mousemove', (e) => {
    gsap.to(lumeInance, {
        duration: 0.8,
        x: e.clientX - 300,
        y: e.clientY - 300,
        ease: "power2.out"
    });
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
            body: JSON.stringify({ message })
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

        // Update stats if present in response (LUME is System Master)
        if (data.stats) {
            updateStats(data.stats);
        }
    } catch (err) {
        appendMessage('bot', "System error. Intelligence link severed. Reconnecting...");
    }
}

function updateStats(stats) {
    if (stats.revenue) {
        gsap.to("#stat-revenue", {
            duration: 1,
            innerText: stats.revenue,
            snap: { innerText: 1 },
            onUpdate: function () {
                this.targets()[0].innerText = `$${parseFloat(this.targets()[0].innerText).toLocaleString()}`;
            }
        });
    }
    if (stats.projects) {
        gsap.to("#stat-projects", { duration: 1, innerText: stats.projects, snap: { innerText: 1 } });
    }
}

function quickCommand(cmd) {
    userInput.value = cmd;
    sendMessage();
}

function appendMessage(role, text) {
    const card = document.createElement('div');
    card.className = `editorial-card ${role}-card`;
    card.innerHTML = formatMarkdown(text);

    chatWindow.appendChild(card);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    gsap.from(card, { duration: 0.5, y: 20, opacity: 0, ease: "power2.out" });
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
    } else {
        confirmDeleteBtn.disabled = true;
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
