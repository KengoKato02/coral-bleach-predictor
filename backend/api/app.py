from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import requests
import re
import json
from datetime import datetime

# Configuration constants
LLAMA_API_URL = "http://localhost:11434/api/chat"
LLM_MODEL = "llama3.1"
TEMPERATURE_RANGE = (-5, 40)  # Typical range for ocean temperatures in °C
DHW_RANGE = (0, 20)  # Typical range for Degree Heating Weeks
REQUIRED_FIELDS = ['region', 'date', 'min_sst', 'max_sst', 'hotspot_sst', 'sst_anomaly', 'dhw_90th']

# Region-specific information
REGION_INFO = {
    'Caribbean': {
        'bleaching_threshold': 30.0,
        'typical_range': (24, 32)
    },
    'Great Barrier Reef': {
        'bleaching_threshold': 29.0,
        'typical_range': (22, 30)
    },
    'Polynesia': {
        'bleaching_threshold': 30.5,
        'typical_range': (25, 32)
    },
    'South Asia': {
        'bleaching_threshold': 31.0,
        'typical_range': (26, 33)
    }
}

app = Flask(__name__, static_folder='../../frontend', static_url_path='')
CORS(app)

# Mapping BAA levels to risk information
RISK_LEVELS = {
    0: {
        "status": "Healthy Conditions",
        "description": "Coral reef are thriving with optimal water temperatures. Perfect conditions for coral growth and recovery."
    },
    1: {
        "status": "Bleaching Watch",
        "description": "Early thermal stress detected in monitoring data. Sensitive coral species should be monitored closely for initial stress responses."
    },
    2: {
        "status": "Bleaching Warning",
        "description": "Moderate thermal stress is affecting coral health. Bleaching may begin in sensitive species within the next few days."
    },
    3: {
        "status": "High Risk Alert",
        "description": "High thermal stress detected across the reef system. Widespread coral bleaching is expected to occur soon."
    },
    4: {
        "status": "Critical Emergency",
        "description": "Critical thermal stress levels reached. Severe coral bleaching and potential mortality are imminent without immediate intervention."
    }
}

def validate_temperature_data(data):
    """Validate input temperature data"""
    if not request.is_json:
        return {'error': 'Content-Type must be application/json'}, 400

    if not all(field in data for field in REQUIRED_FIELDS):
        return {
            'error': 'Missing required fields',
            'required_fields': REQUIRED_FIELDS
        }, 400

    if data['region'] not in REGION_INFO:
        return {
            'error': 'Invalid region',
            'valid_regions': list(REGION_INFO.keys())
        }, 400

    try:
        # Validate date format
        datetime.strptime(data['date'], '%Y-%m-%d')
        
        # Validate temperature values
        for field in ['min_sst', 'max_sst', 'hotspot_sst', 'sst_anomaly']:
            data[field] = float(data[field])
            if not TEMPERATURE_RANGE[0] <= data[field] <= TEMPERATURE_RANGE[1]:
                return {
                    'error': f'Invalid value for {field}. Must be between {TEMPERATURE_RANGE[0]}°C and {TEMPERATURE_RANGE[1]}°C'
                }, 400
        
        # Validate DHW
        data['dhw_90th'] = float(data['dhw_90th'])
        if not DHW_RANGE[0] <= data['dhw_90th'] <= DHW_RANGE[1]:
            return {
                'error': f'Invalid value for DHW. Must be between {DHW_RANGE[0]} and {DHW_RANGE[1]}'
            }, 400

    except ValueError as e:
        return {
            'error': f'Invalid value format: {str(e)}'
        }, 400

    return None

def get_llama_prediction(data):
    """Get prediction from the model"""
    try:
        region_info = REGION_INFO[data['region']]
        response = requests.post(
            LLAMA_API_URL,
            json={
                "model": LLM_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": f"""You are a coral reef monitoring system for the {data['region']} region. 
                        The bleaching threshold for this region is {region_info['bleaching_threshold']}°C, 
                        with typical temperature range of {region_info['typical_range'][0]}-{region_info['typical_range'][1]}°C.
                        Always respond with ONLY a single number (0-4) representing the BAA level. No explanation needed."""
                    },
                    {
                        "role": "user",
                        "content": f"""Date: {data['date']}
                        SST values: MIN={data['min_sst']}, MAX={data['max_sst']}, 
                        HOTSPOT={data['hotspot_sst']}, ANOMALY={data['sst_anomaly']}, 
                        DHW={data['dhw_90th']}
                        Predict BAA (0-4). 
                        Respond with ONLY the number."""
                    }
                ],
                "stream": False,
                "temperature": 0.1
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return None, {
                'error': f'Error calling model {LLM_MODEL}',
                'status_code': response.status_code
            }, 500

        return response.json(), None, None

    except requests.exceptions.ConnectionError:
        return None, {
            'error': f'Could not connect to model {LLM_MODEL}. Make sure it is running on port 11434'
        }, 503
    except requests.exceptions.Timeout:
        return None, {
            'error': f'Model {LLM_MODEL} request timed out'
        }, 504

def extract_baa_level(llama_response):
    """Extract BAA level from model response"""
    if not llama_response.get('message', {}).get('content'):
        return None, {
            'error': 'Empty response from model',
            'full_response': llama_response
        }, 500
        
    response_text = llama_response['message']['content'].strip()
    if not response_text:
        return None, {
            'error': 'Empty response text from model',
            'full_response': llama_response
        }, 500
        
    # Try to find "BAA: X" pattern first
    baa_match = re.search(r'BAA:\s*(\d+)', response_text)
    if baa_match:
        baa_level = int(baa_match.group(1))
    else:
        # Fallback to finding any number if BAA: X pattern not found
        numbers = re.findall(r'\d+', response_text)
        if not numbers:
            return None, {
                'error': 'No numeric value found in response',
                'response_text': response_text
            }, 500
        baa_level = int(numbers[0])
        
    if not 0 <= baa_level <= 4:
        return None, {
            'error': 'BAA level out of range',
            'received_value': baa_level,
            'response_text': response_text
        }, 500

    return baa_level, None, None

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

# Serve static files (CSS, JS, images)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/predict', methods=['POST'])
def predict_bleaching():
    """Predict coral bleaching risk based on temperature data"""
    try:
        data = request.get_json()
        
        # Validate input data
        validation_error = validate_temperature_data(data)
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]

        # Get prediction from llama
        llama_response, error, status_code = get_llama_prediction(data)
        if error:
            return jsonify(error), status_code

        # Extract BAA level
        baa_level, error, status_code = extract_baa_level(llama_response)
        if error:
            return jsonify(error), status_code

        # Get risk information
        risk_info = RISK_LEVELS[baa_level]
        
        return jsonify({
            'baa_level': baa_level,
            'risk_status': risk_info['status'],
            'description': risk_info['description']
        })

    except Exception as e:
        app.logger.error(f'Unexpected error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with the LLM model"""
    try:
        data = request.get_json()
        
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        if 'message' not in data:
            return jsonify({'error': 'Missing message field'}), 400

        def generate():
            try:
                # Prepare messages list with system prompt and history
                messages = [
                    {
                        "role": "system",
                        "content": """You are a coral reef monitoring assistant. You help users understand coral bleaching risks, 
                        interpret temperature data, and provide recommendations for coral reef protection. Be concise but informative."""
                    }
                ]
                
                # Add conversation history if provided
                if 'history' in data:
                    messages.extend(data['history'])
                
                # Add current user message
                messages.append({
                    "role": "user",
                    "content": data['message']
                })

                response = requests.post(
                    LLAMA_API_URL,
                    json={
                        "model": LLM_MODEL,
                        "messages": messages,
                        "stream": True,
                        "temperature": 0.7
                    },
                    stream=True,
                )

                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': f'Error calling model {LLM_MODEL}'})}\n\n"
                    return

                for line in response.iter_lines():
                    if line:
                        try:
                            json_response = json.loads(line.decode('utf-8'))
                            if json_response.get('message', {}).get('content'):
                                content = json_response['message']['content']
                                yield f"data: {json.dumps({'content': content})}\n\n"
                        except json.JSONDecodeError:
                            continue

            except requests.exceptions.ConnectionError:
                yield f"data: {json.dumps({'error': f'Could not connect to model {LLM_MODEL}. Make sure it is running on port 11434'})}\n\n"
            except requests.exceptions.Timeout:
                yield f"data: {json.dumps({'error': f'Model {LLM_MODEL} request timed out'})}\n\n"
            except Exception as e:
                app.logger.error(f'Unexpected error in chat: {str(e)}')
                yield f"data: {json.dumps({'error': 'Internal server error'})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        app.logger.error(f'Unexpected error in chat: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/init-chat', methods=['POST'])
def init_chat():
    """Generate initial greeting message based on analysis data"""
    try:
        data = request.get_json()
        
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        required_fields = ['min_sst', 'max_sst', 'hotspot_sst', 'sst_anomaly', 'risk_level', 'risk_status', 'description']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields', 'required_fields': required_fields}), 400

        def generate():
            try:
                response = requests.post(
                    LLAMA_API_URL,
                    json={
                        "model": LLM_MODEL,
                        "messages": [
                            {
                                "role": "system",
                                "content": """You are a coral reef monitoring assistant. Respond ONLY with a greeting message that follows this exact structure:

                                1. Start with "Hello! I am your AI coral reef assistant."
                                2. Follow with "I see these temperature readings:"
                                3. List the temperatures as bullet points
                                4. State the risk level and status (make the status bold with **text**)
                                5. Add the description
                                6. End with a short question about how you can help

DO NOT add any additional text, quotes, or commentary about the greeting itself. Start directly with "Hello!"."""
                            },
                            {
                                "role": "user",
                                "content": f"""Create an initial greeting with these values:
                                - Minimum Temperature: {data['min_sst']}°C
                                - Maximum Temperature: {data['max_sst']}°C
                                - Hotspot Temperature: {data['hotspot_sst']}°C
                                - Temperature Anomaly: {data['sst_anomaly']}°C
                                - Risk Level: {data['risk_level']}
                                - Risk Status: {data['risk_status']}
                                - Description: {data['description']}"""
                            }
                        ],
                        "stream": True,
                        "temperature": 0.7
                    },
                    stream=True,
                )

                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': f'Error calling model {LLM_MODEL}'})}\n\n"
                    return

                for line in response.iter_lines():
                    if line:
                        try:
                            json_response = json.loads(line.decode('utf-8'))
                            if json_response.get('message', {}).get('content'):
                                content = json_response['message']['content']
                                yield f"data: {json.dumps({'content': content})}\n\n"
                        except json.JSONDecodeError:
                            continue

            except requests.exceptions.ConnectionError:
                yield f"data: {json.dumps({'error': f'Could not connect to model {LLM_MODEL}. Make sure it is running on port 11434'})}\n\n"
            except requests.exceptions.Timeout:
                yield f"data: {json.dumps({'error': f'Model {LLM_MODEL} request timed out'})}\n\n"
            except Exception as e:
                app.logger.error(f'Unexpected error in init chat: {str(e)}')
                yield f"data: {json.dumps({'error': 'Internal server error'})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        app.logger.error(f'Unexpected error in init chat: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested URL was not found on the server.',
        'available_endpoints': {
            '/': 'GET - Home page',
            '/predict': 'POST - Predict coral bleaching risk',
            '/chat': 'POST - Chat with the AI assistant'
        }
    }), 404

if __name__ == '__main__':
    app.run(debug=True, port=8000) 