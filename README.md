Dynamic Personal Portfolio & AI Assistant
A full-stack, serverless-ready personal portfolio and blog website built with Python and Flask. This project showcases professional experience, hosts technical blog articles, and features Elia, a custom AI assistant powered by the Groq Llama-3 API.

Designed for robust deployment, it includes seamless Google OAuth integration, secure email-based OTP verification, and a dual-database architecture (SQLite for local development, PostgreSQL via Aiven for production).

✨ Key Features
Custom AI Assistant (Elia): Context-aware chatbot utilizing the Groq API (llama-3.1-8b-instant) to answer professional inquiries and assist visitors in real-time.

Secure Authentication System:

Traditional username/password login with Werkzeug security hashing.

Google Workspace OAuth 2.0 integration.

Time-sensitive Email OTP verification using Flask-Mail and Brevo SMTP.

Dynamic Blog & Content: Filterable blog system with detailed article routing.

Live GitHub Telemetry: Pulls real-time repository metrics (stars, forks, open issues) directly from GitHub's API to display project statistics.

Adaptive Database Routing: Automatically detects the environment. Routes to a local SQLite cluster for development and an external PostgreSQL cloud database when deployed to Vercel.

Corporate Proxy Bypass: Custom httpx monkey-patching to allow seamless API connections and SSL verification bypass when developing behind strict corporate network firewalls.

🛠️ Technology Stack
Backend: Python 3.12, Flask, Flask-SQLAlchemy

Database: PostgreSQL (Aiven Cloud), SQLite3 (Local)

AI Integration: Groq Cloud API

Authentication: Google Auth (google-auth, id_token)

Email Gateway: Flask-Mail, Brevo SMTP

Deployment: Vercel (Serverless Functions)

📋 Prerequisites
To run this project locally, ensure you have the following installed:

Python 3.9+

Git

You will also need active API keys for:

Groq Cloud (For the AI Assistant)

Google Cloud Console (For OAuth 2.0 Client ID)

Brevo / Sendinblue (For SMTP relay)

🚀 Local Setup & Installation
1. Clone the repository

Bash
git clone https://github.com/Mrijaj/UpdatedPortfolio.git
cd UpdatedPortfolio
2. Create and activate a virtual environment

Bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
3. Install dependencies

Bash
pip install -r requirements.txt
4. Configure Environment Variables
Create a .env file in the root directory and add the following parameters:

Ini, TOML
# Flask Security
FLASK_SECRET_KEY=your_secure_random_key

# Database (Leave blank locally to default to SQLite)
DATABASE_URL=

# Groq AI
GROQ_API_KEY=your_groq_api_key

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com

# Email Transport (Brevo)
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USERNAME=your_brevo_smtp_login
MAIL_PASSWORD=your_brevo_smtp_password
MAIL_DEFAULT_SENDER=your_verified_sender_email@gmail.com

# Local Environment Overrides
MY_PHONE=your_phone_number
BYPASS_PROXY_SSL=true # Set to 'true' if developing behind a strict corporate proxy
5. Initialize the Database and Run the Application
Because database initialization is decoupled from the root application context for Vercel, run the following commands in your Python terminal to build the local SQLite tables for the first time:

Python
from app import app, db
with app.app_context():
    db.create_all()
Then, start the server:

Bash
python app.py
The application will be live at [http://127.0.0.1:5000](http://127.0.0.1:5000)

☁️ Deployment (Vercel)
This application is highly optimized for Vercel's serverless environment.

Ensure your requirements.txt is encoded in pure UTF-8.

Connect your GitHub repository to Vercel.

In the Vercel Project Settings, add all the environment variables listed in the .env section above.

Set the DATABASE_URL to your production Aiven PostgreSQL connection URI (ensure it ends with ?sslmode=require).

Vercel will automatically build the environment and route external storage appropriately without trying to execute DDL queries during the build phase.
