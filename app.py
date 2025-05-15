from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {os.getenv('ADMIN_USER', 'admin'): {'password': generate_password_hash(os.getenv('ADMIN_PASSWORD', 'admin123'))}}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def home():
    return render_template("form.html")

@app.route('/submit', methods=["POST"])
def submit():
    name = request.form["name"]
    phone = request.form["phone"]
    status = request.form["status"]
    reason = request.form["reason"] if status == "Absent" else ""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_entry = pd.DataFrame([[timestamp, name, phone, status, reason]],
                             columns=["DateTime", "Name", "Phone", "Status", "Reason"])

    excel_path = os.getenv('EXCEL_PATH', '/app/static/attendance.xlsx')
    try:
        existing = pd.read_excel(excel_path)
        df = pd.concat([existing, new_entry], ignore_index=True)
    except FileNotFoundError:
        df = new_entry

    df.to_excel(excel_path, index=False)

    return render_template("success.html")

@app.route('/admin', methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and check_password_hash(users[username]["password"], password):
            user = User(username)
            login_user(user)
            return redirect(url_for("download"))
        return "Invalid credentials", 403
    return '''
        <form method="POST">
            <label>Username:</label><input name="username" required><br>
            <label>Password:</label><input name="password" type="password" required><br>
            <button type="submit">Login</button>
        </form>
    '''

@app.route('/download')
@login_required
def download():
    excel_path = os.getenv('EXCEL_PATH', '/app/static/attendance.xlsx')
    return send_file(excel_path, as_attachment=True)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))