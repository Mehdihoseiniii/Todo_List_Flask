# app.py
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this-should-be-changed-in-production'  # تغییر بدید قبل از پابلیش
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# loader برای Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ثبت‌نام
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        if not username or not password:
            flash('نام کاربری و رمز عبور لازم است', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('این نام کاربری قبلاً وجود دارد', 'warning')
            return redirect(url_for('register'))
        u = User(username=username)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash('ثبت‌نام با موفقیت انجام شد. حالا وارد شوید.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# ورود
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('ورود موفقیت‌آمیز بود', 'success')
            return redirect(url_for('index'))
        flash('نام کاربری یا رمز اشتباه است', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

# خروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('خروج انجام شد', 'info')
    return redirect(url_for('login'))

# پنل اصلی: لیست تسک‌ها و اضافه کردن
@app.route('/', methods=['GET','POST'])
@login_required
def index():
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        if title:
            t = Todo(title=title, user_id=current_user.id)
            db.session.add(t)
            db.session.commit()
            flash('تسک اضافه شد', 'success')
        return redirect(url_for('index'))

    todos = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', todos=todos)

# تِوگل وضعیت (انجام / نشده)
@app.route('/toggle/<int:todo_id>')
@login_required
def toggle(todo_id):
    t = Todo.query.get_or_404(todo_id)
    if t.user_id != current_user.id:
        flash('دسترسی ندارید', 'danger')
        return redirect(url_for('index'))
    t.done = not t.done
    db.session.commit()
    return redirect(url_for('index'))

# حذف تسک
@app.route('/delete/<int:todo_id>')
@login_required
def delete(todo_id):
    t = Todo.query.get_or_404(todo_id)
    if t.user_id != current_user.id:
        flash('دسترسی ندارید', 'danger')
        return redirect(url_for('index'))
    db.session.delete(t)
    db.session.commit()
    flash('تسک حذف شد', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # ایجاد جداول اگر وجود ندارند
    with app.app_context():
        db.create_all()
    app.run(debug=True)
