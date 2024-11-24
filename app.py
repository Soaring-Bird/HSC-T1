from flask import Flask, render_template, request, redirect, url_for, session,g
import sqlite3
from hashlib import sha1
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

sqlite3.connect('main.db').executescript(open('sql/schema.sql').read())

def query_db(query, args=(), commit=False):
    conn = sqlite3.connect('main.db')
    cursor = conn.execute(query, args)
    if commit:
        conn.commit()
    result = cursor.fetchall()
    conn.close()
    return result
 
@app.route('/')
def index(): return render_template('index.html')

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
        query_db("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
        (username, request.form.get('mail'), hashed_password), commit=True)
        return render_template('signup.html', message="Account created successfully! Please log in.", category="success")
    return render_template('signup.html', message=' ')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = sha1(password.encode('utf-8')).hexdigest()
        user = query_db("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        if user:
            session['username'] = username
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
    items = query_db("""SELECT t.movieID, t.movieName, t.genre, t.year, MAX(r.timestamp) AS latest_review
        FROM movies AS t LEFT JOIN mReviews AS r ON t.movieID = r.movieID WHERE 1=1
        GROUP BY t.movieID ORDER BY latest_review DESC NULLS LAST""")
    return render_template('browse_reviews.html', items=items)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if not session.get('username'): #will be modified for admin update
        return render_template('add.html', message='You must be admin to add a movie.', category='error')
    if request.method == 'POST':
        query_db(f"INSERT INTO movies (movieName, genre, year) VALUES (?, ?, ?)",
                 (request.form['name'], request.form['genre'], request.form['year']), commit=True)
        return render_template('add.html', message=f'Movie added!', category='success')
    return render_template('add.html')

@app.route('/review/<int:id>')
def review(id):
    title, year, genre = query_db("SELECT movieName, year, genre FROM movies WHERE movieID = ?", (id,))[0]
    if session.get('username'):
        reviews = query_db("SELECT * FROM mReviews WHERE movieID = ?", (id,))
    else: # so even if they remove blur css property from css, they still can't see the reviews.
        reviews = ''
    return render_template('review.html', main=reviews, heading=f"{title}-{year}-{genre}", 
        message=request.args.get('message'), category=request.args.get('category'), item=id)

@app.route('/addreview/<int:id>', methods=['POST'])
def add_review(id):
    if not session.get('username'): #in case added by url
        return redirect(url_for('review', id=id, message='You must sign in to review!', category='error'))
    query_db(f"INSERT INTO mReviews (user, stars, comment, movieID) VALUES (?, ?, ?, ?)",
             (session['username'], int(request.form.get('stars')), request.form['comment'], id), commit=True)
    return redirect(url_for('review', id=id, message="Review added!", category='success'))


if __name__ == '__main__':
    app.run(debug=True, port=8000)