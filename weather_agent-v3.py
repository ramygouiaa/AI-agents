import logging
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enhanced logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeatherAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WeatherAgent/3.0',
            'Content-Type': 'application/json'
        })
        
        # Initialize Groq agent
        self.agent = Agent(
            name="Weather Agent",
            model=Groq(id="llama-3.3-70b-versatile"),
            instructions="You are a helpful weather assistant that can get weather data for any city.",
            show_tool_calls=True,
            markdown=True,
            debug_mode=True
        )

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
                'current': 'temperature_2m,wind_speed_10m',
                'timezone': 'auto'
            }
            response = self.session.get(
                "https://api.open-meteo.com/v1/forecast",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            weather_data = response.json().get('current', {})
            
            # Add time difference warning
            api_time = datetime.fromisoformat(weather_data['time'])
            system_time = datetime.now()
            time_diff = abs((api_time - system_time).total_seconds())
            
            if time_diff > 3600:  # If difference is more than 1 hour
                logger.warning(f"Significant time difference detected: API time {api_time} vs System time {system_time}")
                weather_data['time_warning'] = (
                    f"Note: Weather data is from {api_time.strftime('%Y-%m-%d %H:%M')} "
                    f"(current system time is {system_time.strftime('%Y-%m-%d %H:%M')})"
                )
            
            logger.debug(f"Received weather data: {weather_data}")
            return weather_data
        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
            return {'error': str(e)}

    def get_current_date(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def query_weather(self, city: str) -> Dict[str, Any]:
        logger.info(f"Querying weather for city: {city}")
        logger.debug(f"Starting weather query process for: {city}")
        
        # Create or append to weather_summary.txt
        with open("weather_summary.txt", "a") as f:
            f.write(f"\n{'=' * 50}\nWeather Summary for {city} on {self.get_current_date()}\n")
        
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
        
        # Include time warning if present
        if 'time_warning' in weather_data:
            weather_info += f"\n{weather_data['time_warning']}"
        
        # Use Groq agent for natural language processing
        response = self.agent.run(
            f"Here is the current weather data for {city}:\n{weather_info}\n"
            "Please summarize this weather information in a user-friendly way, "
            "making sure to include the exact time (HH:MM) along with the date."
        )
        
        summary = response.messages[-1].content if response and response.messages else "No summary available"
        
        # Write the full summary to the file
        with open("weather_summary.txt", "a") as f:
            f.write(f"\n{'=' * 50}\nWeather Summary for {city} on {self.get_current_date()}\n")
            f.write(summary + "\n")
            
        return {
            'city': city,
            'coordinates': {'latitude': lat, 'longitude': lon},
            'weather': weather_data,
            'summary': summary,
            'date': self.get_current_date()
        }

if __name__ == "__main__":
    agent = WeatherAgent()
    result = agent.query_weather("london")
    print(json.dumps(result, indent=2))
