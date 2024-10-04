# Unread Gmail Summary Bot!

## Overview
This Python script automates the process of summarizing unread Gmail messages using the Gmail API and the OpenAI API. The summarized emails are then sent to a specified relay email address for easy review.

![image](https://github.com/user-attachments/assets/5cce775e-f837-4921-bba2-2f70ed986a58)

The script performs the following tasks:
1. **Authentication**: Authenticates with Gmail via OAuth2 to access the user's inbox.
2. **Email Retrieval**: Fetches unread emails and extracts relevant information such as sender, subject, and body content.
3. **Summarization**: Uses OpenAI's API to generate concise bullet-point summaries of email content.
4. **Email Composition**: Creates an email message containing the summarized information.
5. **Sending Email**: Sends the summary email to a relay email address using the Gmail API.

## Prerequisites

Before running the script, ensure you have the following installed and set up:

1. **Python 3.x**: Install Python from the official [Python website](https://www.python.org/downloads/).
2. **Gmail API credentials**: You will need to enable the Gmail API and download OAuth2 credentials:
    - Go to the [Google API Console](https://console.cloud.google.com/).
    - Enable the Gmail API for your project.
    - Download the `credentials.json` file for OAuth2 access.
3. **OpenAI API Key**: Obtain an API key from [OpenAI](https://beta.openai.com/signup/).
4. **Install dependencies** using `pip`:
    ```bash
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client openai python-dotenv beautifulsoup4
    ```

## Setup

1. **Environment Variables**:
   Create a `.env` file in the root directory of the project and add the following variable:
   ```bash
   OPENAI_API_KEY=your-openai-api-key
   ```
   Replace `your-openai-api-key` with your actual OpenAI API key.

2. **API Key for OpenAI**:
   The script reads the API key from a file named `API_KEY` (located in the same directory). Create this file and add your OpenAI API key inside it.

3. **OAuth2 Credentials**:
   Download the `credentials.json` file from the Google API Console and place it in the same directory as the script.

## How to Run

1. **Authentication**:
   - When running the script for the first time, it will prompt you to authenticate via OAuth2 by opening a browser window. This step generates a `token.json` file to save your credentials for future runs.
   
2. **Execution**:
   Run the script using the following command:
   ```bash
   python email_summarizer.py
   ```

3. **Gmail Relay Address**:
   Ensure you set the correct relay address in the script by modifying the `relay_email` variable to your desired email forwarding address.

4. **Summarization**:
   The script will retrieve the unread emails, summarize them using OpenAI's GPT-3.5 Turbo model, and forward the summaries to your relay email address.

## Script Breakdown

1. **`authenticate_gmail()`**:
   Handles Gmail API authentication using OAuth2. It checks for a saved token in `token.json` and refreshes or generates a new token if needed.

2. **`get_unread_emails()`**:
   Fetches unread emails from the user's Gmail inbox, extracting information such as sender, subject, date, and the email body.

3. **`extract_body()`**:
   Decodes the email content from either text or HTML format and cleans it up by removing any hyperlinks.

4. **`summarize_email()`**:
   Sends the email content to OpenAI’s GPT model and returns a summarized version in bullet points.

5. **`compose_email()`**:
   Formats the summaries into an HTML email body and prepares it for sending.

6. **`send_email()`**:
   Sends the composed email to the relay email address using the Gmail API.

7. **`main()`**:
   Orchestrates the entire process: authenticates Gmail, fetches emails, summarizes content, and sends the summary email.

## Logging

The script logs each email's summary to a file called `email_summaries.log`. You can use this log to track all the processed emails and summaries.

## Additional Notes

- **Error Handling**: If there's an issue with OpenAI or Gmail API, the error is logged and reported in the console.
- **HTML Clean-up**: The email body is cleaned up from unnecessary HTML tags and hyperlinks to ensure clean summaries.
