from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta, date
from functools import wraps
import random
import string
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aliearn.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads/payments'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Utility Functions
def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def record_transaction(user_id, amount, transaction_type, details):
    transaction = Transaction(
        user_id=user_id,
        amount=amount,
        transaction_type=transaction_type,
        details=details
    )
    db.session.add(transaction)
    db.session.commit()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash('You do not have permission to access this page', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Models
class InvestmentPackage(db.Model):
    __tablename__ = 'investment_package'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    level = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    investments = db.relationship('Investment', back_populates='package')

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    referral_code = db.Column(db.String(10), unique=True)
    invited_by = db.Column(db.String(10))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    investments = db.relationship('Investment', back_populates='user')
    transactions = db.relationship('Transaction', back_populates='user')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Investment(db.Model):
    __tablename__ = 'investment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('investment_package.id'), nullable=False)
    transaction_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    invested_at = db.Column(db.DateTime, default=datetime.utcnow)
    expected_completion = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    admin_notes = db.Column(db.Text)
    payment_proof = db.Column(db.String(100))
    
    user = db.relationship('User', back_populates='investments')
    package = db.relationship('InvestmentPackage', back_populates='investments')

class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reward = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    completed_by = db.Column(db.Text)

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='transactions')

# Initialize database tables
with app.app_context():
    db.create_all()
    
    # Create initial data
    if InvestmentPackage.query.count() == 0:
        packages = [
            InvestmentPackage(name="VIP 1", price=400, profit=780, duration_days=20, level=1),
            InvestmentPackage(name="VIP 2", price=800, profit=1500, duration_days=26, level=2),
            InvestmentPackage(name="VIP 3", price=1200, profit=2300, duration_days=26, level=3),
            InvestmentPackage(name="VIP 4", price=2000, profit=4100, duration_days=26, level=4)
        ]
        db.session.bulk_save_objects(packages)
    
    if Task.query.count() == 0:
        tasks = [
            Task(title="Review Product", description="Write a product review", reward=10.0, category="Review", difficulty="Easy"),
            Task(title="Share Deal", description="Share on social media", reward=15.0, category="Social", difficulty="Medium"),
            Task(title="Rate App", description="Rate the mobile app", reward=20.0, category="Review", difficulty="Easy"),
            Task(title="Product Testing", description="Test and provide feedback", reward=30.0, category="Testing", difficulty="Hard")
        ]
        db.session.bulk_save_objects(tasks)
    
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            phone='911111111',
            password=generate_password_hash('adminpassword'),
            is_admin=True,
            referral_code=generate_referral_code(),
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        db.session.commit()

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        invitation_code = request.form.get('invitation_code', '').strip()
        agreement = request.form.get('agreement')
        captcha = request.form.get('captcha', '').upper()
        captcha_text = request.form.get('captcha_text', '').upper()

        # Validation
        errors = []
        if not username:
            errors.append('Username is required')
        if not phone or len(phone) != 9:
            errors.append('Valid Ethiopian phone number required')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        if not agreement:
            errors.append('You must agree to the terms')
        if captcha != captcha_text:
            errors.append('Invalid CAPTCHA code')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken')
        if User.query.filter_by(phone=phone).first():
            errors.append('Phone number already registered')

        if not errors:
            try:
                referral_code = generate_referral_code()
                user = User(
                    username=username,
                    phone=phone,
                    referral_code=referral_code,
                    invited_by=invitation_code if invitation_code else None
                )
                user.set_password(password)
                db.session.add(user)

                if invitation_code:
                    referrer = User.query.filter_by(referral_code=invitation_code).first()
                    if referrer:
                        referrer.balance += 50.0
                        record_transaction(
                            referrer.id,
                            50.0,
                            'referral',
                            f'Referral bonus for {username}'
                        )

                db.session.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('Registration failed. Please try again.', 'danger')
        else:
            for error in errors:
                flash(error, 'danger')

    captcha = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))
    return render_template('register.html', captcha_text=captcha)

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    
    # Calculate earnings
    total_earned = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == user.id,
        Transaction.transaction_type == 'task'
    ).scalar() or 0.0
    
    referral_earned = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == user.id,
        Transaction.transaction_type == 'referral'
    ).scalar() or 0.0
    
    active_investments_count = Investment.query.filter_by(
        user_id=user.id,
        status='approved'
    ).count()
    
    # Get tasks
    tasks = Task.query.all()
    available_tasks = [t for t in tasks if str(user.id) not in (t.completed_by or '').split(',')]
    
    task_categories = {}
    for task in available_tasks:
        if task.category not in task_categories:
            task_categories[task.category] = []
        task_categories[task.category].append(task)
    
    # Get transactions
    transactions = Transaction.query.filter_by(
        user_id=user.id
    ).order_by(
        Transaction.created_at.desc()
    ).limit(5).all()
    
    # Get investments
    investments = db.session.query(Investment, InvestmentPackage)\
        .join(InvestmentPackage, Investment.package_id == InvestmentPackage.id)\
        .filter(Investment.user_id == user.id)\
        .order_by(Investment.invested_at.desc())\
        .limit(3)\
        .all()
    
    captcha = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))
    
    return render_template(
        'dashboard.html',
        user=user,
        total_earned=total_earned,
        referral_earned=referral_earned,
        active_investments_count=active_investments_count,
        task_categories=task_categories,
        transactions=transactions,
        investments=investments,
        datetime=datetime,
        captcha_text=captcha
    )

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    
    total_earned = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == user.id,
        Transaction.transaction_type == 'task'
    ).scalar() or 0.0
    
    referral_earned = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == user.id,
        Transaction.transaction_type == 'referral'
    ).scalar() or 0.0
    
    return render_template(
        'profile.html',
        user=user,
        total_earned=total_earned,
        referral_earned=referral_earned
    )

@app.route('/investment_packages')
@login_required
def investment_packages():
    packages = InvestmentPackage.query.order_by(InvestmentPackage.level).all()
    return render_template('investment_packages.html', packages=packages)

@app.route('/invest_package/<int:package_id>', methods=['GET', 'POST'])
@login_required
def invest_package(package_id):
    package = InvestmentPackage.query.get_or_404(package_id)
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        transaction_number = request.form.get('transaction_number')
        
        # Handle file upload
        if 'payment_proof' not in request.files:
            flash('No payment proof uploaded', 'danger')
            return redirect(request.url)
        
        file = request.files['payment_proof']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            investment = Investment(
                user_id=user.id,
                package_id=package.id,
                transaction_number=transaction_number,
                expected_completion=datetime.utcnow() + timedelta(days=package.duration_days),
                payment_proof=filename
            )
            db.session.add(investment)
            db.session.commit()
            
            record_transaction(
                user.id,
                0,
                'investment',
                f'Invested in {package.name} package'
            )
            
            flash('Investment submitted for verification!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('invest_package.html', package=package, user=user)

@app.route('/my_investments')
@login_required
def my_investments():
    investments = db.session.query(Investment, InvestmentPackage)\
        .join(InvestmentPackage, Investment.package_id == InvestmentPackage.id)\
        .filter(Investment.user_id == session['user_id'])\
        .order_by(Investment.invested_at.desc())\
        .all()
    return render_template('my_investments.html', investments=investments)

@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    user = User.query.get(session['user_id'])
    task = Task.query.get(task_id)
    
    if not task or str(user.id) in (task.completed_by or '').split(','):
        return jsonify({'error': 'Task unavailable'}), 400
    
    user.balance += task.reward
    task.completed_by = f"{task.completed_by or ''},{user.id}" if task.completed_by else str(user.id)
    
    record_transaction(
        user.id,
        task.reward,
        'task',
        f'Completed task: {task.title}'
    )
    
    db.session.commit()
    return jsonify({
        'success': True,
        'balance': user.balance,
        'message': f'Task completed! +{task.reward} ETB'
    })

@app.route('/claim_daily_reward', methods=['POST'])
@login_required
def claim_daily_reward():
    user = User.query.get(session['user_id'])
    today = date.today()
    
    # Check if already claimed today
    last_claim = Transaction.query.filter_by(
        user_id=user.id,
        transaction_type='daily_reward',
        details=f"Daily reward {today}"
    ).first()
    
    if last_claim:
        return jsonify({'error': 'You already claimed your daily reward today'})
    
    # Verify CAPTCHA
    if request.form.get('captcha_input', '').upper() != request.form.get('captcha_text', ''):
        return jsonify({'error': 'Invalid CAPTCHA code'})
    
    # Grant reward
    reward_amount = 50
    user.balance += reward_amount
    record_transaction(
        user.id,
        reward_amount,
        'daily_reward',
        f"Daily reward {today}"
    )
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Daily reward of {reward_amount} ETB claimed!',
        'new_balance': user.balance
    })

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'})
    
    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'})
    
    if new_password != confirm_password:
        return jsonify({'error': 'Passwords do not match'})
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)