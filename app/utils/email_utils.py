"""
Email utilities for sending certificates and notifications.
"""

from flask import current_app, render_template
from flask_mail import Message
from app import mail
import logging

logger = logging.getLogger(__name__)

def send_certificate_email(participant, event, certificate):
    """Send certificate email to participant."""
    try:
        msg = Message(
            subject=f'Certificate for {event.name}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[participant.email]
        )
        
        # Render email template
        msg.html = render_template('emails/certificate_email.html',
                                 participant=participant,
                                 event=event,
                                 certificate=certificate)
        
        mail.send(msg)
        logger.info(f"Certificate email sent to {participant.email}")
        
    except Exception as e:
        logger.error(f"Failed to send certificate email to {participant.email}: {str(e)}")
        raise e

def send_ticket_email(participant, event):
    """Send ticket email to participant."""
    try:
        msg = Message(
            subject=f'Your Ticket for {event.name}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[participant.email]
        )
        
        # Render email template
        msg.html = render_template('emails/ticket_email.html',
                                 participant=participant,
                                 event=event)
        
        mail.send(msg)
        logger.info(f"Ticket email sent to {participant.email}")
        
    except Exception as e:
        logger.error(f"Failed to send ticket email to {participant.email}: {str(e)}")
        raise e