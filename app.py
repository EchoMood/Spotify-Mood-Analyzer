# This script sets up a Flask web application with routes for different pages.
# It includes routes for the home page, a visualisation page, an upload page, and a share page.
# It also checks for the required packages and prints a message if they are not installed.
try:
    from flask import Flask, render_template
except ImportError:
    print("\nMissing required packages! Please run:")
    print("   pip install -r requirements.txt\n")
    exit(1)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/visualise')
def visualise():
    return render_template('visualise.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/share')
def share():
    return render_template('share.html')

if __name__ == '__main__':
    app.run(debug=True)