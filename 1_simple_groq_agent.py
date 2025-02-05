from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Create an instance of the Agent
agent_instance = Agent(
    model=Groq(id="llama-3.3-70b-versatile")
)

# Call the print_response method on the instance
agent_instance.print_response("explain for a 5 year old kid why the sky is blue")
