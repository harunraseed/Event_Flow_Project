"""
Database models for the Event Ticketing System.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# This will be imported and initialized by app.py
db = SQLAlchemy()

class Event(db.Model):
    """Event model for storing event information."""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    alias_name = db.Column(db.String(50), nullable=False)  # Event alias for ticket IDs
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time)  # Event time
    logo_filename = db.Column(db.String(255))  # Event logo filename
    location = db.Column(db.String(300))  # Event location
    google_maps_url = db.Column(db.String(500))  # Google Maps URL
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)  # Detailed event instructions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Certificate configuration fields
    certificate_type = db.Column(db.String(50), default='participation')
    organizer_name = db.Column(db.String(200))
    organizer_logo_url = db.Column(db.String(500))
    sponsor_name = db.Column(db.String(200))
    sponsor_logo_url = db.Column(db.String(500))
    event_location_cert = db.Column(db.String(300))  # Location for certificate (may differ from event location)
    event_theme = db.Column(db.String(100))
    signature1_name = db.Column(db.String(100))
    signature1_title = db.Column(db.String(100))
    signature1_image_url = db.Column(db.String(500))
    signature2_name = db.Column(db.String(100))
    signature2_title = db.Column(db.String(100))
    signature2_image_url = db.Column(db.String(500))
    certificate_template = db.Column(db.String(50), default='professional')
    certificate_config_updated = db.Column(db.DateTime)
    
    # Relationship with participants
    participants = db.relationship('Participant', backref='event', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Event {self.name}>'
    
    @property
    def total_participants(self):
        """Get total number of participants for this event."""
        return len(self.participants)
    
    @property
    def checked_in_count(self):
        """Get number of participants who have checked in."""
        return sum(1 for p in self.participants if p.checked_in)
    
    @property
    def attendance_rate(self):
        """Calculate attendance rate as percentage."""
        if self.total_participants == 0:
            return 0
        return round((self.checked_in_count / self.total_participants) * 100, 2)
    
    @property
    def emails_sent_count(self):
        """Get number of participants who have been sent emails."""
        return sum(1 for p in self.participants if p.email_sent)
    
    def generate_next_ticket_number(self):
        """Generate the next ticket number for this event."""
        # Get the highest ticket number for this event
        last_participant = Participant.query.filter_by(event_id=self.id)\
                                           .order_by(Participant.id.desc())\
                                           .first()
        
        if last_participant:
            # Extract the last number from the ticket
            try:
                last_number = int(last_participant.ticket_number.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
            
        # Format: ALIAS-MM-YYYY-NNN
        month = self.date.strftime('%m')
        year = self.date.strftime('%Y')
        ticket_number = f"{self.alias_name.upper()}-{month}-{year}-{next_number:03d}"
        
        return ticket_number
    
    @property
    def auto_generated_maps_url(self):
        """Generate Google Maps URL from location if no direct URL provided."""
        if self.location:
            import urllib.parse
            return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(self.location)}"
        return None
    
    @property 
    def maps_link(self):
        """Get the actual Google Maps URL (either provided or generated)."""
        # If user provided a direct Google Maps URL, use that
        if self.google_maps_url:
            return self.google_maps_url
        # Otherwise, generate from location
        elif self.location:
            import urllib.parse
            return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(self.location)}"
        return None
    
    def update_certificate_config(self, config_data):
        """Update certificate configuration for this event."""
        self.certificate_type = config_data.get('certificate_type', 'participation')
        self.organizer_name = config_data.get('organizer_name')
        self.organizer_logo_url = config_data.get('organizer_logo_url')
        self.sponsor_name = config_data.get('sponsor_name')
        self.sponsor_logo_url = config_data.get('sponsor_logo_url')
        self.event_location_cert = config_data.get('event_location', self.location)
        self.event_theme = config_data.get('event_theme')
        self.signature1_name = config_data.get('signature1_name')
        self.signature1_title = config_data.get('signature1_title')
        self.signature1_image_url = config_data.get('signature1_image_url')
        self.signature2_name = config_data.get('signature2_name')
        self.signature2_title = config_data.get('signature2_title')
        self.signature2_image_url = config_data.get('signature2_image_url')
        self.certificate_template = config_data.get('certificate_template', 'professional')
        self.certificate_config_updated = datetime.utcnow()
    
    def get_certificate_config(self):
        """Get certificate configuration as a dictionary."""
        return {
            'certificate_type': self.certificate_type or 'participation',
            'organizer_name': self.organizer_name,
            'organizer_logo_url': self.organizer_logo_url,
            'sponsor_name': self.sponsor_name,
            'sponsor_logo_url': self.sponsor_logo_url,
            'event_location': self.event_location_cert or self.location,
            'event_theme': self.event_theme,
            'signature1_name': self.signature1_name,
            'signature1_title': self.signature1_title,
            'signature1_image_url': self.signature1_image_url,
            'signature2_name': self.signature2_name,
            'signature2_title': self.signature2_title,
            'signature2_image_url': self.signature2_image_url,
            'certificate_template': self.certificate_template or 'professional'
        }
    
    @property
    def has_certificate_config(self):
        """Check if event has certificate configuration set up."""
        return bool(self.organizer_name and self.certificate_config_updated)
    
    @property
    def certificates_issued_count(self):
        """Get number of certificates issued for this event."""
        return Certificate.query.join(Participant).filter(
            Participant.event_id == self.id
        ).count()

class Participant(db.Model):
    """Participant model for storing participant information."""
    __tablename__ = 'participants'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    checked_in = db.Column(db.Boolean, default=False)
    checkin_time = db.Column(db.DateTime)
    email_sent = db.Column(db.Boolean, default=False)  # New: Track if email was sent
    email_sent_at = db.Column(db.DateTime)  # New: When email was sent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint for event_id and email
    __table_args__ = (db.UniqueConstraint('event_id', 'email', name='_event_email_uc'),)
    
    def __repr__(self):
        return f'<Participant {self.name} - {self.ticket_number}>'
    
    def check_in(self):
        """Mark participant as checked in."""
        self.checked_in = True
        self.checkin_time = datetime.utcnow()
    
    def check_out(self):
        """Mark participant as checked out."""
        self.checked_in = False
        self.checkin_time = None
    
    @property
    def status(self):
        """Get participant status as string."""
        return "Checked In" if self.checked_in else "Not Checked In"
    
    def mark_email_sent(self):
        """Mark email as sent for this participant."""
        self.email_sent = True
        self.email_sent_at = datetime.utcnow()
    
    @property
    def email_status(self):
        """Get email status as string."""
        if self.email_sent:
            return f"Sent {self.email_sent_at.strftime('%m/%d %H:%M')}" if self.email_sent_at else "Sent"
        return "Not Sent"
    
    @property
    def certificate_status(self):
        """Get certificate status as string."""
        if self.certificate:
            return f"Issued {self.certificate.issued_date.strftime('%m/%d/%Y')}"
        return "Not Issued"
    
    @property
    def has_certificate(self):
        """Check if participant has been issued a certificate."""
        return self.certificate is not None

class Certificate(db.Model):
    """Certificate model for storing issued e-certificates."""
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=False)
    certificate_number = db.Column(db.String(50), unique=True, nullable=False)
    issued_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='issued')  # issued, cancelled
    certificate_type = db.Column(db.String(50), default='participation')  # participation, completion, achievement
    
    # Certificate content configuration
    organizer_name = db.Column(db.String(200))
    organizer_logo_url = db.Column(db.String(500))
    sponsor_name = db.Column(db.String(200))
    sponsor_logo_url = db.Column(db.String(500))
    event_location = db.Column(db.String(300))
    event_theme = db.Column(db.String(300))
    
    # Signature information
    signature1_name = db.Column(db.String(100))
    signature1_title = db.Column(db.String(100))
    signature1_image_url = db.Column(db.String(500))
    signature2_name = db.Column(db.String(100))
    signature2_title = db.Column(db.String(100))
    signature2_image_url = db.Column(db.String(500))
    
    # Email tracking
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship back to participant
    participant = db.relationship('Participant', backref=db.backref('certificate', uselist=False))
    
    def __repr__(self):
        return f'<Certificate {self.certificate_number}>'
    
    def generate_certificate_number(self):
        """Generate unique certificate number."""
        # Format: CERT-EVENTID-PARTICIPANTID-YYYYMMDD-XXXX
        
        # Get participant directly from database since relationship might not be loaded
        participant = Participant.query.get(self.participant_id)
        if not participant:
            raise ValueError(f"Participant with ID {self.participant_id} not found")
            
        event_id = participant.event_id
        participant_id = self.participant_id
        date_str = datetime.utcnow().strftime('%Y%m%d')
        
        # Get count of certificates issued today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = Certificate.query.filter(
            Certificate.issued_date >= today_start
        ).count()
        
        return f"CERT-{event_id:03d}-{participant_id:04d}-{date_str}-{today_count + 1:04d}"
    
    @property
    def event(self):
        """Get the event this certificate belongs to."""
        return self.participant.event if self.participant else None
    
    @property
    def certificate_status(self):
        """Get certificate status for display"""
        if self.email_sent:
            return "Issued & Sent"
        elif self.status == 'issued':
            return "Generated"
        return self.status.title()

# ================= QUIZ MODELS =================

class Quiz(db.Model):
    """Quiz model for storing quiz configuration and linkage to events."""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    timer_per_question = db.Column(db.Integer, default=30)  # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship('Event', backref=db.backref('quizzes', lazy=True))
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    participants = db.relationship('QuizParticipant', backref='quiz', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Quiz {self.name} (Event {self.event_id})>'

class QuizQuestion(db.Model):
    """QuizQuestion model for storing MCQ questions for a quiz."""
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)  # Comma-separated options
    correct_answer = db.Column(db.String(200), nullable=False)

    def get_options(self):
        """Get options as a list."""
        return [opt.strip() for opt in self.options.split(',')]

    def __repr__(self):
        return f'<QuizQuestion {self.id}>'

class QuizParticipant(db.Model):
    """QuizParticipant model for tracking quiz session per participant."""
    __tablename__ = 'quiz_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=True)  # Optional link to event participant
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    score = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Integer, default=0)  # Total time taken (seconds)

    # Relationships
    answers = db.relationship('QuizAnswer', backref='quiz_participant', lazy=True, cascade='all, delete-orphan')
    participant = db.relationship('Participant', backref=db.backref('quiz_sessions', lazy=True))

    def __repr__(self):
        return f'<QuizParticipant {self.name} ({self.email})>'

class QuizAnswer(db.Model):
    """QuizAnswer model for storing answers and timing per question per participant."""
    __tablename__ = 'quiz_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_participant_id = db.Column(db.Integer, db.ForeignKey('quiz_participants.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    answer = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    time_taken = db.Column(db.Integer, default=0)  # Time taken to answer (seconds)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    question = db.relationship('QuizQuestion', backref=db.backref('answers', lazy=True))

    def __repr__(self):
        return f'<QuizAnswer Q{self.question_id} by P{self.quiz_participant_id}>'