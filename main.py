import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# SECURITY: Use environment variables, never hardcode keys
API_KEY = os.getenv("AIzaSyCnbYYxP4PqDcmAYAqKpb3IkAgXC_yzVM4")

DataBlueprint = {
    "type": "object",
    "properties": {
        "topic": {"type": "string", "description": "The clean, formatted name of the searched topic"},
        "summary": {"type": "string", "description": "A concise 2-sentence summary"},
        "statistics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "value": {"type": "number"},
                    "unit": {"type": "string"}
                },
                "required": ["label", "value", "unit"]
            }
        }
    },
    "required": ["topic", "summary", "statistics"]
}

# --- ADDED THIS ROUTE TO FIX THE 404 ERROR ---
@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Server is running! Use /api/stats?query=your_topic to get data."})

@app.route('/api/stats', methods=['GET'])
def get_market_stats():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
        
    if not API_KEY:
        return jsonify({"error": "Gemini API Key is missing in environment variables."}), 500

    # Note: Ensure you use valid current model names like 'gemini-1.5-flash'
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro']
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": f"Provide verified, historical statistical trends for: {query}"}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": DataBlueprint,
            "temperature": 0.0
        }
    }

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        try:
            response = requests.post(url, headers=headers, json=payload)
            response_json = response.json()
            
            if "candidates" in response_json:
                raw_ai_text = response_json['candidates'][0]['content']['parts'][0]['text']
                return jsonify(json.loads(raw_ai_text))
                
        except Exception:
            continue

    return jsonify({"error": "Service temporarily unavailable."}), 503

if __name__ == '__main__':
    app.run()