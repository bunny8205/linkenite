from flask import Flask, render_template, jsonify, request
from email_handler import EmailHandler
from ai_processor import AIProcessor
from datetime import datetime, timedelta
import json
from collections import defaultdict
import traceback
import sqlite3
import re
import os
from config import DATABASE_URI

app = Flask(__name__)
app.config.from_pyfile('config.py')

email_handler = EmailHandler()
ai_processor = AIProcessor()


# Database setup
def init_db():
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS emails
              (
                  id
                  TEXT
                  PRIMARY
                  KEY,
                  sender
                  TEXT,
                  subject
                  TEXT,
                  body
                  TEXT,
                  date
                  TEXT,
                  sentiment
                  TEXT,
                  urgency
                  TEXT,
                  requirements
                  TEXT,
                  ai_response
                  TEXT,
                  status
                  TEXT,
                  processed_at
                  TEXT
              )
              ''')
    c.execute('''
              CREATE TABLE IF NOT EXISTS email_stats
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY
                  AUTOINCREMENT,
                  total_received
                  INTEGER,
                  resolved
                  INTEGER,
                  pending
                  INTEGER,
                  by_sentiment
                  TEXT,
                  by_urgency
                  TEXT,
                  last_updated
                  TEXT
              )
              ''')
    conn.commit()
    conn.close()


init_db()


def get_db_connection():
    conn = sqlite3.connect('emails.db')
    conn.row_factory = sqlite3.Row
    return conn


def load_emails_from_db():
    conn = get_db_connection()
    emails = conn.execute('SELECT * FROM emails').fetchall()
    conn.close()
    return [dict(email) for email in emails]


def save_email_to_db(email_data):
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO emails 
        (id, sender, subject, body, date, sentiment, urgency, requirements, ai_response, status, processed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        email_data['id'], email_data['sender'], email_data['subject'], email_data['body'],
        email_data['date'], email_data['sentiment'], email_data['urgency'], email_data['requirements'],
        email_data['ai_response'], email_data['status'], email_data['processed_at']
    ))
    conn.commit()
    conn.close()


def update_email_in_db(email_id, updates):
    conn = get_db_connection()
    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values())
    values.append(email_id)
    conn.execute(f'UPDATE emails SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()


def load_stats_from_db():
    conn = get_db_connection()
    stats = conn.execute('SELECT * FROM email_stats ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()

    if stats:
        return {
            'total_received': stats['total_received'],
            'resolved': stats['resolved'],
            'pending': stats['pending'],
            'by_sentiment': json.loads(stats['by_sentiment']),
            'by_urgency': json.loads(stats['by_urgency']),
            'last_updated': stats['last_updated']
        }
    else:
        return {
            'total_received': 0,
            'resolved': 0,
            'pending': 0,
            'by_sentiment': defaultdict(int),
            'by_urgency': defaultdict(int),
            'last_updated': None
        }


def save_stats_to_db(stats):
    conn = get_db_connection()
    conn.execute('''
                 INSERT INTO email_stats (total_received, resolved, pending, by_sentiment, by_urgency, last_updated)
                 VALUES (?, ?, ?, ?, ?, ?)
                 ''', (
                     stats['total_received'],
                     stats['resolved'],
                     stats['pending'],
                     json.dumps(dict(stats['by_sentiment'])),
                     json.dumps(dict(stats['by_urgency'])),
                     stats['last_updated']
                 ))
    conn.commit()
    conn.close()


@app.route('/')
def dashboard():
    return render_template('index.html')


@app.route('/api/emails')
def get_emails():
    """Retrieve and process emails"""
    try:
        # Load existing data from database
        processed_emails = load_emails_from_db()
        email_stats = load_stats_from_db()

        # Get emails from the last 24 hours
        emails = email_handler.search_emails()

        # Process each email with AI
        for email_data in emails:
            # Skip if already processed
            if any(e['id'] == email_data['id'] for e in processed_emails):
                continue

            # Analyze with AI
            email_data['sentiment'] = ai_processor.analyze_sentiment(email_data['body'])
            email_data['urgency'] = ai_processor.determine_urgency(email_data['body'])
            email_data['requirements'] = ai_processor.extract_requirements(email_data['body'])
            email_data['ai_response'] = ai_processor.generate_response(email_data)
            email_data['status'] = 'Pending'
            email_data['processed_at'] = datetime.now().isoformat()

            # Save to database
            save_email_to_db(email_data)
            processed_emails.append(email_data)

            # Update stats
            email_stats['total_received'] += 1
            email_stats['pending'] += 1
            email_stats['by_sentiment'][email_data['sentiment']] += 1
            email_stats['by_urgency'][email_data['urgency']] += 1

        # Save updated stats to database
        email_stats['last_updated'] = datetime.now().isoformat()
        save_stats_to_db(email_stats)

        # Sort by urgency (urgent first) and then by date
        processed_emails.sort(key=lambda x: (0 if x['urgency'] == 'Urgent' else 1, x['date']), reverse=True)

        return jsonify({
            'emails': processed_emails,
            'stats': email_stats
        })
    except Exception as e:
        print(f"Error in get_emails: {e}")
        print(traceback.format_exc())
        return jsonify({
            'emails': load_emails_from_db(),
            'stats': load_stats_from_db(),
            'error': str(e)
        })


@app.route('/api/emails/<email_id>/update', methods=['POST'])
def update_email(email_id):
    """Update email status"""
    data = request.json
    status = data.get('status')

    # Load current stats
    email_stats = load_stats_from_db()
    processed_emails = load_emails_from_db()

    for email in processed_emails:
        if email['id'] == email_id:
            old_status = email['status']

            # Update email in database
            update_email_in_db(email_id, {'status': status})

            # Update stats
            if old_status == 'Pending' and status == 'Resolved':
                email_stats['pending'] -= 1
                email_stats['resolved'] += 1
            elif old_status == 'Resolved' and status == 'Pending':
                email_stats['resolved'] -= 1
                email_stats['pending'] += 1

            # Save updated stats
            email_stats['last_updated'] = datetime.now().isoformat()
            save_stats_to_db(email_stats)

            # Mark as read in email server
            email_handler.mark_as_processed(email_id)

            return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Email not found'})


@app.route('/api/emails/<email_id>/response', methods=['POST'])
def update_response(email_id):
    """Update AI response"""
    data = request.json
    response = data.get('response')

    # Update response in database
    update_email_in_db(email_id, {'ai_response': response})

    return jsonify({'success': True})


@app.route('/api/emails/<email_id>/send', methods=['POST'])
def send_response(email_id):
    """Send response email"""
    data = request.json
    response = data.get('response')

    # Get email details
    processed_emails = load_emails_from_db()
    email = next((e for e in processed_emails if e['id'] == email_id), None)

    if not email:
        return jsonify({'success': False, 'error': 'Email not found'})

    # Extract recipient email
    sender_email = email['sender']
    # Simple email extraction from sender field
    email_match = re.search(r'<(.+?)>', sender_email)
    if email_match:
        recipient_email = email_match.group(1)
    else:
        recipient_email = sender_email

    # Send email
    success = email_handler.send_email(
        recipient_email,
        f"Re: {email['subject']}",
        response,
        reply_to=email_id
    )

    if success:
        # Update status to resolved
        update_email_in_db(email_id, {'status': 'Resolved'})

        # Update stats
        email_stats = load_stats_from_db()
        email_stats['pending'] -= 1
        email_stats['resolved'] += 1
        email_stats['last_updated'] = datetime.now().isoformat()
        save_stats_to_db(email_stats)

        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to send email'})


@app.route('/api/stats')
def get_stats():
    """Get statistics"""
    return jsonify(load_stats_from_db())


@app.route('/api/stats/history')
def get_stats_history():
    """Get historical statistics for charts"""
    conn = get_db_connection()
    stats_history = conn.execute('SELECT * FROM email_stats ORDER BY id DESC LIMIT 24').fetchall()
    conn.close()

    history_data = []
    for stat in stats_history:
        history_data.append({
            'time': stat['last_updated'],
            'total': stat['total_received'],
            'resolved': stat['resolved'],
            'pending': stat['pending'],
            'by_sentiment': json.loads(stat['by_sentiment']),
            'by_urgency': json.loads(stat['by_urgency'])
        })

    return jsonify(history_data)


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])