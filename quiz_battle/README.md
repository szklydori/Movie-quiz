# Emoji Film Quiz (Django)

## Installation & Usage

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd <repo-folder>
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate    # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```

6. **Open in browser:**
   [http://127.0.0.1:8000/]

## How to Run the Tests

1. Make sure you are in your virtual environment and in the project root.
2. Run:
   ```bash
   pytest
   ```


## Documentation, details

After submitting my project proposition, I started working on the implementation. My first step was to set up the Django project structure and lay the foundation for the main features. The application is built around three core quiz types:

### 1. Image Recognition Quiz
Players are shown a movie image and must guess the correct movie title from multiple choices.
- **Implementation:**
  - Uses the TMDb (The Movie Database) API to fetch popular movies and their images
  - (The API key is stored in the `views.py` file)
  - For each question, a random movie is selected, and its image is displayed 

### 2. Actor-Based Quiz
Players are given a list of actors and must guess who they are, what is their name
- **Implementation:**
  - Also leverages the TMDb API to display pictures of actors, actresses
  - The logic for fetching and displaying actor-related questions is handled in the Django views

### 3. Emoji Quiz
Players see a sequence of emojis that represent a movie and must guess the correct title.
- **Implementation:**
  - My original plan was to use the OpenAI API to dynamically generate emoji sequences for movies
  - However, for simplicity and reliability, I decided to pre-generate emoji sequences for 100 movies using ChatGPT and store them in a separate database table
  - This approach eliminated the need for live API calls to OpenAI, making the quiz faster and more stable

### Quiz Difficulty Levels
For each quiz type, users can choose between **Easy** and **Hard** modes:
- **Easy Mode:**  The quiz presents multiple-choice questions, allowing users to select the correct answer from a list of options
- **Hard Mode:**  Users must type in the correct answer themselves, without any answer choices provided. This mode increases the challenge and tests the user's  knowledge.

This dual-difficulty system makes the application accessible for casual players while also providing a challenge for more experienced users.

### Real-Time Battle Mode
The application also features a **real-time battle mode** where two players can compete against each other:
- Players can join a battle room and answer the same questions in real time
- The system keeps track of both players' answers and scores
- At the end of the battle, the winner is determined based on the highest score, or a draw is declared if scores are equal
- The battle mode uses Django Channels and WebSockets for real-time communication, ensuring a responsive and interactive multiplayer experience

### Database Management & Django Admin
- **Database Models:**  The application uses Django's ORM to define models for users, profiles, quiz results, questions, answers, films, and emoji-movie mappings. All quiz data, user progress, and emoji sequences are stored in the database.
- **Data Handling:**  For the emoji quiz, emoji sequences for 100 movies were pre-generated and imported into the database using a custom script. The TMDb API is used to dynamically fetch movie and actor data for the other quiz types, but all user answers and results are stored persistently.
- **Django Admin Interface:**  The Django admin interface is enabled and configured for all major models. You can access the admin panel at `/admin` (username: admin password: 0123). Through the admin interface, you can:
    - View, add, edit, or delete users, profiles, quiz results, questions, answers, films, and emoji-movie entries
    - Easily inspect user progress, quiz statistics, and the emoji database
    - Manage or update the emoji-movie mappings if you want to add new movies or update emoji sequences
- **Database Migrations:**  All model changes are managed using Django's migration system (python manage.py makemigrations and python manage.py migrate). This ensures the database schema is always in sync with the codebase.

### Additional Features
- **Challenge Mode:**  A time-limited (60 seconds) quiz mode where users answer as many questions as possible. Scores are saved and displayed in the user's profile. The mode is implemented as a single-page AJAX application for a seamless user experience.
- **User Profiles & Leaderboard:**  Each user has a profile page showing their total score, best game, achievements, and personal challenge mode high scores. The leaderboard displays the top scores for all users (except challenge mode which is personal so everyone can see only themselves).
- **Testing:**  The project includes comprehensive unit and integration tests using pytest and pytest-django. Tests cover models, forms, views, API endpoints, session handling, and edge cases.
- **Frontend:**  The HTML interface uses a simple Bootstrap-based design for a clean and responsive look.





