from flask import Flask, render_template, request, redirect, url_for, session,g
import sqlite3
from hashlib import sha1
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

sqlite3.connect('main.db').executescript(open('sql/schema.sql').read())

@app.before_request
def set_globals(): 
    #Similarly, in future one can modularise this by setting global vars 
    session.setdefault('type', 'movie')
    session.setdefault('age', 5)
    if session.get('type') == 'movie':
        g.table = 'movies'
        g.review_table = 'mReviews'
        g.id_column = 'movieID'
        g.name_column = 'movieName'
    else:
        g.table = 'games'
        g.review_table = 'gReviews'
        g.id_column = 'gameID'
        g.name_column = 'gameName'

def query_db(query, args=(), commit=False):
    conn = sqlite3.connect('main.db')
    cursor = conn.execute(query, args)
    if commit:
        conn.commit()
    result = cursor.fetchall()
    conn.close()
    return result
 
@app.route('/set_type', methods=['POST'])
def set_type():
    session['type'] = request.form.get('type')
    return redirect(url_for('browse_reviews'))

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        password = request.form.get('password')
        username = request.form.get('username')
        if password != request.form.get('password_confirmation'): 
            return render_template('signup.html', message="Passwords do not match", category="error")
        if query_db("SELECT 1 FROM users WHERE username = ?", (username,)):
            return render_template('signup.html', message="Username already exists", category="error")
        hashed_password = sha1(password.encode('utf-8')).hexdigest()
        query_db("INSERT INTO users (username, email, password, dob) VALUES (?, ?, ?, ?)", 
        (username, request.form.get('mail'), hashed_password, request.form.get('dob')), commit=True)
        return render_template('signup.html', message="Account created successfully! Please log in.", category="success")
    return render_template('signup.html', message=' ')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = sha1(password.encode('utf-8')).hexdigest()
        user_data = query_db("""SELECT username, CAST((JULIANDAY('now') - JULIANDAY(dob)) / 365.25 AS INTEGER) AS age 
                                FROM users WHERE username = ? AND password = ? """, (username, hashed_password))
        if user_data:
            username, age = user_data[0]  
            session['username'] = username
            session['age'] = age
            return render_template('login.html', message="Login successful", category="success")
        else:
            return render_template('login.html', message="Invalid username or password", category="error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  
    return redirect(url_for('login'))  

@app.route('/browse_reviews')
def browse_reviews():
    filter_option = request.args.get('filter', None)
    time_condition = ""
    if filter_option == "10mins": time_condition = f"AND r.timestamp >= datetime('now', '-10 minutes', 'localtime')"
    elif filter_option == "1hour": time_condition = f"AND r.timestamp >= datetime('now', '-1 hour', 'localtime')"
    elif filter_option == "today": time_condition = f"AND date(r.timestamp) = date('now', 'localtime')"
    else: time_condition == ""
    items = query_db(f"""SELECT t.{g.id_column}, t.{g.name_column}, t.genre, t.year, t.rating, MAX(r.timestamp) AS latest_review
        FROM {g.table} AS t LEFT JOIN {g.review_table} AS r ON t.{g.id_column} = r.{g.id_column} WHERE 1=1 {time_condition}
        GROUP BY t.{g.id_column} ORDER BY latest_review DESC NULLS LAST""")
    return render_template('browse_reviews.html', items=items)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if not session.get('username'): #will be modified for admin update
        return render_template('add.html', message=f'You must be logged in to add a {session["type"]}.', category='error')
    if request.method == 'POST':
        query_db(f"INSERT INTO {g.table} ({session["type"]}Name, genre, year, rating) VALUES (?, ?, ?, ?)",
                 (request.form['name'], request.form['genre'], request.form['year'], request.form['rating']), commit=True)
        return render_template('add.html', message=f'{session["type"].title()} added!', category='success')
    return render_template('add.html')

@app.route('/review/<int:id>')
def review(id):
    title, year, genre, rating = query_db(f"SELECT {g.name_column}, year, genre, rating FROM {g.table} WHERE {g.id_column} = ?", (id,))[0]
    rating_min= {'G': 9, 'PG': 9, 'M': 15, 'MA 15+': 15, 'R 18+': 18, 'X 18+': 18}[rating]
    # so even if they remove blur css property from css, they still can't see the reviews.
    reviews = query_db(f"SELECT * FROM {g.review_table} WHERE {g.id_column} = ?", (id,)) if session.get('username') and session['age']>=rating_min else ''
    return render_template('review.html', main=reviews, title=title, year=year, genre=genre, rating=rating, age_min=rating_min,
        message=request.args.get('message'), category=request.args.get('category'), item=id)

@app.route('/addreview/<int:id>', methods=['POST'])
def add_review(id):
    if not session.get('username'): #in case added by url
        return redirect(url_for('review', id=id, message='You must sign in to review!', category='error'))
    query_db(f"INSERT INTO {g.review_table} (user, stars, comment, {g.id_column}) VALUES (?, ?, ?, ?)",
             (session['username'], int(request.form.get('stars')), request.form['comment'], id), commit=True)
    return redirect(url_for('review', id=id, message="Review added!", category='success'))

@app.route('/delete/<int:id>/<int:review_id>')
def delete_task(id, review_id):
    review_user = query_db(f"SELECT user FROM {g.review_table} WHERE id=?", (review_id,))
    if not review_user or review_user[0][0] != session.get('username'):
        return redirect(url_for('review', id=id, message="Unauthorized action.", category="error"))
    query_db(f"DELETE FROM {g.review_table} WHERE id=?", (review_id,), commit=True)
    return redirect(url_for('review', id=id, message="Review deleted!", category="success"))

@app.route('/editreview/<int:id>/<int:review_id>', methods=['POST'])
def edit_review(id, review_id):
    if not session.get('username'):
        return redirect(url_for('review', id=id, message="You must sign in to edit reviews!", category="error"))
    review_user = query_db(f"SELECT user FROM {g.review_table} WHERE id=?", (review_id,))
    if not review_user or review_user[0][0] != session.get('username'):
        return redirect(url_for('review', id=id, message="Unauthorized action.", category="error"))
    query_db(f"UPDATE {g.review_table} SET comment = ?, stars = ? WHERE id = ?", 
             (request.form.get('comment'), request.form.get('stars'), review_id), commit=True)
    return redirect(url_for('review', id=id, message="Review updated!", category="success"))

if __name__ == '__main__':
    app.run(debug=True, port=8000)