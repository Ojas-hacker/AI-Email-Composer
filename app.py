from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import google.generativeai as genai
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-gemini-api-key-here')
genai.configure(api_key=GEMINI_API_KEY)

# Database configuration
DATABASE = 'email_composer.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    
    # Create recipients table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            industry TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create company_data table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS company_data (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            industry TEXT NOT NULL,
            website TEXT,
            headquarters TEXT,
            mission TEXT,
            founded TEXT,
            employees TEXT,
            services TEXT,
            achievements TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create email_history table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS email_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_id INTEGER,
            email_type TEXT NOT NULL,
            subject TEXT,
            content TEXT NOT NULL,
            custom_message TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipient_id) REFERENCES recipients (id)
        )
    ''')
    
    # Insert default company data if not exists
    company_exists = conn.execute('SELECT COUNT(*) FROM company_data').fetchone()[0]
    if company_exists == 0:
        conn.execute('''
            INSERT INTO company_data 
            (id, name, industry, website, headquarters, mission, founded, employees, services, achievements)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'TechCorp Solutions',
            'Software Development',
            'www.techcorp.com',
            'San Francisco, CA',
            'Empowering businesses through innovative technology solutions',
            '2020',
            '50-100',
            json.dumps(['Web Development', 'Mobile Apps', 'AI Solutions', 'Cloud Services']),
            json.dumps([
                'Launched AI-powered customer service platform',
                'Expanded to 3 new markets',
                'Achieved 99.9% uptime for cloud services'
            ])
        ))
    
    conn.commit()
    conn.close()

class DatabaseManager:
    @staticmethod
    def add_recipient(name, email, company, position, industry, notes=''):
        """Add new recipient to database"""
        conn = get_db()
        try:
            conn.execute('''
                INSERT INTO recipients (name, email, company, position, industry, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, email, company, position, industry, notes))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_all_recipients():
        """Get all recipients from database"""
        conn = get_db()
        recipients = conn.execute('''
            SELECT * FROM recipients ORDER BY created_at DESC
        ''').fetchall()
        conn.close()
        return [dict(row) for row in recipients]
    
    @staticmethod
    def get_recipient_by_id(recipient_id):
        """Get recipient by ID"""
        conn = get_db()
        recipient = conn.execute('''
            SELECT * FROM recipients WHERE id = ?
        ''', (recipient_id,)).fetchone()
        conn.close()
        return dict(recipient) if recipient else None
    
    @staticmethod
    def update_recipient(recipient_id, name, email, company, position, industry, notes=''):
        """Update recipient information"""
        conn = get_db()
        conn.execute('''
            UPDATE recipients 
            SET name=?, email=?, company=?, position=?, industry=?, notes=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (name, email, company, position, industry, notes, recipient_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete_recipient(recipient_id):
        """Delete recipient from database"""
        conn = get_db()
        conn.execute('DELETE FROM recipients WHERE id = ?', (recipient_id,))
        conn.execute('DELETE FROM email_history WHERE recipient_id = ?', (recipient_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_company_data():
        """Get company data from database"""
        conn = get_db()
        company = conn.execute('SELECT * FROM company_data WHERE id = 1').fetchone()
        conn.close()
        
        if company:
            data = dict(company)
            data['services'] = json.loads(data['services']) if data['services'] else []
            data['achievements'] = json.loads(data['achievements']) if data['achievements'] else []
            return data
        return {}
    
    @staticmethod
    def update_company_data(name, industry, website, headquarters, mission, founded, employees, services, achievements):
        """Update company data"""
        conn = get_db()
        conn.execute('''
            UPDATE company_data 
            SET name=?, industry=?, website=?, headquarters=?, mission=?, founded=?, employees=?, 
                services=?, achievements=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=1
        ''', (name, industry, website, headquarters, mission, founded, employees, 
              json.dumps(services), json.dumps(achievements)))
        conn.commit()
        conn.close()
    
    @staticmethod
    def save_email_history(recipient_id, email_type, subject, content, custom_message=''):
        """Save generated email to history"""
        conn = get_db()
        conn.execute('''
            INSERT INTO email_history (recipient_id, email_type, subject, content, custom_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (recipient_id, email_type, subject, content, custom_message))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_email_history(recipient_id=None, limit=50):
        """Get email history"""
        conn = get_db()
        if recipient_id:
            history = conn.execute('''
                SELECT eh.*, r.name, r.email, r.company 
                FROM email_history eh
                JOIN recipients r ON eh.recipient_id = r.id
                WHERE eh.recipient_id = ?
                ORDER BY eh.generated_at DESC
                LIMIT ?
            ''', (recipient_id, limit)).fetchall()
        else:
            history = conn.execute('''
                SELECT eh.*, r.name, r.email, r.company 
                FROM email_history eh
                JOIN recipients r ON eh.recipient_id = r.id
                ORDER BY eh.generated_at DESC
                LIMIT ?
            ''', (limit,)).fetchall()
        conn.close()
        return [dict(row) for row in history]

class EmailComposer:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def generate_email(self, recipient_data, email_type, custom_message=""):
        """Generate personalized email using Gemini AI"""
        
        company_data = DatabaseManager.get_company_data()
        
        company_context = f"""
        Company Information:
        - Name: {company_data.get('name', 'TechCorp Solutions')}
        - Industry: {company_data.get('industry', 'Technology')}
        - Services: {', '.join(company_data.get('services', []))}
        - Mission: {company_data.get('mission', '')}
        - Founded: {company_data.get('founded', '')}
        - Website: {company_data.get('website', '')}
        - Recent Achievements: {', '.join(company_data.get('achievements', []))}
        """
        
        recipient_context = f"""
        Recipient Information:
        - Name: {recipient_data['name']}
        - Company: {recipient_data['company']}
        - Position: {recipient_data['position']}
        - Industry: {recipient_data['industry']}
        - Notes: {recipient_data.get('notes', '')}
        """
        
        prompts = {
            "introduction": f"""
            Write a professional introduction email from {company_data.get('name', 'our company')} to introduce our company and services.
            Make it personalized and engaging. Keep it concise but informative.
            Start with a clear subject line on the first line, followed by the email body.
            
            {company_context}
            {recipient_context}
            
            Additional context: {custom_message}
            """,
            
            "follow_up": f"""
            Write a follow-up email from {company_data.get('name', 'our company')} to check in and see if there are any opportunities for collaboration.
            Make it friendly and professional.
            Start with a clear subject line on the first line, followed by the email body.
            
            {company_context}
            {recipient_context}
            
            Additional context: {custom_message}
            """,
            
            "proposal": f"""
            Write a business proposal email from {company_data.get('name', 'our company')} suggesting how our services could benefit their company.
            Focus on value proposition and specific benefits.
            Start with a clear subject line on the first line, followed by the email body.
            
            {company_context}
            {recipient_context}
            
            Additional context: {custom_message}
            """,
            
            "newsletter": f"""
            Write a company newsletter email from {company_data.get('name', 'our company')} sharing recent updates and achievements.
            Make it engaging and informative.
            Start with a clear subject line on the first line, followed by the email body.
            
            {company_context}
            {recipient_context}
            
            Additional context: {custom_message}
            """
        }
        
        try:
            response = self.model.generate_content(prompts.get(email_type, prompts["introduction"]))
            email_content = response.text
            
            # Extract subject line (first line) and content
            lines = email_content.split('\n', 1)
            subject = lines[0].replace('Subject:', '').strip()
            content = lines[1] if len(lines) > 1 else email_content
            
            # Save to history
            DatabaseManager.save_email_history(
                recipient_data['id'], email_type, subject, email_content, custom_message
            )
            
            return email_content, subject
        except Exception as e:
            return f"Error generating email: {str(e)}", "Error"

# Initialize database and email composer
init_db()
email_composer = EmailComposer()

@app.route('/')
def index():
    recipients = DatabaseManager.get_all_recipients()
    company_data = DatabaseManager.get_company_data()
    return render_template('index.html', recipients=recipients, company_data=company_data)

@app.route('/add_recipient', methods=['POST'])
def add_recipient():
    name = request.form['name']
    email = request.form['email']
    company = request.form['company']
    position = request.form['position']
    industry = request.form['industry']
    notes = request.form.get('notes', '')
    
    if DatabaseManager.add_recipient(name, email, company, position, industry, notes):
        flash('Recipient added successfully!', 'success')
    else:
        flash('Error: Email already exists!', 'error')
    
    return redirect(url_for('index'))

@app.route('/edit_recipient/<int:recipient_id>')
def edit_recipient(recipient_id):
    recipient = DatabaseManager.get_recipient_by_id(recipient_id)
    if not recipient:
        flash('Recipient not found!', 'error')
        return redirect(url_for('index'))
    return render_template('edit_recipient.html', recipient=recipient)

@app.route('/update_recipient/<int:recipient_id>', methods=['POST'])
def update_recipient(recipient_id):
    name = request.form['name']
    email = request.form['email']
    company = request.form['company']
    position = request.form['position']
    industry = request.form['industry']
    notes = request.form.get('notes', '')
    
    DatabaseManager.update_recipient(recipient_id, name, email, company, position, industry, notes)
    flash('Recipient updated successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/compose_email', methods=['POST'])
def compose_email():
    recipient_id = int(request.form['recipient_id'])
    email_type = request.form['email_type']
    custom_message = request.form.get('custom_message', '')
    
    # Find recipient
    recipient = DatabaseManager.get_recipient_by_id(recipient_id)
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404
    
    # Generate email
    email_content, subject = email_composer.generate_email(recipient, email_type, custom_message)
    
    return jsonify({
        'success': True,
        'email_content': email_content,
        'subject': subject,
        'recipient': recipient
    })

@app.route('/delete_recipient/<int:recipient_id>')
def delete_recipient(recipient_id):
    DatabaseManager.delete_recipient(recipient_id)
    flash('Recipient deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/company_data')
def company_data():
    company_data = DatabaseManager.get_company_data()
    return render_template('company_data.html', company_data=company_data)

@app.route('/update_company_data', methods=['POST'])
def update_company_data():
    name = request.form['name']
    industry = request.form['industry']
    website = request.form['website']
    headquarters = request.form['headquarters']
    mission = request.form['mission']
    founded = request.form.get('founded', '')
    employees = request.form.get('employees', '')
    
    # Process services
    services_text = request.form.get('services', '')
    services = [s.strip() for s in services_text.split('\n') if s.strip()]
    
    # Process achievements
    achievements_text = request.form.get('achievements', '')
    achievements = [a.strip() for a in achievements_text.split('\n') if a.strip()]
    
    DatabaseManager.update_company_data(
        name, industry, website, headquarters, mission, founded, employees, services, achievements
    )
    
    flash('Company data updated successfully!', 'success')
    return redirect(url_for('company_data'))

@app.route('/email_history')
def email_history():
    history = DatabaseManager.get_email_history()
    return render_template('email_history.html', history=history)

@app.route('/recipient_history/<int:recipient_id>')
def recipient_history(recipient_id):
    recipient = DatabaseManager.get_recipient_by_id(recipient_id)
    history = DatabaseManager.get_email_history(recipient_id)
    return render_template('recipient_history.html', recipient=recipient, history=history)

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    conn = get_db()
    
    total_recipients = conn.execute('SELECT COUNT(*) FROM recipients').fetchone()[0]
    total_emails = conn.execute('SELECT COUNT(*) FROM email_history').fetchone()[0]
    
    # Email types distribution
    email_types = conn.execute('''
        SELECT email_type, COUNT(*) as count 
        FROM email_history 
        GROUP BY email_type
    ''').fetchall()
    
    # Recent activity (last 7 days)
    recent_activity = conn.execute('''
        SELECT DATE(generated_at) as date, COUNT(*) as count
        FROM email_history 
        WHERE generated_at >= date('now', '-7 days')
        GROUP BY DATE(generated_at)
        ORDER BY date DESC
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'total_recipients': total_recipients,
        'total_emails': total_emails,
        'email_types': [{'type': row[0], 'count': row[1]} for row in email_types],
        'recent_activity': [{'date': row[0], 'count': row[1]} for row in recent_activity]
    })

if __name__ == '__main__':
    app.run(debug=True)