const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const lumeInance = document.querySelector('.lume-inance');

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
        appendMessage('bot', data.reply);

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

window.quickCommand = quickCommand;
