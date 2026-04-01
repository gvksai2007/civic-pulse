from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
 
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'civic-report-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///civic_reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
 
db = SQLAlchemy(app)
 
# ─── MODELS ──────────────────────────────────────────────────────────────────
 
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reports = db.relationship('Report', backref='author', lazy=True)
    votes = db.relationship('Vote', backref='voter', lazy=True)
 
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
 
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
 
    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'email': self.email}
 
 
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(30), default='open')       # open, in_progress, resolved
    priority = db.Column(db.String(20), default='medium')   # low, medium, high, critical
    location = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    votes_list = db.relationship('Vote', backref='report', lazy=True)
    comments = db.relationship('Comment', backref='report', lazy=True)
 
    @property
    def vote_count(self):
        return len(self.votes_list)
 
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'status': self.status,
            'priority': self.priority,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'author': self.author.username,
            'vote_count': self.vote_count,
            'comment_count': len(self.comments)
        }
 
 
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'report_id'),)
 
 
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User', backref='comments')
 
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author.username,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }
 
 
# ─── AUTH DECORATOR ──────────────────────────────────────────────────────────
 
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated
 
 
# ─── ROUTES ──────────────────────────────────────────────────────────────────
 
@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
 
@app.route('/map')
def map_view():
    return render_template('map.html')
 
# ── Auth API ──
 
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username taken'}), 400
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    session['username'] = user.username
    return jsonify({'message': 'Registered successfully', 'user': user.to_dict()})
 
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    session['user_id'] = user.id
    session['username'] = user.username
    return jsonify({'message': 'Logged in', 'user': user.to_dict()})
 
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})
 
@app.route('/api/me')
def me():
    if 'user_id' not in session:
        return jsonify({'user': None})
    user = User.query.get(session['user_id'])
    return jsonify({'user': user.to_dict() if user else None})
 
# ── Reports API ──
 
@app.route('/api/reports', methods=['GET'])
def get_reports():
    category = request.args.get('category')
    status = request.args.get('status')
    sort = request.args.get('sort', 'newest')
    q = Report.query
    if category and category != 'all':
        q = q.filter_by(category=category)
    if status and status != 'all':
        q = q.filter_by(status=status)
    if sort == 'votes':
        reports = q.all()
        reports.sort(key=lambda r: r.vote_count, reverse=True)
    elif sort == 'oldest':
        reports = q.order_by(Report.created_at.asc()).all()
    else:
        reports = q.order_by(Report.created_at.desc()).all()
    return jsonify({'reports': [r.to_dict() for r in reports]})
 
@app.route('/api/reports', methods=['POST'])
@login_required
def create_report():
    data = request.get_json()
    report = Report(
        title=data['title'],
        description=data['description'],
        category=data['category'],
        priority=data.get('priority', 'medium'),
        location=data.get('location', ''),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        user_id=session['user_id']
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({'report': report.to_dict()}), 201
 
@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    report = Report.query.get_or_404(report_id)
    data = report.to_dict()
    data['comments'] = [c.to_dict() for c in report.comments]
    return jsonify({'report': data})
 
@app.route('/api/reports/<int:report_id>/vote', methods=['POST'])
@login_required
def vote_report(report_id):
    report = Report.query.get_or_404(report_id)
    existing = Vote.query.filter_by(user_id=session['user_id'], report_id=report_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'voted': False, 'vote_count': report.vote_count})
    vote = Vote(user_id=session['user_id'], report_id=report_id)
    db.session.add(vote)
    db.session.commit()
    return jsonify({'voted': True, 'vote_count': report.vote_count})
 
@app.route('/api/reports/<int:report_id>/comment', methods=['POST'])
@login_required
def add_comment(report_id):
    data = request.get_json()
    comment = Comment(content=data['content'], user_id=session['user_id'], report_id=report_id)
    db.session.add(comment)
    db.session.commit()
    return jsonify({'comment': comment.to_dict()}), 201
 
@app.route('/api/reports/<int:report_id>/status', methods=['PATCH'])
@login_required
def update_status(report_id):
    report = Report.query.get_or_404(report_id)
    if report.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    report.status = data['status']
    db.session.commit()
    return jsonify({'report': report.to_dict()})
 
# ── Stats API ──
 
@app.route('/api/stats')
def get_stats():
    total = Report.query.count()
    open_count = Report.query.filter_by(status='open').count()
    resolved = Report.query.filter_by(status='resolved').count()
    in_progress = Report.query.filter_by(status='in_progress').count()
    by_category = {}
    for r in Report.query.all():
        by_category[r.category] = by_category.get(r.category, 0) + 1
    return jsonify({
        'total': total,
        'open': open_count,
        'resolved': resolved,
        'in_progress': in_progress,
        'by_category': by_category,
        'users': User.query.count()
    })
 
 
# ─── SEED DATA ───────────────────────────────────────────────────────────────
 
def seed_data():
    if User.query.count() > 0:
        return
    u1 = User(username='alex_citizen', email='alex@city.com')
    u1.set_password('password123')
    u2 = User(username='maria_reports', email='maria@city.com')
    u2.set_password('password123')
    db.session.add_all([u1, u2])
    db.session.commit()
 
    sample_reports = [
        Report(title='Large Pothole on Main St', description='Dangerous pothole causing tire damage near intersection with Oak Ave. Has been here for 3 weeks.', category='roads', priority='high', status='open', location='Main St & Oak Ave', latitude=40.7128, longitude=-74.0060, user_id=u1.id),
        Report(title='Broken Street Light', description='Street light on Elm Street has been out for two weeks making the area unsafe at night.', category='lighting', priority='medium', status='in_progress', location='Elm Street, Block 4', latitude=40.7148, longitude=-74.0080, user_id=u2.id),
        Report(title='Overflowing Garbage Bins', description='Public bins at Central Park entrance overflowing since Monday. Creating a sanitation issue.', category='sanitation', priority='high', status='open', location='Central Park North Entrance', latitude=40.7168, longitude=-74.0040, user_id=u1.id),
        Report(title='Graffiti on Library Wall', description='Offensive graffiti appeared on the south wall of the public library. Needs immediate removal.', category='vandalism', priority='medium', status='resolved', location='City Public Library', latitude=40.7108, longitude=-74.0070, user_id=u2.id),
        Report(title='Flooded Sidewalk', description='Sidewalk on Broadway floods every time it rains due to blocked drainage. Very dangerous for pedestrians.', category='flooding', priority='critical', status='open', location='Broadway & 5th', latitude=40.7138, longitude=-74.0050, user_id=u1.id),
        Report(title='Damaged Park Bench', description='Park bench near the fountain is broken with sharp edges. Risk of injury to children.', category='parks', priority='low', status='open', location='Riverside Park, Fountain Area', latitude=40.7158, longitude=-74.0090, user_id=u2.id),
    ]
    db.session.add_all(sample_reports)
    db.session.commit()
 
    for uid, rid in [(u1.id, 1), (u2.id, 1), (u1.id, 3), (u2.id, 5), (u1.id, 5)]:
        db.session.add(Vote(user_id=uid, report_id=rid))
    db.session.commit()
 
 
# ── This runs on both "python app.py" AND gunicorn ──
with app.app_context():
    db.create_all()
    seed_data()
 
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)