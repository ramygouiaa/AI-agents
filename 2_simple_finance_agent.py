from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv
from phi.tools.yfinance import YFinanceTools

load_dotenv()

def get_company_symbol(company: str) -> str:
    """Use this function to get the symbol for a company.

    Args:
        company (str): The name of the company.
    
    Returns:
        str: The symbol for the company.
    """

    symbols = {
        "Phidata": "PDTA",
        "Apple": "AAPL",
        "Amazon": "AMZN",
        "Google": "GOOGL",
    }

    return symbols.get(company, "Unknown")

# Create an instance of the Agent
agent_instance = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, stock_fundamentals=True)],
    show_tool_calls=True,
    markdown=True,
    instructions=["Use tables to display data."],
    debug_mode=True

)

# Call the print_response method on the instance
agent_instance.print_response("Summerize and compare analyst recommendations and fundamentals for TSLA and AAPL.")

