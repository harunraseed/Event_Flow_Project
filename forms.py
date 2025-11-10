"""
Flask-WTF forms for the Event Ticketing System.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, DateField, TimeField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional
from wtforms.widgets import DateInput

class EventForm(FlaskForm):
    """Form for creating a new event."""
    name = StringField('Event Name', 
                      validators=[DataRequired(), Length(min=3, max=200)],
                      render_kw={"placeholder": "Enter event name"})
    
    alias_name = StringField('Event Alias', 
                           validators=[DataRequired(), Length(min=2, max=50)],
                           render_kw={"placeholder": "Enter short alias (e.g., TECH2024, CONF25)"})
    
    date = DateField('Event Date', 
                    validators=[DataRequired()],
                    render_kw={"type": "date"})
    
    time = TimeField('Event Time',
                    validators=[Optional()],
                    render_kw={"type": "time"})
    
    logo = FileField('Event Logo (Optional)',
                    validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')],
                    render_kw={"accept": ".jpg,.jpeg,.png,.gif"})
    
    location = StringField('Event Location',
                          validators=[Optional(), Length(max=300)],
                          render_kw={"placeholder": "Enter event location (e.g., Conference Hall A, 123 Main St)"})
    
    google_maps_url = StringField('Google Maps Link (Optional)',
                                 validators=[Optional(), Length(max=500)],
                                 render_kw={"placeholder": "Paste Google Maps URL here (optional)"})
    
    description = TextAreaField('Event Description',
                               validators=[Optional(), Length(max=1000)],
                               render_kw={"placeholder": "Enter event description (optional)", 
                                        "rows": 4})
    
    organizer_name = StringField('Event Organizer Name',
                                validators=[Optional(), Length(max=200)],
                                render_kw={"placeholder": "Enter organizer name (e.g., Azure Developer Community)"})
    
    instructions = TextAreaField('Event Instructions',
                                validators=[Optional(), Length(max=5000)],
                                render_kw={"placeholder": "Enter detailed event instructions (e.g., what to bring, parking info, agenda, dress code, etc.)", 
                                         "rows": 8})
    
    submit = SubmitField('Create Event')

class ParticipantUploadForm(FlaskForm):
    """Form for uploading participants CSV file."""
    csv_file = FileField('Participants CSV File',
                        validators=[
                            FileRequired(),
                            FileAllowed(['csv'], 'CSV files only!')
                        ],
                        render_kw={"accept": ".csv"})
    
    submit = SubmitField('Upload Participants')

class ManualParticipantForm(FlaskForm):
    """Form for manually adding a single participant."""
    name = StringField('Participant Name', 
                      validators=[DataRequired(), Length(min=2, max=100)],
                      render_kw={"placeholder": "Enter participant's full name"})
    
    email = StringField('Email Address', 
                       validators=[DataRequired(), Email(), Length(max=120)],
                       render_kw={"placeholder": "Enter participant's email address"})
    
    check_in_immediately = BooleanField('Check-in immediately', default=False)
    
    submit = SubmitField('Add Participant')

class EditParticipantForm(FlaskForm):
    """Form for editing participant information."""
    name = StringField('Participant Name', 
                      validators=[DataRequired(), Length(min=2, max=100)],
                      render_kw={"placeholder": "Enter participant's full name"})
    
    email = StringField('Email Address', 
                       validators=[DataRequired(), Email(), Length(max=120)],
                       render_kw={"placeholder": "Enter participant's email address"})
    
    checked_in = BooleanField('Checked In Status')
    
    email_sent = BooleanField('Email Sent Status')
    
    submit = SubmitField('Update Participant')

class CertificateForm(FlaskForm):
    """Form for certificate operations."""
    certificate_type = SelectField('Certificate Type',
                                 choices=[('completion', 'Certificate of Completion'),
                                        ('participation', 'Certificate of Participation')],
                                 default='completion')
    
    send_to_all_checked_in = BooleanField('Send to all checked-in participants', default=True)
    
    submit = SubmitField('Generate & Send Certificates')

class AttendanceForm(FlaskForm):
    """Form for marking attendance."""
    participant_id = StringField('Participant ID', validators=[DataRequired()])
    checked_in = BooleanField('Checked In')
    submit = SubmitField('Update Attendance')

class BulkEmailForm(FlaskForm):
    """Form for sending bulk emails."""
    email_subject = StringField('Email Subject',
                               validators=[DataRequired(), Length(min=5, max=200)],
                               render_kw={"placeholder": "Enter email subject"})
    
    email_message = TextAreaField('Email Message',
                                 validators=[DataRequired(), Length(min=10, max=2000)],
                                 render_kw={"placeholder": "Enter email message", 
                                          "rows": 6})
    
    submit = SubmitField('Send Emails')

class SearchForm(FlaskForm):
    """Form for searching participants."""
    search_query = StringField('Search Participants',
                              validators=[Optional(), Length(max=100)],
                              render_kw={"placeholder": "Search by name, email, or ticket number"})
    
    status_filter = SelectField('Filter by Status',
                               choices=[
                                   ('all', 'All Participants'),
                                   ('checked_in', 'Checked In'),
                                   ('not_checked_in', 'Not Checked In')
                               ],
                               default='all')
    
    submit = SubmitField('Search')

class EventSelectForm(FlaskForm):
    """Form for selecting an event."""
    event_id = SelectField('Select Event',
                          coerce=int,
                          validators=[DataRequired()])
    
    submit = SubmitField('Select Event')
    
    def __init__(self, events=None, *args, **kwargs):
        super(EventSelectForm, self).__init__(*args, **kwargs)
        if events:
            self.event_id.choices = [(event.id, f"{event.name} - {event.date}") for event in events]
        else:
            self.event_id.choices = []

class CertificateForm(FlaskForm):
    """Form for certificate configuration and generation"""
    certificate_type = SelectField('Certificate Type', 
                                 choices=[('participation', 'Participation'), 
                                         ('completion', 'Completion'),
                                         ('achievement', 'Achievement')],
                                 default='participation')
    
    # Certificate content configuration
    organizer_name = StringField('Organizer Name', 
                               default='Azure Developer Community Tamilnadu',
                               render_kw={'placeholder': 'e.g.,  Azure Developer Community Tamilnadu'})
    organizer_logo_file = FileField('Organizer Logo Upload', 
                                   validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Images only!')])
    organizer_logo_url = StringField('Or Organizer Logo URL',
                                   render_kw={'placeholder': 'https://example.com/logo.png'})
    
    sponsor_name = StringField('Sponsor/Partner Name',
                             default='Microsoft',
                             render_kw={'placeholder': 'e.g., Microsoft'})
    sponsor_logo_file = FileField('Sponsor Logo Upload',
                                 validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Images only!')])
    sponsor_logo_url = StringField('Or Sponsor Logo URL',
                                 render_kw={'placeholder': 'https://example.com/sponsor-logo.png'})
    
    event_location = StringField('Event Location',
                               render_kw={'placeholder': 'e.g., Microsoft Ferns Office, Bellandur - Bengaluru'})
    event_theme = StringField('Event Theme/Technology',
                            default='advanced technologies and innovation',
                            render_kw={'placeholder': 'e.g., advanced AI technologies, cloud computing'})
    
    # Signature information
    signature1_name = StringField('First Signatory Name',
                                render_kw={'placeholder': 'e.g., Your Name'})
    signature1_title = StringField('First Signatory Title',
                                 default='Organizer',
                                 render_kw={'placeholder': 'e.g., Microsoft MVP, Organiser Azure Developer Community Tamilnadu'})
    signature1_file = FileField('First Signature Upload',
                               validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Images only!')])
    signature1_image_url = StringField('Or First Signature URL',
                                     render_kw={'placeholder': 'https://example.com/signature1.png'})
    
    signature2_name = StringField('Second Signatory Name',
                                render_kw={'placeholder': 'e.g., Your Name'})
    signature2_title = StringField('Second Signatory Title',
                                 default='Event Lead',
                                 render_kw={'placeholder': 'e.g., Microsoft MVP - AI, Organiser Azure Developer Community Tamilnadu'})
    signature2_file = FileField('Second Signature Upload',
                               validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Images only!')])
    signature2_image_url = StringField('Or Second Signature URL',
                                     render_kw={'placeholder': 'https://example.com/signature2.png'})
    
    # Action options
    send_to_all_checked_in = BooleanField('Send to all checked-in participants', default=True)
    
    submit = SubmitField('Generate & Send Certificates')

class QuizForm(FlaskForm):
    """Form for creating a new quiz."""
    name = StringField('Quiz Name', 
                      validators=[DataRequired(), Length(min=3, max=200)],
                      render_kw={"placeholder": "Enter quiz name"})
    
    timer_per_question = SelectField('Time per Question (seconds)',
                                   choices=[(10, '10 seconds'), (15, '15 seconds'), 
                                           (20, '20 seconds'), (30, '30 seconds'), 
                                           (45, '45 seconds'), (60, '60 seconds')],
                                   default=30,
                                   coerce=int)
    
    submit = SubmitField('Create Quiz')

class QuizQuestionUploadForm(FlaskForm):
    """Form for uploading quiz questions via CSV."""
    file = FileField('Questions CSV File', 
                    validators=[FileRequired(), FileAllowed(['csv'], 'CSV files only!')],
                    render_kw={"accept": ".csv"})
    
    submit = SubmitField('Upload Questions')

class QuizJoinForm(FlaskForm):
    """Form for participants to join a quiz."""
    name = StringField('Your Name', 
                      validators=[DataRequired(), Length(min=2, max=100)],
                      render_kw={"placeholder": "Enter your full name"})
    
    email = StringField('Your Email', 
                       validators=[DataRequired(), Email()],
                       render_kw={"placeholder": "Enter your email address"})
    
    submit = SubmitField('Join Quiz')