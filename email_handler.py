import imaplib2 as imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG


class EmailHandler:
    def __init__(self):
        self.mail = None

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL(EMAIL_CONFIG['server'], EMAIL_CONFIG['port'])
            self.mail.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
            self.mail.select('inbox')
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self):
        try:
            if self.mail:
                self.mail.logout()
                self.mail = None
        except Exception as e:
            print(f"Error during logout: {e}")
            pass

    def search_emails(self):
        """Search for emails with support-related terms"""
        support_emails = []

        try:
            # Connect fresh for each request
            if not self.connect():
                return []

            # Search for emails from the last 24 hours
            since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            status, messages = self.mail.search(None, f'(SINCE {since_date})')

            if status != 'OK':
                self.disconnect()
                return []

            email_ids = messages[0].split()

            for email_id in email_ids:
                try:
                    # Use BODY.PEEK[] instead of RFC822 to avoid marking as read
                    status, msg_data = self.mail.fetch(email_id, '(BODY.PEEK[])')

                    if status != 'OK' or not msg_data:
                        continue

                    # Only accept proper (tuple, bytes) parts
                    valid_parts = [part for part in msg_data if isinstance(part, tuple) and len(part) > 1]
                    if not valid_parts:
                        continue

                    msg_bytes = valid_parts[0][1]
                    if not isinstance(msg_bytes, (bytes, bytearray)):
                        continue

                    msg = email.message_from_bytes(msg_bytes)

                    subject, encoding = decode_header(msg["Subject"])[0] if msg["Subject"] else ("No Subject", None)
                    if isinstance(subject, bytes):
                        try:
                            subject = subject.decode(encoding or 'utf-8', errors='ignore')
                        except Exception:
                            subject = subject.decode('utf-8', errors='ignore')

                    # Check if subject contains any search terms
                    if any(term.lower() in subject.lower() for term in EMAIL_CONFIG['search_terms']):
                        email_data = self.parse_email(msg, email_id, subject)
                        support_emails.append(email_data)

                except Exception as e:
                    print(f"Error processing email {email_id}: {e}")
                    # Reconnect if connection is lost
                    if "illegal in state" in str(e).lower():
                        self.disconnect()
                        if not self.connect():
                            break  # Break out of the loop if we can't reconnect
                    continue

            return support_emails

        except Exception as e:
            print(f"Error searching emails: {e}")
            return []
        finally:
            # Always disconnect to clean up connection
            self.disconnect()

    def parse_email(self, msg, email_id, subject):
        """Extract relevant information from email"""
        # Extract sender
        sender = msg.get("From", "")

        # Extract date
        date = msg.get("Date", "")

        # Extract body
        body = ""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body = part.get_payload(decode=True)
                        if body:
                            body = body.decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True)
                if body:
                    body = body.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error parsing email body: {e}")
            body = "Could not parse email body"

        # Extract contact information
        phone_numbers = []
        emails = []

        if body:
            try:
                phone_numbers = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', body)
            except:
                pass

            try:
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', body)
            except:
                pass

        return {
            'id': email_id.decode() if isinstance(email_id, bytes) else str(email_id),
            'sender': sender,
            'subject': subject,
            'body': body,
            'date': date,
            'contacts': {
                'phone_numbers': list(set(phone_numbers)),
                'emails': list(set(emails))
            }
        }

    def mark_as_processed(self, email_id):
        """Mark email as processed (read)"""
        # Connect fresh for each operation
        if not self.connect():
            return False

        try:
            # Ensure email_id is in the correct format
            if isinstance(email_id, str):
                email_id = email_id.encode()
            self.mail.store(email_id, '+FLAGS', '\\Seen')
            return True
        except Exception as e:
            print(f"Error marking email as processed: {e}")
            return False
        finally:
            # Clean up connection
            self.disconnect()

    def send_email(self, to_email, subject, body, reply_to=None):
        """Send an email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_CONFIG['username']
            msg['To'] = to_email
            msg['Subject'] = subject

            if reply_to:
                msg['In-Reply-To'] = reply_to
                msg['References'] = reply_to

            # Add body to email
            msg.attach(MIMEText(body, 'plain'))

            # Create SMTP session
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])

            # Send email
            text = msg.as_string()
            server.sendmail(EMAIL_CONFIG['username'], to_email, text)
            server.quit()

            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False