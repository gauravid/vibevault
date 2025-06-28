from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Config
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Gauru@9422",
    database="finance_tracker"
)
cursor = db.cursor(dictionary=True)

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect('/dashboard')
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
        db.commit()
        return redirect('/login')
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    # Fetch last 14 days of transactions
    cursor.execute("""
        SELECT * FROM transactions 
        WHERE user_id = %s AND date >= CURDATE() - INTERVAL 14 DAY
    """, (session['user_id'],))
    transactions = cursor.fetchall()

    df = pd.DataFrame(transactions)

    tips = []
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['week'] = df['date'].dt.isocalendar().week

        current_week = datetime.now().isocalendar().week
        last_week = current_week - 1

        weekly_summary = df.groupby(['week', 'category'])['amount'].sum().unstack().fillna(0)

        if current_week in weekly_summary.index and last_week in weekly_summary.index:
            for category in weekly_summary.columns:
                last = weekly_summary.at[last_week, category]
                curr = weekly_summary.at[current_week, category]

                if last > 0:
                    change_pct = ((curr - last) / last) * 100
                    if change_pct > 10:
                        tips.append(f"⚠️ You spent {change_pct:.1f}% more on {category} this week than last.")
                    elif change_pct < -10:
                        tips.append(f"✅ You cut your {category} spending by {abs(change_pct):.1f}% compared to last week.")

    # Aggregate category-wise totals for chart
    category_totals = df.groupby('category')['amount'].sum().to_dict()

    return render_template(
        'dashboard.html',
        transactions=transactions,
        chart_data=category_totals,
        tips=tips
    )

@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = request.form['amount']
        category = request.form['category']
        date_val = request.form['date']
        description = request.form['description']

        print("Received data:", amount, category, date_val, description)

        cursor.execute("""
            INSERT INTO transactions (user_id, amount, category, date, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['user_id'], amount, category, date_val, description))
        db.commit()

        return redirect('/dashboard')

    return render_template('add_transaction.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']
        description = request.form['description']
        cursor.execute("UPDATE transactions SET amount = %s, category = %s, date = %s, description = %s WHERE id = %s AND user_id = %s",
                       (amount, category, date, description, id, session['user_id']))
        db.commit()
        return redirect('/dashboard')

    cursor.execute("SELECT * FROM transactions WHERE id = %s AND user_id = %s", (id, session['user_id']))
    txn = cursor.fetchone()
    return render_template('edit_transaction.html', txn=txn)

@app.route('/delete/<int:id>')
def delete_transaction(id):
    if 'user_id' not in session:
        return redirect('/login')
    cursor.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (id, session['user_id']))
    db.commit()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
