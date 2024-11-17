from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/')
def index(): return render_template('index.html')

@app.route('/browse_reviews')
def browse_reviews():
    return render_template('browse_reviews.html')

if __name__ == '__main__':
    app.run(debug=True, port=8000)