import os
import django

# Django környezet beállítása
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_battle.settings')
django.setup()

from quiz.models import EmojiMovie

# Példa filmek és emoji megfelelőik
EMOJI_MOVIES = [
    {
        'title': 'Titanic',
        'emoji_representation': '🚢 ❄️ 💑',
        'year': 1997,
        'genre': 'Romance',
        'difficulty': 1
    },
    {
        'title': 'The Lion King',
        'emoji_representation': '🦁 👑 🌅',
        'year': 1994,
        'genre': 'Animation',
        'difficulty': 1
    },
    {
        'title': 'The Matrix',
        'emoji_representation': '🕶️ 💊 🌐',
        'year': 1999,
        'genre': 'Sci-Fi',
        'difficulty': 2
    },
    {
        'title': 'Jurassic Park',
        'emoji_representation': '🦖 🦕 🏝️',
        'year': 1993,
        'genre': 'Adventure',
        'difficulty': 1
    },
    {
        'title': 'The Godfather',
        'emoji_representation': '👨‍👦 🎭 🍷',
        'year': 1972,
        'genre': 'Crime',
        'difficulty': 3
    },
    {
        'title': 'Star Wars',
        'emoji_representation': '⚔️ 🌟 🚀',
        'year': 1977,
        'genre': 'Sci-Fi',
        'difficulty': 1
    },
    {
        'title': 'The Wizard of Oz',
        'emoji_representation': '👠 🌈 🏰',
        'year': 1939,
        'genre': 'Fantasy',
        'difficulty': 2
    },
    {
        'title': 'Jaws',
        'emoji_representation': '🦈 🌊 🏖️',
        'year': 1975,
        'genre': 'Thriller',
        'difficulty': 2
    },
    {
        'title': 'The Silence of the Lambs',
        'emoji_representation': '🦋 🧠 🎭',
        'year': 1991,
        'genre': 'Thriller',
        'difficulty': 4
    },
    {
        'title': 'Back to the Future',
        'emoji_representation': '⏰ 🚗 ⚡',
        'year': 1985,
        'genre': 'Sci-Fi',
        'difficulty': 2
    },
    {
        'title': 'Forrest Gump',
        'emoji_representation': '🏃 🍫 🏃',
        'year': 1994,
        'genre': 'Drama',
        'difficulty': 2
    },
    {
        'title': 'The Shining',
        'emoji_representation': '🏨 👨‍👦 🔪',
        'year': 1980,
        'genre': 'Horror',
        'difficulty': 3
    },
    {
        'title': 'Pulp Fiction',
        'emoji_representation': '💼 💉 🎭',
        'year': 1994,
        'genre': 'Crime',
        'difficulty': 3
    },
    {
        'title': 'The Dark Knight',
        'emoji_representation': '🦇 🃏 🎭',
        'year': 2008,
        'genre': 'Action',
        'difficulty': 2
    },
    {
        'title': 'Inception',
        'emoji_representation': '💭 🎡 🌪️',
        'year': 2010,
        'genre': 'Sci-Fi',
        'difficulty': 3
    },
    {
        'title': 'The Lord of the Rings',
        'emoji_representation': '💍 🧙‍♂️ 🧝‍♂️',
        'year': 2001,
        'genre': 'Fantasy',
        'difficulty': 2
    },
    {
        'title': 'Fight Club',
        'emoji_representation': '👊 🧼 💥',
        'year': 1999,
        'genre': 'Drama',
        'difficulty': 3
    },
    {
        'title': 'The Hangover',
        'emoji_representation': '🍺 🐯 👶',
        'year': 2009,
        'genre': 'Comedy',
        'difficulty': 2
    },
    {
        'title': 'The Notebook',
        'emoji_representation': '📔 💑 🌧️',
        'year': 2004,
        'genre': 'Romance',
        'difficulty': 1
    },
    {
        'title': 'The Avengers',
        'emoji_representation': '🦸‍♂️ 🦸‍♀️ 💥',
        'year': 2012,
        'genre': 'Action',
        'difficulty': 1
    },
    {
        'title': 'The Social Network',
        'emoji_representation': '💻 👨‍💻 👥',
        'year': 2010,
        'genre': 'Drama',
        'difficulty': 2
    },
    {
        'title': 'La La Land',
        'emoji_representation': '🎵 💃 🌟',
        'year': 2016,
        'genre': 'Musical',
        'difficulty': 2
    },
    {
        'title': 'The Grand Budapest Hotel',
        'emoji_representation': '🏨 🎭 🎪',
        'year': 2014,
        'genre': 'Comedy',
        'difficulty': 3
    },
    {
        'title': 'The Revenant',
        'emoji_representation': '🐻 ❄️ 🏹',
        'year': 2015,
        'genre': 'Adventure',
        'difficulty': 3
    },
    {
        'title': 'The Wolf of Wall Street',
        'emoji_representation': '💰 🎭 🚀',
        'year': 2013,
        'genre': 'Biography',
        'difficulty': 3
    }
]

def populate_database():
    # Töröljük a meglévő adatokat
    EmojiMovie.objects.all().delete()
    
    # Új filmek hozzáadása
    for movie_data in EMOJI_MOVIES:
        EmojiMovie.objects.create(**movie_data)
        print(f"Added: {movie_data['title']}")

if __name__ == '__main__':
    print("Populating database with emoji movies...")
    populate_database()
    print("Database population completed!") 