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

    // Function to parse markdown-like formatting
    const parseMarkdown = (text) => {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold text
            .replace(/\n/g, '<br>');  // Line breaks
    };

    // Function to create and append a message to the chat
    const appendMessage = (text, isUser = false) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user-message' : 'ai-message'}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                <span class="message-text">${parseMarkdown(text)}</span>
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
                                aiMessageText.innerHTML = parseMarkdown(fullResponse);
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
    aiButton.addEventListener('click', async () => {
        const chatContainer = document.querySelector('.chat-container');
        chatContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Get all form values
        const minSST = form.querySelector('input[placeholder="Enter minimum temperature"]').value;
        const maxSST = form.querySelector('input[placeholder="Enter maximum temperature"]').value;
        const hotspotSST = form.querySelector('input[placeholder="Enter hotspot temperature"]').value;
        const anomalySST = form.querySelector('input[placeholder="Enter temperature anomaly"]').value;

        // Get current risk
        const currentRisk = riskStatus.textContent;
        const currentDescription = riskDescription.textContent;
        const riskLevel = riskNumber.textContent;

        try {
            // Create new AbortController for this request
            abortController = new AbortController();

            // Create a message container for the AI response
            const aiMessageDiv = appendMessage('', false);
            const aiMessageText = aiMessageDiv.querySelector('.message-text');
            let fullResponse = '';

            // Call the init-chat endpoint
            const response = await fetch('http://localhost:8000/init-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    min_sst: minSST,
                    max_sst: maxSST,
                    hotspot_sst: hotspotSST,
                    sst_anomaly: anomalySST,
                    risk_level: riskLevel,
                    risk_status: currentRisk,
                    description: currentDescription
                }),
                signal: abortController.signal
            });

            if (!response.ok) {
                throw new Error('Failed to get initial greeting');
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
                                aiMessageText.innerHTML = parseMarkdown(fullResponse);
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
            appendMessage('Sorry, I encountered an error starting the conversation. Please try again.');
        } finally {
            // Reset abort controller
            abortController = null;
            // Focus the chat input for user's response
            chatInput.focus();
        }
    });

    // Function to collect form data
    const collectFormData = () => {
        const modelSelect = document.getElementById('modelSelect');
        const regionSelect = document.getElementById('regionSelect');
        const dateSelect = document.getElementById('dateSelect');
        
        return {
            model: modelSelect.value,  // Add model selection
            region: regionSelect.value,
            date: dateSelect.value,
            min_sst: parseFloat(form.querySelector('input[placeholder="Enter minimum temperature"]').value),
            max_sst: parseFloat(form.querySelector('input[placeholder="Enter maximum temperature"]').value),
            hotspot_sst: parseFloat(form.querySelector('input[placeholder="Enter hotspot temperature"]').value),
            sst_anomaly: parseFloat(form.querySelector('input[placeholder="Enter temperature anomaly"]').value),
            dhw_90th: parseFloat(form.querySelector('input[placeholder="Enter DHW value"]').value)
        };
    };

    // Function to validate form data
    const validateFormData = (data) => {
        if (!data.region) return 'Please select a region';
        if (!data.date) return 'Please select a date';
        if (isNaN(data.min_sst)) return 'Please enter minimum SST';
        if (isNaN(data.max_sst)) return 'Please enter maximum SST';
        if (isNaN(data.hotspot_sst)) return 'Please enter hotspot SST';
        if (isNaN(data.sst_anomaly)) return 'Please enter SST anomaly';
        if (isNaN(data.dhw_90th)) return 'Please enter DHW value';
        return null;
    };

    // Handle predict button click
    predictButton.addEventListener('click', async () => {
        const data = collectFormData();
        const validationError = validateFormData(data);
        
        if (validationError) {
            alert(validationError);
            return;
        }

        try {
            // Show loading state
            predictButton.disabled = true;
            predictButton.textContent = 'ANALYZING...';

            const response = await fetch('http://localhost:8000/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error('Failed to get prediction');
            }

            const result = await response.json();
            
            // Update the output section
            riskNumber.textContent = result.risk_level;
            riskStatus.textContent = result.status;
            riskDescription.textContent = result.description;
            
            // Update colors based on risk level
            updateRiskColors(result.risk_level);
            
            // Show the output section
            outputSection.style.visibility = 'visible';
            outputSection.style.opacity = '1';
            
            // Scroll to output section
            outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            console.error('Error:', error);
            alert('Failed to get prediction. Please try again.');
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
