document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');

    function getCoursesContext() {
        if (!window.coursesData || window.coursesData.length === 0) {
            return 'No courses available yet.';
        }
        return window.coursesData.map(course => 
            `- ${course.title}: ${course.description} (Category: ${course.category}, Level: ${course.level})`
        ).join('\n');
    }

    function buildSystemPrompt() {
        const coursesContext = getCoursesContext();
        return `You are StudyBuddy AI Assistant, a helpful and professional AI that helps users with general questions and course recommendations.

When users ask about course recommendations:
1. Ask clarifying questions about their interests, goals, skills, or needs if needed
2. Use the available courses information to suggest suitable courses
3. Be friendly and encouraging

Available courses:
${coursesContext}

Respond in Russian (or the language the user uses) in a clear, accurate, and user-friendly way.`;
    }

    function addMessage(content, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user' : 'ai'}`;
        messageDiv.textContent = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message ai typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        chatInput.value = '';
        sendBtn.disabled = true;
        chatInput.disabled = true;

        addTypingIndicator();

        try {
            const systemPrompt = buildSystemPrompt();
            const fullPrompt = `${systemPrompt}\n\nUser: ${message}\nAssistant:`;

            const response = await puter.ai.chat(fullPrompt, { model: 'gpt-5.4-nano' });
            
            removeTypingIndicator();
            addMessage(response, false);
        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage('Извините, произошла ошибка. Попробуйте позже.', false);
        }

        sendBtn.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
