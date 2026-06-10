document.addEventListener('DOMContentLoaded', function() {
    const aiBtn = document.getElementById('aiAssistantBtn');
    const aiChat = document.getElementById('aiAssistantChat');
    const aiClose = document.getElementById('aiAssistantClose');
    const floatingChatMessages = document.getElementById('floatingChatMessages');
    const floatingChatInput = document.getElementById('floatingChatInput');
    const floatingSendBtn = document.getElementById('floatingSendBtn');

    if (!aiBtn || !aiChat) return;

    aiBtn.addEventListener('click', function() {
        aiChat.classList.toggle('open');
    });

    if (aiClose) {
        aiClose.addEventListener('click', function() {
            aiChat.classList.remove('open');
        });
    }

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

    function addMessage(content, isUser, container) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user' : 'ai'}`;
        messageDiv.textContent = content;
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }

    function addTypingIndicator(container) {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message ai typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = '<span></span><span></span><span></span>';
        container.appendChild(typingDiv);
        container.scrollTop = container.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    async function sendFloatingMessage() {
        const message = floatingChatInput.value.trim();
        if (!message) return;

        addMessage(message, true, floatingChatMessages);
        floatingChatInput.value = '';
        floatingSendBtn.disabled = true;
        floatingChatInput.disabled = true;

        addTypingIndicator(floatingChatMessages);

        try {
            const systemPrompt = buildSystemPrompt();
            const fullPrompt = `${systemPrompt}\n\nUser: ${message}\nAssistant:`;

            const response = await puter.ai.chat(fullPrompt, { model: 'gpt-5.4-nano' });
            
            removeTypingIndicator();
            addMessage(response, false, floatingChatMessages);
        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage('Извините, произошла ошибка. Попробуйте позже.', false, floatingChatMessages);
        }

        floatingSendBtn.disabled = false;
        floatingChatInput.disabled = false;
        floatingChatInput.focus();
    }

    if (floatingSendBtn && floatingChatInput) {
        floatingSendBtn.addEventListener('click', sendFloatingMessage);
        floatingChatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendFloatingMessage();
            }
        });
    }
});
