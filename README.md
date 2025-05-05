# EchoMood

![Made with Flask](https://img.shields.io/badge/Made%20with-Flask-blue)
![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-Personal%20Use-lightgrey)

---

## 🎵 Project Overview


EchoMood is a web application for analyzing your Spotify listening history and visualizing user moods and personality traits based on music preferences.  
Upload your Spotify data and generate beautiful, insightful visualizations of your musical personality!

---

## ⚙️ Requirements

- Python 3.8+
- pip (Python package installer)

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

## 🚀 How to Run the App

After installing the dependencies, start the Flask development server by running:

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

## 🛠️ Project Structure

```
Spotify-Mood-Analyzer/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── index.html
│   ├── visualise.html
│   ├── upload.html
│   └── share.html
└── static/
    ├── css/
    │   ├── index.css
    │   ├── visualise.css
    │   ├── upload.css
    │   └── share.css
    └── js/
        ├── index.js
        ├── visualise.js
        ├── upload.js
        └── share.js
```

- `app.py` — Main Flask application.
- `templates/` — HTML templates rendered by Flask.
- `static/css/` — CSS files, one for each HTML page.
- `static/js/` — JavaScript files, one for each HTML page. 
- `requirements.txt` — Python dependencies.
- `README.md` — Project documentation.

---

## 🔥 Features

- Upload Spotify listening history for analysis.
- Generate mood profiles based on musical taste.
- Visualize inferred personality traits.
- Share visualized results easily.
- Clean, responsive web interface.

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

- Make sure you are using Python version 3.8 or higher.

---

## 📜 License

This project is licensed for personal and educational use.  
For commercial use, please contact the owner.

---

## 👌 Acknowledgements

Built with ❤️ using:
- [Flask](https://flask.palletsprojects.com/)
- [Spotify API](https://developer.spotify.com/documentation/web-api/)

---

