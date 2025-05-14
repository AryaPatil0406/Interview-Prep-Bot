# app.py - Main Flask Application

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import os
import json
import random
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)
CORS(app)

# Database configuration
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'chatbot')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'aryu')
DB_PORT = os.environ.get('DB_PORT', '5432')

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    conn.autocommit = True
    return conn

# Create tables if they don't exist
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Users table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Interview categories
    cur.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL,
        description TEXT
    )
    ''')
    
    # Questions table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
        question_text TEXT NOT NULL,
        difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
        sample_answer TEXT
    )
    ''')
    
    # User interview sessions
    cur.execute('''
    CREATE TABLE IF NOT EXISTS interview_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        score INTEGER
    )
    ''')
    
    # User answers
    cur.execute('''
    CREATE TABLE IF NOT EXISTS user_answers (
        id SERIAL PRIMARY KEY,
        session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
        question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
        user_answer TEXT,
        rating INTEGER CHECK (rating BETWEEN 1 AND 5),
        feedback TEXT
    )
    ''')
    
    # Seed some initial data if tables are empty
    cur.execute('SELECT COUNT(*) FROM categories')
    if cur.fetchone()[0] == 0:
        # Insert default categories
        categories = [
            ('Software Engineering', 'Technical questions for software developers'),
            ('Data Science', 'Questions related to data analysis, machine learning, and statistics'),
            ('Product Management', 'Questions for product managers'),
            ('Behavioral', 'Common behavioral interview questions'),
            ('System Design', 'System design and architecture questions')
        ]
        
        for category in categories:
            cur.execute('INSERT INTO categories (name, description) VALUES (%s, %s)', category)
            
        # Add some sample questions
        questions = [
            # Software Engineering
            (1, 'What is the difference between a stack and a queue?', 'medium', 'A stack follows Last-In-First-Out (LIFO) principle where elements are added and removed from the same end, while a queue follows First-In-First-Out (FIFO) where elements are added at one end and removed from the other.'),
            (1, 'Explain the concept of recursion with an example.', 'medium', 'Recursion is when a function calls itself to solve a smaller instance of the same problem. A classic example is calculating factorial: factorial(n) = n * factorial(n-1), with factorial(0) = 1 as the base case.'),
            (1, 'What is time complexity and why is it important?', 'easy', 'Time complexity measures how the runtime of an algorithm grows as the input size increases. It\'s important because it helps us predict the performance and scalability of our code.'),
            
            # Data Science
            (2, 'Explain the difference between supervised and unsupervised learning.', 'easy', 'Supervised learning uses labeled data where the algorithm learns to predict outputs based on input features. Unsupervised learning works with unlabeled data to find patterns or structures without predefined outputs.'),
            (2, 'What is overfitting and how can you prevent it?', 'medium', 'Overfitting occurs when a model learns the training data too well, including its noise and outliers, performing poorly on new data. Prevention methods include cross-validation, regularization, early stopping, and using more training data.'),
            
            # Product Management
            (3, 'How would you prioritize features for a new product?', 'medium', 'I would prioritize features using frameworks like RICE (Reach, Impact, Confidence, Effort) or MoSCoW (Must-have, Should-have, Could-have, Won\'t-have). I\'d consider factors like business goals, user needs, technical feasibility, and available resources.'),
            
            # Behavioral
            (4, 'Tell me about a time you faced a difficult challenge at work.', 'medium', 'When answering, use the STAR method: Situation, Task, Action, Result. Describe a specific situation, the task required, actions you took, and positive results achieved.'),
            (4, 'How do you handle conflict with team members?', 'medium', 'I address conflicts directly but respectfully. I focus on understanding the other person\'s perspective, clearly communicating my own, and working together to find a solution that addresses both parties\' concerns.'),
            
            # System Design
            (5, 'How would you design a URL shortening service like bit.ly?', 'hard', 'I would design a system with: 1) A hashing function to create short URLs, 2) A database to store mappings between short and long URLs, 3) An API service to handle URL creation and redirection, 4) A caching layer for frequently accessed URLs, and 5) Analytics tracking for URL usage.')
        ]
        
        for question in questions:
            cur.execute('INSERT INTO questions (category_id, question_text, difficulty, sample_answer) VALUES (%s, %s, %s, %s)', question)
    
    conn.commit()
    cur.close()
    conn.close()

# Initialize database on startup
init_db()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'error': 'All fields are required'}), 400
    
    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id',
            (username, email, password_hash)
        )
        user_id = cur.fetchone()[0]
        
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({'success': True, 'user_id': user_id, 'username': username}), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'Username or email already exists'}), 409
    finally:
        cur.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({'error': 'Username and password are required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute('SELECT id, username, password_hash FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True, 'user_id': user['id'], 'username': user['username']}), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
    finally:
        cur.close()
        conn.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True}), 200

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute('SELECT * FROM categories ORDER BY name')
        categories = cur.fetchall()
        return jsonify(categories), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/questions', methods=['GET'])
def get_questions():
    category_id = request.args.get('category_id')
    difficulty = request.args.get('difficulty')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = 'SELECT q.*, c.name as category_name FROM questions q JOIN categories c ON q.category_id = c.id WHERE 1=1'
    params = []
    
    if category_id:
        query += ' AND q.category_id = %s'
        params.append(category_id)
        
    if difficulty:
        query += ' AND q.difficulty = %s'
        params.append(difficulty)
    
    try:
        cur.execute(query, params)
        questions = cur.fetchall()
        return jsonify(questions), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/start-interview', methods=['POST'])
def start_interview():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
        
    data = request.get_json()
    category_id = data.get('category_id')
    difficulty = data.get('difficulty', None)
    question_count = data.get('question_count', 5)
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Create interview session
        cur.execute(
            'INSERT INTO interview_sessions (user_id, category_id) VALUES (%s, %s) RETURNING id',
            (session['user_id'], category_id)
        )
        session_id = cur.fetchone()['id']
        
        # Get questions for this interview
        query = 'SELECT * FROM questions WHERE category_id = %s'
        params = [category_id]
        
        if difficulty:
            query += ' AND difficulty = %s'
            params.append(difficulty)
            
        query += ' ORDER BY RANDOM() LIMIT %s'
        params.append(question_count)
        
        cur.execute(query, params)
        questions = cur.fetchall()
        
        interview_data = {
            'session_id': session_id,
            'questions': questions
        }
        
        return jsonify(interview_data), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
        
    data = request.get_json()
    session_id = data.get('session_id')
    question_id = data.get('question_id')
    user_answer = data.get('user_answer')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check if this session belongs to the logged-in user
        cur.execute(
            'SELECT user_id FROM interview_sessions WHERE id = %s',
            (session_id,)
        )
        result = cur.fetchone()
        if not result or result['user_id'] != session['user_id']:
            return jsonify({'error': 'Unauthorized access to this session'}), 403
            
        # Get the question details
        cur.execute('SELECT * FROM questions WHERE id = %s', (question_id,))
        question = cur.fetchone()
        
        # Simple automatic rating based on keyword matching
        # In a real system, this could use AI/NLP to provide better feedback
        rating = 3  # Default medium rating
        feedback = "Your answer is acceptable. "
        
        if question:
            sample_answer = question['sample_answer'].lower()
            user_answer_lower = user_answer.lower()
            
            # Very simple keyword matching (this would be more sophisticated in a real app)
            keywords = sample_answer.split()[:10]  # First 10 words as keywords
            matches = sum(1 for keyword in keywords if keyword.lower() in user_answer_lower)
            
            if len(user_answer_lower.split()) < 20:
                rating = 2
                feedback += "Your answer is too brief. Try to elaborate more."
            elif matches > len(keywords) * 0.7:
                rating = 5
                feedback += "Excellent answer that covers key points."
            elif matches > len(keywords) * 0.5:
                rating = 4
                feedback += "Good answer with most important concepts."
            elif matches > len(keywords) * 0.3:
                rating = 3
                feedback += "Decent answer but missing some important points."
            else:
                rating = 2
                feedback += "Your answer misses several key concepts."
                
        # Save the user's answer
        cur.execute(
            'INSERT INTO user_answers (session_id, question_id, user_answer, rating, feedback) VALUES (%s, %s, %s, %s, %s)',
            (session_id, question_id, user_answer, rating, feedback)
        )
        
        return jsonify({
            'success': True,
            'rating': rating,
            'feedback': feedback,
            'sample_answer': question['sample_answer'] if question else ""
        }), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/complete-interview', methods=['POST'])
def complete_interview():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
        
    data = request.get_json()
    session_id = data.get('session_id')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check if this session belongs to the logged-in user
        cur.execute(
            'SELECT user_id FROM interview_sessions WHERE id = %s',
            (session_id,)
        )
        result = cur.fetchone()
        if not result or result['user_id'] != session['user_id']:
            return jsonify({'error': 'Unauthorized access to this session'}), 403
            
        # Calculate average score
        cur.execute(
            'SELECT AVG(rating) as avg_score FROM user_answers WHERE session_id = %s',
            (session_id,)
        )
        avg_score = cur.fetchone()['avg_score'] or 0
        score = int(round(avg_score))
        
        # Mark session as completed
        cur.execute(
            'UPDATE interview_sessions SET completed_at = NOW(), score = %s WHERE id = %s',
            (score, session_id)
        )
        
        # Get summary data
        cur.execute('''
            SELECT 
                q.question_text, 
                ua.user_answer, 
                ua.rating, 
                ua.feedback,
                q.sample_answer
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            WHERE ua.session_id = %s
        ''', (session_id,))
        answers = cur.fetchall()
        
        return jsonify({
            'success': True,
            'score': score,
            'answers': answers
        }), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/user/history', methods=['GET'])
def get_user_history():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute('''
            SELECT 
                is.id,
                is.created_at,
                is.completed_at,
                is.score,
                c.name as category_name,
                COUNT(ua.id) as questions_answered
            FROM interview_sessions is
            JOIN categories c ON is.category_id = c.id
            LEFT JOIN user_answers ua ON is.id = ua.session_id
            WHERE is.user_id = %s
            GROUP BY is.id, c.name
            ORDER BY is.created_at DESC
        ''', (session['user_id'],))
        
        history = cur.fetchall()
        return jsonify(history), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/session/<int:session_id>', methods=['GET'])
def get_session_details(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check if this session belongs to the logged-in user
        cur.execute(
            'SELECT user_id FROM interview_sessions WHERE id = %s',
            (session_id,)
        )
        result = cur.fetchone()
        if not result or result['user_id'] != session['user_id']:
            return jsonify({'error': 'Unauthorized access to this session'}), 403
        
        # Get session info
        cur.execute('''
            SELECT 
                is.id,
                is.created_at,
                is.completed_at,
                is.score,
                c.name as category_name
            FROM interview_sessions is
            JOIN categories c ON is.category_id = c.id
            WHERE is.id = %s
        ''', (session_id,))
        
        session_info = cur.fetchone()
        
        # Get answers for this session
        cur.execute('''
            SELECT 
                q.question_text, 
                ua.user_answer, 
                ua.rating, 
                ua.feedback,
                q.sample_answer
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            WHERE ua.session_id = %s
        ''', (session_id,))
        
        answers = cur.fetchall()
        
        return jsonify({
            'session': session_info,
            'answers': answers
        }), 200
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)