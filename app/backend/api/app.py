from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import requests
import re
import json
from datetime import datetime
import joblib
import numpy as np
import os
import pandas as pd

# Load the Part 1 models
MODEL_DIR = os.path.join(os.path.dirname(__file__), '../models')
coral_model = joblib.load(os.path.join(MODEL_DIR, 'coral_bleaching_predictor.pkl'))
scaler = joblib.load(os.path.join(MODEL_DIR, 'scaler.pkl'))

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

def get_part1_prediction(data):
    """Get prediction from the Part 1 model"""
    try:
        print("\n=== Starting prediction process ===")
        print("1. Raw input data:", json.dumps(data, indent=2))
        
        # Extract date components
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month
        day = date_obj.day
        
        # Determine season
        seasons = {
            'Fall': [9, 10, 11],
            'Spring': [3, 4, 5],
            'Summer': [6, 7, 8],
            'Winter': [12, 1, 2]
        }
        current_season = next(season for season, months in seasons.items() if month in months)
        season_features = {f'Season_{s}': 1 if s == current_season else 0 for s in seasons.keys()}
        
        print("\n2. Date components:")
        print(f"Year: {year}, Month: {month}, Day: {day}, Season: {current_season}")
        
        # Create region encoding (one-hot)
        regions = ['Caribbean', 'Great Barrier Reef', 'Polynesia', 'South Asia']
        region_features = {f'Region_{r}': 1 if r == data['region'] else 0 for r in regions}
        print("\n3. Region encoding:")
        print(json.dumps(region_features, indent=2))
        
        # Calculate derived features
        ssta_dhw_interaction = data['sst_anomaly'] * data['dhw_90th']
        ssta_squared = data['sst_anomaly'] ** 2
        ssta_above_threshold = 1 if data['sst_anomaly'] > 0 else 0
        
        print("\n4. Calculated features:")
        print(f"SSTA_DHW_interaction: {ssta_dhw_interaction}")
        print(f"SSTA_squared: {ssta_squared}")
        print(f"SSTA_above_threshold: {ssta_above_threshold}")
        
        # Create features in exact order as model expects
        features = pd.DataFrame([{
            # Exact order from model.feature_names_in_
            'YYYY': year,
            'MM': month,
            'DD': day,
            'SST_MIN': data['min_sst'],
            'SST_MAX': data['max_sst'],
            'SST@90th_HS': data['hotspot_sst'],
            'SSTA@90th_HS': data['sst_anomaly'],
            '90th_HS>0': data['hotspot_sst'],
            'DHW_from_90th_HS>1': data['dhw_90th'],
            'SST_MIN_lag_back_4': data['min_sst'],
            'SST_MAX_lag_back_4': data['max_sst'],
            'SST@90th_HS_lag_back_4': data['hotspot_sst'],
            'SSTA@90th_HS_lag_back_3': data['sst_anomaly'],
            '90th_HS>0_lag_back_4': data['hotspot_sst'],
            'DHW_from_90th_HS>1_lag_forward_29': data['dhw_90th'],
            'SSTA_above_threshold': ssta_above_threshold,
            '90th_HS_above_0': 1 if data['hotspot_sst'] > 0 else 0,
            'SSTA_squared': ssta_squared,
            'SSTA_DHW_interaction': ssta_dhw_interaction,
            'Season_Fall': season_features['Season_Fall'],
            'Season_Spring': season_features['Season_Spring'],
            'Season_Summer': season_features['Season_Summer'],
            'Season_Winter': season_features['Season_Winter'],
            'Region_Caribbean': region_features['Region_Caribbean'],
            'Region_Great Barrier Reef': region_features['Region_Great Barrier Reef'],
            'Region_Polynesia': region_features['Region_Polynesia'],
            'Region_South Asia': region_features['Region_South Asia']
        }])
        
        print("\n5. Features DataFrame:")
        print(features.to_string())
        print("\nFeature names in order:", list(features.columns))
        
        print("\n6. Model's expected feature names:")
        print(coral_model.feature_names_in_ if hasattr(coral_model, 'feature_names_in_') else "Feature names not available in model")
        
        # Scale the features
        scaled_features = scaler.transform(features)
        print("\n7. Scaled features shape:", scaled_features.shape)
        print("Scaled features:")
        print(scaled_features)
        
        # Get prediction
        prediction = coral_model.predict(scaled_features)[0]
        print("\n8. Raw model prediction:", prediction)
        
        # Ensure prediction is in valid range
        prediction = max(0, min(4, int(round(prediction))))
        print("9. Final adjusted prediction:", prediction)
        print("\n=== Prediction process completed ===\n")
        
        return prediction, None, None
        
    except Exception as e:
        import traceback
        print("\n=== Error in prediction process ===")
        print("Error type:", type(e).__name__)
        print("Error message:", str(e))
        print("\nFull traceback:")
        print(traceback.format_exc())
        print("=== Error details end ===\n")
        return None, {
            'error': f'Error using Part 1 model: {str(e)}\nTraceback: {traceback.format_exc()}'
        }, 500

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

# Serve static files (CSS, JS, images)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/predict', methods=['POST'])
def predict_bleaching():
    """Predict coral bleaching risk"""
    data = request.json
    print("Received data:", data)  # Debug print
    
    # Validate input data
    validation_error = validate_temperature_data(data)
    if validation_error:
        print("Validation error:", validation_error)  # Debug print
        return jsonify(validation_error[0]), validation_error[1]
    
    # Get selected model
    model_type = data.get('model', 'part1')  # Default to part1 if not specified
    print("Selected model:", model_type)  # Debug print
    
    # Get prediction based on model type
    if model_type == 'part1':
        baa_level, error, status_code = get_part1_prediction(data)
    else:  # llama3.1
        llama_response, error, status_code = get_llama_prediction(data)
        if error:
            print("LLaMA error:", error)  # Debug print
            return jsonify(error), status_code
        baa_level, error, status_code = extract_baa_level(llama_response)
    
    if error:
        print("Prediction error:", error)  # Debug print
        return jsonify(error), status_code
    
    # Get risk information for the BAA level
    risk_info = RISK_LEVELS[baa_level]
    print("Risk info:", risk_info)  # Debug print
    
    return jsonify({
        'risk_level': baa_level,
        'status': risk_info['status'],
        'description': risk_info['description']
    })

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