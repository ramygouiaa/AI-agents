from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.yfinance import YFinanceTools
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

web_agent = Agent(
    name="Web Agent",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[DuckDuckGo(search=True, news=True)],
    instructions="Always include sources and references.",
    show_tool_calls=True,
    markdown=True,
)

finance_agent = Agent(
    name="Finance Agent",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True)],
    instructions="use tables to display data",
    show_tool_calls=True,
    markdown=True,
)

agent_team_lead = Agent(
    team=[web_agent, finance_agent],
    model=Groq(id="llama-3.3-70b-versatile"),
    instructions="Use the web agent to search for information and the finance agent to analyze the data.",
    show_tool_calls=True,
    markdown=True,
    debug_mode=True,
)

agent_team_lead.print_response("Summerize analyst recommendations and stock price then share the latest news for NVDA.")
