# Event Ticketing and Attendance Management System

# Event Ticketing & Quiz Management Application

A comprehensive Flask-based web application for managing events, conducting interactive quizzes, and generating certificates. Built with a world-class architecture for production deployment on Azure.

## 🚀 Features

### Event Management
- Create and manage multiple events
- Upload participant lists via CSV
- Generate QR codes for event access
- Real-time dashboard with participant statistics
- Professional certificate generation (PDF)
- Email notifications with embedded certificates

### Interactive Quiz System
- 📝 **Question Management**: Upload questions via Excel or add manually
- 🏆 **Real-time Competition**: Support for 100+ concurrent participants
- 📱 **Mobile-First Design**: Optimized mobile interface for participants
- ⏱️ **Timed Questions**: Configurable timer (20-30 seconds)
- 🥇 **Winner Calculation**: Fastest finger first with accuracy scoring
- 📊 **Live Results**: Real-time leaderboard and winner announcements
- 🎯 **CRUD Operations**: Complete quiz and question management

### Technical Features
- 🏗️ **Production Architecture**: Flask application factory pattern with blueprints
- 🔄 **Database Migrations**: Alembic-based version control
- ☁️ **Azure Ready**: Configured for Azure Web App deployment
- 🔒 **Security**: Environment-based configuration management
- 📊 **Monitoring**: Comprehensive logging and error handling
- 🎨 **Modern UI**: Bootstrap 5 with responsive design

## 🏗️ Architecture

```
app/
├── __init__.py              # Application factory
├── models.py               # Database models
├── config.py               # Configuration management
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── email_utils.py      # Email handling
│   ├── certificate_utils.py # PDF generation
│   └── quiz_utils.py       # Quiz logic
└── routes/                 # Blueprint modules
    ├── __init__.py
    ├── main.py            # Home routes
    ├── events.py          # Event management
    ├── quiz.py            # Quiz functionality
    └── certificates.py    # Certificate generation
```

## 🚦 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd event-ticketing-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Create .env file
   copy .env.example .env  # Windows
   # cp .env.example .env    # Linux/Mac
   
   # Edit .env with your settings
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///app.db
   MAIL_SERVER=smtp.gmail.com
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

5. **Initialize database**
   ```bash
   python migrate_manager.py init
   python migrate_manager.py create "Initial migration"
   python migrate_manager.py upgrade
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

   Visit `http://localhost:5000`

### Production Deployment (Azure Web App)

1. **Prepare for deployment**
   ```bash
   # Ensure all dependencies are listed
   pip freeze > requirements.txt
   
   # Create production database migration
   python migrate_manager.py create "Production deployment"
   ```

2. **Deploy to Azure**
   - Push to GitHub repository
   - Configure Azure Web App with GitHub Actions
   - Set environment variables in Azure portal
   - The app will automatically deploy using `startup.py`

## 📊 Database Models

### Core Models
- **Event**: Event information and settings
- **Participant**: Event participant details
- **Quiz**: Quiz configuration and metadata
- **QuizQuestion**: Individual quiz questions
- **QuizParticipant**: Quiz participant tracking
- **QuizAnswer**: Participant responses and scoring

### Key Relationships
- Events → Participants (One-to-Many)
- Quiz → Questions (One-to-Many)
- Quiz → Participants (One-to-Many)
- Participants → Answers (One-to-Many)

## 🎯 Quiz System Usage

### Creating a Quiz

1. **Navigate to Quiz Management**
   - Click "Quiz Management" in the navigation

2. **Create New Quiz**
   - Fill in quiz details (name, duration, timer settings)
   - Set participant limits and scoring rules

3. **Add Questions**
   - **Option A**: Upload Excel file with questions
     - Use the provided template
     - Include question, options A-D, correct answer
   - **Option B**: Add questions manually
     - Use the question management interface
     - Create multiple choice questions with 4 options

### Conducting a Quiz

1. **Start Quiz Session**
   - Generate QR code for participant access
   - Share QR code or direct link with participants

2. **Participant Experience**
   - Participants scan QR code or visit link
   - Enter name and email
   - Answer timed questions on mobile device
   - View real-time results

3. **Monitor Progress**
   - View live participant count
   - Monitor answer submissions
   - See real-time leaderboard

### Viewing Results

- **Winner Calculation**: Fastest correct answers win
- **Detailed Analytics**: View all participant responses
- **Export Options**: Download results as CSV
- **Certificates**: Generate winner certificates

## 🔧 Configuration

### Environment Variables

```env
# Application Settings
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Azure Settings (for production)
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection
```

### Configuration Classes
- **DevelopmentConfig**: Local development settings
- **ProductionConfig**: Azure production settings
- **TestingConfig**: Unit testing configuration

## 📁 File Structure

### Template Organization
```
templates/
├── base.html                    # Base template with navigation
├── index.html                   # Home page
├── create_event.html           # Event creation form
├── event_dashboard.html        # Event management dashboard
├── quiz/                       # Quiz-related templates
│   ├── quiz_list.html         # Quiz listing
│   ├── create_quiz.html       # Quiz creation
│   ├── quiz_dashboard.html    # Quiz management
│   └── take_quiz.html         # Participant quiz interface
└── certificates/               # Certificate templates
    └── certificate_simple_pdf.html
```

### Static Assets
```
static/
├── css/
│   └── style.css              # Custom styles
├── js/
│   ├── quiz.js                # Quiz functionality
│   └── dashboard.js           # Dashboard interactions
└── uploads/                   # File uploads
    ├── logos/                 # Event logos
    └── certificates/          # Generated certificates
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-flask

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Test Structure
- Unit tests for models and utilities
- Integration tests for routes
- End-to-end tests for quiz functionality

## 🚀 Deployment

### Azure Web App Deployment

1. **GitHub Integration**
   - Connect Azure Web App to GitHub repository
   - Enable continuous deployment

2. **Configuration**
   - Set environment variables in Azure portal
   - Configure Python runtime version

3. **Database Setup**
   - Use Azure Database for PostgreSQL
   - Run migrations on first deployment

### Local Production Testing
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn --config gunicorn.conf.py startup:app
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- Create an issue for bug reports
- Use discussions for questions and feature requests
- Check the wiki for additional documentation

## 🏆 Acknowledgments

- Flask and SQLAlchemy communities
- Bootstrap for responsive UI components
- Azure for cloud hosting platform
- Contributors and testers

## Features

- **Event Management**: Create events with name, date, and description
- **CSV Upload**: Bulk upload participants via CSV file
- **Unique Tickets**: Auto-generated unique ticket numbers for each participant
- **Email Notifications**: Automated email delivery with ticket details
- **Attendance Tracking**: Real-time check-in/check-out functionality
- **Dashboard**: Admin dashboard with statistics and participant management
- **Export Reports**: CSV export of attendance data
- **Responsive Design**: Bootstrap-based responsive UI

## Project Structure

```
event-ticketing-app/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── forms.py               # Flask-WTF forms
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── create_event.html # Event creation form
│   ├── upload_participants.html # CSV upload form
│   ├── event_dashboard.html # Event dashboard
│   ├── 404.html          # 404 error page
│   ├── 500.html          # 500 error page
│   └── email/
│       └── ticket_email.html # Email template
├── static/
│   └── css/
│       └── style.css     # Custom CSS
└── uploads/              # CSV file uploads directory
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- VS Code (recommended)
- Git (optional)

### 2. Installation

1. **Clone or download the project to your workspace:**
   ```bash
   cd d:\Harun\Azure_Developer_Community\event-ticketing-app
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configuration

1. **Copy the environment file:**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` file with your settings:**
   ```
   SECRET_KEY=your-super-secret-key-here
   DATABASE_URL=sqlite:///event_ticketing.db
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

### 4. Email Setup (Gmail Example)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password:**
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in `.env` file

### 5. Running the Application

1. **Initialize the database (first time only):**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Open in browser:**
   ```
   http://localhost:5000
   ```

### 6. VS Code Setup

1. **Open the project in VS Code:**
   ```bash
   code .
   ```

2. **Install recommended extensions:**
   - Python
   - Flask
   - HTML CSS Support
   - Bootstrap 5 Quick Snippets

3. **Configure Python interpreter:**
   - Press `Ctrl+Shift+P`
   - Type "Python: Select Interpreter"
   - Select the virtual environment interpreter

## Usage Guide

### Creating an Event

1. Navigate to the home page
2. Click "Create New Event"
3. Fill in event details (name, date, description)
4. Click "Create Event"

### Adding Participants

1. After creating an event, you'll be redirected to upload participants
2. Prepare a CSV file with columns: `name`, `email`
3. Upload the CSV file
4. Participants will be automatically added and emailed their tickets

### Managing Attendance

1. Go to the event dashboard
2. View all participants and their status
3. Click "Check In" or "Check Out" to update attendance
4. Export attendance report as needed

### CSV Format Example

```csv
name,email
John Doe,john@example.com
Jane Smith,jane@example.com
Bob Johnson,bob@example.com
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page with events list |
| GET/POST | `/create_event` | Create new event |
| GET/POST | `/upload_participants/<event_id>` | Upload participants CSV |
| GET | `/event/<event_id>/dashboard` | Event dashboard |
| POST | `/participant/<participant_id>/checkin` | Toggle check-in status |
| GET | `/event/<event_id>/export` | Export attendance CSV |
| GET | `/send_emails/<event_id>` | Send bulk emails |

## Database Schema

### Events Table
- `id` (Primary Key)
- `name` (String, required)
- `date` (Date, required)
- `description` (Text, optional)
- `created_at` (DateTime)

### Participants Table
- `id` (Primary Key)
- `event_id` (Foreign Key)
- `name` (String, required)
- `email` (String, required)
- `ticket_number` (String, unique)
- `checked_in` (Boolean, default False)
- `checkin_time` (DateTime, nullable)
- `created_at` (DateTime)

## Troubleshooting

### Email Issues
- Verify SMTP settings in `.env`
- Check app password for Gmail
- Ensure firewall allows SMTP connections

### Database Issues
- Delete `event_ticketing.db` and restart app to reset database
- Check file permissions in the project directory

### CSV Upload Issues
- Ensure CSV has required columns: `name`, `email`
- Check file encoding (UTF-8 recommended)
- Maximum file size: 16MB

## Production Deployment

For production deployment:

1. Change `SECRET_KEY` to a secure random value
2. Use a production database (PostgreSQL recommended)
3. Configure a production SMTP service
4. Set `debug=False` in `app.py`
5. Use a production WSGI server (Gunicorn, uWSGI)

## License

This project is open source and available under the MIT License.

## Support

For issues or questions, please create an issue in the project repository.