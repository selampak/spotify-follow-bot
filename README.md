
# Spotify Follow Bot 🎧

This is an automated bot that follows Spotify users using a graphical interface built with Python. It stores followed users in a local SQLite database.

---

## 🛠 Requirements

### 1. Python
- Python 3.9 or higher must be installed.  
[Download Python](https://www.python.org/downloads/)

### 2. Required Python Libraries

Install the necessary libraries by running:

```bash
pip install selenium customtkinter pystray pillow webdriver-manager
```

> On Linux, `tkinter` might need to be installed separately:
> ```bash
> sudo apt install python3-tk
> ```

### 3. Chrome & Automatic ChromeDriver

- Google Chrome must be installed: [Download Chrome](https://www.google.com/chrome/)
- `webdriver-manager` automatically manages ChromeDriver — no manual download required.

Make sure this code is used for the driver:

```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
```

---

## 🚀 Running the Program

Open a terminal in the project directory and run:

```bash
python Spotify_Follow_Bot.py
```

---

## 🧾 Usage

1. Enter your Spotify login credentials.
2. Input the target user ID to start following.
3. Set limits and delay configurations.
4. Click the “Start” button to launch the bot.

---

## 💾 Data Management

- Followed users are stored in `followed_users.db` (SQLite).
- Settings are saved in `settings.json`.
- Language and theme preferences are stored in `lang/*.json` and `themes.json`.

---

## 👨‍💻 Developer

- Developer info is shown in the “Producer” tab in the GUI.
- GitHub profile can be opened directly from the app.

---

## ⚠️ Disclaimer

This bot may violate Spotify’s terms of service. Use it at your own risk — your account may be suspended.

---
