import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Enhanced logging configuration for detailed debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeatherAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WeatherAgent/2.0',
            'Content-Type': 'application/json'
        })
        
        self.LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"
        self.system_prompt = "You are a helpful weather assistant that can get weather data for any city."
        self.tools = self._initialize_tools()
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def _initialize_tools(self) -> list:
        return [
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

    def get_coordinates(self, city: str) -> Tuple[Optional[float], Optional[float]]:
        try:
            logger.debug(f"Fetching coordinates for city: {city}")
            params = {'format': 'json', 'q': city}
            response = self.session.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Received coordinates data: {data}")
            if data:
                lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
                logger.info(f"Coordinates for {city}: Latitude={lat}, Longitude={lon}")
                return lat, lon
            logger.warning(f"No coordinates found for city: {city}")
            return None, None
        except Exception as e:
            logger.error(f"Error getting coordinates: {e}")
            return None, None

    def get_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        try:
            logger.debug(f"Fetching weather for coordinates: Lat={latitude}, Lon={longitude}")
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'current': 'temperature_2m,wind_speed_10m'
            }
            response = self.session.get(
                "https://api.open-meteo.com/v1/forecast",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            weather_data = response.json().get('current', {})
            logger.debug(f"Received weather data: {weather_data}")
            return weather_data
        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
            return {'error': str(e)}

    def get_current_date(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def call_lm_studio(self, user_query: str) -> Dict[str, Any]:
        try:
            self.messages.append({"role": "user", "content": user_query})
            
            payload = {
                'model': 'mistral-nemo-instruct-2407',
                'messages': self.messages,
                'tools': self.tools,
                'stream': False
            }
            
            logger.debug(f"Sending request to LM Studio API: {payload}")
            
            self.session.headers.update({
                'Connection': 'keep-alive',
                'Keep-Alive': 'timeout=600, max=100'
            })
            
            response = self.session.post(
                self.LM_STUDIO_API_URL,
                json=payload,
                timeout=600,
                stream=True
            )
            
            full_response = ""
            try:
                for chunk in response.iter_content(chunk_size=None):
                    if chunk:
                        try:
                            chunk_str = chunk.decode('utf-8')
                            full_response += chunk_str
                            logger.debug(f"Received chunk: {chunk_str}")
                            
                            if len(full_response) % 1000 == 0:
                                self.session.get(self.LM_STUDIO_API_URL, timeout=1)
                                
                        except UnicodeDecodeError as e:
                            logger.error(f"Error decoding chunk: {e}")
                            continue
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error during streaming: {e}")
                return {"error": f"Connection lost: {str(e)}"}
            
            if not full_response:
                logger.error("Empty response received from LM Studio API")
                try:
                    logger.info("Attempting one retry...")
                    return self.call_lm_studio(user_query)
                except Exception as e:
                    logger.error(f"Retry failed: {e}")
                    return {"error": "Empty response from LM Studio API after retry"}
                
            # First try parsing as regular JSON
            try:
                response_data = json.loads(full_response)
            except json.JSONDecodeError:
                # If regular JSON fails, try to extract the JSON part
                json_start = full_response.find('{')
                json_end = full_response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = full_response[json_start:json_end]
                    try:
                        response_data = json.loads(json_str)
                    except json.JSONDecodeError:
                        # If we can't parse JSON, handle as plain text
                        return {
                            "message": {
                                "content": full_response.strip(),
                                "role": "assistant"
                            }
                        }
                else:
                    # If we can't find JSON, handle as plain text
                    return {
                        "message": {
                            "content": full_response.strip(),
                            "role": "assistant"
                        }
                    }
            
            logger.debug(f"Received final response from LM Studio: {response_data}")
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]
            elif "message" in response_data:
                return response_data
            elif isinstance(response_data, dict):
                return response_data
            return {"error": "No valid response from LM Studio"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error calling LM Studio API: {e}")
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error calling LM Studio API: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    def query_weather(self, city: str) -> Dict[str, Any]:
        logger.info(f"Querying weather for city: {city}")
        logger.debug(f"Starting weather query process for: {city}")
        
        lat, lon = self.get_coordinates(city)
        if lat is None or lon is None:
            return {'error': 'Could not get coordinates for city'}
            
        weather_data = self.get_weather(lat, lon)
        if 'error' in weather_data:
            return weather_data
            
        weather_info = (
            f"The current weather in {city} (coordinates: {lat}, {lon}) is:\n"
            f"Temperature: {weather_data.get('temperature_2m', 'N/A')}°C\n"
            f"Wind Speed: {weather_data.get('wind_speed_10m', 'N/A')} m/s\n"
            f"Time: {weather_data.get('time', 'N/A')}"
        )
        
        lm_response = self.call_lm_studio(
            f"Here is the current weather data for {city}:\n{weather_info}\n"
            "Please summarize this weather information in a user-friendly way."
        )
        
        return {
            'city': city,
            'coordinates': {'latitude': lat, 'longitude': lon},
            'weather': weather_data,
            'lm_response': lm_response,
            'date': self.get_current_date()
        }

if __name__ == "__main__":
    agent = WeatherAgent()
    result = agent.query_weather("Prague")
    print(json.dumps(result, indent=2))
