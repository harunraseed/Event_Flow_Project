from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from app.models import Event, Participant, Certificate, db
from app.forms import EventForm, ParticipantForm, CertificateConfigForm
import pandas as pd
import os
import io
import time
import logging
from datetime import datetime
import uuid

events = Blueprint('events', __name__)
logger = logging.getLogger(__name__)

@events.route('/create', methods=['GET', 'POST'])
def create_event():
    """Create a new event."""
    form = EventForm()
    if form.validate_on_submit():
        try:
            # Handle logo file upload
            logo_url = None
            if form.logo.data:
                filename = secure_filename(form.logo.data.filename)
                if filename:
                    # Generate unique filename
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    logo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'logos', unique_filename)
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                    
                    form.logo.data.save(logo_path)
                    logo_url = f"uploads/logos/{unique_filename}"
            
            event = Event(
                name=form.name.data,
                description=form.description.data,
                date=form.date.data,
                location=form.location.data,
                max_participants=form.max_participants.data,
                logo_url=logo_url
            )
            db.session.add(event)
            db.session.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('events.event_dashboard', event_id=event.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating event: {str(e)}")
            flash('Error creating event. Please try again.', 'danger')
    
    return render_template('create_event.html', form=form)

@events.route('/<int:event_id>/dashboard')
def event_dashboard(event_id):
    """Display event dashboard with participants and statistics."""
    event = Event.query.get_or_404(event_id)
    participants = Participant.query.filter_by(event_id=event_id).all()
    
    # Calculate statistics
    total_participants = len(participants)
    checked_in = sum(1 for p in participants if p.checked_in)
    emails_sent = sum(1 for p in participants if p.email_sent)
    
    return render_template('event_dashboard.html', 
                         event=event, 
                         participants=participants,
                         total_participants=total_participants,
                         checked_in=checked_in,
                         emails_sent=emails_sent)

@events.route('/<int:event_id>/participant/add', methods=['GET', 'POST'])
def add_participant(event_id):
    """Add a single participant to an event."""
    event = Event.query.get_or_404(event_id)
    form = ParticipantForm()
    
    if form.validate_on_submit():
        try:
            participant = Participant(
                event_id=event_id,
                name=form.name.data,
                email=form.email.data,
                company=form.company.data,
                position=form.position.data,
                phone=form.phone.data
            )
            db.session.add(participant)
            db.session.commit()
            flash('Participant added successfully!', 'success')
            return redirect(url_for('events.event_dashboard', event_id=event_id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding participant: {str(e)}")
            flash('Error adding participant. Please try again.', 'danger')
    
    return render_template('add_participant.html', form=form, event=event)

@events.route('/<int:event_id>/participant/<int:participant_id>/edit', methods=['GET', 'POST'])
def edit_participant(event_id, participant_id):
    """Edit an existing participant."""
    event = Event.query.get_or_404(event_id)
    participant = Participant.query.filter_by(id=participant_id, event_id=event_id).first_or_404()
    
    form = ParticipantForm(obj=participant)
    
    if form.validate_on_submit():
        try:
            participant.name = form.name.data
            participant.email = form.email.data
            participant.company = form.company.data
            participant.position = form.position.data
            participant.phone = form.phone.data
            db.session.commit()
            flash('Participant updated successfully!', 'success')
            return redirect(url_for('events.event_dashboard', event_id=event_id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating participant: {str(e)}")
            flash('Error updating participant. Please try again.', 'danger')
    
    return render_template('edit_participant.html', form=form, event=event, participant=participant)

@events.route('/<int:event_id>/upload_participants', methods=['GET', 'POST'])
def upload_participants(event_id):
    """Upload participants from Excel/CSV file."""
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected.', 'danger')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected.', 'danger')
                return redirect(request.url)
            
            if file and file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
                # Read the file
                if file.filename.lower().endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                participants_added = 0
                for _, row in df.iterrows():
                    try:
                        participant = Participant(
                            event_id=event_id,
                            name=str(row.get('name', '')).strip(),
                            email=str(row.get('email', '')).strip().lower(),
                            company=str(row.get('company', '')).strip(),
                            position=str(row.get('position', '')).strip(),
                            phone=str(row.get('phone', '')).strip()
                        )
                        
                        if participant.name and participant.email:
                            db.session.add(participant)
                            participants_added += 1
                        
                    except Exception as e:
                        logger.error(f"Error adding participant from row: {str(e)}")
                        continue
                
                db.session.commit()
                flash(f'Successfully uploaded {participants_added} participants!', 'success')
            else:
                flash('Please upload an Excel (.xlsx) or CSV file.', 'danger')
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading participants: {str(e)}")
            flash('Error processing file. Please check the format and try again.', 'danger')
    
    return render_template('upload_participants.html', event=event)

@events.route('/<int:event_id>/participant/<int:participant_id>/checkin')
def toggle_checkin(event_id, participant_id):
    """Toggle participant check-in status."""
    participant = Participant.query.filter_by(id=participant_id, event_id=event_id).first_or_404()
    
    try:
        participant.checked_in = not participant.checked_in
        if participant.checked_in:
            participant.check_in_time = datetime.now()
        else:
            participant.check_in_time = None
        
        db.session.commit()
        
        status = 'checked in' if participant.checked_in else 'checked out'
        flash(f'{participant.name} has been {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling check-in: {str(e)}")
        flash('Error updating check-in status.', 'danger')
    
    return redirect(url_for('events.event_dashboard', event_id=event_id))

@events.route('/<int:event_id>/participant/<int:participant_id>/delete', methods=['POST'])
def delete_participant(event_id, participant_id):
    """Delete a participant."""
    participant = Participant.query.filter_by(id=participant_id, event_id=event_id).first_or_404()
    
    try:
        db.session.delete(participant)
        db.session.commit()
        flash(f'{participant.name} has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting participant: {str(e)}")
        flash('Error deleting participant.', 'danger')
    
    return redirect(url_for('events.event_dashboard', event_id=event_id))

@events.route('/<int:event_id>/export')
def export_participants(event_id):
    """Export participants to Excel file."""
    event = Event.query.get_or_404(event_id)
    participants = Participant.query.filter_by(event_id=event_id).all()
    
    # Create DataFrame
    data = []
    for p in participants:
        data.append({
            'Name': p.name,
            'Email': p.email,
            'Company': p.company or '',
            'Position': p.position or '',
            'Phone': p.phone or '',
            'Checked In': 'Yes' if p.checked_in else 'No',
            'Check-in Time': p.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if p.check_in_time else '',
            'Email Sent': 'Yes' if p.email_sent else 'No'
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Participants', index=False)
    
    output.seek(0)
    
    filename = f"{event.name.replace(' ', '_')}_participants.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )