const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const lumeInance = document.querySelector('.lume-inance');

// Lume-inance follow effect
document.addEventListener('mousemove', (e) => {
    const x = e.clientX - 300;
    const y = e.clientY - 300;
    lumeInance.style.transform = `translate(${x}px, ${y}px)`;
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
    } catch (err) {
        appendMessage('bot', "I'm having trouble connecting right now. Please check your connection.");
    }
}

function appendMessage(role, text) {
    const card = document.createElement('div');
    card.className = `editorial-card ${role}-card`;
    
    let content = '';
    if (role === 'bot') {
        content = `<div class="ink-bar"></div><div class="card-content">${formatMarkdown(text)}</div>`;
    } else {
        content = `<div class="card-content">${text}</div>`;
    }
    
    card.innerHTML = content;
    chatWindow.appendChild(card);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function formatMarkdown(text) {
    // Simple formatter for visibility
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
               .replace(/### (.*?)\n/g, '<h3 class="card-headline">$1</h3>')
               .replace(/\n/g, '<br>');
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
