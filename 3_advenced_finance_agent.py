import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv
from phi.tools.yfinance import YFinanceTools
import yfinance as yf

# Load environment variables
load_dotenv()

# Email configuration (load from environment variables)
EMAIL_HOST = os.getenv("EMAIL_HOST")  # e.g., "smtp.gmail.com"
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))  # e.g., 587 for TLS
EMAIL_USER = os.getenv("EMAIL_USER")  # Your email address
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Your email password or app-specific password

print(EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD)

def send_email(to_email: str, subject: str, body: str) -> str:
    """Send an email with the provided subject and body.

    Args:
        to_email (str): The recipient's email address.
        subject (str): The subject of the email.
        body (str): body of the message.

    Returns:
        str: A message indicating success or failure.
    """
    if not all([EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD]):
        return "Email configuration is incomplete. Please check environment variables."

    try:
        # Create the email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        # Send the email
        with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())

        return f"Email sent successfully to {to_email}."
    except Exception as e:
        return f"Failed to send email: {str(e)}"

# Create an instance of the Agent
agent_instance = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools(stock_price=True), send_email],  # Use the YFinance tool
          # Add the email tool,
    show_tool_calls=True,
    markdown=True,
    instructions=[
        "Use the tools needed to provide current stock prices."
    ],
    debug_mode=True,
)

# Fetch stock prices using yfinance
nvda = yf.Ticker("NVDA")
msft = yf.Ticker("MSFT")

nvda_price = nvda.info['currentPrice']
msft_price = msft.info['currentPrice']

# Construct the email body with actual prices
email_body = f"The current stock price for NVDA is ${nvda_price} and for MSFT is ${msft_price}."
print(email_body)
# Send the email
send_email("user@example.com", "Current Stock Prices for NVDA and MSFT", email_body)

# Removed the print_response call to prevent additional emails
agent_instance.print_response("Provide the current stock prices for NVDA and MSFT.")