# Velora 🌐

**Velora** is a sleek, modern, full-stack social media application designed to bring people together. Share your stories, discover amazing content, and connect with friends globally.

## ✨ Features
- **User Authentication:** Secure signup and login system using hashed passwords.
- **Dynamic Feed:** Real-time post feed with accurate "time-ago" timestamps.
- **Instagram-Style Carousels:** Create and view swipeable, multi-image post carousels.
- **Hashtag Parsing:** Automatic in-text rendering of `#hashtags`.
- **Social Engagement:** Like, comment, and connect (follow) with other users.
- **Profile Management:** Edit profile details, view personal posts, and track connections.
- **Responsive Design:** Mobile-first, sleek UI built with Bootstrap 5 and custom CSS.

## 🚀 Tech Stack
- **Backend:** Python, Flask
- **Database:** PostgreSQL (with SQLAlchemy ORM)
- **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2, JavaScript
- **Animations:** AOS (Animate On Scroll)

## 🛠️ Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Velora.git
   cd Velora
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows use: myenv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Set up your local environment variables for the database:
   ```bash
   export DATABASE_URL="postgresql://username:password@localhost/velora"
   export SECRET_KEY="your_secret_key_here"
   ```
   *(If `DATABASE_URL` is omitted, the app will default to a local SQLite database for quick testing).*

5. **Run the Application:**
   ```bash
   flask run
   ```
   *The app will be running at http://127.0.0.1:5000/*

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!

## 📝 License
This project is open-source and available under the [MIT License](LICENSE).
