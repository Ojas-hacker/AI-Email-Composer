# AI Email Composer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-000000.svg?logo=flask)](https://flask.palletsprojects.com/)
[![Gemini](https://img.shields.io/badge/Gemini-AI-4285F4?logo=google)](https://ai.google.dev/)

AI Email Composer is a powerful web application that leverages Google's Gemini AI to help you craft personalized, professional emails with ease. The application allows you to manage recipients, store company information, and generate contextually appropriate emails for various purposes.

## ✨ Features

- **AI-Powered Email Generation**: Generate professional emails using Google's Gemini AI
- **Recipient Management**: Store and manage recipient information including name, email, company, and position
- **Company Profiles**: Maintain detailed company information for personalized email content
- **Email History**: Track all generated emails with timestamps and details
- **Responsive Design**: Clean, modern interface that works on desktop and mobile devices
- **Database Integration**: SQLite database for data persistence

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ojas-hacker/AI-Email-Composer.git
   cd ai-email-composer
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     FLASK_SECRET_KEY=your_secret_key_here
     ```

5. **Initialize the database**
   The database will be created automatically when you first run the application.

### Running the Application

```bash
python app.py
```

Open your web browser and navigate to `http://localhost:5000`

## 🛠️ Usage

1. **Add Recipients**: Go to the Recipients section and add the people you want to email
2. **Set Up Company Information**: Add your company details in the Company Data section
3. **Compose Emails**: Use the Compose Email section to generate personalized emails
4. **View History**: Check the Email History section to see all generated emails

## 📁 Project Structure

```
ai-email-composer/
├── app.py                # Main application file
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment variables
├── email_composer.db     # SQLite database (created on first run)
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── company_data.html # Company information form
    ├── edit_recipient.html # Edit recipient form
    ├── email_history.html # Email history view
    ├── index.html        # Main dashboard
    └── recipient_history.html # Recipient-specific email history
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - The web framework used
- [Google Gemini AI](https://ai.google.dev/) - For the AI capabilities
- [SQLite](https://www.sqlite.org/) - For database storage

## 📧 Contact

Ojas Kawalkar - [@ojaskawalkar](https://instagram.com/ojaskawalkar) - rjkojas@gmail.com
