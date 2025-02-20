import json
import os
import requests
import logging
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set the LM Studio API base URL
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# --------------------------------------------------------------
# Define the tool (function) that we want to call
# --------------------------------------------------------------

def get_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """Fetch weather data for a given location."""
    try:
        response = requests.get(
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}"
            f"&current=temperature_2m,wind_speed_10m"
            f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
        )
        response.raise_for_status()
        data = response.json()
        return data.get("current", {})
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        return {"error": str(e)}

# --------------------------------------------------------------
# Step 1: Call model with get_weather tool defined
# --------------------------------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current temperature for provided coordinates in Celsius.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                },
                "required": ["latitude", "longitude"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]

system_prompt = "You are a helpful weather assistant."

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "What's the weather like in London today?"},
]

# Send request to LM Studio
response = requests.post(
    LM_STUDIO_API_URL,
    headers={"Content-Type": "application/json"},
    json={
        "model": "deepseek-r1-distill-qwen-7b",
        "messages": messages,
        "tools": tools,
        "stream": True,
    },
)

# Parse the response with error handling
try:
    completion = response.json()
    if not completion.get("choices"):
        raise ValueError("Invalid response format: missing choices")
except (json.JSONDecodeError, ValueError) as e:
    logger.error(f"Error parsing API response: {e}")
    completion = {"error": str(e)}

# --------------------------------------------------------------
# Step 2: Model decides to call function(s)
# --------------------------------------------------------------

def call_function(name, args):
    if name == "get_weather":
        return get_weather(**args)

# Extract tool calls with validation
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
else:
    logger.error("No valid choices in completion response")

# --------------------------------------------------------------
# Step 3: Supply result and call model again
# --------------------------------------------------------------

class WeatherResponse(BaseModel):
    temperature: float = Field(
        description="The current temperature in Celsius for the given location."
    )
    response: str = Field(
        description="A natural language response to the user's question."
    )

# Send updated request with weather data
response_2 = requests.post(
    LM_STUDIO_API_URL,
    headers={"Content-Type": "application/json"},
    json={
        "model": "deepseek-r1-distill-qwen-7b",
        "messages": messages,
        "tools": tools,
    },
)

completion_2 = response_2.json()

# --------------------------------------------------------------
# Step 4: Check model response
# --------------------------------------------------------------

# Process final response with validation
if "choices" in completion_2 and len(completion_2["choices"]) > 0:
    final_response = completion_2["choices"][0]["message"]
    if "content" in final_response:
        print(final_response["content"])
    else:
        print("Received response without content:", final_response)
else:
    print("Error: Invalid final response format")
