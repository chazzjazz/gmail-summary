import os
import base64
import logging
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import openai
from openai import OpenAI
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail API SCOPES
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]

# Forward to self via Relay address
relay_email = 'emailid+relay@gmail.com'

# Load environment variables from .env file
load_dotenv()

# Logging setup
logging.basicConfig(filename='email_summaries.log', level=logging.INFO, format='%(asctime)s - %(message)s')


def authenticate_gmail():
    """Authenticate and return the Gmail API service."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service


def get_unread_emails(service, max_results=10, query = "is:unread"):
    """Retrieve a list of unread emails based on the specified query."""
    results = service.users().messages().list(userId='me', maxResults=max_results, q=query).execute()
    messages = results.get('messages', [])

    emails = []
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        payload = msg['payload']
        headers = payload.get('headers', [])
        subject = sender = date = None

        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
            if header['name'] == 'From':
                sender = header['value']
            if header['name'] == 'Date':
                date = header['value']

        body = extract_body(payload)
        emails.append({
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body,
            'id': message['id']  # For generating Gmail link
        })
    return emails


def remove_hyperlinks(text):
    """Remove hyperlinks from the text."""
    import re
    return re.sub(r'http[s]?://\S+', '', text)


def extract_body(payload):
    """Extract the body of the email, prioritizing plain text and cleaning HTML."""
    data = None

    if 'parts' in payload:
        parts = payload['parts']
        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                break
            elif part['mimeType'] == 'text/html':
                data = part['body']['data']

        if data is not None:
            text = base64.urlsafe_b64decode(data.encode('UTF-8')).decode('UTF-8')
            soup = BeautifulSoup(text, 'html.parser')
            clean_text = soup.get_text()
            clean_text = remove_hyperlinks(clean_text)
            return clean_text
    else:
        data = payload['body']['data']
        text = base64.urlsafe_b64decode(data.encode('UTF-8')).decode('UTF-8')
        soup = BeautifulSoup(text, 'html.parser')
        clean_text = soup.get_text()
        return clean_text

    return ""


openai_api_key = open("API_KEY", 'r').read().strip()

if not openai_api_key:
    raise ValueError("API key not found. Make sure it's properly set in the file.")

client = OpenAI(api_key=openai_api_key)


def summarize_email(content):
    """Summarize the given email content using OpenAI API."""
    try:
        prompt = (
            f"Summarize the following email in no more than 3 bullet points. "
            f"Make sure each key point is listed as a bullet point:\n\n{content}"
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes emails."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.5
        )

        summary = response.choices[0].message.content.strip()

        summary_lines = summary.split('\n')
        bullet_point_summary = ""
        for line in summary_lines:
            clean_line = line.strip()
            if clean_line and not clean_line.startswith('-'):
                bullet_point_summary += f"- {clean_line}\n"
            else:
                bullet_point_summary += f"{clean_line}\n"

        return bullet_point_summary

    except openai.error.OpenAIError as e:
        logging.error(f"Error in OpenAI summarization: {e}")
        return "Error generating summary."


def compose_email(recipient, subject, summary):
    """Compose an email message with the summary in HTML format."""
    message = MIMEMultipart("alternative")
    message['to'] = recipient
    message['subject'] = subject

    # Replace newlines in summary with HTML <br> tags
    formatted_summary = summary.replace('\n', '<br>')

    # Create HTML content with the summary
    html_content = f"""
        <html>
        <body>
            <h3>Email Summary</h3>
            <p>{formatted_summary}</p>  <!-- Use the pre-formatted summary -->
        </body>
        </html>
        """

    # Attach HTML content to the email
    body = MIMEText(html_content, 'html')
    message.attach(body)

    # Encode the message to send via Gmail API
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


def send_email(service, email):
    """Send an email using Gmail API."""
    try:
        sent_message = service.users().messages().send(userId='me', body=email).execute()
        print('Successfully sent message.')
    except Exception as error:
        print(f'Error: {error}')
        sent_message = None
    return sent_message


def main():
    # Authenticate Gmail API
    service = authenticate_gmail()

    # Get unread emails from Gmail
    emails = get_unread_emails(service, max_results=10, query="is:unread")

    # Initialize a string to accumulate all summaries in HTML format
    email_summaries = ""

    # Summarize each email and accumulate the summaries
    for email in emails:
        print(f"Summarizing email from {email['sender']} with subject '{email['subject']}'")
        summary = summarize_email(email['body'])

        # Construct the summary for this specific email in HTML format
        email_summary = (
            f"<p><strong>From:</strong> {email['sender']}<br>"
            f"<strong>Subject:</strong> {email['subject']}<br>"
            f"<strong>Timestamp:</strong> {email['date']}<br>"
            # f"<strong>Link:</strong> <a href='https://mail.google.com/mail/u/0/#inbox/{email['id']}'>View Email</a><br>" #check URL in Gmail to see if link should be u/0 or other
            f"<strong>Link:</strong> <a href='https://mail.google.com/mail/u/1/#inbox/{email['id']}'>View Email</a><br>" # My preferred email is u/1
            f"<strong>Summary:</strong><br>{summary.replace('- ', '• ')}<br></p><hr>"
        )

        # Add this email's summary to the overall summary string
        email_summaries += email_summary

        # Log the summary
        logging.info(email_summary)

    # Send the accumulated summary email if there are any unread emails
    if email_summaries:
        recipient = relay_email  # Set the recipient email
        subject = "Summary of Unread Emails"
        composed_email = compose_email(recipient, subject, email_summaries)
        send_email(service, composed_email)


if __name__ == '__main__':
    main()
