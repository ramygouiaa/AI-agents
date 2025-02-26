import imaplib
import email
import json
import base64
import os
from dotenv import load_dotenv
from email.header import decode_header
from datetime import datetime


# At the top of your script
os.environ["GMAIL_EMAIL"] = "ramigouia1990@gmail.com"
os.environ["GMAIL_PASSWORD"] = "vxyahpqrprojpnmq"
os.environ["SEARCH_ADDRESS"] = "rabai.elyes@gmail.com"


def decode_str(encoded_string):
    """Decode encoded email header strings"""
    if encoded_string:
        decoded_parts = decode_header(encoded_string)
        return ''.join([
            part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
            for part, encoding in decoded_parts
        ])
    return ''

def get_email_content(message):
    """Extract text content from email message"""
    content = ""
    
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if "attachment" not in content_disposition:
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        content += body
                    except:
                        try:
                            content += part.get_payload(decode=True).decode('latin-1')
                        except:
                            content += "Error decoding email content"
    else:
        content_type = message.get_content_type()
        if content_type == "text/plain":
            try:
                content = message.get_payload(decode=True).decode('utf-8')
            except:
                try:
                    content = message.get_payload(decode=True).decode('latin-1')
                except:
                    content = "Error decoding email content"
                    
    return content

def get_attachments(message):
    """Extract attachment information from email message"""
    attachments = []
    
    if message.is_multipart():
        for part in message.walk():
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    filename = decode_str(filename)
                    size = len(part.get_payload(decode=True))
                    attachments.append({
                        "filename": filename,
                        "size": size,
                        "content_type": part.get_content_type()
                    })
                    
    return attachments

def fetch_emails_from_sender(email_address, password, search_address, max_emails=10):
    """
    Fetch emails from a specific sender in Gmail inbox
    
    Args:
        email_address (str): Your Gmail address
        password (str): Your Gmail password or app password
        search_address (str): The email address to search for
        max_emails (int): Maximum number of emails to retrieve
        
    Returns:
        list: List of emails in JSON format
    """
    print(f"Connecting to Gmail for account: {email_address}")
    # Debug: Check password string (without revealing full password)
    password_length = len(password) if password else 0
    print(f"Using password with length: {password_length}")
    
    try:
        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        
        # Login to account
        print("Attempting login...")
        mail.login(email_address, password)
        print("Login successful!")
        
        # Select inbox
        print("Selecting inbox...")
        mail.select("INBOX")
        
        # Search for all emails from the specified address
        print(f"Searching for emails from: {search_address}")
        status, messages = mail.search(None, f'FROM "{search_address}"')
        
        if status != "OK":
            print(f"No messages found from {search_address}")
            return []
        
        # Get list of email IDs
        email_ids = messages[0].split()
        email_count = len(email_ids)
        print(f"Found {email_count} emails from {search_address}")
        
        # Limit the number of emails to process
        if max_emails < len(email_ids):
            email_ids = email_ids[-max_emails:]
            print(f"Processing only the most recent {max_emails} emails")
        
        email_list = []
        
        # Process each email
        for i, email_id in enumerate(reversed(email_ids)):
            print(f"Processing email {i+1}/{len(email_ids)}...")
            # Fetch the email
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                print(f"Error fetching email ID: {email_id}")
                continue
                
            # Parse the email content
            raw_email = msg_data[0][1]
            message = email.message_from_bytes(raw_email)
            
            # Extract email details
            msg_from = decode_str(message["From"])
            msg_to = decode_str(message["To"])
            msg_subject = decode_str(message["Subject"])
            msg_date = decode_str(message["Date"])
            
            print(f"Email from: {msg_from}, Subject: {msg_subject}")
            
            # Get text content
            text_content = get_email_content(message)
            
            # Get attachments
            attachments = get_attachments(message)
            
            # Create email object
            email_obj = {
                "from": msg_from,
                "to": msg_to,
                "subject": msg_subject,
                "date": msg_date,
                "textContent": text_content,
                "attachments": attachments
            }
            
            email_list.append(email_obj)
        
        print(f"Successfully processed {len(email_list)} emails")
        return email_list
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return []
    
    finally:
        # Close the connection
        try:
            print("Closing connection...")
            mail.close()
            mail.logout()
            print("Connection closed")
        except:
            print("Error closing connection")

def main():
    """Main function to run the script"""
    # Load environment variables from .env file
    print("Loading environment variables...")
    load_dotenv()
    
    # Get credentials from environment variables
    your_email = os.environ.get("GMAIL_EMAIL", "").strip()
    password = os.environ.get("GMAIL_PASSWORD", "").strip()
    
    # Verify that required environment variables are set
    if not your_email:
        print("Error: GMAIL_EMAIL environment variable not set in .env file")
        return
    
    if not password:
        print("Error: GMAIL_PASSWORD environment variable not set in .env file")
        return
    
    print(f"Email address loaded: {your_email}")
    print(f"Password loaded: {'*' * len(password)}")
    
    # Get the sender address to search for
    search_address = os.environ.get("SEARCH_ADDRESS", "").strip()
    
    # Fetch emails
    emails = fetch_emails_from_sender(your_email, password, search_address)
    
    # Print as JSON
    if emails:
        print("\nFound emails:")
        print(json.dumps(emails, indent=2))
    else:
        print("\nNo emails found or error occurred")

if __name__ == "__main__":
    main()
    
"""
Example .env file:

GMAIL_EMAIL=youremail@gmail.com
GMAIL_PASSWORD=your_password_or_app_password
"""