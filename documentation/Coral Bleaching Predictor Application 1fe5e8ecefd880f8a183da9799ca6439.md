# Coral Bleaching Predictor Application

We have developed a Coral Bleaching Predictor based on the NOAA Coral Reef Watch Virtual Station dataset. Our model uses seven key parameters as inputs: region selection (Caribbean, Great Barrier Reef, Polynesia, South Asia), date (YYYY-MM-DD format), minimum and maximum sea surface temperature (SST_MIN, SST_MAX), SST at 90th percentile hotspot (SST@90th_HS), SST anomaly at 90th percentile (SSTA@90th_HS), and Degree Heating Weeks from 90th percentile (DHW_90th). The model outputs predictions on the Bleaching Alert Area (BAA) scale from levels 0-4, corresponding to No Stress, Bleaching Watch, Bleaching Warning, Alert Level 1, and Alert Level 2.
Our application combines our custom-trained model with Llama 3.1. The architecture works as follows: users input comprehensive coral monitoring data (region, date, SST_MIN, SST_MAX, SST@90th_HS, SSTA@90th_HS, DHW_90th), which gets processed by either our custom ML model or Llama 3.1 (selectable via dropdown) to produce a coral bleaching alert level from 0 to 4. Users receive the prediction result along with a brief description of what that alert level means. If users want more detailed analysis, they can choose to interact with our AI assistant (Llama 3.1), which provides comprehensive explanations, recommendations, and can answer follow-up questions about the specific prediction and input parameters.

![Screenshot 2025-05-26 at 09.34.58.png](Coral%20Bleaching%20Predictor%20Application%201fe5e8ecefd880f8a183da9799ca6439/Screenshot_2025-05-26_at_09.34.58.png)

The core idea behind this approach is that we're using the LLM as an optional intelligent interface that users can engage with when they want a deeper analysis of their predictions. This gives us the precision of a domain-specific model combined with the natural language capabilities of modern AI systems.

## Selection of local model

When selecting an LLM, we evaluated several options including Llama 3.1 and Mistral 7B. After comparing their capabilities, we decided that Llama 3.1 was the best fit for our application.

The main advantage of Llama 3.1 is its 128,000 token context window, which is significantly larger than Mistral's 32,000 tokens. The larger context means our system can maintain coherent discussions about coral health over longer conversations without losing important details.

Llama 3.1 offers excellent hardware efficiency, with the 8B parameter model running smoothly on standard hardware with 8GB of RAM. According to Meta's official benchmarks, Llama 3.1 demonstrates strong quantitative reasoning capabilities, achieving 96.8% on GSM8K (mathematical reasoning) and 96.9% on ARC Challenge (scientific reasoning tasks). These documented performance metrics on quantitative analysis tasks suggest it can effectively interpret the numerical relationships in our coral temperature data.

Mistral 7B is a capable model, but it has several limitations for our use case. Its shorter context window could potentially be insufficient for the coral data analysis we need, and in our testing, we found it less consistent in scientific reasoning tasks. Additionally, Mistral's mathematical reasoning benchmarks are generally lower than Llama 3.1's performance.

![Screenshot 2025-05-25 at 12.02.27.png](Coral%20Bleaching%20Predictor%20Application%201fe5e8ecefd880f8a183da9799ca6439/Screenshot_2025-05-25_at_12.02.27.png)

## Set up for Llama 3.1

We created a Flask back-end application that communicates with the local Llama API. The setup requires minimum 8GB of RAM to run the model.

Our application uses Llama 3.1 for two purposes with different configurations:

### Prediction (Alternative to our custom trained model)

| Parameter | Value | Purpose |
| --- | --- | --- |
| **Temperature** | `0.1` | Low randomness for scientific accuracy |
| **Stream** | `False` | Complete response mode for reliable parsing |
| **System Role** | `You are a coral reef monitoring system for the {data['region']} region. The bleaching threshold for this region is {region_info['bleaching_threshold']}°C, with typical temperature range of {region_info['typical_range'][0]} {region_info['typical_range'][1]}°C. Always respond with ONLY a single number (0-4) representing the BAA level. No explanation needed.` | Forces structured numeric responses |
| **Output Format** | `Single number (0-4)` | BAA level prediction only |

### Chat assistant

| Parameter | Value | Purpose |
| --- | --- | --- |
| **Temperature** | `0.7` | Higher creativity for natural conversations |
| **Stream** | `True` | Real-time streaming responses for better user experience |
| **System Role** | `“You are a coral reef monitoring assistant. You help users understand coral bleaching risks, interpret temperature data, and provide recommendations for coral reef protection. Be concise but informative....”` | Role of coral reef monitoring assistant |

## API Endpoints

`/predict` - Coral bleaching prediction

- **Input validation**: Temperature ranges (-5°C to 40°C)
- **Model selection**: Users can choose between custom model or Llama 3.1
- **Structured output**: Returns BAA level + risk description
- **Error handling**: Connection, timeout, and parsing errors

`/init-chat` - handles initial chat greeting based on analysis data

- **Automatic greeting generation -** creates personalized message based on the prediction results
- **Structured format** - consistent greeting template with temperature summary and risk explanation

`/chat` - handles chat messages with Llama3.1

- **Streaming responses**: Real-time chat using Server-Sent Events
- **Context-aware**: Understands coral bleaching domain
- **Conversational**: Q&A about predictions
- **Error handling**:  handling of connection issues

## Comparative analysis: Custom Model vs. Llama 3.1

The key question we needed to answer was whether our custom-trained model provides advantages over using a general large language model like Llama 3.1 directly for coral bleaching predictions. After extensive testing and analysis, we found significant differences between these approaches.

We ran tests using various scenarios from our dataset, covering everything from normal conditions (BAA Level 0) through severe bleaching alerts (BAA Level 4).

### Key findings:

- Our custom model correctly identified patterns in several test scenarios
- Llama 3.1 consistently failed to provide accurate BAA-level predictions

**Accuracy:**

Our custom model performed significantly better than Llama 3.1 at making accurate predictions. It successfully identified patterns in various scenarios, suggesting it learned meaningful relationships between temperature parameters and bleaching risk levels from the NOAA training data. 

Despite careful prompt engineering and configuration optimization, Llama 3.1 consistently provided incorrect BAA-level predictions. This failure highlights an important limitation: general language models, even when prompted with domain-specific context, lack the precise quantitative relationships needed for accurate scientific predictions. 

This wasn't really surprising since our model learned specific relationships between temperature parameters and bleaching risk levels directly from the NOAA training data. It was trained to recognize the exact patterns that indicate different levels of coral stress based on real monitoring station measurements.

**Response speed:**
Our model also demonstrated a clear advantage in response speed. Predictions are nearly instantaneous since they involve straightforward matrix operations on preprocessed features. In contrast, Llama’s predictions are significantly slower due to the text generation process.

These results validate our hybrid architecture decision:

- **Our model**: Handles precise numerical predictions with speed and consistency
- **Llama 3.1**: Provides natural language explanations and interactive capabilities

Rather than competing for the same task, each component serves its optimal purpose. The testing demonstrates that attempting to use Llama 3.1 for direct prediction would significantly compromise system accuracy. These results highlight that current LLMs are excellent for reasoning and explanation, but they are not suitable replacements for specialized models in quantitative scientific applications requiring precise predictions.

### Conclusion

Our hybrid approach successfully combines the precision of specialized machine learning with modern language models while avoiding the drawbacks of pure AI solutions. By using a custom model trained on coral-specific data for predictions and Llama 3.1 for explanations and user interaction, we've created a system that provides consistent, scientifically reliable predictions while remaining accessible and practical for real-world applications.

Our experience highlights some important lessons about using AI for scientific applications. First, specialized training really does matter when you need precise, quantitative predictions. Even though Llama 3.1 is incredibly sophisticated and knows a lot about coral biology, it doesn't have the specific calibration needed for our exact prediction task.
Second, we learned that current large language models, while excellent for reasoning and explanation, aren't suitable replacements for specialized models in scientific applications that require precise, reproducible predictions. They're amazing at helping users understand results and explore ideas, but they shouldn't be the primary prediction engine for critical scientific decisions.
Finally, our testing confirmed that hybrid approaches can be really powerful because they let you leverage the complementary strengths of different AI technologies instead of trying to force one system to do everything. This seems like an important insight as AI continues to develop. Sometimes the best solution isn't the most advanced single model, but rather a thoughtful combination of specialized tools working together.

## References

[https://ai.meta.com/blog/meta-llama-3-1/](https://ai.meta.com/blog/meta-llama-3-1/)

[https://ollama.com/library/llama3.1](https://ollama.com/library/llama3.1)

[https://github.com/ollama/ollama/blob/main/docs/api.md](https://github.com/ollama/ollama/blob/main/docs/api.md)