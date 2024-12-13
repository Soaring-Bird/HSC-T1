from flask import Flask, render_template, request, redirect, url_for, session, g, send_from_directory
import sqlite3  
from hashlib import sha1  
app = Flask(__name__)
# Secret key for managing sessions and securely signing cookies
app.secret_key = "wo^3udhwekjfq34hgf&/3rohf3ed"
# Initialize the SQLite database by executing the schema script during startup
sqlite3.connect('main.db').executescript(open('sql/schema.sql').read())

# Route to handle offline access 
@app.route('/offline')
def offline():
    return render_template('offline.html')

# Route to serve the service worker JavaScript file, as /sw.js doesn't work for web. 
@app.route('/sw.js')
def serve_service_worker():
    return send_from_directory('.', 'sw.js')

# Function to set session-wide and global variables before processing each request
@app.before_request
def set_globals(): 
    session.setdefault('admin', False)  # Tracks if the user is an admin
    session.setdefault('type', 'movie')  # Default review type (movie or game)
    session.setdefault('age', 200)  # Default age (set to an unrealistic high value for non-logged-in users so age errors don't come up)
    session.setdefault('username', 'Guest')  # Default username for unauthenticated users
    if session['type'] == 'movie': #Table, review_table, id_column, name_column for movies
        g.table = 'movies' 
        g.review_table = 'mReviews' 
        g.id_column = 'movieID'  
        g.name_column = 'movieName'  
    else:   #Same but for games
        g.table = 'games'  
        g.review_table = 'gReviews'  
        g.id_column = 'gameID'  
        g.name_column = 'gameName'  

# Utility function to execute database queries to make my life easier
# query: SQL query to execute
# args: Parameters for the query
# commit: Whether to commit the changes (for INSERT/UPDATE/DELETE queries)
def query_db(query, args=(), commit=False):
    conn = sqlite3.connect('main.db')  # Connect to the database
    cursor = conn.execute(query, args)  # Execute the query with the provided arguments
    if commit:
        conn.commit()  # Commit changes if specified
    result = cursor.fetchall()  # Fetch all results from the query
    conn.close()  # Close the database connection
    return result

# Route to set the type of reviews (movie or game)
@app.route('/set_type', methods=['POST'])
def set_type():
    session['type'] = request.form.get('type')  # Update the session variable based on user input
    return redirect(url_for('browse_reviews'))  

# Route for the home page
@app.route('/')
def index():
    # Query to check if the user has any warnings in their account
    result = query_db("SELECT warning FROM users WHERE username = ?", (session['username'],))
    warning = result[0][0] if result else None  # Extract the warning message if available
    return render_template('index.html', warning=warning)  # Render the home page with the warning

# Route for user signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':  # For the form submission
        password = request.form.get('password')  # Get the password entered by the user
        username = request.form.get('username')  # Get the username entered by the user 
        # Check if the passwords match and return warning accordingly
        if password != request.form.get('password_confirmation'):
            return render_template('signup.html', message="Passwords do not match", category="error")
        # Check if the username already exists and return message accourdingly
        if query_db("SELECT 1 FROM users WHERE username = ?", (username,)):
            return render_template('signup.html', message="Username already exists", category="error")
        # Hash the password for secure storage
        hashed_password = sha1(password.encode('utf-8')).hexdigest()
        # Insert the new user into the database
        query_db("INSERT INTO users (username, email, password, dob) VALUES (?, ?, ?, ?)", 
                 (username, request.form.get('mail'), hashed_password, request.form.get('dob')), commit=True)
        # Confirm successful account creation
        return render_template('signup.html', message="Account created successfully! Please log in.", category="success")
    # Render the signup form, message is smth so it looks nice.
    return render_template('signup.html', message=' ')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Handle form submission
        if session['username'] != 'Guest':  # Prevent login if already logged in
            return render_template('login.html', message="Error: already logged in.", category="error")
        username = request.form.get('username')  # Get the username entered by the user
        password = request.form.get('password')  # Get the password entered by the user
        hashed_password = sha1(password.encode('utf-8')).hexdigest()  # Hash the password
        # Query the database to validate the username and password
        user_data = query_db("""SELECT username, CAST((JULIANDAY('now') - JULIANDAY(dob)) / 365.25 AS INTEGER) AS age 
                                FROM users WHERE username = ? AND password = ? """, (username, hashed_password))
        if user_data:  # If valid credentials are found
            username, age = user_data[0]  # Extract username and age
            # Grant admin privileges to specific usernames
            if username in ['admin1', 'admin12', 'admin2']:
                session['admin'] = True
            session['username'] = username  # Update session with the logged-in username
            session['age'] = age  # Update session with the user's age
            return render_template('login.html', message="Login successful", category="success")
        else:
            return render_template('login.html', message="Invalid username or password", category="error")
    # Render the login form
    return render_template('login.html')

# Route for user logout
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from the session
    session.pop('admin', None)  # Remove admin flag from the session
    session.pop('age', None)  # Remove age from the session
    return redirect(url_for('login'))  # Redirect to the login page

# Route to browse reviews based on filters
@app.route('/browse_reviews')
def browse_reviews():
    filter_option = request.args.get('filter', None)  # Get the filter option from the query parameters
    # Set time condition for filtering reviews
    time_condition = ""
    if filter_option == "10mins": 
        time_condition = "AND r.timestamp >= datetime('now', '-10 minutes', 'localtime')"
    elif filter_option == "1hour": 
        time_condition = "AND r.timestamp >= datetime('now', '-1 hour', 'localtime')"
    elif filter_option == "today": 
        time_condition = "AND date(r.timestamp) = date('now', 'localtime')"
    # Query to fetch reviews along with associated items (movies or games)
    items = query_db(f"""SELECT t.{g.id_column}, t.{g.name_column}, t.genre, t.year, t.rating, MAX(r.timestamp) AS latest_review
        FROM {g.table} AS t LEFT JOIN {g.review_table} AS r ON t.{g.id_column} = r.{g.id_column} WHERE 1=1 {time_condition}
        GROUP BY t.{g.id_column} ORDER BY latest_review DESC NULLS LAST""")
    # Render the browse reviews page with the fetched items
    return render_template('browse_reviews.html', items=items)

# Route to add a new movie or game (only accessible by admins)
@app.route('/add', methods=['GET', 'POST'])
def add():
    if not session['admin']:  # Restrict access to admins only
        return render_template('add.html', message=f'You must be admin to add a {session["type"]}.', category='error')
    if request.method == 'POST':  # To handle form submission
        # Insert the new item into the appropriate table
        query_db(f"INSERT INTO {g.table} ({session["type"]}Name, genre, year, rating) VALUES (?, ?, ?, ?)",
                 (request.form['name'], request.form['genre'], request.form['year'], request.form['rating']), commit=True)
        return render_template('add.html', message=f'{session["type"].title()} added!', category='success')
    # Render the add item form
    return render_template('add.html')

# Route to display reviews for a specific item (movie or game)
@app.route('/review/<int:id>')
def review(id):
    # Query to fetch details (title, year, genre, rating) of the selected item
    title, year, genre, rating = query_db(f"SELECT {g.name_column}, year, genre, rating FROM {g.table} WHERE {g.id_column} = ?", (id,))[0]
    # Determine the minimum age requirement based on the rating
    rating_min = {'G': 9, 'PG': 9, 'PG-13': 13, 'M': 15,'MA 15+': 15, 'R 18+': 18, 'X 18+': 18}[rating]
    # Fetch reviews only if the user is logged in and meets the age requirement
    reviews = query_db(f"SELECT * FROM {g.review_table} WHERE {g.id_column} = ?", (id,)) if session['username'] != 'Guest' and session['age'] >= rating_min else ''
    # Render the review page with the item and review details
    return render_template('review.html', main=reviews, title=title, year=year, genre=genre, rating=rating, age_min=rating_min,
        message=request.args.get('message'), category=request.args.get('category'), item=id)

# Route to add a review for a specific item
@app.route('/addreview/<int:id>', methods=['POST'])
def add_review(id):
    # Redirect guests to log in before they can add a review
    if session['username'] == 'Guest':  # Prevent guests from reviewing
        return redirect(url_for('review', id=id, message='You must sign in to review!', category='error'))
    # Insert the review into the database
    query_db(f"INSERT INTO {g.review_table} (user, stars, comment, {g.id_column}) VALUES (?, ?, ?, ?)",
        (session['username'], int(request.form.get('stars')), request.form['comment'], id), commit=True)
    # Redirect back to the review page with a success message
    return redirect(url_for('review', id=id, message="Review added!", category='success'))

# Route to delete a specific review (admin only)
@app.route('/delete/<int:id>/<int:review_id>')
def delete_task(id, review_id):
    if not session['admin']:  # Restrict deletion to admins
        return redirect(url_for('review', id=id, message="Unauthorized action.", category="error"))
    # Delete the specified review from the database
    query_db(f"DELETE FROM {g.review_table} WHERE id=?", (review_id,), commit=True)
    # Redirect back to the review page with a success message
    return redirect(url_for('review', id=id, message="Review deleted!", category="success"))

# Route to delete a user (admin only)
@app.route('/terminate/<int:id>/<username>')
def delete_user(id, username):
    if not session['admin']:  # Restrict user termination to admins
        return redirect(url_for('review', id=id, message="Unauthorized action.", category="error"))
    # Remove the user from the database and anonymize their reviews
    query_db(f"DELETE FROM users WHERE username=?", (username,), commit=True)
    query_db(f"UPDATE {g.review_table} SET user=? WHERE user = ?", ('Deleted User', username), commit=True)
    # Redirect back to the review page with a success message
    return redirect(url_for('review', id=id, message="User deleted!", category="success"))

# Route to issue a warning to a user (admin only)
@app.route('/warn/<int:id>/<username>', methods=['POST'])
def warn_user(id, username):
    if not session['admin']:  # Restrict warnings to admins
        return redirect(url_for('review', id=id, message="Unauthorized action.", category="error"))
    # Add a warning message for the specified user
    query_db("UPDATE users SET warning=? WHERE username=?", ('Warning: ' + request.form.get('warning', '').strip(), username), commit=True)
    # Redirect back to the review page with a success message
    return redirect(url_for('review', id=id, message="Warning added successfully.", category="success"))

# Route to edit a specific review
@app.route('/editreview/<int:id>/<int:review_id>', methods=['POST'])
def edit_review(id, review_id):
    # Verify that the current user is the owner of the review
    review_user = query_db(f"SELECT user FROM {g.review_table} WHERE id=?", (review_id,))
    if not review_user or review_user[0][0] != session['username']:
        return redirect(url_for('review', id=id, message="Unauthorized action.", category="error"))
    # Update the review content and add an edited marker
    query_db(f"UPDATE {g.review_table} SET comment = ?, stars = ? WHERE id = ?", (request.form.get('comment') + "\n[Edited]", request.form.get('stars'), review_id), commit=True)
    # Redirect back to the review page with a success message
    return redirect(url_for('review', id=id, message="Review updated!", category="success"))

if __name__ == '__main__':
    app.run(debug=True, port=8000)