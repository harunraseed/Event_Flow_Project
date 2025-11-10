"""
Database models for the Event Ticketing System.
"""

from datetime import datetime
from app import db

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
    
    # Relationships
    participants = db.relationship('Participant', backref='event', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='event', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Event {self.name}>'
    
    @property
    def formatted_date(self):
        """Return formatted date string."""
        return self.date.strftime('%B %d, %Y')
    
    @property 
    def participant_count(self):
        """Return total number of participants."""
        return len(self.participants)

class Participant(db.Model):
    """Participant model for event attendees."""
    __tablename__ = 'participants'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    checked_in = db.Column(db.Boolean, default=False)
    checkin_time = db.Column(db.DateTime)
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint for event_id and email
    __table_args__ = (db.UniqueConstraint('event_id', 'email', name='_event_email_uc'),)
    
    def __repr__(self):
        return f'<Participant {self.name}>'

class Quiz(db.Model):
    """Quiz model for event quizzes."""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    timer_per_question = db.Column(db.Integer, default=30)  # seconds
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    participants = db.relationship('QuizParticipant', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quiz {self.name}>'

class QuizQuestion(db.Model):
    """Quiz question model."""
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)  # Comma-separated options
    correct_answer = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    answers = db.relationship('QuizAnswer', backref='question', lazy=True, cascade='all, delete-orphan')
    
    def get_options(self):
        """Return list of options."""
        return [option.strip() for option in self.options.split(',') if option.strip()]
    
    def __repr__(self):
        return f'<QuizQuestion {self.id}: {self.question[:50]}>'

class QuizParticipant(db.Model):
    """Quiz participant model."""
    __tablename__ = 'quiz_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Integer, default=0)  # Total time taken in seconds
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    answers = db.relationship('QuizAnswer', backref='participant', lazy=True, cascade='all, delete-orphan')
    
    @property
    def is_completed(self):
        """Check if participant has completed the quiz."""
        return self.completed_at is not None
    
    def __repr__(self):
        return f'<QuizParticipant {self.name}>'

class QuizAnswer(db.Model):
    """Quiz answer model."""
    __tablename__ = 'quiz_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('quiz_participants.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    answer = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    time_taken = db.Column(db.Integer, default=0)  # Time taken in seconds
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<QuizAnswer {self.id}>'

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