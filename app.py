"""
Event Ticketing and Attendance Management System
A Flask web application for managing event ticketing and attendance tracking.
"""

import os
import uuid
import csv
import io
import logging
import time
import json
import base64
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, Response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import qrcode
from io import BytesIO

# Import models and forms
from models import db, Event, Participant, Certificate, Quiz, QuizQuestion, QuizParticipant, QuizAnswer
from forms import EventForm, ParticipantUploadForm, ManualParticipantForm, EditParticipantForm, CertificateForm, AttendanceForm, QuizForm, QuizQuestionUploadForm, QuizJoinForm

def allowed_file(filename):
    """Check if file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, upload_folder='uploads/certificates'):
    """Save uploaded file and return the file path"""
    if file and allowed_file(file.filename):
        # Create upload directory if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        # Return relative path for web access
        return f"/{filepath.replace(os.sep, '/')}"
    return None
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_mail import Mail, Message
from wtforms import StringField, DateField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email
from werkzeug.utils import secure_filename
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///event_ticketing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# DEBUG: Print database configuration
db_uri = app.config['SQLALCHEMY_DATABASE_URI']
if 'postgresql' in db_uri.lower():
    print("🐘 Flask App: Using PostgreSQL (Supabase)")
    print(f"📍 DB Host: {db_uri.split('@')[1].split('/')[0] if '@' in db_uri else 'unknown'}")
elif 'sqlite' in db_uri.lower():
    print("📁 Flask App: Using SQLite")
    print(f"📍 DB File: {db_uri}")
else:
    print(f"❓ Flask App: Unknown database type: {db_uri[:50]}...")
print(f"🔍 Full DB URI: {db_uri}")

# Server configuration for external URLs in emails
app.config['SERVER_NAME'] = os.getenv('SERVER_NAME')  # Set this in production

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize extensions
db.init_app(app)
mail = Mail(app)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """Home page showing all events."""
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('index.html', events=events)

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    """Create a new event."""
    form = EventForm()
    if form.validate_on_submit():
        # Handle logo upload
        logo_filename = None
        if form.logo.data:
            file = form.logo.data
            if file and allowed_file(file.filename):
                # Create uploads directory if it doesn't exist
                upload_folder = 'static/uploads/logos'
                os.makedirs(upload_folder, exist_ok=True)
                
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(upload_folder, unique_filename)
                
                file.save(file_path)
                logo_filename = unique_filename
        
        event = Event(
            name=form.name.data,
            alias_name=form.alias_name.data,
            date=form.date.data,
            time=form.time.data,
            logo_filename=logo_filename,
            location=form.location.data,
            google_maps_url=form.google_maps_url.data,
            description=form.description.data,
            organizer_name=form.organizer_name.data,
            instructions=form.instructions.data
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('upload_participants', event_id=event.id))
    return render_template('create_event.html', form=form)

@app.route('/upload_participants/<int:event_id>', methods=['GET', 'POST'])
def upload_participants(event_id):
    """Upload participants CSV for an event."""
    event = Event.query.get_or_404(event_id)
    form = ParticipantUploadForm()
    
    if form.validate_on_submit():
        file = form.csv_file.data
        filename = secure_filename(file.filename)
        
        try:
            # Read CSV directly from memory with BOM handling
            file_content = file.stream.read()
            
            # Handle BOM (Byte Order Mark) that Excel and other editors add
            if file_content.startswith(b'\xef\xbb\xbf'):
                # UTF-8 BOM detected, remove it
                file_content = file_content[3:]
                logger.info("Removed UTF-8 BOM from CSV file")
            elif file_content.startswith(b'\xff\xfe'):
                # UTF-16 LE BOM detected
                file_content = file_content[2:]
                logger.info("Removed UTF-16 LE BOM from CSV file")
            elif file_content.startswith(b'\xfe\xff'):
                # UTF-16 BE BOM detected
                file_content = file_content[2:]
                logger.info("Removed UTF-16 BE BOM from CSV file")
            
            # Decode to string
            try:
                content_str = file_content.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to other encodings
                try:
                    content_str = file_content.decode('utf-16')
                except UnicodeDecodeError:
                    content_str = file_content.decode('iso-8859-1')
            
            stream = io.StringIO(content_str, newline=None)
            csv_input = csv.DictReader(stream)
            
            # Clean fieldnames to remove any remaining invisible characters
            if csv_input.fieldnames:
                cleaned_fieldnames = []
                for field in csv_input.fieldnames:
                    # Remove BOM and other invisible characters
                    cleaned_field = field.strip().lstrip('\ufeff').strip()
                    cleaned_fieldnames.append(cleaned_field)
                csv_input.fieldnames = cleaned_fieldnames
            
            # Debug: Check what columns are detected
            fieldnames = csv_input.fieldnames
            logger.info(f"CSV columns detected (after cleaning): {fieldnames}")
            
            # Map common column variations to our expected names (with BOM-cleaned versions)
            name_columns = ['name', 'Name', 'NAME', 'participant_name', 'Participant Name', 'full_name', 'Full Name', '﻿name']
            email_columns = ['email', 'Email', 'EMAIL', 'email_address', 'Email Address', 'e-mail', 'E-mail']
            
            # Find which column contains name and email
            name_col = None
            email_col = None
            
            for col in fieldnames:
                col_clean = col.strip().lstrip('\ufeff').strip()  # Extra BOM cleaning
                if col_clean in name_columns or col in name_columns:
                    name_col = col
                if col_clean in email_columns or col in email_columns:
                    email_col = col
            
            if not name_col or not email_col:
                flash(f'CSV format error. Expected columns: name, email. Found columns: {", ".join(fieldnames)}', 'error')
                return redirect(url_for('upload_participants', event_id=event_id))
            
            participants_added = 0
            errors = []
            
            for row_num, row in enumerate(csv_input, start=2):
                try:
                    # Extract data from CSV row using detected column names
                    name = row.get(name_col, '').strip()
                    email = row.get(email_col, '').strip()
                    
                    if not name or not email:
                        errors.append(f"Row {row_num}: Missing name or email")
                        continue
                    
                    # Check if participant already exists for this event
                    existing = Participant.query.filter_by(
                        event_id=event_id,
                        email=email
                    ).first()
                    
                    if existing:
                        errors.append(f"Row {row_num}: Email {email} already registered")
                        continue
                    
                    # Generate ticket number using event format
                    ticket_number = event.generate_next_ticket_number()
                    
                    # Create participant
                    participant = Participant(
                        event_id=event_id,
                        name=name,
                        email=email,
                        ticket_number=ticket_number
                    )
                    
                    db.session.add(participant)
                    participants_added += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            db.session.commit()
            
            if participants_added > 0:
                flash(f'Successfully added {participants_added} participants! You can now send emails from the dashboard.', 'success')
                logger.info(f"Added {participants_added} participants to event {event.name}")
            
            if errors:
                flash(f'Errors encountered: {"; ".join(errors[:5])}', 'warning')
            
            return redirect(url_for('event_dashboard', event_id=event_id))
            
        except Exception as e:
            flash(f'Error processing CSV: {str(e)}', 'error')
    
    return render_template('upload_participants.html', form=form, event=event)

@app.route('/event/<int:event_id>/dashboard')
def event_dashboard(event_id):
    """Event dashboard showing all participants and attendance."""
    event = Event.query.get_or_404(event_id)
    participants = Participant.query.filter_by(event_id=event_id).all()
    
    # Calculate statistics
    total_participants = len(participants)
    checked_in = sum(1 for p in participants if p.checked_in)
    
    # Email statistics
    emails_sent = sum(1 for p in participants if p.email_sent)
    pending_emails = total_participants - emails_sent
    
    # Calculate certificate statistics
    certificates_issued = sum(1 for p in participants if p.has_certificate)
    certificates_sent = sum(1 for p in participants if p.has_certificate and p.certificate.email_sent)
    eligible_for_certificates = sum(1 for p in participants if p.checked_in and not p.has_certificate)
    
    # Certificate configuration status
    certificate_config_status = {
        'configured': event.has_certificate_config,
        'last_updated': event.certificate_config_updated,
        'organizer_name': event.organizer_name,
        'certificate_type': event.certificate_type
    }
    
    return render_template('event_dashboard.html', 
                         event=event, 
                         participants=participants,
                         total_participants=total_participants,
                         checked_in=checked_in,
                         emails_sent=emails_sent,
                         pending_emails=pending_emails,
                         certificates_issued=certificates_issued,
                         certificates_sent=certificates_sent,
                         eligible_for_certificates=eligible_for_certificates,
                         certificate_config_status=certificate_config_status)

@app.route('/event/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    """Delete an event and all its participants."""
    event = Event.query.get_or_404(event_id)
    
    try:
        # Get event info for flash message
        event_name = event.name
        participant_count = len(event.participants)
        
        # First, delete all certificates for participants of this event
        # This prevents foreign key constraint violations
        participant_ids = [p.id for p in event.participants]
        if participant_ids:
            Certificate.query.filter(Certificate.participant_id.in_(participant_ids)).delete(synchronize_session=False)
        
        # Now delete the event (participants will be deleted automatically due to cascade)
        db.session.delete(event)
        db.session.commit()
        
        flash(f'Event "{event_name}" and {participant_count} participants deleted successfully!', 'success')
        logger.info(f"Event '{event_name}' (ID: {event_id}) deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete event {event_id}: {str(e)}")
        flash(f'Failed to delete event. Error: {str(e)}', 'danger')
        return redirect(url_for('event_dashboard', event_id=event_id))
    
    return redirect(url_for('index'))

@app.route('/participant/<int:participant_id>/checkin', methods=['POST'])
def toggle_checkin(participant_id):
    """Toggle participant check-in status."""
    participant = Participant.query.get_or_404(participant_id)
    participant.checked_in = not participant.checked_in
    participant.checkin_time = datetime.now() if participant.checked_in else None
    db.session.commit()
    
    status = 'checked in' if participant.checked_in else 'checked out'
    
    # Check if this is a form submission that should redirect
    if request.form.get('redirect') == 'true':
        flash(f'{participant.name} {status}', 'success')
        return redirect(url_for('event_dashboard', event_id=participant.event_id))
    
    # Otherwise return JSON for AJAX calls
    return jsonify({
        'success': True,
        'message': f'{participant.name} {status}',
        'checked_in': participant.checked_in
    })

@app.route('/event/<int:event_id>/export')
def export_attendance(event_id):
    """Export attendance report as CSV."""
    event = Event.query.get_or_404(event_id)
    participants = Participant.query.filter_by(event_id=event_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Name', 'Email', 'Ticket Number', 'Checked In', 'Check-in Time'])
    
    # Write participant data
    for participant in participants:
        checkin_time = participant.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if participant.checkin_time else ''
        writer.writerow([
            participant.name,
            participant.email,
            participant.ticket_number,
            'Yes' if participant.checked_in else 'No',
            checkin_time
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={event.name}_attendance.csv'
    
    return response

@app.route('/send_selected_emails/<int:event_id>', methods=['POST'])
def send_selected_emails(event_id):
    """Send ticket emails to selected participants."""
    logger.info(f"Starting selected email send for event ID: {event_id}")
    
    event = Event.query.get_or_404(event_id)
    selected_participant_ids = request.form.getlist('selected_participants')
    
    if not selected_participant_ids:
        flash('No participants selected for email sending.', 'warning')
        return redirect(url_for('event_dashboard', event_id=event_id))
    
    # Get selected participants
    participants = Participant.query.filter(
        Participant.event_id == event_id,
        Participant.id.in_(selected_participant_ids)
    ).all()
    
    logger.info(f"Found {len(participants)} selected participants for event: {event.name}")
    
    sent_count = 0
    errors = []
    start_time = time.time()
    
    # Test email connection first
    try:
        test_email_connection()
        logger.info("Email connection test passed")
    except Exception as e:
        logger.error(f"Email connection test failed: {str(e)}")
        flash(f'Email connection failed: {str(e)}', 'error')
        return redirect(url_for('event_dashboard', event_id=event_id))
    
    for i, participant in enumerate(participants, 1):
        try:
            logger.info(f"Sending email {i}/{len(participants)} to: {participant.email}")
            send_ticket_email(participant, event)
            logger.info(f"✅ Email sent to {participant.email}")
            sent_count += 1
            
            # Small delay to avoid overwhelming the SMTP server
            if i < len(participants):
                time.sleep(0.1)
            
        except Exception as e:
            error_msg = f"Failed to send email to {participant.email}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    total_time = time.time() - start_time
    logger.info(f"Selected email send completed in {total_time:.2f}s. Sent: {sent_count}, Errors: {len(errors)}")
    
    if sent_count > 0:
        flash(f'Successfully sent {sent_count} emails to selected participants in {total_time:.1f} seconds!', 'success')
    
    if errors:
        flash(f'Email errors: {"; ".join(errors[:2])}', 'warning')
    
    return redirect(url_for('event_dashboard', event_id=event_id))

@app.route('/send_emails/<int:event_id>')
def send_bulk_emails(event_id):
    """Send ticket emails to all participants of an event."""
    logger.info(f"Starting bulk email send for event ID: {event_id}")
    
    event = Event.query.get_or_404(event_id)
    participants = Participant.query.filter_by(event_id=event_id).all()
    
    logger.info(f"Found {len(participants)} participants for event: {event.name}")
    
    # If it's an AJAX request, return JSON with progress
    if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'status': 'started',
            'total_participants': len(participants),
            'message': f'Starting to send emails to {len(participants)} participants...'
        })
    
    sent_count = 0
    errors = []
    
    # Log email configuration (without sensitive data)
    logger.info(f"Email config - Server: {app.config.get('MAIL_SERVER')}, Port: {app.config.get('MAIL_PORT')}")
    logger.info(f"Email config - Username: {app.config.get('MAIL_USERNAME')}")
    
    start_time = time.time()
    
    # Test email connection first
    try:
        test_email_connection()
        logger.info("Email connection test passed")
    except Exception as e:
        logger.error(f"Email connection test failed: {str(e)}")
        flash(f'Email connection failed: {str(e)}', 'error')
        return redirect(url_for('event_dashboard', event_id=event_id))
    
    for i, participant in enumerate(participants, 1):
        try:
            logger.info(f"Sending email {i}/{len(participants)} to: {participant.email}")
            participant_start = time.time()
            
            send_ticket_email(participant, event)
            
            participant_time = time.time() - participant_start
            logger.info(f"✅ Email sent to {participant.email} in {participant_time:.2f}s")
            sent_count += 1
            
            # Progressive delay to avoid rate limits - increase delay after 25, 50, 75 emails
            if i > 75:
                delay = 3.0  # 3 seconds after 75 emails
            elif i > 50:
                delay = 2.0  # 2 seconds after 50 emails
            elif i > 25:
                delay = 1.0  # 1 second after 25 emails
            else:
                delay = 0.2  # 200ms for first 25 emails
            
            if i < len(participants):
                logger.debug(f"Waiting {delay}s before next email...")
                time.sleep(delay)
            
        except Exception as e:
            error_msg = f"Failed to send email to {participant.email}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            
            # Check for rate limit or quota errors
            error_str = str(e).lower()
            if any(term in error_str for term in ['rate limit', 'quota', 'daily limit', '554', '421', '450']):
                logger.error(f"🚫 Gmail rate limit or daily quota reached at email {i}!")
                flash(f'Gmail daily limit reached after {sent_count} emails. Try again tomorrow or use a different email service.', 'warning')
                break
            
            # If too many consecutive failures, stop
            if len(errors) > 3 and sent_count == 0:
                logger.error("Too many consecutive failures, stopping email send")
                break
    
    total_time = time.time() - start_time
    logger.info(f"Bulk email completed in {total_time:.2f}s. Sent: {sent_count}, Errors: {len(errors)}")
    
    if sent_count > 0:
        flash(f'Successfully sent {sent_count} emails in {total_time:.1f} seconds!', 'success')
    
    if errors:
        flash(f'Email errors: {"; ".join(errors[:2])}', 'warning')
        logger.warning(f"Email errors summary: {len(errors)} failed out of {len(participants)}")
    
    return redirect(url_for('event_dashboard', event_id=event_id))


@app.route('/send_pending_emails/<int:event_id>')
def send_pending_emails(event_id):
    """Send ticket emails only to participants who haven't received them yet."""
    logger.info(f"Starting pending email send for event ID: {event_id}")
    
    event = Event.query.get_or_404(event_id)
    # Only get participants where email_sent is False or NULL
    participants = Participant.query.filter_by(event_id=event_id, email_sent=False).all()
    
    logger.info(f"Found {len(participants)} pending participants for event: {event.name}")
    
    if not participants:
        flash('No pending participants found! All participants have already received their tickets.', 'info')
        return redirect(url_for('event_dashboard', event_id=event_id))
    
    sent_count = 0
    errors = []
    
    # Log email configuration (without sensitive data)
    logger.info(f"Email config - Server: {app.config.get('MAIL_SERVER')}, Port: {app.config.get('MAIL_PORT')}")
    logger.info(f"Email config - Username: {app.config.get('MAIL_USERNAME')}")
    
    start_time = time.time()
    
    # Test email connection first
    try:
        test_email_connection()
        logger.info("Email connection test passed")
    except Exception as e:
        logger.error(f"Email connection test failed: {str(e)}")
        flash(f'Email connection failed: {str(e)}', 'error')
        return redirect(url_for('event_dashboard', event_id=event_id))
    
    for i, participant in enumerate(participants, 1):
        try:
            logger.info(f"Sending pending email {i}/{len(participants)} to: {participant.email}")
            participant_start = time.time()
            
            send_ticket_email(participant, event)
            
            participant_time = time.time() - participant_start
            logger.info(f"✅ Email sent to {participant.email} in {participant_time:.2f}s")
            sent_count += 1
            
            # Progressive delay to avoid rate limits - same as bulk emails
            if i > 75:
                delay = 3.0  # 3 seconds after 75 emails
            elif i > 50:
                delay = 2.0  # 2 seconds after 50 emails
            elif i > 25:
                delay = 1.0  # 1 second after 25 emails
            else:
                delay = 0.2  # 200ms for first 25 emails
            
            if i < len(participants):
                logger.debug(f"Waiting {delay}s before next email...")
                time.sleep(delay)
            
        except Exception as e:
            error_msg = f"Failed to send email to {participant.email}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            
            # Check for rate limit or quota errors
            error_str = str(e).lower()
            if any(term in error_str for term in ['rate limit', 'quota', 'daily limit', '554', '421', '450']):
                logger.error(f"🚫 Gmail rate limit or daily quota reached at email {i}!")
                flash(f'Gmail daily limit reached after {sent_count} emails. Try again tomorrow or use a different email service.', 'warning')
                break
            
            # If too many consecutive failures, stop
            if len(errors) > 3 and sent_count == 0:
                logger.error("Too many consecutive failures, stopping pending email send")
                break
    
    total_time = time.time() - start_time
    logger.info(f"Pending email send completed in {total_time:.2f}s. Sent: {sent_count}, Errors: {len(errors)}")
    
    if sent_count > 0:
        flash(f'Successfully sent {sent_count} pending emails in {total_time:.1f} seconds!', 'success')
    
    if errors:
        flash(f'Email errors: {"; ".join(errors[:2])}', 'warning')
        logger.warning(f"Pending email errors summary: {len(errors)} failed out of {len(participants)}")
    
    return redirect(url_for('event_dashboard', event_id=event_id))


@app.route('/send_emails_progress/<int:event_id>')
def send_emails_with_progress(event_id):
    """Send emails with real-time progress updates via Server-Sent Events."""
    import json
    
    def generate_progress():
        with app.app_context():
            event = Event.query.get_or_404(event_id)
            participants = Participant.query.filter_by(event_id=event_id).all()
        
        yield f"data: {json.dumps({'status': 'started', 'total': len(participants), 'message': 'Starting email send...'})}\n\n"
        
        sent_count = 0
        errors = []
        
        # Test connection first
        try:
            with app.app_context():
                test_email_connection()
            yield f"data: {json.dumps({'status': 'progress', 'message': 'Email connection verified ✅'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': f'Email connection failed: {str(e)}'})}\n\n"
            return
        
        for i, participant in enumerate(participants, 1):
            try:
                yield f"data: {json.dumps({'status': 'progress', 'current': i, 'total': len(participants), 'message': f'Sending to {participant.email}...'})}\n\n"
                
                with app.app_context():
                    send_ticket_email(participant, event)
                sent_count += 1
                
                yield f"data: {json.dumps({'status': 'progress', 'current': i, 'total': len(participants), 'message': f'Sent to {participant.email} ✅'})}\n\n"
                
                # Small delay
                time.sleep(0.1)
                
            except Exception as e:
                errors.append(str(e))
                yield f"data: {json.dumps({'status': 'progress', 'current': i, 'total': len(participants), 'message': f'Failed to send to {participant.email} ❌'})}\n\n"
        
        yield f"data: {json.dumps({'status': 'completed', 'sent': sent_count, 'errors': len(errors), 'message': 'Email send completed!'})}\n\n"
    
    response = app.response_class(generate_progress(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    return response

def send_certificate_email(participant, certificate, event):
    """Send certificate email to participant with PDF attachment"""
    try:
        logger.info(f"Starting certificate email generation for {participant.email}")
        
        # Generate certificate HTML (for preview and ReportLab data)
        certificate_html = render_template('certificate_professional.html',
                                         certificate=certificate,
                                         event=event,
                                         participant=participant,
                                         preview=False)
        
        # Generate simplified HTML for WeasyPrint (no images)
        certificate_simple_html = render_template('certificate_simple_pdf.html',
                                                certificate=certificate,
                                                event=event,
                                                participant=participant,
                                                preview=False)
        
        logger.info(f"Certificate HTML generated, length: {len(certificate_html)}")

        # Try to generate PDF with improved configuration
        pdf_generated = False
        attachment_data = None
        attachment_mimetype = None
        filename = None
        
        # First try with WeasyPrint (most feature-complete)
        try:
            import weasyprint
            import io
            import os
            
            logger.info("Attempting PDF generation with WeasyPrint...")
            
            # Generate PDF from HTML with proper base URL
            pdf_buffer = io.BytesIO()
            
            # Set up proper base URL for resolving relative paths
            base_url = request.url_root if request else 'file://' + os.getcwd() + '/'
            
            # Create HTML document with proper configuration
            html_doc = weasyprint.HTML(
                string=certificate_simple_html,  # Use simplified template without images
                base_url=base_url
            )
            
            # Generate PDF with better error handling
            html_doc.write_pdf(
                pdf_buffer,
                presentational_hints=True,
                optimize_images=True
            )
            
            pdf_buffer.seek(0)
            pdf_data = pdf_buffer.getvalue()
            pdf_size = len(pdf_data)
            
            # Validate PDF was actually generated
            if pdf_size > 1000:  # PDF should be at least 1KB
                logger.info(f"WeasyPrint PDF generated successfully, size: {pdf_size} bytes")
                attachment_data = pdf_data
                attachment_mimetype = "application/pdf"
                filename = f"Certificate_{participant.name.replace(' ', '_')}_{event.name.replace(' ', '_')}.pdf"
                pdf_generated = True
            else:
                logger.warning(f"WeasyPrint generated suspiciously small PDF: {pdf_size} bytes")
                raise Exception("PDF too small, likely failed generation")
            
        except Exception as weasy_error:
            logger.warning(f"WeasyPrint failed: {str(weasy_error)}")
            
            # Try with ReportLab as backup (create simple but guaranteed PDF)
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.pdfgen import canvas
                from reportlab.lib.colors import HexColor
                from reportlab.lib.utils import ImageReader
                import io
                import requests
                from PIL import Image
                
                logger.info("Attempting PDF generation with ReportLab...")
                
                # Helper function for centered text (ReportLab doesn't have drawCentredText)
                def draw_centered_text(canvas, x, y, text):
                    text_width = canvas.stringWidth(text, canvas._fontname, canvas._fontsize)
                    canvas.drawString(x - text_width/2, y, text)
                
                # Create PDF with ReportLab in LANDSCAPE orientation
                pdf_buffer = io.BytesIO()
                from reportlab.lib.pagesizes import landscape
                pagesize = landscape(A4)  # Change to landscape
                pdf_canvas = canvas.Canvas(pdf_buffer, pagesize=pagesize)
                width, height = pagesize  # Get landscape dimensions
                
                # Add certificate content using ReportLab
                # Background and border
                pdf_canvas.setStrokeColor(HexColor('#0078d4'))
                pdf_canvas.setLineWidth(3)
                pdf_canvas.rect(20, 20, width-40, height-40)
                
                # Try to add logos if available (positioned near top border, like cert number placement)
                logo_y = height - 125  # MOVED MUCH CLOSER to top border (was height-140)
                logo_width = 160  # Much larger - increased from 120
                logo_height = 120  # Much larger - increased from 90 (maintaining aspect ratio)
                try:
                    if certificate.organizer_logo_url:
                        # Try to fetch and add organizer logo (LEFT side, right after border)
                        if certificate.organizer_logo_url.startswith('http'):
                            response = requests.get(certificate.organizer_logo_url, timeout=5)
                            if response.status_code == 200:
                                logo_img = ImageReader(io.BytesIO(response.content))
                                pdf_canvas.drawImage(logo_img, 40, logo_y, width=logo_width, height=logo_height, mask='auto', preserveAspectRatio=True)
                        else:
                            # Local file - convert relative path to absolute
                            import os
                            if certificate.organizer_logo_url.startswith('/uploads/'):
                                logo_path = os.path.join(os.getcwd(), certificate.organizer_logo_url[1:])  # Remove leading slash
                            else:
                                logo_path = certificate.organizer_logo_url
                            
                            if os.path.exists(logo_path):
                                logo_img = ImageReader(logo_path)
                                pdf_canvas.drawImage(logo_img, 40, logo_y, width=logo_width, height=logo_height, mask='auto', preserveAspectRatio=True)
                    
                    if certificate.sponsor_logo_url:
                        # Try to fetch and add sponsor logo (RIGHT side, right after border)
                        if certificate.sponsor_logo_url.startswith('http'):
                            response = requests.get(certificate.sponsor_logo_url, timeout=5)
                            if response.status_code == 200:
                                logo_img = ImageReader(io.BytesIO(response.content))
                                pdf_canvas.drawImage(logo_img, width - logo_width - 40, logo_y, width=logo_width, height=logo_height, mask='auto', preserveAspectRatio=True)
                        else:
                            # Local file - convert relative path to absolute
                            import os
                            if certificate.sponsor_logo_url.startswith('/uploads/'):
                                logo_path = os.path.join(os.getcwd(), certificate.sponsor_logo_url[1:])  # Remove leading slash
                            else:
                                logo_path = certificate.sponsor_logo_url
                            
                            if os.path.exists(logo_path):
                                logo_img = ImageReader(logo_path)
                                pdf_canvas.drawImage(logo_img, width - logo_width - 40, logo_y, width=logo_width, height=logo_height, mask='auto', preserveAspectRatio=True)
                except Exception as logo_error:
                    logger.warning(f"Could not add logos to PDF: {logo_error}")
                
                # Title
                pdf_canvas.setFont("Helvetica-Bold", 36)
                pdf_canvas.setFillColor(HexColor('#0078d4'))
                draw_centered_text(pdf_canvas, width/2, height-180, "CERTIFICATE")
                
                # Subtitle
                pdf_canvas.setFont("Helvetica", 18)
                pdf_canvas.setFillColor(HexColor('#323130'))
                draw_centered_text(pdf_canvas, width/2, height-210, f"OF {certificate.certificate_type.upper()}")
                
                # "This is to certify that" text
                pdf_canvas.setFont("Helvetica", 14)
                pdf_canvas.setFillColor(HexColor('#605e5c'))
                draw_centered_text(pdf_canvas, width/2, height-260, "This is to certify that")
                
                # Participant name
                pdf_canvas.setFont("Helvetica-Bold", 28)
                pdf_canvas.setFillColor(HexColor('#323130'))
                draw_centered_text(pdf_canvas, width/2, height-300, participant.name)
                
                # Underline for participant name
                pdf_canvas.setStrokeColor(HexColor('#0078d4'))
                pdf_canvas.setLineWidth(2)
                name_width = pdf_canvas.stringWidth(participant.name, "Helvetica-Bold", 28)
                pdf_canvas.line(width/2 - name_width/2, height-310, width/2 + name_width/2, height-310)
                
                # Event details
                pdf_canvas.setFont("Helvetica", 14)
                pdf_canvas.setFillColor(HexColor('#323130'))
                
                # Description text
                action = "participated in"
                if certificate.certificate_type == 'completion':
                    action = "completed"
                elif certificate.certificate_type == 'achievement':
                    action = "achieved excellence in"
                
                description = f"has successfully {action} the event"
                draw_centered_text(pdf_canvas, width/2, height-350, description)
                
                # Event name
                pdf_canvas.setFont("Helvetica-Bold", 16)
                pdf_canvas.setFillColor(HexColor('#0078d4'))
                draw_centered_text(pdf_canvas, width/2, height-380, f'"{event.name}"')
                
                # Organizer and date info
                pdf_canvas.setFont("Helvetica", 12)
                pdf_canvas.setFillColor(HexColor('#323130'))
                
                organizer = certificate.organizer_name or 'Azure Developer Community Tamilnadu'
                draw_centered_text(pdf_canvas, width/2, height-410, f"organized by {organizer}")
                
                if event.date:
                    draw_centered_text(pdf_canvas, width/2, height-430, f"on {event.date.strftime('%B %d, %Y')}")
                
                if certificate.event_location:
                    draw_centered_text(pdf_canvas, width/2, height-450, f"at {certificate.event_location}")
                
                # Signature section (moved to bottom)
                signature_y = 120  # Moved down from 200
                
                # Signature lines
                pdf_canvas.setStrokeColor(HexColor('#323130'))
                pdf_canvas.setLineWidth(1)
                pdf_canvas.line(150, signature_y, 300, signature_y)  # Left signature line
                pdf_canvas.line(width-300, signature_y, width-150, signature_y)  # Right signature line
                
                # Try to add signature images
                try:
                    if certificate.signature1_image_url:
                        if certificate.signature1_image_url.startswith('http'):
                            response = requests.get(certificate.signature1_image_url, timeout=5)
                            if response.status_code == 200:
                                sig_img = ImageReader(io.BytesIO(response.content))
                                pdf_canvas.drawImage(sig_img, 175, signature_y + 10, width=120, height=50, mask='auto')
                        else:
                            # Local file - convert relative path to absolute
                            import os
                            if certificate.signature1_image_url.startswith('/uploads/'):
                                sig_path = os.path.join(os.getcwd(), certificate.signature1_image_url[1:])  # Remove leading slash
                            else:
                                sig_path = certificate.signature1_image_url
                            
                            if os.path.exists(sig_path):
                                sig_img = ImageReader(sig_path)
                                pdf_canvas.drawImage(sig_img, 175, signature_y + 10, width=120, height=50, mask='auto')
                    
                    if certificate.signature2_image_url:
                        if certificate.signature2_image_url.startswith('http'):
                            response = requests.get(certificate.signature2_image_url, timeout=5)
                            if response.status_code == 200:
                                sig_img = ImageReader(io.BytesIO(response.content))
                                pdf_canvas.drawImage(sig_img, width-295, signature_y + 10, width=120, height=50, mask='auto')
                        else:
                            # Local file - convert relative path to absolute
                            import os
                            if certificate.signature2_image_url.startswith('/uploads/'):
                                sig_path = os.path.join(os.getcwd(), certificate.signature2_image_url[1:])  # Remove leading slash
                            else:
                                sig_path = certificate.signature2_image_url
                            
                            if os.path.exists(sig_path):
                                sig_img = ImageReader(sig_path)
                                pdf_canvas.drawImage(sig_img, width-295, signature_y + 10, width=120, height=50, mask='auto')
                except Exception as sig_error:
                    logger.warning(f"Could not add signatures to PDF: {sig_error}")
                
                # Signature names
                signature1_name = certificate.signature1_name or 'Authorized Signatory'
                signature2_name = certificate.signature2_name or 'Event Organizer'
                
                pdf_canvas.setFont("Helvetica-Bold", 11)
                pdf_canvas.setFillColor(HexColor('#323130'))
                draw_centered_text(pdf_canvas, 225, signature_y - 20, signature1_name)
                draw_centered_text(pdf_canvas, width-225, signature_y - 20, signature2_name)
                
                # Signature titles
                signature1_title = certificate.signature1_title or 'Microsoft MVP'
                signature2_title = certificate.signature2_title or 'Microsoft MVP'
                
                pdf_canvas.setFont("Helvetica", 9)
                pdf_canvas.setFillColor(HexColor('#605e5c'))
                draw_centered_text(pdf_canvas, 225, signature_y - 35, signature1_title)
                draw_centered_text(pdf_canvas, width-225, signature_y - 35, signature2_title)
                
                # Footer with certificate details (moved down)
                pdf_canvas.setFont("Helvetica-Bold", 10)
                pdf_canvas.setFillColor(HexColor('#0078d4'))
                pdf_canvas.drawString(50, 50, f"Certificate No: {certificate.certificate_number}")
                pdf_canvas.drawString(width-250, 50, f"Issued: {certificate.issued_date.strftime('%B %d, %Y')}")
                
                # Corner accents
                pdf_canvas.setStrokeColor(HexColor('#0078d4'))
                pdf_canvas.setLineWidth(4)
                # Top left
                pdf_canvas.line(35, height-35, 85, height-35)
                pdf_canvas.line(35, height-35, 35, height-85)
                # Top right
                pdf_canvas.line(width-85, height-35, width-35, height-35)
                pdf_canvas.line(width-35, height-35, width-35, height-85)
                # Bottom left
                pdf_canvas.line(35, 85, 85, 85)
                pdf_canvas.line(35, 85, 35, 35)
                # Bottom right
                pdf_canvas.line(width-85, 85, width-35, 85)
                pdf_canvas.line(width-35, 85, width-35, 35)
                
                pdf_canvas.save()
                
                pdf_buffer.seek(0)
                pdf_data = pdf_buffer.getvalue()
                pdf_size = len(pdf_data)
                
                logger.info(f"ReportLab PDF generated successfully, size: {pdf_size} bytes")
                
                attachment_data = pdf_data
                attachment_mimetype = "application/pdf"
                filename = f"Certificate_{participant.name.replace(' ', '_')}_{event.name.replace(' ', '_')}.pdf"
                pdf_generated = True
                
            except Exception as reportlab_error:
                logger.warning(f"ReportLab also failed: {str(reportlab_error)}")
        
        # Final fallback to HTML if both PDF methods failed
        if not pdf_generated:
            logger.error("All PDF generation methods failed, using HTML fallback")
            attachment_data = certificate_html.encode('utf-8')
            attachment_mimetype = "text/html"
            filename = f"Certificate_{participant.name.replace(' ', '_')}_{event.name.replace(' ', '_')}.html"
        
        # Create email message
        msg = Message(
            subject=f'Certificate of {certificate.certificate_type.title()} - {event.name}',
            recipients=[participant.email],
            html=render_template('emails/certificate_email.html',
                               participant=participant,
                               event=event,
                               certificate=certificate),
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        logger.info(f"Email message created for {participant.email}")
        
        # Attach certificate
        msg.attach(filename, attachment_mimetype, attachment_data)
        
        logger.info(f"Certificate attached as {filename}")
        
        # Send email
        logger.info("Sending email...")
        mail.send(msg)
        
        # Update certificate email_sent status
        certificate.email_sent = True
        db.session.commit()
        
        logger.info(f"Certificate email with attachment sent successfully to {participant.email}")
        
    except Exception as e:
        logger.error(f"Failed to send certificate email to {participant.email}: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise e

def test_email_connection():
    """Test email connection without sending."""
    import smtplib
    
    mail_server = app.config.get('MAIL_SERVER')
    mail_port = app.config.get('MAIL_PORT')
    mail_username = app.config.get('MAIL_USERNAME')
    mail_password = app.config.get('MAIL_PASSWORD')
    
    logger.info(f"Testing connection to {mail_server}:{mail_port}")
    
    server = smtplib.SMTP(mail_server, mail_port, timeout=10)
    server.starttls()
    server.login(mail_username, mail_password)
    server.quit()
    
    logger.info("Email connection test successful")

def send_ticket_email(participant, event):
    """Send individual ticket email to a participant."""
    try:
        logger.info(f"Preparing email for {participant.email}")
        
        subject = f"Registration Confirmation - Your Ticket for {event.name}"
        
        # Log template rendering
        logger.debug("Rendering email template...")
        
        # Create a custom context
        template_context = {
            'participant': participant,
            'event': event
        }
        
        html_body = render_template('email/ticket_email.html', **template_context)
        logger.debug("Email template rendered successfully")
        
        # Create message
        logger.debug("Creating email message...")
        msg = Message(
            subject=subject,
            recipients=[participant.email],
            html=html_body
        )
        logger.debug(f"Email message created with subject: {subject}")
        
        # Attach logo as embedded image if event has one
        if event.logo_filename:
            try:
                import os
                logo_file_path = os.path.join('static', 'uploads', 'logos', event.logo_filename)
                
                if os.path.exists(logo_file_path):
                    # Attach the logo file with CID for embedding
                    with open(logo_file_path, 'rb') as logo_file:
                        logo_data = logo_file.read()
                        
                    # Determine MIME type
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(logo_file_path)
                    if not mime_type:
                        mime_type = 'image/jpeg' if logo_file_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                    
                    # Extract main type and subtype
                    main_type, sub_type = mime_type.split('/', 1)
                    
                    # Attach the image with Content-ID
                    msg.attach(
                        filename=event.logo_filename,
                        content_type=mime_type,
                        data=logo_data,
                        disposition='inline',
                        headers={'Content-ID': '<event_logo>'}
                    )
                    
                    logger.info(f"✅ Attached logo as embedded image: {event.logo_filename}")
                else:
                    logger.warning(f"Logo file not found for attachment: {logo_file_path}")
                    
            except Exception as attachment_error:
                logger.warning(f"Failed to attach logo: {attachment_error}")
                # Continue sending email without logo
        
        # Send email with timeout and retry handling
        logger.info(f"Attempting to send email to {participant.email}...")
        send_start = time.time()
        
        # Configure Flask-Mail to use shorter timeouts with retry logic
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with mail.connect() as conn:
                    conn.send(msg)
                break  # Success, exit retry loop
                
            except Exception as send_error:
                retry_count += 1
                logger.warning(f"Email send attempt {retry_count} failed for {participant.email}: {str(send_error)}")
                
                # Check for rate limit or quota errors
                error_str = str(send_error).lower()
                if any(term in error_str for term in ['rate limit', 'quota', 'daily limit', '554', '421', '450']):
                    logger.error(f"🚫 Rate limit or quota exceeded for {participant.email}")
                    raise Exception(f"Email quota/rate limit exceeded: {send_error}")
                
                if retry_count >= max_retries:
                    raise send_error
                    
                # Wait before retry
                time.sleep(2 ** retry_count)  # Exponential backoff
        
        send_time = time.time() - send_start
        logger.info(f"✅ Email sent successfully to {participant.email} in {send_time:.2f}s")
        
        # Mark email as sent
        participant.mark_email_sent()
        db.session.commit()
        
    except Exception as e:
        logger.error(f"❌ Failed to send email to {participant.email}: {str(e)}")
        logger.error(f"Email config debug - Server: {app.config.get('MAIL_SERVER')}")
        logger.error(f"Email config debug - Port: {app.config.get('MAIL_PORT')}")
        logger.error(f"Email config debug - Username: {app.config.get('MAIL_USERNAME')}")
        logger.error(f"Email config debug - TLS: {app.config.get('MAIL_USE_TLS')}")
        logger.error(f"Email config debug - SSL: {app.config.get('MAIL_USE_SSL')}")
        raise e

@app.route('/send_single_email/<int:participant_id>')
def send_single_email(participant_id):
    """Send email to a single participant."""
    participant = Participant.query.get_or_404(participant_id)
    event = participant.event
    
    try:
        send_ticket_email(participant, event)
        flash(f'Email sent successfully to {participant.email}!', 'success')
    except Exception as e:
        logger.error(f"Failed to send single email: {str(e)}")
        flash(f'Failed to send email to {participant.email}: {str(e)}', 'danger')
    
    return redirect(url_for('event_dashboard', event_id=event.id))

@app.route('/debug/email-config')
def debug_email_config():
    """Debug route to check email configuration."""
    config_info = {
        'MAIL_SERVER': app.config.get('MAIL_SERVER'),
        'MAIL_PORT': app.config.get('MAIL_PORT'),
        'MAIL_USERNAME': app.config.get('MAIL_USERNAME'),
        'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS'),
        'MAIL_USE_SSL': app.config.get('MAIL_USE_SSL'),
        'MAIL_DEFAULT_SENDER': app.config.get('MAIL_DEFAULT_SENDER'),
        'MAIL_PASSWORD_SET': bool(app.config.get('MAIL_PASSWORD')),
        'MAIL_PASSWORD_LENGTH': len(app.config.get('MAIL_PASSWORD', '')),
        'MAIL_PASSWORD_PREVIEW': app.config.get('MAIL_PASSWORD', '')[:4] + '*' * 8
    }
    logger.info(f"Email configuration debug: {config_info}")
    return jsonify(config_info)

@app.route('/debug/test-flask-mail')
def test_flask_mail_route():
    """Test Flask-Mail from within the running app."""
    try:
        logger.info("Testing Flask-Mail from within the app...")
        
        # Create test message
        msg = Message(
            subject="Flask App Email Test",
            recipients=[app.config.get('MAIL_USERNAME')],
            body="This is a test email from the Flask application",
            sender=app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        logger.info(f"Sending test email to {app.config.get('MAIL_USERNAME')}")
        mail.send(msg)
        
        logger.info("Test email sent successfully!")
        return jsonify({"success": True, "message": "Test email sent successfully!"})
        
    except Exception as e:
        logger.error(f"Test email failed: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test-single-email/<int:participant_id>')
def test_single_email(participant_id):
    """Test sending email to a single participant."""
    participant = Participant.query.get_or_404(participant_id)
    event = participant.event
    
    try:
        logger.info(f"Testing single email to {participant.email}")
        start_time = time.time()
        
        # Test connection first
        test_email_connection()
        logger.info("Single test: Email connection successful")
        
        # Send test email
        send_ticket_email(participant, event)
        
        test_time = time.time() - start_time
        logger.info(f"Single email test completed in {test_time:.2f}s")
        
        flash(f'✅ Test email sent successfully to {participant.email} in {test_time:.1f}s!', 'success')
    except Exception as e:
        logger.error(f"Single email test failed: {str(e)}")
        flash(f'❌ Test email failed: {str(e)}', 'error')
    
    return redirect(url_for('event_dashboard', event_id=event.id))

@app.route('/quick_email_test/<int:event_id>')
def quick_email_test(event_id):
    """Quick email test - just test connection and send to first participant."""
    event = Event.query.get_or_404(event_id)
    participants = Participant.query.filter_by(event_id=event_id).limit(1).all()
    
    if not participants:
        flash('No participants found to test email with.', 'warning')
        return redirect(url_for('event_dashboard', event_id=event_id))
    
    participant = participants[0]
    
    try:
        logger.info(f"Quick email test starting for {participant.email}")
        start_time = time.time()
        
        # Test connection first
        test_email_connection()
        logger.info("Quick test: Email connection successful")
        
        # Send test email
        send_ticket_email(participant, event)
        
        test_time = time.time() - start_time
        logger.info(f"Quick test completed in {test_time:.2f}s")
        
        flash(f'✅ Quick test successful! Email sent to {participant.email} in {test_time:.1f}s', 'success')
        
    except Exception as e:
        logger.error(f"Quick test failed: {str(e)}")
        flash(f'❌ Quick test failed: {str(e)}', 'error')
    
    return redirect(url_for('event_dashboard', event_id=event_id))

@app.route('/event/<int:event_id>/certificates/test')
def certificate_test(event_id):
    """Test page for certificate functionality"""
    event = Event.query.get_or_404(event_id)
    return render_template('certificate_test.html', event=event)

@app.route('/event/<int:event_id>/certificates/preview', methods=['GET', 'POST'])
def certificate_preview(event_id):
    """Show certificate preview page"""
    event = Event.query.get_or_404(event_id)
    form = CertificateForm()
    
    # Pre-populate form with saved event configuration if available
    if request.method == 'GET' and event.has_certificate_config:
        config = event.get_certificate_config()
        form.certificate_type.data = config['certificate_type']
        form.organizer_name.data = config['organizer_name']
        form.organizer_logo_url.data = config['organizer_logo_url']
        form.sponsor_name.data = config['sponsor_name']
        form.sponsor_logo_url.data = config['sponsor_logo_url']
        form.event_location.data = config['event_location']
        form.event_theme.data = config['event_theme']
        form.signature1_name.data = config['signature1_name']
        form.signature1_title.data = config['signature1_title']
        form.signature1_image_url.data = config['signature1_image_url']
        form.signature2_name.data = config['signature2_name']
        form.signature2_title.data = config['signature2_title']
        form.signature2_image_url.data = config['signature2_image_url']
        
        flash(f'✅ Certificate configuration loaded for {event.name}', 'info')
    
    # Handle file uploads on POST
    if request.method == 'POST':
        uploaded_files = {}
        
        # Handle organizer logo upload
        if form.organizer_logo_file.data:
            organizer_logo_path = save_uploaded_file(form.organizer_logo_file.data)
            if organizer_logo_path:
                uploaded_files['organizer_logo_url'] = organizer_logo_path
        
        # Handle sponsor logo upload
        if form.sponsor_logo_file.data:
            sponsor_logo_path = save_uploaded_file(form.sponsor_logo_file.data)
            if sponsor_logo_path:
                uploaded_files['sponsor_logo_url'] = sponsor_logo_path
        
        # Handle signature uploads
        if form.signature1_file.data:
            sig1_path = save_uploaded_file(form.signature1_file.data)
            if sig1_path:
                uploaded_files['signature1_image_url'] = sig1_path
        
        if form.signature2_file.data:
            sig2_path = save_uploaded_file(form.signature2_file.data)
            if sig2_path:
                uploaded_files['signature2_image_url'] = sig2_path
        
        # Store uploaded file paths in session for preview
        if uploaded_files:
            from flask import session
            session['uploaded_files'] = uploaded_files
            flash('Files uploaded successfully! Use the preview button to see your certificate.', 'success')
    
    # Get statistics
    total_participants = Participant.query.filter_by(event_id=event_id).count()
    checked_in_participants = Participant.query.filter_by(event_id=event_id, checked_in=True).all()
    checked_in_count = len(checked_in_participants)
    
    # Get participants eligible for certificates (checked in but no certificate yet)
    eligible_participants = []
    already_issued = 0
    
    for participant in checked_in_participants:
        if participant.has_certificate:
            already_issued += 1
        else:
            eligible_participants.append(participant)
    
    eligible_for_certificate = len(eligible_participants)
    
    return render_template('certificate_standalone.html',
                         event=event,
                         form=form,
                         total_participants=total_participants,
                         checked_in_count=checked_in_count,
                         eligible_for_certificate=eligible_for_certificate,
                         already_issued=already_issued,
                         eligible_participants=eligible_participants)

@app.route('/event/<int:event_id>/certificates/test-minimal')
def certificate_test_minimal(event_id):
    """Minimal test page for certificate interactions"""
    return render_template('certificate_test_minimal.html')

@app.route('/event/<int:event_id>/certificates/standalone')
def certificate_standalone(event_id):
    """Standalone certificate page without base template"""
    event = Event.query.get_or_404(event_id)
    form = CertificateForm()
    
    # Get participant statistics
    total_participants = Participant.query.filter_by(event_id=event_id).count()
    checked_in_count = Participant.query.filter_by(event_id=event_id, checked_in=True).count()
    
    # Get eligible participants (checked in)
    eligible_participants = Participant.query.filter_by(
        event_id=event_id, 
        checked_in=True
    ).all()
    
    eligible_for_certificate = len(eligible_participants)
    already_issued = 0
    
    return render_template('certificate_standalone.html',
                         event=event,
                         form=form,
                         total_participants=total_participants,
                         checked_in_count=checked_in_count,
                         eligible_for_certificate=eligible_for_certificate,
                         already_issued=already_issued,
                         eligible_participants=eligible_participants)

@app.route('/event/<int:event_id>/certificates/clean')
def certificate_preview_clean(event_id):
    """Clean certificate preview page without complex CSS/JS"""
    event = Event.query.get_or_404(event_id)
    form = CertificateForm()
    
    # Get participant statistics
    total_participants = Participant.query.filter_by(event_id=event_id).count()
    checked_in_count = Participant.query.filter_by(event_id=event_id, checked_in=True).count()
    
    # Get eligible participants (checked in)
    eligible_participants = Participant.query.filter_by(
        event_id=event_id, 
        checked_in=True
    ).all()
    
    eligible_for_certificate = len(eligible_participants)
    already_issued = 0  # You can implement this based on your certificate tracking
    
    return render_template('certificate_preview_clean.html',
                         event=event,
                         form=form,
                         total_participants=total_participants,
                         checked_in_count=checked_in_count,
                         eligible_for_certificate=eligible_for_certificate,
                         already_issued=already_issued,
                         eligible_participants=eligible_participants)

@app.route('/event/<int:event_id>/certificate/preview')
def preview_certificate(event_id):
    """Preview a sample certificate"""
    event = Event.query.get_or_404(event_id)
    
    # Use saved event configuration if available, otherwise fall back to query parameters
    if event.has_certificate_config:
        config = event.get_certificate_config()
        certificate_type = config['certificate_type']
        organizer_name = config['organizer_name']
        organizer_logo_url = config['organizer_logo_url']
        sponsor_name = config['sponsor_name'] 
        sponsor_logo_url = config['sponsor_logo_url']
        event_location = config['event_location']
        event_theme = config['event_theme']
        signature1_name = config['signature1_name']
        signature1_title = config['signature1_title']
        signature1_image_url = config['signature1_image_url']
        signature2_name = config['signature2_name']
        signature2_title = config['signature2_title']
        signature2_image_url = config['signature2_image_url']
    else:
        # Fall back to query parameters for dynamic preview
        certificate_type = request.args.get('type', 'participation')
        organizer_name = request.args.get('organizer_name', 'Azure Developer Community Tamilnadu')
        sponsor_name = request.args.get('sponsor_name', 'Microsoft')
        event_location = request.args.get('event_location', f'{event.location}' if event.location else 'Microsoft Ferns Office, Bellandur - Bengaluru')
        event_theme = request.args.get('event_theme', 'advanced technologies and innovation')
        signature1_name = request.args.get('signature1_name', '')
        signature1_title = request.args.get('signature1_title', 'Microsoft MVP')
        signature2_name = request.args.get('signature2_name', '')
        signature2_title = request.args.get('signature2_title', 'Microsoft MVP')
        
        # Get uploaded file URLs from session
        from flask import session
        uploaded_files = session.get('uploaded_files', {})
        organizer_logo_url = uploaded_files.get('organizer_logo_url') or request.args.get('organizer_logo_url')
        sponsor_logo_url = uploaded_files.get('sponsor_logo_url') or request.args.get('sponsor_logo_url')
        signature1_image_url = uploaded_files.get('signature1_image_url') or request.args.get('signature1_image_url')
        signature2_image_url = uploaded_files.get('signature2_image_url') or request.args.get('signature2_image_url')
    
    # Create a sample participant for preview
    sample_participant = type('obj', (object,), {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'ticket_number': 'SAMPLE-001',
        'checkin_time': datetime.now()
    })
    
    # Create a sample certificate with configuration
    sample_certificate = type('obj', (object,), {
        'certificate_number': f'CERT-{event.id:03d}-SAMPLE-{datetime.now().strftime("%Y%m%d")}-0001',
        'certificate_type': certificate_type,
        'issued_date': datetime.now(),
        'event': event,
        'participant': sample_participant,
        'organizer_name': organizer_name,
        'organizer_logo_url': organizer_logo_url,
        'sponsor_name': sponsor_name,
        'sponsor_logo_url': sponsor_logo_url,
        'event_location': event_location,
        'event_theme': event_theme,
        'signature1_name': signature1_name,
        'signature1_title': signature1_title,
        'signature1_image_url': signature1_image_url,
        'signature2_name': signature2_name,
        'signature2_title': signature2_title,
        'signature2_image_url': signature2_image_url
    })
    
    return render_template('certificate_professional.html', 
                         certificate=sample_certificate,
                         event=event,
                         participant=sample_participant,
                         preview=True)

@app.route('/participant/<int:participant_id>/certificate/preview')
def preview_single_certificate(participant_id):
    """Preview certificate for a specific participant"""
    participant = Participant.query.get_or_404(participant_id)
    event = participant.event
    
    # Get the actual certificate if it exists
    certificate = participant.certificate
    if not certificate:
        flash('No certificate found for this participant.', 'error')
        return redirect(url_for('event_dashboard', event_id=event.id))
    
    return render_template('certificate_professional.html',
                         certificate=certificate,
                         event=event,
                         participant=participant,
                         preview=True)

@app.route('/participant/<int:participant_id>/certificate/download')
def download_certificate(participant_id):
    """Download certificate as PDF for a specific participant"""
    participant = Participant.query.get_or_404(participant_id)
    certificate = participant.certificate
    
    if not certificate:
        flash('No certificate found for this participant.', 'error')
        return redirect(url_for('event_dashboard', event_id=participant.event_id))
    
    try:
        # For now, return the HTML version
        # TODO: Implement PDF generation using weasyprint or similar
        html_content = render_template('certificate_professional.html',
                                     certificate=certificate,
                                     event=participant.event,
                                     participant=participant,
                                     preview=False)
        
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Content-Disposition'] = f'attachment; filename="certificate_{certificate.certificate_number}.html"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating certificate download: {str(e)}")
        flash('Error generating certificate download.', 'error')
        return redirect(url_for('event_dashboard', event_id=participant.event_id))

@app.route('/participant/<int:participant_id>/certificate/reissue', methods=['POST'])
def reissue_certificate_single(participant_id):
    """Re-issue certificate for a single participant"""
    participant = Participant.query.get_or_404(participant_id)
    event = participant.event
    
    if not participant.checked_in:
        flash('Participant must be checked in to receive a certificate.', 'error')
        return redirect(url_for('event_dashboard', event_id=event.id))
    
    if not event.has_certificate_config:
        flash('Certificate configuration is required before issuing certificates.', 'error')
        return redirect(url_for('certificate_preview', event_id=event.id))
    
    try:
        # Delete existing certificate if it exists
        if participant.certificate:
            db.session.delete(participant.certificate)
        
        # Get certificate configuration from event
        config = event.get_certificate_config()
        
        # Create new certificate
        certificate = Certificate(
            participant_id=participant.id,
            certificate_type=config.get('certificate_type', 'participation'),
            certificate_number=f'CERT-{event.id:03d}-{participant.id:04d}-{datetime.now().strftime("%Y%m%d")}-R{int(datetime.now().timestamp()) % 1000:03d}',
            organizer_name=config.get('organizer_name', 'Azure Developer Community Tamilnadu'),
            organizer_logo_url=config.get('organizer_logo_url'),
            sponsor_name=config.get('sponsor_name', 'Microsoft'),
            sponsor_logo_url=config.get('sponsor_logo_url'),
            event_location=config.get('event_location'),
            event_theme=config.get('event_theme'),
            signature1_name=config.get('signature1_name'),
            signature1_title=config.get('signature1_title'),
            signature1_image_url=config.get('signature1_image_url'),
            signature2_name=config.get('signature2_name'),
            signature2_title=config.get('signature2_title'),
            signature2_image_url=config.get('signature2_image_url')
        )
        
        db.session.add(certificate)
        db.session.commit()
        
        # Send certificate email
        send_certificate_email(participant, certificate, event)
        
        flash(f'Certificate re-issued and sent to {participant.name} successfully!', 'success')
        logger.info(f"Certificate re-issued for participant {participant.id} in event {event.id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error re-issuing certificate for participant {participant.id}: {str(e)}")
        flash(f'Error re-issuing certificate for {participant.name}.', 'error')
    
    return redirect(url_for('event_dashboard', event_id=event.id))

@app.route('/test_pdf_generation/<int:participant_id>')
def test_pdf_generation(participant_id):
    """Test route to debug PDF generation directly"""
    try:
        participant = Participant.query.get_or_404(participant_id)
        certificate = participant.certificate
        
        if not certificate:
            return f"No certificate found for participant {participant.name}"
        
        event = participant.event
        
        # Generate certificate HTML
        certificate_html = render_template('certificate_professional.html',
                                         certificate=certificate,
                                         event=event,
                                         participant=participant,
                                         preview=False)
        
        # Try WeasyPrint first
        try:
            import weasyprint
            import io
            
            pdf_buffer = io.BytesIO()
            weasyprint.HTML(string=certificate_html).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            
            response = make_response(pdf_buffer.read())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="test_certificate.pdf"'
            return response
            
        except Exception as e:
            return f"WeasyPrint failed: {str(e)}<br><br>Will try ReportLab fallback in email function."
        
    except Exception as e:
        import traceback
        return f"Error: {str(e)}<br><br>Traceback:<br><pre>{traceback.format_exc()}</pre>"

@app.route('/test_certificate_email/<int:participant_id>')
def test_certificate_email_route(participant_id):
    """Test route to debug certificate email sending"""
    try:
        participant = Participant.query.get_or_404(participant_id)
        certificate = participant.certificate
        
        if not certificate:
            return f"No certificate found for participant {participant.name}"
        
        event = participant.event
        
        # Test email sending
        send_certificate_email(participant, certificate, event)
        
        return f"Certificate email sent successfully to {participant.email}"
        
    except Exception as e:
        import traceback
        return f"Error: {str(e)}<br><br>Traceback:<br><pre>{traceback.format_exc()}</pre>"

@app.route('/event/<int:event_id>/certificates/reissue', methods=['POST'])
def reissue_certificates_bulk(event_id):
    """Re-issue certificates for selected participants"""
    logger.info(f"Bulk re-issue request received for event {event_id}")
    
    event = Event.query.get_or_404(event_id)
    
    if not event.has_certificate_config:
        flash('Certificate configuration is required before issuing certificates.', 'error')
        return redirect(url_for('certificate_preview', event_id=event.id))
    
    participant_ids = request.form.getlist('selected_participants')
    logger.info(f"Received participant IDs: {participant_ids}")
    
    if not participant_ids:
        flash('No participants selected.', 'warning')
        return redirect(url_for('event_dashboard', event_id=event.id))
    
    try:
        success_count = 0
        error_count = 0
        
        for participant_id in participant_ids:
            participant = Participant.query.get(participant_id)
            if not participant or participant.event_id != event.id:
                continue
                
            if not participant.checked_in:
                error_count += 1
                continue
            
            try:
                # Delete existing certificate if it exists
                if participant.certificate:
                    db.session.delete(participant.certificate)
                
                # Get certificate configuration from event
                config = event.get_certificate_config()
                
                # Create new certificate
                certificate = Certificate(
                    participant_id=participant.id,
                    certificate_type=config.get('certificate_type', 'participation'),
                    certificate_number=f'CERT-{event.id:03d}-{participant.id:04d}-{datetime.now().strftime("%Y%m%d")}-R{int(datetime.now().timestamp()) % 1000:03d}',
                    organizer_name=config.get('organizer_name', 'Azure Developer Community Tamilnadu'),
                    organizer_logo_url=config.get('organizer_logo_url'),
                    sponsor_name=config.get('sponsor_name', 'Microsoft'),
                    sponsor_logo_url=config.get('sponsor_logo_url'),
                    event_location=config.get('event_location'),
                    event_theme=config.get('event_theme'),
                    signature1_name=config.get('signature1_name'),
                    signature1_title=config.get('signature1_title'),
                    signature1_image_url=config.get('signature1_image_url'),
                    signature2_name=config.get('signature2_name'),
                    signature2_title=config.get('signature2_title'),
                    signature2_image_url=config.get('signature2_image_url')
                )
                
                db.session.add(certificate)
                db.session.commit()
                
                # Send certificate email
                send_certificate_email(participant, certificate, event)
                
                success_count += 1
                logger.info(f"Certificate re-issued for participant {participant.id} in event {event.id}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error re-issuing certificate for participant {participant.id}: {str(e)}")
                error_count += 1
        
        # Show results
        if success_count > 0:
            flash(f'Successfully re-issued {success_count} certificate(s).', 'success')
        if error_count > 0:
            flash(f'Failed to re-issue {error_count} certificate(s). Check that participants are checked in.', 'warning')
        
    except Exception as e:
        logger.error(f"Error in bulk certificate re-issue: {str(e)}")
        flash('Error processing bulk certificate re-issue.', 'error')
    
    return redirect(url_for('event_dashboard', event_id=event.id))

@app.route('/event/<int:event_id>/certificates/generate', methods=['POST'])
def generate_certificates(event_id):
    """Generate and send certificates to eligible participants"""
    event = Event.query.get_or_404(event_id)
    form = CertificateForm()
    
    if form.validate_on_submit():
        try:
            # Handle file uploads first
            uploaded_files = {}
            
            # Handle organizer logo upload
            if form.organizer_logo_file.data:
                organizer_logo_path = save_uploaded_file(form.organizer_logo_file.data)
                if organizer_logo_path:
                    uploaded_files['organizer_logo_url'] = organizer_logo_path
            
            # Handle sponsor logo upload
            if form.sponsor_logo_file.data:
                sponsor_logo_path = save_uploaded_file(form.sponsor_logo_file.data)
                if sponsor_logo_path:
                    uploaded_files['sponsor_logo_url'] = sponsor_logo_path
            
            # Handle signature uploads
            if form.signature1_file.data:
                sig1_path = save_uploaded_file(form.signature1_file.data)
                if sig1_path:
                    uploaded_files['signature1_image_url'] = sig1_path
            
            if form.signature2_file.data:
                sig2_path = save_uploaded_file(form.signature2_file.data)
                if sig2_path:
                    uploaded_files['signature2_image_url'] = sig2_path
            
            # Prepare certificate configuration data
            certificate_config = {
                'certificate_type': form.certificate_type.data,
                'organizer_name': form.organizer_name.data,
                'organizer_logo_url': uploaded_files.get('organizer_logo_url') or form.organizer_logo_url.data,
                'sponsor_name': form.sponsor_name.data,
                'sponsor_logo_url': uploaded_files.get('sponsor_logo_url') or form.sponsor_logo_url.data,
                'event_location': form.event_location.data,
                'event_theme': form.event_theme.data,
                'signature1_name': form.signature1_name.data,
                'signature1_title': form.signature1_title.data,
                'signature1_image_url': uploaded_files.get('signature1_image_url') or form.signature1_image_url.data,
                'signature2_name': form.signature2_name.data,
                'signature2_title': form.signature2_title.data,
                'signature2_image_url': uploaded_files.get('signature2_image_url') or form.signature2_image_url.data,
                'certificate_template': 'professional'
            }
            
            # Save certificate configuration to event
            event.update_certificate_config(certificate_config)
            db.session.commit()
            
            logger.info(f"Certificate configuration saved for event {event.name}")
            
            # Get eligible participants
            eligible_participants = Participant.query.filter_by(
                event_id=event_id, 
                checked_in=True
            ).all()
            
            # Filter out participants who already have certificates
            participants_to_process = [p for p in eligible_participants if not p.has_certificate]
            
            if not participants_to_process:
                flash('No participants are eligible for certificates.', 'warning')
                return redirect(url_for('certificate_preview', event_id=event_id))
            
            certificates_created = 0
            certificates_sent = 0
            errors = []
            
            for participant in participants_to_process:
                try:
                    # Create certificate record with all configuration from event
                    certificate = Certificate(
                        participant_id=participant.id,
                        certificate_type=certificate_config['certificate_type'],
                        issued_date=datetime.now(),
                        organizer_name=certificate_config['organizer_name'],
                        organizer_logo_url=certificate_config['organizer_logo_url'],
                        sponsor_name=certificate_config['sponsor_name'],
                        sponsor_logo_url=certificate_config['sponsor_logo_url'],
                        event_location=certificate_config['event_location'],
                        event_theme=certificate_config['event_theme'],
                        signature1_name=certificate_config['signature1_name'],
                        signature1_title=certificate_config['signature1_title'],
                        signature1_image_url=certificate_config['signature1_image_url'],
                        signature2_name=certificate_config['signature2_name'],
                        signature2_title=certificate_config['signature2_title'],
                        signature2_image_url=certificate_config['signature2_image_url']
                    )
                    
                    # Generate certificate number
                    certificate.certificate_number = certificate.generate_certificate_number()
                    
                    db.session.add(certificate)
                    db.session.flush()  # Get the certificate ID
                    
                    certificates_created += 1
                    
                    # Send certificate email
                    try:
                        send_certificate_email(participant, certificate, event)
                        certificate.email_sent = True
                        certificate.email_sent_date = datetime.now()
                        certificates_sent += 1
                        logger.info(f"Certificate sent to {participant.email}")
                    except Exception as email_error:
                        logger.error(f"Failed to send certificate email to {participant.email}: {str(email_error)}")
                        errors.append(f"Certificate created for {participant.name} but email failed: {str(email_error)}")
                    
                except Exception as e:
                    logger.error(f"Failed to create certificate for {participant.name}: {str(e)}")
                    errors.append(f"Failed to create certificate for {participant.name}: {str(e)}")
                    continue
            
            db.session.commit()
            
            # Provide feedback
            if certificates_created > 0:
                flash(f'✅ Successfully created {certificates_created} certificates and saved configuration for {event.name}!', 'success')
                
            if certificates_sent > 0:
                flash(f'📧 Successfully sent {certificates_sent} certificate emails!', 'success')
            
            if errors:
                for error in errors[:5]:  # Show max 5 errors
                    flash(f'⚠️ {error}', 'warning')
                if len(errors) > 5:
                    flash(f'⚠️ ...and {len(errors) - 5} more errors. Check logs for details.', 'warning')
                    
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error generating certificates: {str(e)}")
            flash(f'❌ Error generating certificates: {str(e)}', 'error')
    else:
        # Form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'❌ {field}: {error}', 'error')
    
    return redirect(url_for('certificate_preview', event_id=event_id))

@app.route('/event/<int:event_id>/certificates/config', methods=['POST'])
def save_certificate_config(event_id):
    """Save certificate configuration for an event without generating certificates"""
    event = Event.query.get_or_404(event_id)
    form = CertificateForm()
    
    if form.validate_on_submit():
        try:
            # Handle file uploads first
            uploaded_files = {}
            
            # Handle organizer logo upload
            if form.organizer_logo_file.data:
                organizer_logo_path = save_uploaded_file(form.organizer_logo_file.data)
                if organizer_logo_path:
                    uploaded_files['organizer_logo_url'] = organizer_logo_path
            
            # Handle sponsor logo upload
            if form.sponsor_logo_file.data:
                sponsor_logo_path = save_uploaded_file(form.sponsor_logo_file.data)
                if sponsor_logo_path:
                    uploaded_files['sponsor_logo_url'] = sponsor_logo_path
            
            # Handle signature uploads
            if form.signature1_file.data:
                sig1_path = save_uploaded_file(form.signature1_file.data)
                if sig1_path:
                    uploaded_files['signature1_image_url'] = sig1_path
            
            if form.signature2_file.data:
                sig2_path = save_uploaded_file(form.signature2_file.data)
                if sig2_path:
                    uploaded_files['signature2_image_url'] = sig2_path
            
            # Prepare certificate configuration data
            certificate_config = {
                'certificate_type': form.certificate_type.data,
                'organizer_name': form.organizer_name.data,
                'organizer_logo_url': uploaded_files.get('organizer_logo_url') or form.organizer_logo_url.data,
                'sponsor_name': form.sponsor_name.data,
                'sponsor_logo_url': uploaded_files.get('sponsor_logo_url') or form.sponsor_logo_url.data,
                'event_location': form.event_location.data,
                'event_theme': form.event_theme.data,
                'signature1_name': form.signature1_name.data,
                'signature1_title': form.signature1_title.data,
                'signature1_image_url': uploaded_files.get('signature1_image_url') or form.signature1_image_url.data,
                'signature2_name': form.signature2_name.data,
                'signature2_title': form.signature2_title.data,
                'signature2_image_url': uploaded_files.get('signature2_image_url') or form.signature2_image_url.data,
                'certificate_template': 'professional'
            }
            
            # Save certificate configuration to event
            event.update_certificate_config(certificate_config)
            db.session.commit()
            
            flash(f'✅ Certificate configuration saved successfully for {event.name}!', 'success')
            logger.info(f"Certificate configuration saved for event {event.name}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving certificate configuration: {str(e)}")
            flash(f'❌ Error saving certificate configuration: {str(e)}', 'error')
    else:
        # Form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'❌ {field}: {error}', 'error')
    
    return redirect(url_for('certificate_preview', event_id=event_id))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    from flask import send_from_directory
    return send_from_directory('uploads', filename)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

@app.route('/debug_pdf_generation')
def debug_pdf_generation():
    """Test PDF generation for debugging"""
    from flask import make_response
    import tempfile
    
    # Get first event and participant for testing
    event = Event.query.first()
    if not event:
        return "No events found", 404
    
    participant = Participant.query.filter_by(event_id=event.id).first()
    if not participant:
        return "No participants found", 404
    
    # Get or create certificate
    certificate = Certificate.query.filter_by(participant_id=participant.id).first()
    if not certificate:
        return "No certificate found", 404
    
    try:
        logger.info("Starting PDF generation test...")
        
        # Try WeasyPrint first
        try:
            import weasyprint
            logger.info("Attempting PDF generation with WeasyPrint...")
            
            certificate_html = render_template('certificates/certificate_simple_pdf.html',
                                             certificate=certificate,
                                             participant=participant,
                                             event=event)
            
            pdf_data = weasyprint.HTML(string=certificate_html).write_pdf()
            logger.info(f"WeasyPrint PDF generated successfully, size: {len(pdf_data)} bytes")
            
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=test_certificate.pdf'
            return response
            
        except Exception as weasy_error:
            logger.warning(f"WeasyPrint failed: {str(weasy_error)}")
            
            # Try ReportLab fallback
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib.colors import HexColor
                from reportlab.lib.utils import ImageReader
                import io
                
                logger.info("Attempting PDF generation with ReportLab...")
                
                # Helper function for centered text
                def draw_centered_text_debug(canvas, x, y, text):
                    text_width = canvas.stringWidth(text, canvas._fontname, canvas._fontsize)
                    canvas.drawString(x - text_width/2, y, text)
                
                pdf_buffer = io.BytesIO()
                from reportlab.lib.pagesizes import landscape
                pagesize = landscape(A4)  # Landscape orientation
                pdf_canvas = canvas.Canvas(pdf_buffer, pagesize=pagesize)
                width, height = pagesize
                
                # Simple test PDF
                pdf_canvas.setFont("Helvetica-Bold", 36)
                pdf_canvas.setFillColor(HexColor('#0078d4'))
                draw_centered_text_debug(pdf_canvas, width/2, height-180, "CERTIFICATE")
                
                pdf_canvas.setFont("Helvetica", 18)
                pdf_canvas.setFillColor(HexColor('#323130'))
                draw_centered_text_debug(pdf_canvas, width/2, height-210, f"OF {certificate.certificate_type.upper()}")
                
                pdf_canvas.setFont("Helvetica-Bold", 28)
                draw_centered_text_debug(pdf_canvas, width/2, height-300, participant.name)
                
                pdf_canvas.save()
                
                pdf_buffer.seek(0)
                pdf_data = pdf_buffer.getvalue()
                
                logger.info(f"ReportLab PDF generated successfully, size: {len(pdf_data)} bytes")
                
                response = make_response(pdf_data)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'inline; filename=test_certificate_reportlab.pdf'
                return response
                
            except Exception as reportlab_error:
                logger.error(f"ReportLab also failed: {str(reportlab_error)}")
                return f"Both PDF generation methods failed. WeasyPrint: {weasy_error}, ReportLab: {reportlab_error}", 500
    
    except Exception as e:
        logger.error(f"Test PDF generation failed: {str(e)}")
        return f"Test PDF generation failed: {str(e)}", 500

@app.route('/event/<int:event_id>/certificates/test-simple')
def certificate_test_simple(event_id):
    """Simple test certificate page"""
    event = Event.query.get_or_404(event_id)
    form = CertificateForm()
    
    # Get statistics
    total_participants = Participant.query.filter_by(event_id=event_id).count()
    checked_in_participants = Participant.query.filter_by(event_id=event_id, checked_in=True).all()
    checked_in_count = len(checked_in_participants)
    
    eligible_participants = []
    already_issued = 0
    
    for participant in checked_in_participants:
        if participant.has_certificate:
            already_issued += 1
        else:
            eligible_participants.append(participant)
    
    eligible_for_certificate = len(eligible_participants)
    
    return render_template('certificate_test_simple.html',
                         event=event,
                         form=form,
                         total_participants=total_participants,
                         checked_in_count=checked_in_count,
                         eligible_for_certificate=eligible_for_certificate,
                         already_issued=already_issued,
                         eligible_participants=eligible_participants)

# ===== NEW PARTICIPANT MANAGEMENT FEATURES =====

@app.route('/event/<int:event_id>/participant/add', methods=['GET', 'POST'])
def add_participant_manually(event_id):
    """Add a single participant manually to an event."""
    event = Event.query.get_or_404(event_id)
    form = ManualParticipantForm()
    
    if form.validate_on_submit():
        try:
            name = form.name.data.strip()
            email = form.email.data.strip()
            check_in_immediately = form.check_in_immediately.data
            
            # Check for duplicate email in this event
            existing = Participant.query.filter_by(event_id=event_id, email=email).first()
            if existing:
                flash(f'A participant with email {email} already exists in this event.', 'error')
                return render_template('add_participant.html', event=event, form=form)
            
            # Generate ticket number
            ticket_number = event.generate_next_ticket_number()
            
            # Create new participant
            participant = Participant(
                name=name,
                email=email,
                event_id=event_id,
                ticket_number=ticket_number,
                checked_in=check_in_immediately,
                checkin_time=datetime.now() if check_in_immediately else None
            )
            
            db.session.add(participant)
            db.session.commit()
            
            success_msg = f'Successfully added participant: {name} with ticket {ticket_number}'
            if check_in_immediately:
                success_msg += ' (checked in automatically)'
            
            flash(success_msg, 'success')
            return redirect(url_for('event_dashboard', event_id=event_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding participant: {str(e)}', 'error')
            logger.error(f"Error adding participant manually: {str(e)}")
    
    return render_template('add_participant.html', event=event, form=form)

@app.route('/event/<int:event_id>/participant/<int:participant_id>/edit', methods=['GET', 'POST'])
def edit_participant(event_id, participant_id):
    """Edit participant information."""
    event = Event.query.get_or_404(event_id)
    participant = Participant.query.get_or_404(participant_id)
    
    # Ensure participant belongs to this event
    if participant.event_id != event_id:
        flash('Participant not found in this event.', 'error')
        return redirect(url_for('event_dashboard', event_id=event_id))
    
    form = EditParticipantForm()
    
    if form.validate_on_submit():
        try:
            # Check if email is being changed and if it's already used by another participant
            if form.email.data != participant.email:
                existing_participant = Participant.query.filter_by(
                    event_id=event_id, 
                    email=form.email.data
                ).first()
                
                if existing_participant and existing_participant.id != participant_id:
                    flash('Email address is already registered for this event by another participant.', 'error')
                    return render_template('edit_participant.html', event=event, participant=participant, form=form)
            
            # Store original values for logging
            original_name = participant.name
            original_email = participant.email
            original_checked_in = participant.checked_in
            original_email_sent = participant.email_sent
            
            # Update participant fields
            participant.name = form.name.data
            participant.email = form.email.data
            participant.checked_in = form.checked_in.data
            participant.email_sent = form.email_sent.data
            
            # If email_sent is being set to True and it wasn't before, set the timestamp
            if form.email_sent.data and not original_email_sent:
                participant.email_sent_at = datetime.utcnow()
            elif not form.email_sent.data and original_email_sent:
                # If email_sent is being set to False, clear the timestamp
                participant.email_sent_at = None
            
            db.session.commit()
            
            # Log the changes
            changes = []
            if original_name != participant.name:
                changes.append(f"name: '{original_name}' → '{participant.name}'")
            if original_email != participant.email:
                changes.append(f"email: '{original_email}' → '{participant.email}'")
            if original_checked_in != participant.checked_in:
                changes.append(f"checked_in: {original_checked_in} → {participant.checked_in}")
            if original_email_sent != participant.email_sent:
                changes.append(f"email_sent: {original_email_sent} → {participant.email_sent}")
            
            if changes:
                logger.info(f"Participant {participant.id} updated: {', '.join(changes)}")
                flash(f'Successfully updated participant: {participant.name}', 'success')
            else:
                flash('No changes were made.', 'info')
                
            return redirect(url_for('event_dashboard', event_id=event_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating participant {participant_id}: {str(e)}")
            flash(f'Error updating participant: {str(e)}', 'error')
    
    # Pre-populate form with current data
    if request.method == 'GET':
        form.name.data = participant.name
        form.email.data = participant.email
        form.checked_in.data = participant.checked_in
        form.email_sent.data = participant.email_sent
    
    return render_template('edit_participant.html', event=event, participant=participant, form=form)

@app.route('/event/<int:event_id>/participant/<int:participant_id>/delete', methods=['POST'])
def delete_participant_single(event_id, participant_id):
    """Delete a single participant from an event."""
    try:
        event = Event.query.get_or_404(event_id)
        participant = Participant.query.filter_by(id=participant_id, event_id=event_id).first_or_404()
        
        participant_name = participant.name
        
        # Delete associated certificate if exists
        if participant.has_certificate:
            db.session.delete(participant.certificate)
        
        # Delete participant
        db.session.delete(participant)
        db.session.commit()
        
        flash(f'Successfully deleted participant: {participant_name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting participant: {str(e)}', 'error')
        logger.error(f"Error deleting participant {participant_id}: {str(e)}")
    
    return redirect(url_for('event_dashboard', event_id=event_id))

@app.route('/event/<int:event_id>/participants/delete', methods=['POST'])
def delete_participants_bulk(event_id):
    """Delete multiple participants from an event."""
    try:
        event = Event.query.get_or_404(event_id)
        selected_participants = request.form.getlist('selected_participants')
        
        if not selected_participants:
            flash('No participants selected for deletion.', 'warning')
            return redirect(url_for('event_dashboard', event_id=event_id))
        
        deleted_count = 0
        deleted_names = []
        
        for participant_id in selected_participants:
            participant = Participant.query.filter_by(id=participant_id, event_id=event_id).first()
            if participant:
                deleted_names.append(participant.name)
                
                # Delete associated certificate if exists
                if participant.has_certificate:
                    db.session.delete(participant.certificate)
                
                # Delete participant
                db.session.delete(participant)
                deleted_count += 1
        
        db.session.commit()
        
        if deleted_count > 0:
            flash(f'Successfully deleted {deleted_count} participants: {", ".join(deleted_names)}', 'success')
        else:
            flash('No participants were deleted.', 'warning')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting participants: {str(e)}', 'error')
        logger.error(f"Error deleting bulk participants: {str(e)}")
    
    return redirect(url_for('event_dashboard', event_id=event_id))

# ================= QUIZ FUNCTIONALITY =================

@app.route('/event/<int:event_id>/quiz/create', methods=['GET', 'POST'])
def create_quiz(event_id):
    """Create a new quiz for an event."""
    event = Event.query.get_or_404(event_id)
    form = QuizForm()
    
    if form.validate_on_submit():
        try:
            # Create new quiz
            quiz = Quiz(
                event_id=event_id,
                name=form.name.data,
                timer_per_question=form.timer_per_question.data
            )
            
            db.session.add(quiz)
            db.session.commit()
            
            flash(f'Quiz "{form.name.data}" created successfully!', 'success')
            return redirect(url_for('quiz_dashboard', event_id=event_id, quiz_id=quiz.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating quiz: {str(e)}', 'error')
            logger.error(f"Error creating quiz: {str(e)}")
    
    return render_template('create_quiz.html', event=event, form=form)

@app.route('/event/<int:event_id>/quiz/<int:quiz_id>/dashboard')
def quiz_dashboard(event_id, quiz_id):
    """Dashboard for managing a specific quiz."""
    event = Event.query.get_or_404(event_id)
    quiz = Quiz.query.filter_by(id=quiz_id, event_id=event_id).first_or_404()
    
    # Get quiz statistics
    total_questions = len(quiz.questions)
    total_participants = len(quiz.participants)
    completed_participants = len([p for p in quiz.participants if p.completed_at])
    
    return render_template('quiz_dashboard.html', 
                         event=event, 
                         quiz=quiz,
                         total_questions=total_questions,
                         total_participants=total_participants,
                         completed_participants=completed_participants)

@app.route('/event/<int:event_id>/quiz/<int:quiz_id>/upload_questions', methods=['POST'])
def upload_quiz_questions(event_id, quiz_id):
    """Upload quiz questions from Excel file."""
    event = Event.query.get_or_404(event_id)
    quiz = Quiz.query.filter_by(id=quiz_id, event_id=event_id).first_or_404()
    
    try:
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(url_for('quiz_dashboard', event_id=event_id, quiz_id=quiz_id))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('quiz_dashboard', event_id=event_id, quiz_id=quiz_id))
        
        if file and file.filename.endswith('.csv'):
            # Read CSV file
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            
            questions_added = 0
            for row in csv_input:
                question_text = row.get('question', '').strip()
                options = row.get('options', '').strip()
                correct_answer = row.get('correctanswer', '').strip()
                
                if question_text and options and correct_answer:
                    quiz_question = QuizQuestion(
                        quiz_id=quiz_id,
                        question=question_text,
                        options=options,
                        correct_answer=correct_answer
                    )
                    db.session.add(quiz_question)
                    questions_added += 1
            
            db.session.commit()
            flash(f'Successfully uploaded {questions_added} questions!', 'success')
            
        else:
            flash('Please upload a CSV file.', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error uploading questions: {str(e)}', 'error')
        logger.error(f"Error uploading quiz questions: {str(e)}")
    
    return redirect(url_for('quiz_dashboard', event_id=event_id, quiz_id=quiz_id))

@app.route('/event/<int:event_id>/quiz/<int:quiz_id>/delete', methods=['POST'])
def delete_quiz(event_id, quiz_id):
    """Delete a quiz and all its associated data."""
    try:
        quiz = Quiz.query.filter_by(id=quiz_id, event_id=event_id).first_or_404()
        
        # Delete all answers for questions in this quiz
        questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
        for question in questions:
            QuizAnswer.query.filter_by(question_id=question.id).delete()
        
        # Delete all participants
        QuizParticipant.query.filter_by(quiz_id=quiz_id).delete()
        
        # Delete all questions
        QuizQuestion.query.filter_by(quiz_id=quiz_id).delete()
        
        # Delete the quiz itself
        db.session.delete(quiz)
        db.session.commit()
        
        flash(f'Quiz "{quiz.name}" has been deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting quiz: {str(e)}', 'error')
        logger.error(f"Error deleting quiz {quiz_id}: {str(e)}")
    
    return redirect(url_for('event_dashboard', event_id=event_id))

@app.route('/event/<int:event_id>/quiz/<int:quiz_id>/question/<int:question_id>/delete', methods=['POST'])
def delete_quiz_question(event_id, quiz_id, question_id):
    """Delete a specific quiz question."""
    try:
        question = QuizQuestion.query.filter_by(id=question_id, quiz_id=quiz_id).first_or_404()
        
        # Delete all answers for this question
        QuizAnswer.query.filter_by(question_id=question_id).delete()
        
        # Delete the question
        db.session.delete(question)
        db.session.commit()
        
        flash(f'Question "{question.question}" has been deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting question: {str(e)}', 'error')
        logger.error(f"Error deleting question {question_id}: {str(e)}")
    
    return redirect(url_for('quiz_dashboard', event_id=event_id, quiz_id=quiz_id))

@app.route('/event/<int:event_id>/quiz/<int:quiz_id>/add_question', methods=['GET', 'POST'])
def add_quiz_question(event_id, quiz_id):
    """Add a question manually to the quiz."""
    event = Event.query.get_or_404(event_id)
    quiz = Quiz.query.filter_by(id=quiz_id, event_id=event_id).first_or_404()
    
    if request.method == 'POST':
        try:
            question_text = request.form.get('question', '').strip()
            option1 = request.form.get('option1', '').strip()
            option2 = request.form.get('option2', '').strip()
            option3 = request.form.get('option3', '').strip()
            option4 = request.form.get('option4', '').strip()
            correct_answer = request.form.get('correct_answer', '').strip()
            
            if not all([question_text, option1, option2, option3, option4, correct_answer]):
                flash('All fields are required!', 'error')
                return render_template('add_quiz_question.html', event=event, quiz=quiz)
            
            # Combine options into comma-separated string
            options = f"{option1},{option2},{option3},{option4}"
            
            # Validate correct answer is one of the options
            if correct_answer not in [option1, option2, option3, option4]:
                flash('Correct answer must be one of the provided options!', 'error')
                return render_template('add_quiz_question.html', event=event, quiz=quiz)
            
            quiz_question = QuizQuestion(
                quiz_id=quiz_id,
                question=question_text,
                options=options,
                correct_answer=correct_answer
            )
            
            db.session.add(quiz_question)
            db.session.commit()
            
            flash('Question added successfully!', 'success')
            return redirect(url_for('quiz_dashboard', event_id=event_id, quiz_id=quiz_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding question: {str(e)}', 'error')
            logger.error(f"Error adding quiz question: {str(e)}")
    
    return render_template('add_quiz_question.html', event=event, quiz=quiz)

@app.route('/quiz/<int:quiz_id>/join')
def join_quiz(quiz_id):
    """Join quiz page for participants (mobile-friendly)."""
    quiz = Quiz.query.get_or_404(quiz_id)
    event = quiz.event
    
    return render_template('quiz_join.html', quiz=quiz, event=event)

@app.route('/quiz/<int:quiz_id>/register', methods=['POST'])
def register_quiz_participant(quiz_id):
    """Register a participant for the quiz."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        
        if not name or not email:
            return jsonify({'success': False, 'message': 'Name and email are required.'})
        
        # Check if participant already registered
        existing = QuizParticipant.query.filter_by(quiz_id=quiz_id, email=email).first()
        if existing:
            return jsonify({'success': False, 'message': 'You are already registered for this quiz.'})
        
        # Create quiz participant
        quiz_participant = QuizParticipant(
            quiz_id=quiz_id,
            name=name,
            email=email
        )
        
        db.session.add(quiz_participant)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Registration successful!',
            'participant_id': quiz_participant.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering quiz participant: {str(e)}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'})

@app.route('/quiz/<int:quiz_id>/start/<int:participant_id>')
def start_quiz(quiz_id, participant_id):
    """Start the quiz for a participant."""
    quiz = Quiz.query.get_or_404(quiz_id)
    participant = QuizParticipant.query.filter_by(id=participant_id, quiz_id=quiz_id).first_or_404()
    
    # Convert objects to dictionaries for JSON serialization
    quiz_data = {
        'id': quiz.id,
        'name': quiz.name,
        'timer_per_question': quiz.timer_per_question,
        'event_id': quiz.event_id
    }
    
    participant_data = {
        'id': participant.id,
        'name': participant.name,
        'email': participant.email,
        'quiz_id': participant.quiz_id
    }
    
    questions_data = []
    for q in quiz.questions:
        questions_data.append({
            'id': q.id,
            'question': q.question,
            'options': q.options,
            'correct_answer': q.correct_answer
        })
    
    return render_template('quiz_interface.html', 
                         quiz=quiz,
                         participant=participant,
                         questions=quiz.questions,
                         quiz_data=quiz_data,
                         participant_data=participant_data,
                         questions_data=questions_data)

@app.route('/quiz/<int:quiz_id>/submit_answer', methods=['POST'])
def submit_quiz_answer(quiz_id):
    """Submit answer for a quiz question."""
    try:
        data = request.get_json()
        participant_id = data.get('participant_id')
        question_id = data.get('question_id')
        answer = data.get('answer')
        time_taken = data.get('time_taken', 0)
        
        participant = QuizParticipant.query.filter_by(id=participant_id, quiz_id=quiz_id).first_or_404()
        question = QuizQuestion.query.filter_by(id=question_id, quiz_id=quiz_id).first_or_404()
        
        # Check if answer is correct
        is_correct = answer.strip().lower() == question.correct_answer.strip().lower()
        
        # Save answer
        quiz_answer = QuizAnswer(
            quiz_participant_id=participant_id,
            question_id=question_id,
            answer=answer,
            is_correct=is_correct,
            time_taken=time_taken
        )
        
        db.session.add(quiz_answer)
        
        # Update participant score and total time
        if is_correct:
            participant.score += 1
        participant.total_time += time_taken
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_correct': is_correct,
            'correct_answer': question.correct_answer
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting quiz answer: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to submit answer.'})

@app.route('/quiz/<int:quiz_id>/complete/<int:participant_id>', methods=['POST'])
def complete_quiz(quiz_id, participant_id):
    """Mark quiz as completed for a participant."""
    try:
        participant = QuizParticipant.query.filter_by(id=participant_id, quiz_id=quiz_id).first_or_404()
        participant.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Quiz completed successfully!'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error completing quiz: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to complete quiz.'})

@app.route('/quiz/<int:quiz_id>/results')
def quiz_results(quiz_id):
    """Show quiz results and winners."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Get completed participants sorted by score (desc) and total time (asc)
    participants = QuizParticipant.query.filter_by(quiz_id=quiz_id)\
                                      .filter(QuizParticipant.completed_at.isnot(None))\
                                      .order_by(QuizParticipant.score.desc(), 
                                               QuizParticipant.total_time.asc())\
                                      .all()
    
    return render_template('quiz_results.html', 
                         quiz=quiz, 
                         participants=participants)

@app.route('/event/<int:event_id>/quiz/<int:quiz_id>/qr_code')
def generate_quiz_qr(event_id, quiz_id):
    """Generate QR code for quiz access."""
    quiz = Quiz.query.filter_by(id=quiz_id, event_id=event_id).first_or_404()
    
    # Generate QR code URL
    quiz_url = url_for('join_quiz', quiz_id=quiz_id, _external=True)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(quiz_url)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('quiz_qr_code.html', 
                         quiz=quiz, 
                         quiz_url=quiz_url,
                         qr_code_base64=qr_code_base64)

if __name__ == '__main__':
    # app.run(debug=True)