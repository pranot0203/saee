import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '5f36a0d8e2b8f9c1d4e7a2b5c8d1e4f7a0b3c6d9e2f5a8b1')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///voting.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prn = db.Column(db.String(13), unique=True, nullable=False) # 13 digit PRN
    name = db.Column(db.String(100))
    mobile = db.Column(db.String(15))
    email = db.Column(db.String(120)) # Added email field
    mother_name = db.Column(db.String(100))
    class_name = db.Column(db.String(50))
    division = db.Column(db.String(10))
    year = db.Column(db.String(20)) # e.g. "2023-2024" or "First Year"
    password = db.Column(db.String(50)) # Only used for Admin
    role = db.Column(db.String(10), default='student') # 'student' or 'admin'
    has_voted = db.Column(db.Boolean, default=False)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50))
    division = db.Column(db.String(10))
    position = db.Column(db.String(100)) # e.g. President, Vice President
    photo_url = db.Column(db.String(200)) # Placeholder for image path
    votes = db.Column(db.Integer, default=0)

class ElectionState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=False)
    is_finished = db.Column(db.Boolean, default=False)
    winner_declared = db.Column(db.Boolean, default=False)

# Initialize DB
def init_db():
    with app.app_context():
        db.create_all()
        # Create Admin if not exists
        if not User.query.filter_by(role='admin').first():
            # Admin uses PRN 'admin' for login
            admin = User(prn='admin', name='Administrator', password='admin123', role='admin')
            db.session.add(admin)
            
        # Create initial election state
        if not ElectionState.query.first():
            state = ElectionState(is_active=False, is_finished=False)
            db.session.add(state)
            
        db.session.commit()

# Ensure DB is initialized before first request
@app.before_request
def create_tables():
    # This ensures tables are created even if not running via 'python app.py'
    # but we should only do it once. Flask-SQLAlchemy handles 'create_all' safely.
    db.create_all()
    # Also check for admin and state inside a context
    if not User.query.filter_by(role='admin').first():
        admin = User(prn='admin', name='Administrator', password='admin123', role='admin')
        db.session.add(admin)
        db.session.commit()
    if not ElectionState.query.first():
        state = ElectionState(is_active=False, is_finished=False)
        db.session.add(state)
        db.session.commit()

# Routes

@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user:
            return redirect(url_for('vote_page'))
    return render_template('index.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        prn = request.form.get('prn')
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        mother_name = request.form.get('mother_name')
        
        user = User.query.filter_by(prn=prn).first()
        
        if user and user.role == 'student':
            if (user.name.lower().strip() == name.lower().strip() and 
                (user.mobile and user.mobile.strip() == mobile.strip()) and
                user.mother_name.lower().strip() == mother_name.lower().strip()):
                
                session['user_id'] = user.id
                return redirect(url_for('vote_page'))
            else:
                flash('Verification Failed! Details (Name/Mobile/Mother Name) do not match our records.')
        else:
            flash(f'Student with PRN "{prn}" not found in dataset. Please contact Admin.')
        return redirect(url_for('student_login'))
    
    return render_template('student_login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        prn = request.form.get('prn')
        password = request.form.get('password')
        
        user = User.query.filter_by(prn=prn, role='admin').first()
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid Admin Credentials')
            return redirect(url_for('admin_login'))
            
    return render_template('admin_login.html')

@app.route('/login')
def login_redirect():
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/vote')
def vote_page():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user = User.query.get(session['user_id'])
    if not user:
         session.pop('user_id', None)
         return redirect(url_for('index'))

    state = ElectionState.query.first()
    
    if state.is_finished or state.winner_declared:
        return redirect(url_for('results_page'))

    candidates = Candidate.query.all()
    return render_template('vote.html', user=user, candidates=candidates, election_active=state.is_active)

@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    user = User.query.get(session['user_id'])
    state = ElectionState.query.first()
    
    if not state.is_active:
        flash("Election is not active!")
        return redirect(url_for('vote_page'))
        
    if user.has_voted:
        flash("You have already voted!")
        return redirect(url_for('vote_page'))
        
    candidate_id = request.form['candidate_id']
    candidate = Candidate.query.get(candidate_id)
    
    if candidate:
        candidate.votes += 1
        user.has_voted = True
        db.session.commit()
        flash("Vote cast successfully!")
        return render_template('thank_you.html')
    
    return redirect(url_for('vote_page'))

# Admin Routes
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return redirect(url_for('vote_page'))
        
    candidates = Candidate.query.all()
    state = ElectionState.query.first()
    
    # Get uploaded datasets summary
    # Group by Class, Division, Year and count students
    datasets = db.session.query(
        User.class_name, 
        User.division, 
        User.year, 
        db.func.count(User.id).label('count')
    ).filter_by(role='student').group_by(User.class_name, User.division, User.year).all()
    
    return render_template('admin.html', candidates=candidates, state=state, datasets=datasets)

import csv
import io

# ... existing imports ...

@app.route('/admin/upload_dataset', methods=['POST'])
def upload_dataset():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return redirect(url_for('vote_page'))

    class_name = request.form.get('class_name')
    division = request.form.get('division')
    year = request.form.get('year')
    
    if not class_name or not division or not year:
        flash('Class, Division and Year are required!')
        return redirect(url_for('admin_dashboard'))

    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('admin_dashboard'))
        
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('admin_dashboard'))
        
    if file:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        
        # Expected CSV Format: PRN, Name, Mobile, Mother Name
        # Skip header if exists? Let's assume header exists if first row not numeric
        
        added_count = 0
        error_count = 0
        
        for i, row in enumerate(csv_input):
            if i == 0 and "prn" in row[0].lower():
                continue # Skip header
                
            if len(row) < 4:
                continue
                
            prn = row[0].strip()
            name = row[1].strip()
            mobile = row[2].strip()
            mother_name = row[3].strip()
            
            if User.query.filter_by(prn=prn).first():
                error_count += 1 # Already exists
                continue
                
            new_student = User(prn=prn, name=name, mobile=mobile, mother_name=mother_name, class_name=class_name, division=division, year=year, role='student')
            db.session.add(new_student)
            added_count += 1
            
        db.session.commit()
        flash(f'Dataset uploaded for {class_name}-{division} ({year}): {added_count} students added. {error_count} duplicates skipped.')
        
    return redirect(url_for('admin_dashboard'))

# ... existing routes ...
@app.route('/admin/add_candidate', methods=['POST'])
def add_candidate():
    name = request.form['name']
    position = request.form['position']
    class_name = request.form['class_name']
    division = request.form['division']
    
    photo_url = "https://via.placeholder.com/100"
    
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            # Add random prefix to avoid overwrites
            filename = f"{random.randint(1000, 9999)}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_url = url_for('static', filename=f'uploads/{filename}')
            
    new_candidate = Candidate(name=name, position=position, class_name=class_name, division=division, photo_url=photo_url)
    db.session.add(new_candidate)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_candidate/<int:id>', methods=['POST'])
def delete_candidate(id):
    print(f"DEBUG: Attempting to delete candidate with ID: {id}")
    if 'user_id' not in session:
        print("DEBUG: User not in session")
        return redirect(url_for('index'))
    user = User.query.get(session['user_id'])
    if not user or user.role != 'admin':
        print(f"DEBUG: Access denied for user: {user.name if user else 'None'} (role: {user.role if user else 'N/A'})")
        return redirect(url_for('vote_page'))
        
    candidate = Candidate.query.get_or_404(id)
    print(f"DEBUG: Deleting candidate: {candidate.name}")
    db.session.delete(candidate)
    db.session.commit()
    flash(f'Candidate "{candidate.name}" deleted successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_dataset', methods=['POST'])
def delete_dataset():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return redirect(url_for('vote_page'))

    class_name = request.form.get('class_name')
    division = request.form.get('division')
    year = request.form.get('year')
    
    # Delete students matching class, division, and year
    deleted_count = User.query.filter_by(
        class_name=class_name, 
        division=division, 
        year=year, 
        role='student'
    ).delete()
    
    db.session.commit()
    flash(f'Dataset for {class_name}-{division} ({year}) deleted. {deleted_count} students removed.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_election', methods=['POST'])
def toggle_election():
    action = request.form['action'] # 'start', 'stop', 'reset'
    state = ElectionState.query.first()
    
    if action == 'start':
        state.is_active = True
        state.is_finished = False
        state.winner_declared = False
    elif action == 'stop':
        state.is_active = False
        state.is_finished = True
    elif action == 'reset':
        state.is_active = False
        state.is_finished = False
        state.winner_declared = False
        # Reset votes
        candidates = Candidate.query.all()
        for c in candidates:
            c.votes = 0
        users = User.query.all()
        for u in users:
            u.has_voted = False
            
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/declare_winner', methods=['POST'])
def declare_winner():
    state = ElectionState.query.first()
    state.winner_declared = True
    state.is_active = False
    state.is_finished = True
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/results')
def results_page():
    state = ElectionState.query.first()
    
    # Sort candidates by votes (descending) and name (alphabetical) for ties
    candidates = Candidate.query.order_by(Candidate.votes.desc(), Candidate.name).all()
    total_votes = sum(c.votes for c in candidates)
    
    # Assign President (1st) and Vice President (2nd)
    president = candidates[0] if len(candidates) > 0 else None
    vice_president = candidates[1] if len(candidates) > 1 else None
    
    # Restrict view for students if winner not declared
    if not state.winner_declared and 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.role != 'admin':
             flash("Results are not yet declared.")
             return redirect(url_for('vote_page'))

    return render_template('results.html', 
                           candidates=candidates, 
                           total_votes=total_votes, 
                           president=president, 
                           vice_president=vice_president, 
                           state=state)

@app.route('/api/verify_profile', methods=['POST'])
def api_verify_profile():
    data = request.get_json()
    prn = data.get('prn')
    name = data.get('name')
    mobile = data.get('mobile')
    mother_name = data.get('mother_name')
    
    user = User.query.filter_by(prn=prn).first()
    
    if user and user.role == 'student':
        if (user.name.lower().strip() == name.lower().strip() and 
            (user.mobile and user.mobile.strip() == mobile.strip()) and
            user.mother_name.lower().strip() == mother_name.lower().strip()):
            
            session['user_id'] = user.id
            return jsonify({'success': True, 'redirect': url_for('vote_page')})
        else:
            return jsonify({'success': False, 'message': 'Verification Failed! Details do not match.'})
    else:
        return jsonify({'success': False, 'message': 'Student with this PRN not found.'})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
