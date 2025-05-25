document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.analysis-form');
    const predictButton = document.querySelector('.predict-button');
    const outputSection = document.querySelector('.analysis-output');
    const riskNumber = document.querySelector('.risk-number');
    const riskStatus = document.querySelector('.risk-status');
    const riskDescription = document.querySelector('.risk-description');
    const assistanceTitle = document.querySelector('.assistance-title');
    
    // Chat elements
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const chatActionButton = document.getElementById('chatActionButton');
    const aiButton = document.querySelector('.ai-button');

    // Controller for cancelling ongoing requests
    let abortController = null;

    // Risk level color mapping
    const riskColors = {
        0: '#4CAF50', // Green for Healthy
        1: '#EAC75E', // Yellow for Watch
        2: '#C66238', // Orange for Warning
        3: '#F44336', // Red for High Risk
        4: '#8c140a' // Dark red for Critical
    };

    // Function to update all risk-related colors
    const updateRiskColors = (level) => {
        const color = riskColors[level];
        riskNumber.style.color = color;
        riskStatus.style.color = color;
        assistanceTitle.style.color = color;
        outputSection.style.setProperty('--risk-color', color);
    };

    // Function to create and append a message to the chat
    const appendMessage = (text, isUser = false) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user-message' : 'ai-message'}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                <span class="message-text">${text}</span>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    };

    // Function to toggle button state
    const toggleButtonState = (isGenerating) => {
        chatActionButton.textContent = isGenerating ? 'Cancel' : 'Send';
        chatInput.disabled = isGenerating;
    };

    // Function to handle chat action (send/cancel)
    const handleChatAction = async () => {
        // If currently generating, cancel the request
        if (abortController) {
            abortController.abort();
            return;
        }

        const message = chatInput.value.trim();
        if (!message) return;

        // Clear input
        chatInput.value = '';

        // Add user message to chat
        appendMessage(message, true);

        try {
            // Create new AbortController for this request
            abortController = new AbortController();
            
            // Show cancel state
            toggleButtonState(true);

            // Create a message container for the AI response
            const aiMessageDiv = appendMessage('', false);
            const aiMessageText = aiMessageDiv.querySelector('.message-text');
            let fullResponse = '';

            // Call your local LLM API with streaming
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message
                }),
                signal: abortController.signal
            });

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            // Handle the stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.error) {
                                aiMessageText.textContent = `Error: ${data.error}`;
                                throw new Error(data.error);
                            }
                            if (data.content) {
                                fullResponse += data.content;
                                aiMessageText.textContent = fullResponse;
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                        } catch (e) {
                            console.error('Error parsing SSE data:', e);
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Error:', error);
            if (error.name === 'AbortError') {
                appendMessage('Response generation was cancelled.');
            } else {
                appendMessage('Sorry, I encountered an error. Please try again.');
            }
        } finally {
            // Reset button state and clear abort controller
            toggleButtonState(false);
            abortController = null;
        }
    };

    // Event listeners for chat
    chatActionButton.addEventListener('click', handleChatAction);
    
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleChatAction();
        }
    });

    // Connect "Ask AI Assistant" button to chat
    aiButton.addEventListener('click', () => {
        chatInput.focus();
        const currentRisk = riskStatus.textContent;
        const currentDescription = riskDescription.textContent;
        chatInput.value = `Can you explain more about the "${currentRisk}" status? The system says: "${currentDescription}"`;
    });

    predictButton.addEventListener('click', async (e) => {
        e.preventDefault();

        // Get values from form
        const minSST = parseFloat(form.querySelector('input[placeholder="Enter minimum temperature"]').value);
        const maxSST = parseFloat(form.querySelector('input[placeholder="Enter maximum temperature"]').value);
        const hotspotSST = parseFloat(form.querySelector('input[placeholder="Enter hotspot temperature"]').value);
        const anomalySST = parseFloat(form.querySelector('input[placeholder="Enter temperature anomaly"]').value);

        // Validate inputs
        if (isNaN(minSST) || isNaN(maxSST) || isNaN(hotspotSST) || isNaN(anomalySST)) {
            alert('Please fill in all temperature values with valid numbers');
            return;
        }

        try {
            // Show loading state
            predictButton.disabled = true;
            predictButton.textContent = 'Analyzing...';
            
            // Call backend API
            const response = await fetch('http://localhost:8000/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    min_sst: minSST,
                    max_sst: maxSST,
                    hotspot_sst: hotspotSST,
                    sst_anomaly: anomalySST
                })
            });

            if (!response.ok) {
                throw new Error('Failed to get prediction');
            }

            const data = await response.json();
            
            // Update UI with prediction
            riskNumber.textContent = data.baa_level;
            riskStatus.textContent = data.risk_status;
            riskDescription.textContent = data.description;

            // Update all risk-related colors
            updateRiskColors(data.baa_level);
            
            // Show the output section
            outputSection.style.visibility = 'visible';
            outputSection.style.opacity = '1';

            // Scroll to output section
            outputSection.scrollIntoView({ behavior: 'smooth', block: 'center' });

        } catch (error) {
            console.error('Error:', error);
            alert('Error getting prediction. Please try again.');
        } finally {
            // Reset button state
            predictButton.disabled = false;
            predictButton.textContent = 'PREDICT BLEACHING RISK';
        }
    });

    // Add input validation and formatting
    const temperatureInputs = form.querySelectorAll('input[type="number"]');
    temperatureInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            // Limit to 2 decimal places
            if (e.target.value.includes('.')) {
                const parts = e.target.value.split('.');
                if (parts[1].length > 2) {
                    e.target.value = parseFloat(e.target.value).toFixed(2);
                }
            }
        });
    });
});
