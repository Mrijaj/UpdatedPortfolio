import os
import ssl
import certifi
import httpx
import random
import datetime
import re
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from groq import Groq
from flask_mail import Mail, Message
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# ==========================================
# 0. LOAD ENVIRONMENT VARIABLES FIRST
# ==========================================
# This must happen before ANY os.getenv() checks!
load_dotenv(override=True)
os.environ["SSL_CERT_FILE"] = certifi.where()

# ==========================================
# 1. THE "MONKEY PATCH" (BYPASS HPE PROXY)
# ==========================================
# SECURED: Only runs if explicitly enabled via local .env file
if os.getenv("BYPASS_PROXY_SSL") == "true":
    original_client_init = httpx.Client.__init__


    def patched_client_init(self, *args, **kwargs):
        kwargs['verify'] = False
        original_client_init(self, *args, **kwargs)


    httpx.Client.__init__ = patched_client_init

    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except AttributeError:
        pass

# ==========================================
# 2. FLASK & DATABASE CONFIGURATION
# ==========================================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_fallback_secret")

# Automated Environment Gatekeeper (Vercel Ready & Local Safe)
# If we are locally bypassing the proxy, FORCE the local SQLite database.
if os.getenv("BYPASS_PROXY_SSL") == "true":
    database_url = 'sqlite:///portfolio.db'
    print("🚀 [SYSTEM] Local environment detected. Routing to local SQLite cluster.")
else:
    # If not local, look for the production cloud database (Vercel)
    database_url = os.environ.get('DATABASE_URL')

    # Fallback just in case Vercel is missing the variable
    if not database_url:
        database_url = 'sqlite:///portfolio.db'
        print("⚠️ [WARNING] No cloud DATABASE_URL found in production. Falling back to ephemeral SQLite.")
    else:
        # SQLAlchemy 1.4+ requires 'postgresql://' instead of 'postgres://'
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        print("☁️ [SYSTEM] Cloud database detected. Routing to external persistent storage.")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mount Mail Config to Flask Instance Layer
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp-relay.brevo.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'ijaz04186@gmail.com')

db = SQLAlchemy(app)
mail = Mail(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    google_id = db.Column(db.String(200), unique=True, nullable=True)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)


# ==========================================
# 3. GROQ / ELIA CONFIGURATION
# ==========================================
GROQ_KEY = os.getenv("GROQ_API_KEY")
MY_PHONE = os.getenv("MY_PHONE", "6202736628")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

client = Groq(api_key=GROQ_KEY)

if os.getenv("VERCEL"):
    SUBSCRIBERS_FILE = "/tmp/subscribers.txt"
else:
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)
    SUBSCRIBERS_FILE = os.path.join(app.instance_path, "subscribers.txt")

# ==========================================
# 4. ELIA'S REFINED KNOWLEDGE BASE
# ==========================================
SYSTEM_INSTRUCTIONS = (
    "You are Elia, the professional AI assistant for Ijaj Hussain. "
    "Your goal is to provide direct and helpful answers based on the following facts: "
    f"--- KNOWLEDGE --- "
    f"Owner: Ijaj Hussain (26 years old). "
    f"Current Role: System Analyst at Hewlett Packard Enterprise (HPE). "
    f"Experience: 2 years in Tech Support, Automation, and System Analysis. "
    f"Location: Pune, India (Hometown: Jamshedpur). "
    f"Education: B.Tech in Computer Engineering from G.H Raisoni College (2023). "
    f"High School: H.S.C from Dayanand Public School (2019). "
    f"Skills: Python, Flask, SQL, ETL Pipelines, Data Analysis, and DBA. "
    f"Hobbies: Cricket, Astronomy, and 'vibe coding'. "
    f"Contact: Email: ijajhussain6202@gmail.com, Phone: {MY_PHONE}. "
    "--- RULES --- "
    "1. ANSWER THE QUESTION DIRECTLY. 2. Keep responses professional, friendly, and concise."
)


# ==========================================
# 5. AI CHAT ENDPOINT (WITH DYNAMIC IDENTITY)
# ==========================================
@app.route("/get_response", methods=["POST"])
def get_response():
    try:
        data = request.get_json(force=True)
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"response": "I'm listening! How can I help you today?"})

        # Inject session awareness into system instructions dynamically
        active_instructions = SYSTEM_INSTRUCTIONS
        if session.get("logged_in") and session.get("user"):
            active_instructions += f" The current authenticated user chatting with you is named '{session.get('user')}'. Address them by their name warmly when appropriate."

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": active_instructions},
                {"role": "user", "content": user_message}
            ],
            temperature=0.6,
            max_tokens=500
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return jsonify({"response": "⚠️ Elia is reconnecting. Please try again!"})


# ==========================================
# 6. CONNECTED ROUTES
# ==========================================
@app.route("/")
def home():
    return render_template("home.html", title="Home")


@app.route("/about")
def about():
    return render_template("about.html", title="About Me")


@app.route("/resume")
def resume():
    links = {
        "college": "https://ghrcem.raisoni.net/",
        "school": "https://www.dayanandpublicschool.edu.in/",
        "company": "https://www.hpe.com/"
    }
    return render_template("resume.html", title="Resume", links=links)


@app.route("/blog/")
def blog():
    category = request.args.get('category')
    all_posts = [
        {
            "id": 1,
            "title": "My Path to System Analyst",
            "date": "Dec 28, 2025",
            "category": "Career",
            "content": "A detailed look at my journey into technical system analysis at HPE."
        },
        {
            "id": 2,
            "title": "Flask and AI Integration",
            "date": "Dec 25, 2025",
            "category": "Web Dev",
            "content": "Exploring how to combine Flask with the Groq Llama 3 API."
        }
    ]
    posts = [p for p in all_posts if not category or p['category'] == category]
    return render_template("blog.html", posts=posts, title="Blog")


@app.route("/blog/article-1")
def article_1():
    return render_template("article_1.html", title="My Path to System Analyst")


@app.route("/blog/article-2")
def article_2():
    return render_template("article_2.html", title="Flask and AI Integration")


@app.route("/blog/post/<int:post_id>")
def post(post_id):
    return render_template("post_detail.html", post_id=post_id)


@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact")


# ==========================================
# 7. SUBSCRIBE & AUTHENTICATION
# ==========================================
@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip()
    if email:
        try:
            with open(SUBSCRIBERS_FILE, "a+", encoding="utf-8") as f:
                f.write(email + "\n")
            return redirect(url_for('thank_you'))
        except Exception as e:
            print(f"❌ Subscription Error: {e}")
            return redirect(url_for('home'))
    return redirect(url_for('home'))


@app.route("/thank-you")
def thank_you():
    return render_template("thankyou.html", title="Subscribed")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for("register"))

        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash("Username or Email already registered.", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Welcome to Ijaj portfolio website, login to continue.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", title="Sign up to continue", google_client_id=GOOGLE_CLIENT_ID)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and user.password_hash and check_password_hash(user.password_hash, password):
            session.clear()  # Session Fixation Guard
            session["logged_in"] = True
            session["user_id"] = user.id
            session["user"] = user.username
            flash("Authorization successful. Welcome back.", "success")
            return redirect(url_for("view_subscribers"))
        else:
            flash("Invalid credentials. Access denied.", "error")

    return render_template("login.html", title="Login to continue", google_client_id=GOOGLE_CLIENT_ID)


# --- OTP LOGIC ---
@app.route("/request-otp", methods=["POST"])
def request_otp():
    email = request.form.get("email", "").strip()
    user = User.query.filter_by(email=email).first()

    if user:
        otp = str(random.randint(100000, 999999))
        user.otp_code = otp
        user.otp_expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)
        db.session.commit()

        try:
            msg = Message(
                subject="Your Portfolio Account Security Key",
                recipients=[email],
                body=f"Hello,\n\nYour one-time access verification key is: {otp}\n\nThis token will expire in exactly 10 minutes for security purposes."
            )
            mail.send(msg)
            flash("OTP security token dispatched to your email address.", "success")
        except Exception as e:
            print(f"❌ Real-time Mail Transport Failure: {e}")
            flash("System infrastructure timed out during dispatch. Check terminal.", "error")

        return render_template("verify_otp.html", email=email)

    flash("Email endpoint configuration mismatch. Node not found.", "error")
    return redirect(url_for("login"))


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    email = request.form.get("email", "").strip()
    code = request.form.get("otp", "").strip()

    user = User.query.filter_by(email=email, otp_code=code).first()

    if user and user.otp_expiry and user.otp_expiry.replace(tzinfo=datetime.timezone.utc) > datetime.datetime.now(
            datetime.timezone.utc):
        session.clear()
        session["logged_in"] = True
        session["user_id"] = user.id
        session["user"] = user.username
        user.otp_code = None
        db.session.commit()
        return redirect(url_for("view_subscribers"))

    flash("Invalid or expired OTP. Please check your code and try again.", "error")
    return render_template("verify_otp.html", email=email)


# --- GOOGLE SIGN-IN ENDPOINT & MULTI-STEP ONBOARDING ---
@app.route("/google-login", methods=["POST"])
def google_login():
    try:
        token = request.json.get('token')

        class ResilientTransport(object):
            def __call__(self, url, method="GET", body=None, headers=None, timeout=None):
                response = httpx.request(method, url, content=body, headers=headers, verify=False)

                class MockResponse:
                    def __init__(self, res):
                        self.status = res.status_code
                        self.headers = dict(res.headers)
                        self.data = res.content

                return MockResponse(response)

        id_info = id_token.verify_oauth2_token(
            token,
            ResilientTransport(),
            GOOGLE_CLIENT_ID
        )

        google_email = id_info.get('email')
        google_id = id_info.get('sub')
        default_name = id_info.get('name', '')

        user = User.query.filter_by(google_id=google_id).first()

        if user:
            session.clear()
            session["logged_in"] = True
            session["user_id"] = user.id
            session["user"] = user.username
            return jsonify({"status": "success"})

        session["temp_oauth_email"] = google_email
        session["temp_oauth_id"] = google_id
        session["temp_oauth_name"] = default_name

        return jsonify({"status": "profile_incomplete"})

    except Exception as e:
        print(f"❌ Detailed Google Auth Failure: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/complete-profile")
def complete_profile():
    if "temp_oauth_email" not in session:
        flash("Authorization state invalid. Please restart login.", "error")
        return redirect(url_for('login'))
    return render_template("complete_profile.html", title="Profile Setup", email=session["temp_oauth_email"])


@app.route("/submit-profile-details", methods=["POST"])
def submit_profile_details():
    if "temp_oauth_email" not in session:
        return redirect(url_for('login'))

    session["temp_username"] = request.form.get("username", "").strip()
    phone_input = request.form.get("phone", "").strip()

    if not re.match(r'^[6-9]\d{9}$', phone_input):
        flash("System rejected input. Please enter a genuine 10-digit Indian mobile number.", "error")
        return render_template("complete_profile.html", title="Profile Setup", email=session["temp_oauth_email"])

    session["temp_phone"] = phone_input

    otp = str(random.randint(100000, 999999))
    session["temp_otp_code"] = otp
    session["temp_otp_expiry"] = (
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)).isoformat()

    try:
        msg = Message(
            subject="Confirm Your Identity - Verification Token",
            recipients=[session["temp_oauth_email"]],
            body=f"Hello {session['temp_username']},\n\nUse this security token to complete your signup: {otp}\n\nValid for 10 minutes."
        )
        mail.send(msg)
        flash("Security token dispatched to your Google Email endpoint.", "success")
    except Exception as e:
        print(f"❌ Brevo Handshake Failure: {e}")
        flash("Transactional communication gateway timeout.", "error")

    return render_template("verify_otp.html", email=session["temp_oauth_email"])


@app.route("/verify-google-otp", methods=["POST"])
def verify_google_otp():
    input_code = request.form.get("otp", "").strip()

    if "temp_otp_code" not in session:
        flash("Session validation timeout. Please restart.", "error")
        return redirect(url_for('login'))

    stored_expiry = datetime.datetime.fromisoformat(session["temp_otp_expiry"])

    if input_code == session["temp_otp_code"] and datetime.datetime.now(datetime.timezone.utc) < stored_expiry:

        # --- NEW SAFETY NET: Check for duplicate username before adding ---
        existing_user = User.query.filter_by(username=session["temp_username"]).first()
        if existing_user:
            flash(f"The username '{session['temp_username']}' is already taken. Please restart and choose another.",
                  "error")
            session.clear()
            return redirect(url_for('login'))

        new_user = User(
            username=session["temp_username"],
            email=session["temp_oauth_email"],
            phone=session["temp_phone"],
            google_id=session["temp_oauth_id"],
            password_hash=None
        )

        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database Commit Error: {e}")
            flash("System failed to commit user identity. Please try again.", "error")
            session.clear()
            return redirect(url_for('login'))

        session.clear()
        session["logged_in"] = True
        session["user_id"] = new_user.id
        session["user"] = new_user.username

        flash("Account provisioned successfully via Google! Welcome back.", "success")
        return redirect(url_for('view_subscribers'))

    flash("Invalid or expired verification credentials.", "error")
    return render_template("verify_otp.html", email=session.get("temp_oauth_email"))


# --- GITHUB TELEMETRY PIPELINE PIPED FROM REAL REPO ---
@app.route("/api/github-blog-metrics")
def github_blog_metrics():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    repo_owner = "Mrijaj"
    repo_name = "Blog-Website"

    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = httpx.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}", headers=headers, verify=False)

        if response.status_code == 200:
            repo_data = response.json()
            return jsonify({
                "status": "ONLINE",
                "name": repo_data.get("name"),
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "language": repo_data.get("language", "Python"),
                "last_updated": repo_data.get("updated_at", "").split("T")[0],
                "open_issues": repo_data.get("open_issues_count", 0),
                "repo_url": repo_data.get("html_url")
            })
        return jsonify({"status": "OFFLINE", "reason": "Repository inaccessible"}), response.status_code
    except Exception as e:
        print(f"❌ GitHub Sync Error: {e}")
        return jsonify({"status": "OFFLINE", "error": str(e)}), 500


@app.route("/admin/view-subscribers")
def view_subscribers():
    if not session.get("logged_in"):
        flash("Authorization required. Please login to continue.", "error")
        return redirect(url_for("login"))

    try:
        registered_users = User.query.all()
    except Exception as e:
        print(f"❌ Database Query Error: {e}")
        registered_users = []
        flash("System Error: Unable to retrieve user registry.", "error")

    return render_template("admin.html", users=registered_users, title="System Dashboard")


# --- USER PROFILE & SETTINGS ---
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not session.get("logged_in"):
        flash("Authorization required. Please login to access settings.", "error")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])

    if request.method == "POST":
        action = request.form.get("action")

        # Profile Data Update
        if action == "update_profile":
            new_username = request.form.get("username", "").strip()
            new_phone = request.form.get("phone", "").strip()

            # Update Username (with collision check)
            if new_username and new_username != user.username:
                existing = User.query.filter_by(username=new_username).first()
                if existing:
                    flash("Username is already reserved by another user.", "error")
                    return redirect(url_for("settings"))
                user.username = new_username
                session["user"] = new_username  # Sync active session state

            # Update Phone (with Regex standard check)
            if new_phone and new_phone != str(user.phone):
                if not re.match(r'^[6-9]\d{9}$', new_phone):
                    flash("System rejected input. Enter a genuine 10-digit Indian mobile number.", "error")
                    return redirect(url_for("settings"))
                user.phone = new_phone

            db.session.commit()
            flash("Profile parameters synchronized successfully.", "success")
            return redirect(url_for("settings"))

    return render_template("settings.html", user=user, title="System Settings")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been securely signed out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)