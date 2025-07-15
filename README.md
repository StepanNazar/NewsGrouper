# NewsGrouper

A news aggregation and grouping application that intelligently organizes
news articles from multiple sources into groups using machine learning clustering algorithms. Built
with Python, Flask, Gemini API, Scikit-learn and PyWebView.

![NewsGrouper Screenshot](/screenshot.png)

## 🚀 Features

- **Intelligent News Grouping**: Automatically groups related news articles and provides AI summary
- **Multi-Source Support**: Aggregates news from various sources (currently supports RSS feeds and Telegram channels)
- **Web Application**: Fully functional web app with user authentication
- **Desktop Application**: Desktop app which runs locally without requiring a remote web server or account creation
- **User Profiles**: Users can create profiles with different news sources per profile

## 🛠️ Technology Stack

- **Backend**: Python, Flask, APIFlask, Flask-SQLAlchemy, Flask-Migrate
- **Machine Learning**: DBSCAN clustering, Gemini text embeddings for semantic similarity
- **Desktop**: PyWebView for desktop app and `pyshortcuts` for creating desktop shortcuts
- **Authentication**: JWT tokens with a refresh mechanism using `Flask-JWT-Extended` library
- **News Parsing**: RSS feed processing using `feedparser` and `beautifulsoup4` libraries

## 📦 Installation

### Desktop App Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/StepanNazar/NewsGrouper.git
   cd NewsGrouper
   ```

1. **Create and activate virtual environment (preferred)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

1. **Install dependencies**

   ```bash
    pip install -r requirements.txt
   ```

1. **Get [Gemini API key](https://aistudio.google.com/apikey)**

1. **Copy `.env.example` to `.env` and set your Gemini API key**

   Edit the `.env` file and set `GEMINI_API_KEY` to your actual API key.

1. **Run the desktop application**

   ```bash
   python src/news_grouper/desktop_app/main.py
   ```

1. **You can create desktop shortcut in app interface and access app from your Desktop or Application menu**

### Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/StepanNazar/NewsGrouper.git
   cd NewsGrouper
   ```

1. **Create and activate virtual environment (preferred)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -r dev-requirements.txt
   ```

1. **Set up the database**

   ```bash
   flask db upgrade
   ```

1. **Get [Gemini API key](https://aistudio.google.com/apikey)**

1. **Copy `.env.example` to `.env` and set your Gemini API key**

   Edit the `.env` file and set `GEMINI_API_KEY` to your actual API key.

1. **Run the development server**

   ```bash
   flask run
   ```

   The API will be available at `http://localhost:5000`
