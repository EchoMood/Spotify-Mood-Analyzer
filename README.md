# EchoMood

![Made with Flask](https://img.shields.io/badge/Made%20with-Flask-blue)
![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue)
![Frontend-HTML](https://img.shields.io/badge/Frontend-HTML5-orange?logo=html5&logoColor=white)
![CSS](https://img.shields.io/badge/Styling-CSS3-blue?logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/Scripting-JavaScript-yellow?logo=javascript&logoColor=black)
![Spotify API](https://img.shields.io/badge/API-Spotify-1DB954?logo=spotify&logoColor=white)
![OpenAI API](https://img.shields.io/badge/API-OpenAI-blueviolet?logo=openai&logoColor=white)
![DALL·E](https://img.shields.io/badge/ImageGen-DALL·E-ff69b4?logo=openai&logoColor=white)
![Ngrok](https://img.shields.io/badge/Tunnel-Ngrok-black?logo=ngrok)
![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-4479A1?logo=databricks&logoColor=white)
![WTForms](https://img.shields.io/badge/Forms-WTForms-informational)
![Jinja2](https://img.shields.io/badge/Templates-Jinja2-orange)
![Pytest](https://img.shields.io/badge/Tests-Pytest-6a5acd?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-Personal%20Use-lightgrey)

---

## 🎵 Project Overview

EchoMood is a web application for analyzing your Spotify listening history and visualizing user moods and personality traits based on music preferences.  
Upload your Spotify data and generate beautiful, insightful visualizations of your musical personality!

---

## ⚙️ Requirements

- Python 3.8+
- pip (Python package installer)
- Spotify Developer Account
- OpenAI API Key
- [Ngrok](https://ngrok.com/) (for local testing)

---

## 📦 Setup Instructions

1. **Clone** this repository or download the source code.

2. **Navigate** to the project directory:
   ```bash
   cd Spotify-Mood-Analyzer
   ```

3. (Optional but recommended) **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # For Mac/Linux
   ```

4. **Install project dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🌐 Setting Up ngrok (for Spotify OAuth and Public Tunneling)

ngrok allows you to expose your local Flask server to the internet, which is essential for handling Spotify OAuth callbacks during development.

### 🔧 Step 1: Install ngrok

#### ✅ Option 1: Via Official Website (Recommended)
1. Visit the [official ngrok download page](https://ngrok.com/download).
2. Download the version appropriate for your operating system.
3. Extract the downloaded archive and place the `ngrok` binary somewhere in your system path (e.g., `/usr/local/bin` or `C:\ngrok\`).

#### ✅ Option 2: Via Homebrew (macOS/Linux only)
```bash
brew install ngrok/ngrok/ngrok
```

### 🪪 Step 2: Sign Up & Get Your Auth Token

1. Go to [https://dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup) and create a free account.
2. Once logged in, navigate to **[Your Authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)**.
3. Copy your **Auth Token**.

### 🔐 Step 3: Connect Your ngrok Account

Paste your token into this command:

```bash
ngrok config add-authtoken <YOUR_AUTH_TOKEN>
```

✅ You should see a confirmation like:
```
Authtoken saved to configuration file: ~/.ngrok2/ngrok.yml
```

### 🚀 Step 4: Start ngrok Tunnel for Your Flask App

Assuming your Flask app runs locally on port `5000`:

```bash
ngrok http 5000
```

You’ll see output like:

```
Forwarding                    https://cafe-ngrok-url.ngrok-free.app -> http://localhost:5000
```

> ✅ Copy the **`https://` public URL** — you'll need this for your Spotify redirect URI.

### 🔄 Step 5: Update Spotify Redirect URI

1. Go to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Select your app → **Edit Settings**.
3. Under **Redirect URIs**, add your ngrok public URL + `/callback`.  
   Example:
   ```
   https://cafe-ngrok-url.ngrok-free.app/callback
   ```
4. Save the changes.

---

---

## 🔑 Setting Up Spotify API (OAuth Integration)

EchoMood uses the **Spotify Web API** to fetch users’ listening history, top tracks, and audio features. To enable this functionality, you'll need to register a Spotify Developer App and configure the necessary environment variables.

### 🎯 Step-by-Step Instructions

#### 1. Create a Spotify Developer Account
- Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
- Sign in using your **Spotify account** (you can use your existing one or create a new one).
- Read and accept the **Developer Terms of Service**.

#### 2. Create an Application
- Click the **“Create an App”** button.
- Enter a suitable **App Name** (e.g., `EchoMood`) and **App Description** (e.g., “A web app for Spotify-based mood analysis”).
- Agree to the terms and create the app.

#### 3. Get Your Credentials
After creating your app, you'll be taken to the app overview screen. Here you’ll find:
- **Client ID**: A unique identifier for your app.
- **Client Secret**: Keep this private. Used to authenticate your app with Spotify.

#### 4. Configure Redirect URIs (VERY IMPORTANT)
Spotify OAuth requires a **Redirect URI**, which is where Spotify will send the user after authentication.

- In the app dashboard, click **Edit Settings**.
- Under **Redirect URIs**, add your callback URI:
  - If running locally with **ngrok**, your URI will look like:
    ```
    https://your-ngrok-subdomain.ngrok-free.app/callback
    ```
  - Replace with your **actual ngrok URL**, which changes each time you restart unless you're on a paid ngrok plan.
- Click **Save**.

#### 5. Set Environment Variables
To securely provide your credentials to the Flask application, add them to your `.env` file or environment configuration:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_REDIRECT_URI=https://your-ngrok-subdomain.ngrok-free.app/callback
```

> ✅ Make sure the redirect URI here **matches exactly** what you added in the Spotify dashboard (including `https://`).

### 🧪 How to Test It

Once configured:

1. Start your Flask server.
2. Expose it using ngrok:
   ```bash
   ngrok http 5000
   ```
3. Update your **redirect URI** in Spotify dashboard with the new ngrok URL (if it changed).
4. Visit your app’s homepage and click **“Connect with Spotify”**.
5. You should be redirected to Spotify's login page. After logging in and granting permissions, you're redirected back to your app and user data is fetched successfully.

---

## 🧠 Setting Up OpenAI API (ChatGPT + DALL·E)

EchoMood uses OpenAI’s powerful models—**ChatGPT (GPT-4)** for mood analysis and personality profiling, and **DALL·E 3** for AI-generated personality images.

### 🔐 Step 1: Create an OpenAI Account

1. Visit [https://platform.openai.com/signup](https://platform.openai.com/signup) and sign up for a free or paid OpenAI account.
2. After logging in, go to the [API Keys page](https://platform.openai.com/account/api-keys).
3. Click **“Create new secret key”**.
4. Copy the key. **You will not be able to view it again later**, so store it securely (e.g., in a `.env` file or password manager).

### ⚙️ Step 2: Configure Environment Variables

In your project’s root directory, create a file named `.env` (if it doesn’t exist) and add the following lines:

```env
# OpenAI API credentials
OPENAI_API_KEY=your_openai_api_key_here

# API URL for GPT-4 chat completions
OPENAI_API_URL=https://api.openai.com/v1/chat/completions

# Preferred language model (EchoMood uses GPT-4 by default)
OPENAI_MODEL=gpt-4
```

If you want to use **DALL·E 3** for image generation, you do not need a separate key. The same `OPENAI_API_KEY` is used to call:

```env
# API endpoint for DALL·E 3 image generation
# Used internally by EchoMood's `generate_personality_image_url()` function
IMAGE_API_URL=https://api.openai.com/v1/images/generations
```

### 🧪 Step 3: Verify the Setup

Ensure you have the OpenAI Python client installed:

```bash
pip install openai
```

Then test your key:

```python
import openai

openai.api_key = "your_openai_api_key_here"
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello, world!"}]
)
print(response.choices[0].message["content"])
```

If this returns a response from ChatGPT, your API key is working correctly.

### 🔒 Security Tips

- Never expose your `OPENAI_API_KEY` in client-side code or public GitHub repositories.
- Add `.env` to your `.gitignore` to prevent accidental commits.
- You may also use `os.environ.get()` in Python to access keys securely from the environment.

---

## 🛠️ Project Structure

```
Spotify-Mood-Analyzer/
├── .env.example
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── forms.py
│   ├── routes/
│   │   ├── user_routes.py
│   │   ├── spotify_routes.py
│   │   ├── admin_routes.py
│   │   ├── visualisation_routes.py
│   │   └── friend_routes.py
│   ├── services/
│   │   └── spotify_ingest.py
│   └── utils/
│       ├── chatgpt.py
│       └── spotify.py
├── migrations/
│   └── alembic.ini
├── static/
│   ├── css/
│   │   ├── index.css
│   │   ├── login.css
│   │   ├── visualise.css
│   │   └── share.css
│   └── js/
│       ├── index.js
│       ├── login.js
│       └── visualise.js
├── templates/
│   ├── login.html
│   ├── signup.html
│   ├── signup_cred.html
│   ├── complete_account.html
│   ├── visualise.html
│   ├── friends.html
│   ├── friend_search.html
│   └── share.html
├── instance/
│   ├── users.db
│   ├── spotify_mood.db
│   └── app.db
├── tests/
│   ├── test_unit.py
│   └── selenium/
│       ├── test_login_flow.py
│       ├── test_homepage_button.py
│       ├── test_friend_search.py
│       ├── test_send_friend_request.py
│       └── test_spotify_connect.py
├── run.py
├── requirements.txt
└── README.md
```

---

## 🚀 How to Run the App

After installing the dependencies and obtaining up the API keys, start the Flask development server by running:

```bash
python3 app.py
```

If successful, you should see output like:

```
 * Running on http://127.0.0.1:5000
```

👉 Open your browser and go to:

> **http://127.0.0.1:5000**

You should now see the Spotify Mood Analyzer web interface!

---

## 🔥 Features

- Upload Spotify listening history for analysis
- Generate mood profiles based on musical taste
- Infer MBTI personality traits using GPT-4
- Generate AI-based personality portrait via DALL·E 3
- Mood-based song recommendations using GPT
- Share visualized results with friends
- Clean, responsive web interface

---

## 🐛 Troubleshooting

- If you encounter an error like:
  ```
  ModuleNotFoundError: No module named 'flask'
  ```
  Ensure you have installed all dependencies:
  ```bash
  pip install -r requirements.txt
  ```

- To **deactivate** the virtual environment:
  ```bash
  deactivate
  ```

- Ensure you are using Python version 3.8 or higher.

## 🧪 Testing

We implemented both unit and system (Selenium) tests to verify key functionalities of the EchoMood application.

### Unit Tests (`tests/test_unit.py`)
- User registration flow and database persistence
- Admin inspection of registered users
- Spotify OAuth redirection
- Friend request creation
- Friend request acceptance and status update

All tests are self-contained and run on an in-memory test database. They simulate form submissions and validate both frontend behavior (redirects) and backend logic (data updates).

To run all unit tests:

```bash
pytest tests/test_unit.py
```

### Selenium Tests (`tests/selenium/`)
These tests simulate real user actions in the browser:

- `test_homepage_button.py`: Ensure "Get Started" button on homepage works
- `test_login_flow.py`: Log in with test account and load dashboard
- `test_friend_search.py`: Search for other users by name/email
- `test_send_friend_request.py`: Send friend request from `test` to `test2`
- `test_spotify_connect.py`: Click "Connect Spotify" and check redirect

To run all Selenium tests:

```bash
python -m unittest discover -s tests/selenium
```


---

## 📜 License

This project is licensed for personal and educational use.  
For commercial use, please contact the owner.

---

## 👌 Acknowledgements

Built with ❤️ using:
- [Flask](https://flask.palletsprojects.com/)
- [Spotify API](https://developer.spotify.com/documentation/web-api/)
- [OpenAI GPT-4 + DALL·E](https://platform.openai.com/)
- [ngrok](https://ngrok.com)

---
