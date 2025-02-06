# Advanced Finance Agent Overview

This project implements an advanced finance agent using the `phi` library, specifically designed to interact with the GROQ model and provide real-time stock information.

## Key Features

- **Dynamic Response Generation**: The agent utilizes the GROQ model to generate tailored responses to user queries.
- **Email Notifications**: The agent can send email notifications with current stock prices, leveraging secure email configuration.
- **Real-Time Stock Data**: Integrates with the `yfinance` library to fetch and provide up-to-date stock prices for various companies.
- **Environment Configuration**: Utilizes environment variables for secure management of sensitive information, such as API keys and email credentials.
- **Error Handling**: Robust error handling mechanisms are in place to manage common issues, such as missing environment variables.

## Getting Started

To run the advanced finance agent, follow these steps:

1. **Set Up Environment Variables**: Ensure that the necessary environment variables are configured in the `.env` file, including:

   - `GROQ_API_KEY`: Your API key for the GROQ model.
   - `EMAIL_HOST`: SMTP server address (e.g., "smtp.gmail.com").
   - `EMAIL_PORT`: SMTP server port (e.g., 587 for TLS).
   - `EMAIL_USER`: Your email address.
   - `EMAIL_PASSWORD`: Your email password or app-specific password.

2. **Install Dependencies**: Make sure to install the required libraries:

   ```bash
   pip install phi yfinance python-dotenv
   ```

3. **Run the Agent**: Execute the agent script to start receiving stock price updates via email.

## Conclusion

The Advanced Finance Agent showcases the potential of AI-driven agents in providing interactive and informative experiences in the finance domain. This implementation serves as a foundation for further enhancements and applications in diverse fields.
