from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from werkzeug.utils import secure_filename
from app.models import Event, Quiz, QuizQuestion, QuizParticipant, QuizAnswer, db
from app.forms import QuizForm
import csv
import io
import qrcode
import base64
import logging
from datetime import datetime

quiz = Blueprint('quiz', __name__)
logger = logging.getLogger(__name__)

@quiz.route('/event/<int:event_id>/quiz/create', methods=['GET', 'POST'])
def create_quiz(event_id):
    """Create a new quiz for an event."""
    event = Event.query.get_or_404(event_id)
    form = QuizForm()
    
    if form.validate_on_submit():
        try:
            quiz_obj = Quiz(
                event_id=event_id,
                name=form.name.data,
                description=form.description.data,
                timer_per_question=form.timer_per_question.data,
                is_active=False
            )
            db.session.add(quiz_obj)
            db.session.commit()
            
            flash('Quiz created successfully!', 'success')
            return redirect(url_for('quiz.quiz_dashboard', event_id=event_id, quiz_id=quiz_obj.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating quiz: {str(e)}', 'error')
            logger.error(f"Error creating quiz: {str(e)}")
    
    return render_template('create_quiz.html', form=form, event=event)

@quiz.route('/event/<int:event_id>/quiz/<int:quiz_id>/dashboard')
def quiz_dashboard(event_id, quiz_id):
    """Quiz management dashboard."""
    event = Event.query.get_or_404(event_id)
    quiz_obj = Quiz.query.filter_by(id=quiz_id, event_id=event_id).first_or_404()
    
    # Get quiz statistics
    total_questions = len(quiz_obj.questions)
    total_participants = QuizParticipant.query.filter_by(quiz_id=quiz_id).count()
    completed_participants = QuizParticipant.query.filter_by(quiz_id=quiz_id, completed_at__ne=None).count()
    
    return render_template('quiz_dashboard.html',
                         event=event,
                         quiz=quiz_obj,
                         total_questions=total_questions,
                         total_participants=total_participants,
                         completed_participants=completed_participants)

@quiz.route('/event/<int:event_id>/quiz/<int:quiz_id>/upload_questions', methods=['POST'])
def upload_quiz_questions(event_id, quiz_id):
    """Upload quiz questions from CSV file."""
    event = Event.query.get_or_404(event_id)
    quiz_obj = Quiz.query.filter_by(id=quiz_id, event_id=event_id).first_or_404()
    
    try:
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(url_for('quiz.quiz_dashboard', event_id=event_id, quiz_id=quiz_id))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('quiz.quiz_dashboard', event_id=event_id, quiz_id=quiz_id))
        
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
    
    return redirect(url_for('quiz.quiz_dashboard', event_id=event_id, quiz_id=quiz_id))

@quiz.route('/event/<int:event_id>/quiz/<int:quiz_id>/delete', methods=['POST'])
def delete_quiz(event_id, quiz_id):
    """Delete a quiz and all its associated data."""
    try:
        quiz_obj = Quiz.query.filter_by(id=quiz_id, event_id=event_id).first_or_404()
        
        # Delete all answers for questions in this quiz
        questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
        for question in questions:
            QuizAnswer.query.filter_by(question_id=question.id).delete()
        
        # Delete all participants
        QuizParticipant.query.filter_by(quiz_id=quiz_id).delete()
        
        # Delete all questions
        QuizQuestion.query.filter_by(quiz_id=quiz_id).delete()
        
        # Delete the quiz itself
        db.session.delete(quiz_obj)
        db.session.commit()
        
        flash(f'Quiz "{quiz_obj.name}" has been deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting quiz: {str(e)}', 'error')
        logger.error(f"Error deleting quiz {quiz_id}: {str(e)}")
    
    return redirect(url_for('events.event_dashboard', event_id=event_id))

@quiz.route('/event/<int:event_id>/quiz/<int:quiz_id>/question/<int:question_id>/delete', methods=['POST'])
def delete_quiz_question(event_id, quiz_id, question_id):
    """Delete a specific quiz question."""
    try:
        question = QuizQuestion.query.filter_by(id=question_id, quiz_id=quiz_id).first_or_404()
        
        # Delete all answers for this question
        QuizAnswer.query.filter_by(question_id=question_id).delete()
        
        # Delete the question
        db.session.delete(question)
        db.session.commit()
        
        flash(f'Question has been deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting question: {str(e)}', 'error')
        logger.error(f"Error deleting question {question_id}: {str(e)}")
    
    return redirect(url_for('quiz.quiz_dashboard', event_id=event_id, quiz_id=quiz_id))

@quiz.route('/event/<int:event_id>/quiz/<int:quiz_id>/add_question', methods=['GET', 'POST'])
def add_quiz_question(event_id, quiz_id):
    """Add a question manually to the quiz."""
    event = Event.query.get_or_404(event_id)
    quiz_obj = Quiz.query.filter_by(id=quiz_id, event_id=event_id).first_or_404()
    
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
                return render_template('add_quiz_question.html', event=event, quiz=quiz_obj)
            
            # Combine options into comma-separated string
            options = f"{option1},{option2},{option3},{option4}"
            
            # Validate correct answer is one of the options
            if correct_answer not in [option1, option2, option3, option4]:
                flash('Correct answer must be one of the provided options!', 'error')
                return render_template('add_quiz_question.html', event=event, quiz=quiz_obj)
            
            quiz_question = QuizQuestion(
                quiz_id=quiz_id,
                question=question_text,
                options=options,
                correct_answer=correct_answer
            )
            
            db.session.add(quiz_question)
            db.session.commit()
            
            flash('Question added successfully!', 'success')
            return redirect(url_for('quiz.quiz_dashboard', event_id=event_id, quiz_id=quiz_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding question: {str(e)}', 'error')
            logger.error(f"Error adding quiz question: {str(e)}")
    
    return render_template('add_quiz_question.html', event=event, quiz=quiz_obj)

@quiz.route('/event/<int:event_id>/quiz/<int:quiz_id>/qr_code')
def generate_quiz_qr(event_id, quiz_id):
    """Generate QR code for quiz participation."""
    event = Event.query.get_or_404(event_id)
    quiz_obj = Quiz.query.filter_by(id=quiz_id, event_id=event_id).first_or_404()
    
    # Generate quiz join URL
    join_url = url_for('quiz.join_quiz', quiz_id=quiz_id, _external=True)
    
    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(join_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_data = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('quiz_qr_code.html',
                         event=event,
                         quiz=quiz_obj,
                         qr_code_data=qr_code_data,
                         join_url=join_url)

@quiz.route('/quiz/<int:quiz_id>/join')
def join_quiz(quiz_id):
    """Join quiz page for participants (mobile-friendly)."""
    quiz_obj = Quiz.query.get_or_404(quiz_id)
    return render_template('quiz_join.html', quiz=quiz_obj)

@quiz.route('/quiz/<int:quiz_id>/register', methods=['POST'])
def register_quiz_participant(quiz_id):
    """Register a participant for the quiz."""
    try:
        quiz_obj = Quiz.query.get_or_404(quiz_id)
        
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        
        if not name or not email:
            return jsonify({'success': False, 'message': 'Name and email are required'})
        
        # Check if participant already exists
        existing = QuizParticipant.query.filter_by(quiz_id=quiz_id, email=email).first()
        if existing:
            return jsonify({
                'success': True, 
                'redirect': url_for('quiz.start_quiz', quiz_id=quiz_id, participant_id=existing.id)
            })
        
        # Create new participant
        participant = QuizParticipant(
            quiz_id=quiz_id,
            name=name,
            email=email,
            start_time=datetime.now()
        )
        db.session.add(participant)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'redirect': url_for('quiz.start_quiz', quiz_id=quiz_id, participant_id=participant.id)
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering quiz participant: {str(e)}")
        return jsonify({'success': False, 'message': 'Registration failed'})

@quiz.route('/quiz/<int:quiz_id>/start/<int:participant_id>')
def start_quiz(quiz_id, participant_id):
    """Start the quiz for a participant."""
    quiz_obj = Quiz.query.get_or_404(quiz_id)
    participant = QuizParticipant.query.filter_by(id=participant_id, quiz_id=quiz_id).first_or_404()
    
    # Convert objects to dictionaries for JSON serialization
    quiz_data = {
        'id': quiz_obj.id,
        'name': quiz_obj.name,
        'timer_per_question': quiz_obj.timer_per_question,
        'event_id': quiz_obj.event_id
    }
    
    participant_data = {
        'id': participant.id,
        'name': participant.name,
        'email': participant.email,
        'quiz_id': participant.quiz_id
    }
    
    questions_data = []
    for q in quiz_obj.questions:
        questions_data.append({
            'id': q.id,
            'question': q.question,
            'options': q.options,
            'correct_answer': q.correct_answer
        })
    
    return render_template('quiz_interface.html', 
                         quiz=quiz_obj,
                         participant=participant,
                         questions=quiz_obj.questions,
                         quiz_data=quiz_data,
                         participant_data=participant_data,
                         questions_data=questions_data)

@quiz.route('/quiz/<int:quiz_id>/submit_answer', methods=['POST'])
def submit_quiz_answer(quiz_id):
    """Submit answer for a quiz question."""
    try:
        data = request.get_json()
        participant_id = data.get('participant_id')
        question_id = data.get('question_id')
        answer = data.get('answer')
        time_taken = data.get('time_taken', 0)
        
        # Validate input
        if not all([participant_id, question_id, answer]):
            return jsonify({'success': False, 'message': 'Missing required data'})
        
        # Check if answer already exists
        existing_answer = QuizAnswer.query.filter_by(
            participant_id=participant_id,
            question_id=question_id
        ).first()
        
        if existing_answer:
            return jsonify({'success': False, 'message': 'Answer already submitted'})
        
        # Get question to check correct answer
        question = QuizQuestion.query.get_or_404(question_id)
        is_correct = answer.strip() == question.correct_answer.strip()
        
        # Create answer record
        quiz_answer = QuizAnswer(
            participant_id=participant_id,
            question_id=question_id,
            answer=answer,
            is_correct=is_correct,
            time_taken=time_taken,
            answered_at=datetime.now()
        )
        
        db.session.add(quiz_answer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_correct': is_correct,
            'correct_answer': question.correct_answer
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting quiz answer: {str(e)}")
        return jsonify({'success': False, 'message': 'Error submitting answer'})

@quiz.route('/quiz/<int:quiz_id>/complete/<int:participant_id>', methods=['POST'])
def complete_quiz(quiz_id, participant_id):
    """Mark quiz as completed for participant."""
    try:
        participant = QuizParticipant.query.filter_by(
            id=participant_id, 
            quiz_id=quiz_id
        ).first_or_404()
        
        participant.completed_at = datetime.now()
        participant.total_time = (datetime.now() - participant.start_time).total_seconds()
        
        # Calculate score
        answers = QuizAnswer.query.filter_by(participant_id=participant_id).all()
        correct_answers = sum(1 for a in answers if a.is_correct)
        participant.score = correct_answers
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error completing quiz: {str(e)}")
        return jsonify({'success': False})

@quiz.route('/quiz/<int:quiz_id>/results')
def quiz_results(quiz_id):
    """Display quiz results and leaderboard."""
    quiz_obj = Quiz.query.get_or_404(quiz_id)
    
    # Get completed participants with scores
    participants = QuizParticipant.query.filter_by(
        quiz_id=quiz_id
    ).filter(
        QuizParticipant.completed_at.isnot(None)
    ).order_by(
        QuizParticipant.score.desc(),
        QuizParticipant.total_time.asc()
    ).all()
    
    # Get quiz statistics
    total_questions = len(quiz_obj.questions)
    total_participants = len(participants)
    
    return render_template('quiz_results.html',
                         quiz=quiz_obj,
                         participants=participants,
                         total_questions=total_questions,
                         total_participants=total_participants)