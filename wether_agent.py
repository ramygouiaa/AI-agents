import json
import requests
import logging
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set the LM Studio API base URL
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

def get_coordinates(city: str) -> Tuple[Optional[float], Optional[float]]:
    """Convert a city name into latitude and longitude using OpenStreetMap API."""
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}"
        headers = {
            'User-Agent': 'WeatherAgent/1.0 (https://github.com/yourusername/weatheragent)'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None, None
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        logger.error(f"Error fetching coordinates: {e}")
        return None, None

def get_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """Fetch weather data for a given location."""
    try:
        response = requests.get(
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}"
            f"&current=temperature_2m,wind_speed_10m"
        )
        response.raise_for_status()
        data = response.json()
        return data.get("current", {})
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        return {"error": str(e)}

def get_current_date() -> str:
    """Get the current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "Get the current date in YYYY-MM-DD format.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_coordinates",
            "description": "Get latitude and longitude coordinates for a given city name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather data for provided coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"}
                },
                "required": ["latitude", "longitude"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

system_prompt = "You are a helpful weather assistant that can get weather data for any city."

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "What's the weather like in tunis today?"}
]

def call_function(name: str, args: Dict[str, Any]):
    if name == "get_current_date":
        return get_current_date()
    elif name == "get_coordinates":
        return get_coordinates(**args)
    elif name == "get_weather":
        return get_weather(**args)
    return None

# Send initial request to LM Studio
try:
    logger.debug(f"Sending request to LM Studio API at {LM_STUDIO_API_URL}")
    request_payload = {
        'model': 'deepseek-r1-distill-qwen-7b',
        'messages': messages,
        'tools': tools,
        'stream': True
    }
    logger.debug(f"Request payload: {json.dumps(request_payload, indent=2)}")
    
    response = requests.post(
        LM_STUDIO_API_URL,
        headers={"Content-Type": "application/json"},
        json={
            "model": "deepseek-r1-distill-qwen-7b",
            "messages": messages,
            "tools": tools,
            "stream": True
        },
        timeout=120
    )
    logger.debug(f"Received response with status code: {response.status_code}")
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"Error connecting to LM Studio API: {e}")
    logger.debug(f"Response content: {response.text if 'response' in locals() else 'No response received'}")
    print("Failed to connect to the weather assistant. Please check if the LM Studio server is running.")
    exit(1)

try:
    logger.debug(f"Raw API response: {response.text}")
    completion = response.json()
    logger.debug(f"Parsed API response: {json.dumps(completion, indent=2)}")
    
    if not isinstance(completion, dict):
        raise ValueError("Invalid response format: expected JSON object")
    if not completion.get("choices"):
        raise ValueError("Invalid response format: missing choices")
    if not isinstance(completion["choices"], list):
        raise ValueError("Invalid response format: choices should be a list")
    if len(completion["choices"]) == 0:
        raise ValueError("Invalid response format: empty choices list")
        
    # Validate the first choice structure
    first_choice = completion["choices"][0]
    if not isinstance(first_choice, dict):
        raise ValueError("Invalid choice format: expected JSON object")
    if "message" not in first_choice:
        raise ValueError("Invalid choice format: missing message field")
        
except (json.JSONDecodeError, ValueError) as e:
    logger.error(f"Error parsing API response: {e}")
    logger.debug(f"Response content: {response.text}")
    completion = {
        "error": str(e),
        "content": "Failed to process weather data. Please try again later.",
        "details": {
            "status_code": response.status_code if 'response' in locals() else None,
            "response_text": response.text if 'response' in locals() else None
        }
    }

# Process tool calls
if "choices" in completion and len(completion["choices"]) > 0:
    message = completion["choices"][0].get("message", {})
    tool_calls = message.get("tool_calls", [])
    
    for tool_call in tool_calls:
        try:
            name = tool_call["function"]["name"]
            args = json.loads(tool_call["function"]["arguments"])
            messages.append(message)

            result = call_function(name, args)
            messages.append(
                {"role": "tool", "tool_call_id": tool_call["id"], "content": json.dumps(result)}
            )
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error processing tool call: {e}")
            messages.append({"role": "system", "content": f"Error processing tool call: {e}"})

# Send updated request with weather data
try:
    response_2 = requests.post(
        LM_STUDIO_API_URL,
        headers={"Content-Type": "application/json"},
        json={
            "model": "deepseek-r1-distill-qwen-7b",
            "messages": messages,
            "tools": tools,
        },
        timeout=120
    )
    response_2.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"Error connecting to LM Studio API: {e}")
    print("Failed to get weather data. Please try again later.")
    exit(1)

completion_2 = response_2.json()

# Process final response
if "choices" in completion_2 and len(completion_2["choices"]) > 0:
    final_response = completion_2["choices"][0]["message"]
    if "content" in final_response:
        print(final_response["content"])
    else:
        print("Received response without content:", final_response)
else:
    print("Error: Invalid final response format")
