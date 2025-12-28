import os
import ssl
import certifi
import httpx
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, flash
)
from dotenv import load_dotenv
from groq import Groq

# ==========================================
# 1. THE "MONKEY PATCH" (BYPASS HPE PROXY)
# ==========================================
original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs['verify'] = False
    original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

os.environ["SSL_CERT_FILE"] = certifi.where()
load_dotenv()

# ==========================================
# 2. FLASK & GROQ CONFIG
# ==========================================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_fallback_secret")

GROQ_KEY = os.getenv("GROQ_API_KEY")
MY_PHONE = os.getenv("MY_PHONE", "6202736628")

client = Groq(api_key=GROQ_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUBSCRIBERS_FILE = os.path.join(BASE_DIR, "subscribers.txt")

# ==========================================
# 3. ELIA'S REFINED KNOWLEDGE BASE
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
    f"Projects: Portfolio Site, CRUD Blog App, and Python Automation. "
    f"Hobbies: Cricket, Astronomy, and 'vibe coding'. "
    f"Contact: Email: ijajhussain6202@gmail.com, Phone: {MY_PHONE}. "

    "--- RULES --- "
    "1. ANSWER THE QUESTION DIRECTLY. Do not start every response with 'I am Elia'. "
    "2. Only introduce yourself as Elia if the user specifically asks 'Who are you?' or greets you for the first time. "
    "3. Keep responses professional, friendly, and concise. "
    "4. If asked for a resume, direct them to the 'Resume' page. "
    "5. Do not repeat your introduction once the conversation has started."
)

# ==========================================
# 4. AI CHAT ENDPOINT
# ==========================================
@app.route("/get_response", methods=["POST"])
def get_response():
    try:
        data = request.get_json(force=True)
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"response": "I'm listening! How can I help you today?"})

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
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
# 5. STANDARD ROUTES
# ==========================================
@app.route("/")
def home(): return render_template("home.html", title="Home")

@app.route("/about")
def about(): return render_template("about.html", title="About Me")

@app.route("/resume")
def resume(): return render_template("resume.html", title="Resume")

@app.route("/blog/")
def blog():
    posts = [
        {"id": 1, "title": "My Path to System Analyst", "category": "Career"},
        {"id": 2, "title": "Flask and AI Integration", "category": "Web Dev"}
    ]
    return render_template("blog.html", posts=posts, title="Blog")

@app.route("/contact")
def contact(): return render_template("contact.html", title="Contact")

# ==========================================
# 6. SUBSCRIBE & ADMIN
# ==========================================
@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email")
    if email:
        with open(SUBSCRIBERS_FILE, "a", encoding="utf-8") as f:
            f.write(email.strip() + "\n")
    return render_template("thankyou.html", title="Subscribed")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "ijaj6202":
            session["logged_in"] = True
            return redirect(url_for("view_subscribers"))
        flash("Invalid credentials!")
    return render_template("login.html", title="Admin Login")

@app.route("/admin/view-subscribers")
def view_subscribers():
    if not session.get("logged_in"): return redirect(url_for("login"))
    emails = []
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
            emails = [e.strip() for e in f if e.strip()]
    return render_template("admin.html", emails=emails, title="Admin Panel")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)