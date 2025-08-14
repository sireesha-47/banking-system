# app.py (continued with next features)

from flask import Flask, request, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random
import smtplib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    account = db.relationship('Account', backref='user', uselist=False)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.String(200))

# Send OTP email function (same as before)
def send_otp_email(receiver_email, otp):
    sender_email = "sireeshapatnana3666@gmail.com"  # 👉 Your Gmail address here
    sender_password = "lnya dvix ejcd xgvp"  # 👉 Your Gmail App Password here

    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"

    message = f"Subject: {subject}\n\n{body}"

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message)
        server.quit()
        print(f"OTP sent successfully to {receiver_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

#send a confirmation email to both
def send_transfer_email(to_email, amount, type, other_party):
    subject = f"Transaction Alert: {type}"
    body = f"You have {type.lower()} ₹{amount} {'to' if type == 'Transferred' else 'from'} {other_party}."
    message = f"Subject: {subject}\n\n{body}"

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("sireeshapatnana3666@gmail.com", "lnya dvix ejcd xgvp")
        server.sendmail("sireeshapatnana3666@gmail.com", to_email, message)
        server.quit()
    except Exception as e:
        print("Email error:", e)


# Existing routes (home, register, login, otp_verify, dashboard) remain unchanged
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')  # Or a separate homepage if you have one

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['temp_user_id'] = user.id
            send_otp_email(user.email, otp)
            return redirect(url_for('otp_verify'))
        else:
            return "Invalid email or password."

    return render_template('login.html')

@app.route('/otp_verify', methods=['GET', 'POST'])
def otp_verify():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if 'otp' in session and entered_otp == session['otp']:
            session['user_id'] = session['temp_user_id']
            session.pop('otp', None)
            session.pop('temp_user_id', None)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid OTP. Please try again."

    return render_template('otp_verify.html')


@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    # 🔍 Check and create account if not exist
    if not user.account:
        new_account = Account(user_id=user.id, balance=0.0)
        db.session.add(new_account)
        db.session.commit()

    if request.method == 'POST':
        amount = float(request.form['amount'])
        user.account.balance += amount
        txn = Transaction(user_id=user.id, amount=amount, type='Deposit', details='Amount deposited')
        db.session.add(txn)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('deposit.html')


@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('dashboard'))

    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        amount = float(request.form['amount'])
        if user.account.balance >= amount:
            user.account.balance -= amount
            txn = Transaction(user_id=user.id, amount=amount, type='Withdraw', details='Amount withdrawn')
            db.session.add(txn)
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            return "Insufficient balance."
    return render_template('withdraw.html')

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    # 🔍 Ensure sender has an account
    if not user.account:
        new_account = Account(user_id=user.id, balance=0.0)
        db.session.add(new_account)
        db.session.commit()

    if request.method == 'POST':
        recipient_email = request.form['recipient_email']
        amount = float(request.form['amount'])

        recipient = User.query.filter_by(email=recipient_email).first()

        # 🔍 Ensure recipient exists and has an account
        if not recipient:
            return "Recipient does not exist."

        if not recipient.account:
            new_account = Account(user_id=recipient.id, balance=0.0)
            db.session.add(new_account)
            db.session.commit()

        # ✅ Now safely proceed
        if user.account.balance >= amount:
            user.account.balance -= amount
            recipient.account.balance += amount

            txn1 = Transaction(user_id=user.id, amount=amount, type='Transfer', details=f'Transferred to {recipient.email}')
            txn2 = Transaction(user_id=recipient.id, amount=amount, type='Transfer', details=f'Received from {user.email}')

            db.session.add_all([txn1, txn2])
            db.session.commit()
            # After db.session.commit()
            print("Sending email to sender...")
            send_transfer_email(user.email, amount, "Transferred", recipient.email)
            print("Sending email to recipient...")
            send_transfer_email(recipient.email, amount, "Received", user.email)


            return redirect(url_for('dashboard'))
        else:
            return "Insufficient funds."

    return render_template('transfer.html')


@app.route('/transactions', methods=['GET'])
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if not user or not user.account:
        return "User or account not found."

    txns = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).all()
    return render_template('transactions.html', transactions=txns)


@app.route('/balance')
def balance():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user and user.account:
        return render_template('balance.html', balance=user.account.balance)
    else:
        return "Account not found", 404


# Ensure account is created with user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password, name=name)
        db.session.add(new_user)
        db.session.commit()

        # ✅ Ensure account creation
        new_account = Account(user_id=new_user.id, balance=0.0)
        db.session.add(new_account)
        db.session.commit()

        return "User registered successfully!"

    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('dashboard.html', user=user)
    return redirect(url_for('dashboard'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
