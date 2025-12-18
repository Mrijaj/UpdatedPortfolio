from flask import Flask, render_template, abort, request, jsonify, session, redirect, url_for, flash
import json
import random
import string
import os

app = Flask(__name__)
app.secret_key = "my_super_secret_key_change_this"

# 1. UPDATED DATA (Added 'category' field)
POSTS = [
    {
        'id': 1,
        'title': 'Starting My Web Development Journey',
        'date': 'December 16, 2025',
        'category': 'Web Dev',  # <--- NEW
        'content': 'Today I started building my portfolio using Flask...'
    },
    {
        'id': 2,
        'title': 'Why I Chose Python',
        'date': 'December 12, 2025',
        'category': 'Python',  # <--- NEW
        'content': 'Python is known for its readability and vast ecosystem...'
    }
]


# ... (Routes for home, about, resume remain the same) ...
@app.route('/')
def home(): return render_template('home.html', title="Home")


@app.route('/about')
def about(): return render_template('about.html', title="About Me")


@app.route('/resume')
def resume(): return render_template('resume.html', title="Resume")


# 2. UPDATED BLOG ROUTE (Handles Filtering)
@app.route('/blog/')
def blog():
    # Check if a category was clicked
    category_filter = request.args.get('category')

    if category_filter:
        # Filter the posts list
        filtered_posts = [p for p in POSTS if p.get('category') == category_filter]
    else:
        # Show all posts
        filtered_posts = POSTS

    return render_template('blog.html', posts=filtered_posts)


# ... (Keep all your other routes: articles, contact, subscribe, admin, chat) ...
# (I am abbreviating here to save space, but keep the rest of your app.py the same!)

@app.route('/article/how-i-built-this')
def article_1(): return render_template('article_1.html', title="How I Built This")


@app.route('/article/why-python')
def article_2(): return render_template('article_2.html', title="Why I Chose Python")


@app.route('/post/<int:post_id>')
def post(post_id):
    post = next((p for p in POSTS if p['id'] == post_id), None)
    if post is None: abort(404)
    return render_template('post_detail.html', post=post)


@app.route('/contact')
def contact(): return render_template('contact.html', title="Contact")


@app.route('/thank-you')
def thank_you(): return render_template('thankyou.html', title="Message Sent")


@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    with open('subscribers.txt', 'a') as file: file.write(f"{email}\n")
    return render_template('thankyou.html', title="Subscribed!")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "ijaj6202":
            session['logged_in'] = True
            return redirect(url_for('view_subscribers'))
        else:
            flash("Invalid Username or Password!")
    return render_template('login.html', title="Admin Login")


@app.route('/admin/view-subscribers')
def view_subscribers():
    if not session.get('logged_in'): return redirect(url_for('login'))
    emails = []
    if os.path.exists('subscribers.txt'):
        with open('subscribers.txt', 'r') as file: emails = file.readlines()
    return render_template('admin.html', emails=emails, title="Admin Panel")


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


def load_intents():
    try:
        with open('intents.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"intents": []}


@app.route('/get_response', methods=['POST'])
def get_response():
    raw_input = request.json.get("message", "").lower()
    user_input = raw_input.translate(str.maketrans('', '', string.punctuation))
    user_words = user_input.split()
    data = load_intents()
    for intent in data['intents']:
        for pattern in intent['patterns']:
            pattern_lower = pattern.lower()
            if " " not in pattern_lower:
                if pattern_lower in user_words: return jsonify({"response": random.choice(intent['responses'])})
            else:
                if pattern_lower in user_input: return jsonify({"response": random.choice(intent['responses'])})
    return jsonify({"response": "Sorry, I am trained to answer questions related to this website only."})


if __name__ == '__main__':
    app.run(debug=True)