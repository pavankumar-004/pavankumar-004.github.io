import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

app = FastAPI()

# Enable CORS so your GitHub Pages frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, you can replace "*" with ["https://pavankumar-004.github.io"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paste your actual Gemini API key here
GEMINI_API_KEY = "AIzaSyCnbYYxP4PqDcmAYAqKpb3IkAgXC_yzVM4"

# Validate Key on startup
if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY" or not GEMINI_API_KEY:
    raise ValueError("❌ Error: Please set your real GEMINI_API_KEY inside main.py")

# Initialize GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

# SYSTEM INSTRUCTION: Forces Gemini to always reply in a clean JSON format that your frontend UI maps to perfectly
SYSTEM_PROMPT = """
You are a backend statistical data engine. Your job is to return data strictly as a JSON object.
Do not wrap your response in markdown code blocks like ```json ... ```. Just return the raw JSON.

The JSON structure MUST look exactly like this:
{
  "summary": "A detailed analysis of the topic formatted cleanly in Markdown (use headers, bullet points, etc. as needed).",
  "statistics": [
    {"timeline": "2024 Q1", "metric": "User Growth", "unit": "15% increase"},
    {"timeline": "2025", "metric": "Market Valuation", "unit": "$2.3 Billion"}
  ]
}
Provide relevant, high-fidelity chronological metrics inside the statistics array based on the user's query.
"""

# Create a persistent chat session with system instructions
chat_session = client.chats.create(
    model="gemini-2.5-flash",
    config={"system_instruction": SYSTEM_PROMPT}
)

# Define request schema
class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_msg = request.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        # Send message to the persistent Google GenAI chat session
        response = chat_session.send_message(user_msg)
        
        # Parse the JSON response from Gemini
        try:
            cleaned_text = response.text.strip().lstrip("```json").rstrip("```").strip()
            data = json.loads(cleaned_text)
        except Exception:
            # Fallback if Gemini breaks JSON formatting rules
            data = {
                "summary": response.text,
                "statistics": [{"timeline": "N/A", "metric": "Data parsing error", "unit": "Error"}]
            }
        
        # Return structured JSON matching your dashboard expectation exactly
        return {
            "topic": user_msg[:30] + "..." if len(user_msg) > 30 else user_msg,
            "summary": data.get("summary", response.text),
            "statistics": data.get("statistics", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Changed host to 0.0.0.0 so web services (Render/Railway) can map ports externally
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)