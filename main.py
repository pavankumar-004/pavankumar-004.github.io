import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("AIzaSyCnbYYxP4PqDcmAYAqKpb3IkAgXC_yzVM4")

# FALLBACK CHECK: If your terminal 'set' command fails, paste your real key string inside these quotes:
if not API_KEY or API_KEY == "your_actual_api_key_here":
    API_KEY = "YOUR_ACTUAL_GEMINI_API_KEY"

DataBlueprint = {
    "type": "object",
    "properties": {
        "topic": {"type": "string", "description": "The clean, formatted name of the searched topic"},
        "summary": {"type": "string", "description": "A concise 2-sentence summary contextualizing the numbers"},
        "statistics": {
            "type": "array",
            "description": "A clean, chronological list of data points",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "The timeline marker (e.g., '2024')"},
                    "value": {"type": "number", "description": "The absolute numerical value"},
                    "unit": {"type": "string", "description": "The unit of measurement (e.g., 'Millions')"}
                },
                "required": ["label", "value", "unit"]
            }
        }
    },
    "required": ["topic", "summary", "statistics"]
}

@app.route('/api/stats', methods=['GET'])
def get_market_stats():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
        
    if not API_KEY or "YOUR_ACTUAL" in API_KEY:
        return jsonify({"error": "Gemini API Key is missing. Please fix it in main.py"}), 500

    # The updated list of valid production models
    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro']
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": f"Provide verified, historical statistical trends for: {query}"}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": DataBlueprint,
            "temperature": 0.0
        }
    }

    # Loop through the active models
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        try:
            response = requests.post(url, headers=headers, json=payload)
            response_json = response.json()
            
            # If a model says it is experiencing high demand, log it and jump to the next one
            if "error" in response_json and "demand" in response_json["error"]["message"].lower():
                print(f"⚠️ {model} is currently overloaded. Trying next model...")
                continue 
                
            if "error" in response_json:
                print(f"❌ Error with model {model}: {response_json['error']['message']}")
                continue
                
            raw_ai_text = response_json['candidates'][0]['content']['parts'][0]['text']
            return jsonify(json.loads(raw_ai_text))
            
        except Exception as e:
            continue

    return jsonify({"error": "All available AI models are completely busy right now. Please refresh in a few moments."}), 503

if __name__ == '__main__':
    print("\n🚀 Fixed Model Pipeline! Server running on http://127.0.0.1:8000")
    app.run(host='127.0.0.1', port=8000, debug=True)