from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from werkzeug.utils import secure_filename
from app.models import Event, Participant, Certificate, db
from app.forms import CertificateConfigForm
from app.utils.email_utils import send_certificate_email
import os
import uuid
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

certificates = Blueprint('certificates', __name__)
logger = logging.getLogger(__name__)

@certificates.route('/event/<int:event_id>/certificates/configure', methods=['GET', 'POST'])
def certificate_configuration(event_id):
    """Configure certificate settings and generate certificates."""
    event = Event.query.get_or_404(event_id)
    form = CertificateConfigForm()
    
    if form.validate_on_submit():
        try:
            # Handle file uploads
            uploaded_files = {}
            upload_fields = ['organizer_logo', 'sponsor_logo', 'signature1_image', 'signature2_image']
            
            for field_name in upload_fields:
                field = getattr(form, field_name)
                if field.data:
                    filename = secure_filename(field.data.filename)
                    if filename:
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'certificates', unique_filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        field.data.save(file_path)
                        uploaded_files[f"{field_name}_url"] = f"uploads/certificates/{unique_filename}"
            
            # Prepare certificate configuration
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
                return redirect(url_for('certificates.certificate_preview', event_id=event_id))
            
            certificates_created = 0
            certificates_sent = 0
            errors = []
            
            for participant in participants_to_process:
                try:
                    # Create certificate record
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
                    
                    db.session.add(certificate)
                    certificates_created += 1
                    
                    # Try to send certificate email
                    try:
                        send_certificate_email(participant, event, certificate)
                        certificates_sent += 1
                    except Exception as email_error:
                        logger.error(f"Failed to send certificate email to {participant.email}: {str(email_error)}")
                        errors.append(f"Failed to send email to {participant.name}: {str(email_error)}")
                        
                except Exception as cert_error:
                    logger.error(f"Failed to create certificate for {participant.name}: {str(cert_error)}")
                    errors.append(f"Failed to create certificate for {participant.name}: {str(cert_error)}")
            
            db.session.commit()
            
            # Show results
            if certificates_created > 0:
                flash(f'Successfully created {certificates_created} certificates!', 'success')
                if certificates_sent > 0:
                    flash(f'Successfully sent {certificates_sent} certificate emails!', 'success')
                if errors:
                    for error in errors:
                        flash(error, 'warning')
            else:
                flash('No certificates were created.', 'warning')
            
            return redirect(url_for('certificates.certificate_preview', event_id=event_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in certificate configuration: {str(e)}")
            flash(f'Error processing certificates: {str(e)}', 'danger')
    
    return render_template('certificate_configuration.html', form=form, event=event)

@certificates.route('/event/<int:event_id>/certificates/preview')
def certificate_preview(event_id):
    """Preview certificate template."""
    event = Event.query.get_or_404(event_id)
    
    # Get a sample participant for preview
    sample_participant = Participant.query.filter_by(event_id=event_id).first()
    if not sample_participant:
        flash('No participants found. Add participants first.', 'warning')
        return redirect(url_for('events.event_dashboard', event_id=event_id))
    
    # Get certificate configuration from event
    cert_config = event.certificate_config or {}
    
    return render_template('certificate_preview.html',
                         event=event,
                         participant=sample_participant,
                         cert_config=cert_config)

@certificates.route('/event/<int:event_id>/certificates/download_all')
def download_all_certificates(event_id):
    """Download all certificates as a ZIP file."""
    event = Event.query.get_or_404(event_id)
    certificates = Certificate.query.join(Participant).filter(
        Participant.event_id == event_id
    ).all()
    
    if not certificates:
        flash('No certificates found for this event.', 'warning')
        return redirect(url_for('events.event_dashboard', event_id=event_id))
    
    # Create ZIP file in memory
    import zipfile
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for cert in certificates:
            try:
                # Generate PDF for each certificate
                pdf_buffer = generate_certificate_pdf(cert)
                if pdf_buffer:
                    filename = f"{cert.participant.name}_certificate.pdf"
                    zip_file.writestr(filename, pdf_buffer.getvalue())
            except Exception as e:
                logger.error(f"Error generating PDF for {cert.participant.name}: {str(e)}")
                continue
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"{event.name}_certificates.zip"
    )

@certificates.route('/certificate/<int:certificate_id>/download')
def download_certificate(certificate_id):
    """Download individual certificate PDF."""
    certificate = Certificate.query.get_or_404(certificate_id)
    
    try:
        pdf_buffer = generate_certificate_pdf(certificate)
        if not pdf_buffer:
            flash('Error generating certificate PDF.', 'danger')
            return redirect(url_for('events.event_dashboard', event_id=certificate.participant.event_id))
        
        filename = f"{certificate.participant.name}_certificate.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error downloading certificate: {str(e)}")
        flash('Error downloading certificate.', 'danger')
        return redirect(url_for('events.event_dashboard', event_id=certificate.participant.event_id))

def generate_certificate_pdf(certificate):
    """Generate PDF certificate."""
    try:
        buffer = io.BytesIO()
        
        # Create PDF with landscape orientation
        p = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)
        
        # Certificate background and styling
        p.setFillColorRGB(0.1, 0.3, 0.6)  # Blue background
        p.rect(0, 0, width, height, fill=1)
        
        # White certificate area
        margin = 50
        p.setFillColorRGB(1, 1, 1)  # White
        p.rect(margin, margin, width - 2*margin, height - 2*margin, fill=1)
        
        # Certificate title
        p.setFillColorRGB(0.1, 0.3, 0.6)  # Blue text
        p.setFont("Helvetica-Bold", 36)
        title = "CERTIFICATE OF PARTICIPATION"
        title_width = p.stringWidth(title, "Helvetica-Bold", 36)
        p.drawString((width - title_width) / 2, height - 150, title)
        
        # Participant name
        p.setFont("Helvetica-Bold", 28)
        p.setFillColorRGB(0.2, 0.2, 0.2)  # Dark gray
        name_text = f"This is to certify that"
        name_width = p.stringWidth(name_text, "Helvetica-Bold", 28)
        p.drawString((width - name_width) / 2, height - 220, name_text)
        
        # Participant name (larger)
        p.setFont("Helvetica-Bold", 32)
        p.setFillColorRGB(0.1, 0.3, 0.6)  # Blue
        participant_name = certificate.participant.name.upper()
        participant_width = p.stringWidth(participant_name, "Helvetica-Bold", 32)
        p.drawString((width - participant_width) / 2, height - 270, participant_name)
        
        # Event details
        p.setFont("Helvetica", 20)
        p.setFillColorRGB(0.2, 0.2, 0.2)  # Dark gray
        event_text = f"has successfully participated in"
        event_width = p.stringWidth(event_text, "Helvetica", 20)
        p.drawString((width - event_width) / 2, height - 320, event_text)
        
        # Event name
        p.setFont("Helvetica-Bold", 24)
        p.setFillColorRGB(0.1, 0.3, 0.6)  # Blue
        event_name = certificate.participant.event.name.upper()
        event_name_width = p.stringWidth(event_name, "Helvetica-Bold", 24)
        p.drawString((width - event_name_width) / 2, height - 360, event_name)
        
        # Date and location
        p.setFont("Helvetica", 16)
        p.setFillColorRGB(0.4, 0.4, 0.4)  # Gray
        date_str = certificate.participant.event.date.strftime("%B %d, %Y")
        location = certificate.event_location or "Virtual Event"
        details_text = f"on {date_str} at {location}"
        details_width = p.stringWidth(details_text, "Helvetica", 16)
        p.drawString((width - details_width) / 2, height - 400, details_text)
        
        # Organizer signature area
        if certificate.signature1_name:
            p.setFont("Helvetica", 12)
            p.drawString(150, 150, "Authorized by:")
            p.line(150, 130, 350, 130)  # Signature line
            p.setFont("Helvetica-Bold", 14)
            p.drawString(150, 110, certificate.signature1_name)
            if certificate.signature1_title:
                p.setFont("Helvetica", 12)
                p.drawString(150, 95, certificate.signature1_title)
        
        # Date issued
        p.setFont("Helvetica", 12)
        issued_date = certificate.issued_date.strftime("%B %d, %Y")
        p.drawString(width - 250, 150, f"Date Issued:")
        p.drawString(width - 250, 130, issued_date)
        
        # Certificate ID
        p.setFont("Helvetica", 10)
        cert_id = f"Certificate ID: CERT-{certificate.id:06d}"
        p.drawString(margin + 20, margin + 20, cert_id)
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logger.error(f"Error generating certificate PDF: {str(e)}")
        return None