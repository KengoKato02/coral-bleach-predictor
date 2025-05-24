document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.analysis-form');
    const predictButton = document.querySelector('.predict-button');
    const outputSection = document.querySelector('.analysis-output');
    const riskNumber = document.querySelector('.risk-number');
    const riskStatus = document.querySelector('.risk-status');
    const riskDescription = document.querySelector('.risk-description');

    // Risk level color mapping
    const riskColors = {
        0: '#4CAF50', // Green for Healthy
        1: '#EAC75E', // Yellow for Watch
        2: '#C66238', // Orange for Warning
        3: '#F44336', // Red for High Risk
        4: '#B71C1C'  // Dark Red for Critical
    };

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
            outputSection.style.opacity = '0.5';
            
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

            // Update colors based on risk level
            outputSection.style.borderTopColor = riskColors[data.baa_level];
            riskNumber.style.color = riskColors[data.baa_level];
            riskStatus.style.color = riskColors[data.baa_level];
            
            // Show output section with animation
            outputSection.style.display = 'flex';
            outputSection.style.opacity = '0';
            setTimeout(() => {
                outputSection.style.opacity = '1';
                outputSection.style.transition = 'opacity 0.5s ease-in-out';
            }, 100);

            // Scroll to output section
            outputSection.scrollIntoView({ behavior: 'smooth', block: 'center' });

        } catch (error) {
            console.error('Error:', error);
            alert('Error getting prediction. Please try again.');
        } finally {
            // Reset button state
            predictButton.disabled = false;
            predictButton.textContent = 'PREDICT BLEACHING RISK';
            outputSection.style.opacity = '1';
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
