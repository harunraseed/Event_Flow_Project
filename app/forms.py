"""
Flask-WTF forms for the Event Ticketing System.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, DateField, TimeField, TextAreaField, SelectField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
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
                          render_kw={"placeholder": "Enter event location"})
    
    description = TextAreaField('Event Description',
                               validators=[Optional(), Length(max=1000)],
                               render_kw={"placeholder": "Enter event description", "rows": 4})
    
    max_participants = IntegerField('Maximum Participants',
                                   validators=[Optional(), NumberRange(min=1, max=10000)],
                                   default=100)
    
    submit = SubmitField('Create Event')

class ParticipantForm(FlaskForm):
    """Form for adding/editing participants."""
    name = StringField('Full Name', 
                      validators=[DataRequired(), Length(min=2, max=100)],
                      render_kw={"placeholder": "Enter participant name"})
    
    email = StringField('Email Address',
                       validators=[DataRequired(), Email(), Length(max=120)],
                       render_kw={"placeholder": "Enter email address"})
    
    company = StringField('Company/Organization',
                         validators=[Optional(), Length(max=100)],
                         render_kw={"placeholder": "Enter company name (optional)"})
    
    position = StringField('Position/Title',
                          validators=[Optional(), Length(max=100)],
                          render_kw={"placeholder": "Enter position (optional)"})
    
    phone = StringField('Phone Number',
                       validators=[Optional(), Length(max=20)],
                       render_kw={"placeholder": "Enter phone number (optional)"})
    
    submit = SubmitField('Save Participant')

class QuizForm(FlaskForm):
    """Form for creating a quiz."""
    name = StringField('Quiz Name',
                      validators=[DataRequired(), Length(min=3, max=200)],
                      render_kw={"placeholder": "Enter quiz name"})
    
    description = TextAreaField('Quiz Description',
                               validators=[Optional(), Length(max=500)],
                               render_kw={"placeholder": "Enter quiz description", "rows": 3})
    
    timer_per_question = IntegerField('Timer per Question (seconds)',
                                     validators=[DataRequired(), NumberRange(min=10, max=300)],
                                     default=30)
    
    submit = SubmitField('Create Quiz')

class CertificateConfigForm(FlaskForm):
    """Form for configuring certificate generation."""
    certificate_type = SelectField('Certificate Type',
                                  choices=[
                                      ('participation', 'Certificate of Participation'),
                                      ('completion', 'Certificate of Completion'),
                                      ('achievement', 'Certificate of Achievement')
                                  ],
                                  default='participation')
    
    organizer_name = StringField('Organizer Name',
                                validators=[DataRequired(), Length(max=200)],
                                render_kw={"placeholder": "Enter organizer name"})
    
    organizer_logo = FileField('Organizer Logo',
                              validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')],
                              render_kw={"accept": ".jpg,.jpeg,.png"})
    
    organizer_logo_url = StringField('Organizer Logo URL',
                                    validators=[Optional(), Length(max=500)],
                                    render_kw={"placeholder": "Or enter logo URL"})
    
    sponsor_name = StringField('Sponsor Name (Optional)',
                              validators=[Optional(), Length(max=200)],
                              render_kw={"placeholder": "Enter sponsor name"})
    
    sponsor_logo = FileField('Sponsor Logo (Optional)',
                            validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')],
                            render_kw={"accept": ".jpg,.jpeg,.png"})
    
    sponsor_logo_url = StringField('Sponsor Logo URL',
                                  validators=[Optional(), Length(max=500)],
                                  render_kw={"placeholder": "Or enter sponsor logo URL"})
    
    event_location = StringField('Event Location',
                                validators=[Optional(), Length(max=200)],
                                render_kw={"placeholder": "Enter event location"})
    
    event_theme = StringField('Event Theme/Color',
                             validators=[Optional(), Length(max=100)],
                             render_kw={"placeholder": "Enter theme or color scheme"})
    
    signature1_name = StringField('Signature 1 Name',
                                 validators=[Optional(), Length(max=100)],
                                 render_kw={"placeholder": "Enter first signatory name"})
    
    signature1_title = StringField('Signature 1 Title',
                                  validators=[Optional(), Length(max=100)],
                                  render_kw={"placeholder": "Enter first signatory title"})
    
    signature1_image = FileField('Signature 1 Image',
                                validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')],
                                render_kw={"accept": ".jpg,.jpeg,.png"})
    
    signature1_image_url = StringField('Signature 1 Image URL',
                                      validators=[Optional(), Length(max=500)],
                                      render_kw={"placeholder": "Or enter signature image URL"})
    
    signature2_name = StringField('Signature 2 Name (Optional)',
                                 validators=[Optional(), Length(max=100)],
                                 render_kw={"placeholder": "Enter second signatory name"})
    
    signature2_title = StringField('Signature 2 Title (Optional)',
                                  validators=[Optional(), Length(max=100)],
                                  render_kw={"placeholder": "Enter second signatory title"})
    
    signature2_image = FileField('Signature 2 Image (Optional)',
                                validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')],
                                render_kw={"accept": ".jpg,.jpeg,.png"})
    
    signature2_image_url = StringField('Signature 2 Image URL',
                                      validators=[Optional(), Length(max=500)],
                                      render_kw={"placeholder": "Or enter signature image URL"})
    
    submit = SubmitField('Generate Certificates')