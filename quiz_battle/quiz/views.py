from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from .models import EmojiMovieDatabase, Profile, QuizResult, Question, Answer, Film
import requests
import random
import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
import time
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

API_KEY = '65ac317aa28e9852f0dd9c6145b376e8'  # my TMDb API key

# Global room list (for demo, not production!)
GLOBAL_BATTLE_ROOMS = {}  # room_name -> set of usernames

# Globális szobakérdés-tároló (szoba_név -> kérdés)
GLOBAL_BATTLE_QUESTIONS = {}  # room_name -> question data

def get_movie_list():
    url = f'https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=hu-HU&page=1'
    response = requests.get(url)
    data = response.json()
    results = data.get('results', [])
    movie_titles = [movie['title'] for movie in results]
    return movie_titles

def index(request):
    return render(request, 'quiz/index.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profile')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def get_movie_backdrop(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}/images?api_key={API_KEY}'
    response = requests.get(url)
    data = response.json()
    backdrops = data.get('backdrops', [])
    if backdrops:
        image_url = 'https://image.tmdb.org/t/p/original' + backdrops[0]['file_path']
        return image_url
    return None

def search_movie(query):
    url = f'https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={query}'
    response = requests.get(url)
    data = response.json()
    results = data.get('results', [])
    if results:
        return results[0]['id']  # the first result's id
    return None

def get_random_movies(n=3):
    url = f'https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}&language=en-US&sort_by=vote_average.desc&vote_count.gte=1000'
    response = requests.get(url)
    data = response.json()
    total_pages = data.get('total_pages', 1)
    max_page = min(total_pages, 500)
    movies = set()
    attempts = 0
    while len(movies) < n and attempts < 10:
        page = random.randint(1, max_page)
        page_url = url + f'&page={page}'
        resp = requests.get(page_url)
        d = resp.json()
        results = d.get('results', [])
        if results:
            movie = random.choice(results)
            title = movie.get('title')
            if title:
                movies.add(title)
        attempts += 1
    return list(movies)

def select_movie_quiz_difficulty(request):
    return render(request, 'quiz/select_movie_quiz_difficulty.html')

def movie_quiz(request):
    feedback = None
    selected_movie = None
    image_url = None
    choices = []
    selected_choice = None
    is_correct = None

    difficulty = request.GET.get('difficulty', 'easy')
    if difficulty not in ['easy', 'hard']:
        return redirect('select_movie_quiz_difficulty')

    quiz_result_id = request.session.get('movie_quiz_result_id')
    quiz_result = None
    if not quiz_result_id:
        quiz_result = QuizResult.objects.create(
            user=request.user,
            quiz_type='image',
            score=0,
            is_challenge=False
        )
        request.session['movie_quiz_result_id'] = quiz_result.id
    else:
        try:
            quiz_result = QuizResult.objects.get(id=quiz_result_id)
        except QuizResult.DoesNotExist:
            quiz_result = QuizResult.objects.create(
                user=request.user,
                quiz_type='image',
                score=0,
                is_challenge=False
            )
            request.session['movie_quiz_result_id'] = quiz_result.id

#not asking the same movie again
    already_asked_titles = set(quiz_result.questions.values_list('content', flat=True))

    def get_movie_with_image(movie_titles):
        random.shuffle(movie_titles)
        for title in movie_titles:
            if title in already_asked_titles:
                continue
            movie_id = search_movie(title)
            if movie_id:
                img_url = get_movie_backdrop(movie_id)
                if img_url:
                    return title, img_url, movie_id
        return None, None, None

    if request.method == 'POST':
        selected_choice = request.POST.get('movie_title')
        correct_title = request.POST.get('correct_title')
        choices_json = request.POST.get('choices_json')
        if choices_json:
            try:
                choices = json.loads(choices_json)
            except json.JSONDecodeError:
                choices = []
        else:
            choices = []
        if 'dont_know' in request.POST:
            feedback = f"The correct answer was: {correct_title}"
            is_correct = None
        elif selected_choice and correct_title:
            is_correct = (selected_choice.strip().lower() == correct_title.strip().lower())
            if is_correct:
                feedback = "Correct answer! 🎉"
                if difficulty == 'hard':
                    request.user.profile.score += 5
                    quiz_result.score += 5
                else:
                    request.user.profile.score += 2
                    quiz_result.score += 2
                request.user.profile.save()
                quiz_result.save()
            else:
                feedback = f"Wrong! The correct answer was: {correct_title}"
        selected_movie = correct_title
        movie_id = search_movie(selected_movie)
        if movie_id:
            image_url = get_movie_backdrop(movie_id)
            if not image_url:
                return redirect(f"{reverse('movie_quiz')}?difficulty={difficulty}")
        else:
            return redirect(f"{reverse('movie_quiz')}?difficulty={difficulty}")

        #save the questions
        film_obj, _ = Film.objects.get_or_create(title=selected_movie)
        question_obj = Question.objects.create(
            quiz_result=quiz_result,
            type='image',
            content=selected_movie,
            correct_answer=correct_title,
            difficulty=2 if difficulty == 'hard' else 1,
            film=film_obj
        )
        #save the answers
        Answer.objects.create(
            quiz_result=quiz_result,
            question=question_obj,
            selected_option=selected_choice or '',
            is_correct=is_correct if is_correct is not None else False
        )
    else:
        max_attempts = 10
        for _ in range(max_attempts):
            MOVIE_LIST = get_random_movies(3)
            # only those movies that have not been asked yet
            MOVIE_LIST = [m for m in MOVIE_LIST if m not in already_asked_titles]
            if not MOVIE_LIST:
                continue
            movie_with_image, img_url, movie_id = get_movie_with_image(MOVIE_LIST)
            if movie_with_image and img_url:
                selected_movie = movie_with_image
                image_url = img_url
                wrong_choices = [m for m in MOVIE_LIST if m != selected_movie]
                if len(wrong_choices) >= 2:
                    wrong_options = random.sample(wrong_choices, 2)
                else:
                    wrong_options = wrong_choices
                choices = [selected_movie] + wrong_options
                random.shuffle(choices)
                break
        else:
            return render(request, 'quiz/movie_quiz.html', {
                'image_url': None,
                'correct_title': None,
                'feedback': 'No more unique movies available for this game.',
                'choices': [],
                'selected_choice': None,
                'is_correct': None,
                'choices_json': '[]',
                'difficulty': difficulty
            })
    return render(request, 'quiz/movie_quiz.html', {
        'image_url': image_url,
        'correct_title': selected_movie,
        'feedback': feedback,
        'choices': choices,
        'selected_choice': selected_choice,
        'is_correct': is_correct,
        'choices_json': json.dumps(choices),
        'difficulty': difficulty
    })

def select_emoji_quiz_difficulty(request):
    return render(request, 'quiz/select_emoji_quiz_difficulty.html')

def emoji_quiz(request):
    movies = list(EmojiMovieDatabase.objects.all())
    if not movies:
        return render(request, 'quiz/emoji_quiz.html', {
            'error': 'No movies found in database. Please run the populate script first.'
        })

    difficulty = request.GET.get('difficulty', 'easy')
    if difficulty not in ['easy', 'hard']:
        return redirect('select_emoji_quiz_difficulty')

    #quiz result handling
    quiz_result_id = request.session.get('emoji_quiz_result_id')
    quiz_result = None
    if not quiz_result_id:
        quiz_result = QuizResult.objects.create(
            user=request.user,
            quiz_type='emoji',
            score=0,
            is_challenge=False
        )
        request.session['emoji_quiz_result_id'] = quiz_result.id
    else:
        try:
            quiz_result = QuizResult.objects.get(id=quiz_result_id)
        except QuizResult.DoesNotExist:
            quiz_result = QuizResult.objects.create(
                user=request.user,
                quiz_type='emoji',
                score=0,
                is_challenge=False
            )
            request.session['emoji_quiz_result_id'] = quiz_result.id

    # not asking the same emoji again
    already_asked_emojis = set(quiz_result.questions.values_list('content', flat=True))

    def get_choices(current_movie, movies):
        all_titles = [m.title for m in movies]
        choices = [current_movie.title]
        while len(choices) < 3:
            c = random.choice(all_titles)
            if c not in choices:
                choices.append(c)
        random.shuffle(choices)
        return choices

    if request.method == 'POST':
        if 'next' in request.POST:
            unused_movies = [m for m in movies if m.emoji_representation not in already_asked_emojis]
            if not unused_movies:
                return render(request, 'quiz/emoji_quiz.html', {
                    'error': 'No more unique emoji questions available for this game.'
                })
            next_movie = random.choice(unused_movies)
            if difficulty == 'easy':
                choices = get_choices(next_movie, movies)
                return render(request, 'quiz/emoji_quiz.html', {
                    'movie': next_movie,
                    'choices': choices,
                    'difficulty': difficulty
                })
            else:
                return render(request, 'quiz/emoji_quiz.html', {
                    'movie': next_movie,
                    'difficulty': difficulty
                })
        current_movie_id = request.POST.get('movie_id')
        try:
            current_movie = EmojiMovieDatabase.objects.get(id=current_movie_id)
        except EmojiMovieDatabase.DoesNotExist:
            unused_movies = [m for m in movies if m.emoji_representation not in already_asked_emojis]
            if not unused_movies:
                return render(request, 'quiz/emoji_quiz.html', {
                    'error': 'No more unique emoji questions available for this game.'
                })
            current_movie = random.choice(unused_movies)
        if 'dont_know' in request.POST:
            if difficulty == 'easy':
                choices = get_choices(current_movie, movies)
                film_obj, _ = Film.objects.get_or_create(title=current_movie.title)
                question_obj = Question.objects.create(
                    quiz_result=quiz_result,
                    type='emoji',
                    content=current_movie.emoji_representation,
                    correct_answer=current_movie.title,
                    difficulty=1,
                    film=film_obj
                )
                Answer.objects.create(
                    quiz_result=quiz_result,
                    question=question_obj,
                    selected_option='',
                    is_correct=False
                )
                return render(request, 'quiz/emoji_quiz.html', {
                    'movie': current_movie,
                    'previous_answer': current_movie.title,
                    'is_correct': None,
                    'show_next': True,
                    'choices': choices,
                    'difficulty': difficulty
                })
            else:
                film_obj, _ = Film.objects.get_or_create(title=current_movie.title)
                question_obj = Question.objects.create(
                    quiz_result=quiz_result,
                    type='emoji',
                    content=current_movie.emoji_representation,
                    correct_answer=current_movie.title,
                    difficulty=2,
                    film=film_obj
                )
                Answer.objects.create(
                    quiz_result=quiz_result,
                    question=question_obj,
                    selected_option='',
                    is_correct=False
                )
                return render(request, 'quiz/emoji_quiz.html', {
                    'movie': current_movie,
                    'previous_answer': current_movie.title,
                    'is_correct': None,
                    'show_next': True,
                    'difficulty': difficulty
                })
        if difficulty == 'easy':
            selected_choice = request.POST.get('answer')
            choices = get_choices(current_movie, movies)
            is_correct = selected_choice and (selected_choice.strip().lower() == current_movie.title.lower())
            film_obj, _ = Film.objects.get_or_create(title=current_movie.title)
            question_obj = Question.objects.create(
                quiz_result=quiz_result,
                type='emoji',
                content=current_movie.emoji_representation,
                correct_answer=current_movie.title,
                difficulty=1,
                film=film_obj
            )
            Answer.objects.create(
                quiz_result=quiz_result,
                question=question_obj,
                selected_option=selected_choice or '',
                is_correct=bool(is_correct)
            )
            if is_correct:
                request.user.profile.score += 2
                quiz_result.score += 2
                request.user.profile.save()
                quiz_result.save()
                return render(request, 'quiz/emoji_quiz.html', {
                    'movie': current_movie,
                    'previous_answer': current_movie.title,
                    'is_correct': True,
                    'user_answer': selected_choice,
                    'show_next': True,
                    'choices': choices,
                    'difficulty': difficulty
                })
            else:
                return render(request, 'quiz/emoji_quiz.html', {
                    'movie': current_movie,
                    'previous_answer': current_movie.title,
                    'is_correct': False,
                    'user_answer': selected_choice,
                    'show_next': True,
                    'choices': choices,
                    'difficulty': difficulty
                })
        else:
            user_answer = request.POST.get('answer', '').strip().lower()
            correct_answer = current_movie.title.lower()
            is_correct = user_answer == correct_answer
            film_obj, _ = Film.objects.get_or_create(title=current_movie.title)
            question_obj = Question.objects.create(
                quiz_result=quiz_result,
                type='emoji',
                content=current_movie.emoji_representation,
                correct_answer=current_movie.title,
                difficulty=2,
                film=film_obj
            )
            Answer.objects.create(
                quiz_result=quiz_result,
                question=question_obj,
                selected_option=user_answer,
                is_correct=is_correct
            )
            if is_correct:
                if difficulty == 'hard':
                    request.user.profile.score += 5
                    quiz_result.score += 5
                else:
                    request.user.profile.score += 2
                    quiz_result.score += 2
                request.user.profile.save()
                quiz_result.save()
                unused_movies = [m for m in movies if m.emoji_representation not in already_asked_emojis]
                if not unused_movies:
                    return render(request, 'quiz/emoji_quiz.html', {
                        'error': 'No more unique emoji questions available for this game.'
                    })
                next_movie = random.choice([m for m in unused_movies if m != current_movie])
                return render(request, 'quiz/emoji_quiz.html', {
                    'movie': next_movie,
                    'previous_answer': current_movie.title,
                    'is_correct': True,
                    'user_answer': user_answer,
                    'difficulty': difficulty
                })
            else:
                return render(request, 'quiz/emoji_quiz.html', {
                    'movie': current_movie,
                    'previous_answer': current_movie.title,
                    'is_correct': False,
                    'user_answer': user_answer,
                    'show_next': True,
                    'difficulty': difficulty
                })
    # GET request
    unused_movies = [m for m in movies if m.emoji_representation not in already_asked_emojis]
    if not unused_movies:
        return render(request, 'quiz/emoji_quiz.html', {
            'error': 'No more unique emoji questions available for this game.'
        })
    current_movie = random.choice(unused_movies)
    if difficulty == 'easy':
        choices = get_choices(current_movie, movies)
        return render(request, 'quiz/emoji_quiz.html', {
            'movie': current_movie,
            'choices': choices,
            'difficulty': difficulty
        })
    else:
        return render(request, 'quiz/emoji_quiz.html', {
            'movie': current_movie,
            'difficulty': difficulty
        })

def get_random_actors_by_gender(gender, n=3):
    url = f'https://api.themoviedb.org/3/person/popular?api_key={API_KEY}&language=en-US&page=1'
    response = requests.get(url)
    data = response.json()
    results = data.get('results', [])
    filtered = [actor for actor in results if actor.get('gender') == gender]
    if len(filtered) < n:
        return []
    return random.sample(filtered, n)

def select_actor_quiz_difficulty(request):
    return render(request, 'quiz/select_actor_quiz_difficulty.html')

def actor_quiz(request):
    feedback = None
    selected_actor = None
    choices = []
    selected_choice = None
    is_correct = None
    actor_image = None

    difficulty = request.GET.get('difficulty', 'easy')
    if difficulty not in ['easy', 'hard']:
        return redirect('select_actor_quiz_difficulty')

    quiz_result_id = request.session.get('actor_quiz_result_id')
    quiz_result = None
    if not quiz_result_id:
        quiz_result = QuizResult.objects.create(
            user=request.user,
            quiz_type='actor',
            score=0,
            is_challenge=False
        )
        request.session['actor_quiz_result_id'] = quiz_result.id
    else:
        try:
            quiz_result = QuizResult.objects.get(id=quiz_result_id)
        except QuizResult.DoesNotExist:
            quiz_result = QuizResult.objects.create(
                user=request.user,
                quiz_type='actor',
                score=0,
                is_challenge=False
            )
            request.session['actor_quiz_result_id'] = quiz_result.id

    already_asked_actors = set(quiz_result.questions.values_list('correct_answer', flat=True))

    if request.method == 'POST':
        selected_choice = request.POST.get('actor_name')
        correct_name = request.POST.get('correct_name')
        choices_json = request.POST.get('choices_json')
        actor_image = request.POST.get('actor_image')
        if choices_json:
            try:
                choices = json.loads(choices_json)
            except json.JSONDecodeError:
                choices = []
        else:
            choices = []
        # Don't know button handling
        if 'dont_know' in request.POST:
            feedback = f"The correct answer was: {correct_name}"
            is_correct = None
        elif selected_choice and correct_name:
            is_correct = (selected_choice.strip().lower() == correct_name.strip().lower())
            if is_correct:
                feedback = "Correct answer! 🎉"
                if difficulty == 'hard':
                    request.user.profile.score += 5
                    quiz_result.score += 5
                else:
                    request.user.profile.score += 2
                    quiz_result.score += 2
                request.user.profile.save()
                quiz_result.save()
            else:
                feedback = f"Wrong! The correct answer was: {correct_name}"
        selected_actor = correct_name

        film_obj = None  #there is no specific film, only the actor
        question_obj = Question.objects.create(
            quiz_result=quiz_result,
            type='actor',
            content=actor_image or '',
            correct_answer=correct_name,
            difficulty=2 if difficulty == 'hard' else 1,
            film=film_obj
        )
        Answer.objects.create(
            quiz_result=quiz_result,
            question=question_obj,
            selected_option=selected_choice or '',
            is_correct=is_correct if is_correct is not None else False
        )
    else:
        max_attempts = 5
        found = False
        for attempt in range(max_attempts):
            if attempt == 0:
                page = 1  # in the first round, the most popular actors
            else:
                page = random.randint(2, 100)  # after that random pages
            url = f'https://api.themoviedb.org/3/person/popular?api_key={API_KEY}&language=en-US&page={page}'
            response = requests.get(url)
            data = response.json()
            results = data.get('results', [])
            unused_actors = [actor for actor in results if actor.get('name') not in already_asked_actors]
            if len(unused_actors) >= 3:
                found = True
                break
        #if we still don't have enough actors, let's use the whole list
        if not found:
            unused_actors = results if results else []
        if not unused_actors or len(unused_actors) < 3:
            return render(request, 'quiz/actor_quiz.html', {
                'actor_image': None,
                'correct_name': None,
                'feedback': 'No more actors available for this game.',
                'choices': [],
                'selected_choice': None,
                'is_correct': None,
                'choices_json': '[]',
                'difficulty': difficulty
            })
        correct_actor = random.choice(unused_actors)
        gender = correct_actor.get('gender')
        same_gender_actors = [actor for actor in unused_actors if actor.get('gender') == gender and actor != correct_actor]
        #if there is not enough actors, let's use the whole list
        if len(same_gender_actors) < 2:
            same_gender_actors = [actor for actor in results if actor.get('gender') == gender and actor != correct_actor]
        if len(same_gender_actors) < 2:
            # if there is not enough actors, let's use the whole list
            same_gender_actors = [actor for actor in results if actor.get('gender') == gender]
            same_gender_actors = [actor for actor in same_gender_actors if actor != correct_actor]
        if len(same_gender_actors) < 2:
            return render(request, 'quiz/actor_quiz.html', {
                'actor_image': None,
                'correct_name': None,
                'feedback': 'No more actors available for this game.',
                'choices': [],
                'selected_choice': None,
                'is_correct': None,
                'choices_json': '[]',
                'difficulty': difficulty
            })
        options = random.sample(same_gender_actors, 2) + [correct_actor]
        random.shuffle(options)
        selected_actor = correct_actor['name']
        actor_image = f"https://image.tmdb.org/t/p/w300{correct_actor['profile_path']}" if correct_actor.get('profile_path') else None
        choices = [actor['name'] for actor in options]
    return render(request, 'quiz/actor_quiz.html', {
        'actor_image': actor_image,
        'correct_name': selected_actor,
        'feedback': feedback,
        'choices': choices,
        'selected_choice': selected_choice,
        'is_correct': is_correct,
        'choices_json': json.dumps(choices),
        'difficulty': difficulty
    })

@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    # Game history 
    game_history = QuizResult.objects.filter(user=request.user).order_by('-started_at')
    # Best score 
    best_result = game_history.order_by('-score').first()
    # Achievements 
    achievements = []
    total_score = profile.score
    total_games = game_history.count()
    total_correct = Answer.objects.filter(quiz_result__user=request.user, is_correct=True).count()
    if total_score >= 100:
        achievements.append('Scored 100+ points!')
    if total_games >= 10:
        achievements.append('Played 10+ games!')
    if total_correct >= 20:
        achievements.append('20+ correct answers!')
    
    # Csak a saját challenge mode eredmények
    challenge_scores = QuizResult.objects.filter(
        is_challenge=True,
        user=request.user
    ).order_by('-score')[:10]
    
    return render(request, 'quiz/profile.html', {
        'profile': profile,
        'game_history': game_history,
        'best_result': best_result,
        'achievements': achievements,
        'challenge_scores': challenge_scores
    })

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Successfully registered! Please sign in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def rank(request):
    profiles = Profile.objects.select_related('user').order_by('-score')
    return render(request, 'quiz/rank.html', {'profiles': profiles})

movie_id = search_movie('Inception')
print(get_movie_backdrop(movie_id))

@login_required
def battle(request):
    global GLOBAL_BATTLE_ROOMS
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        action = request.POST.get('action')
        if action == 'create' and room_name:
            if room_name not in GLOBAL_BATTLE_ROOMS:
                # Új szoba létrehozása, a felhasználóval
                GLOBAL_BATTLE_ROOMS[room_name] = {request.user.username}
                return redirect('battle_room', room_name=room_name)
            else:
                messages.error(request, 'This room name already exists!')
        elif action == 'join' and room_name:
            if room_name in GLOBAL_BATTLE_ROOMS:
                if len(GLOBAL_BATTLE_ROOMS[room_name]) < 2:
                    GLOBAL_BATTLE_ROOMS[room_name].add(request.user.username)
                    return redirect('battle_room', room_name=room_name)
                else:
                    messages.error(request, 'This room is full!')
            else:
                messages.error(request, 'Room does not exist!')

    # Csak azokat a szobákat mutatjuk, ahol még van hely
    available_rooms = {
        room: players
        for room, players in GLOBAL_BATTLE_ROOMS.items()
        if len(players) < 2 or request.user.username in players
    }

    return render(request, 'quiz/battle.html', {
        'active_rooms': available_rooms,
        'username': request.user.username
    })

@login_required
def battle_room(request, room_name):
    global GLOBAL_BATTLE_ROOMS, GLOBAL_BATTLE_QUESTIONS
    
    # Ellenőrizzük, hogy a játékos a szobában van-e
    if room_name not in GLOBAL_BATTLE_ROOMS or request.user.username not in GLOBAL_BATTLE_ROOMS[room_name]:
        messages.error(request, 'You are not in this room!')
        return redirect('battle')
    
    # Ha a szoba nem létezik a kérdések között, generálunk egyet
    if room_name not in GLOBAL_BATTLE_QUESTIONS:
        MOVIE_LIST = get_random_movies(3)
        for title in MOVIE_LIST:
            movie_id = search_movie(title)
            if movie_id:
                img_url = get_movie_backdrop(movie_id)
                if img_url:
                    old_scores = GLOBAL_BATTLE_QUESTIONS.get(room_name, {}).get('scores', {})
                    # Frissítsd, hogy minden játékos benne legyen
                    for user in GLOBAL_BATTLE_ROOMS[room_name]:
                        if user not in old_scores:
                            old_scores[user] = 0
                    GLOBAL_BATTLE_QUESTIONS[room_name] = {
                        'title': title,
                        'image_url': img_url,
                        'answered_users': set(),
                        'scores': old_scores
                    }
                    break
        else:
            GLOBAL_BATTLE_QUESTIONS[room_name] = {
                'title': None,
                'image_url': None,
                'answered_users': set(),
                'scores': {username: 0 for username in GLOBAL_BATTLE_ROOMS[room_name]}
            }

    question = GLOBAL_BATTLE_QUESTIONS[room_name]
    
    show_feedback = False
    is_correct = None
    user_answer = ''
    game_finished = False
    winner = None
    winner_score = None
    is_draw = False

    if request.method == 'POST':
        if 'next_question' in request.POST:
            # Csak akkor generálj új kérdést, ha tényleg mindkét játékos válaszolt
            if len(question['answered_users']) == 2:
                MOVIE_LIST = get_random_movies(3)
                for title in MOVIE_LIST:
                    movie_id = search_movie(title)
                    if movie_id:
                        img_url = get_movie_backdrop(movie_id)
                        if img_url:
                            old_scores = GLOBAL_BATTLE_QUESTIONS.get(room_name, {}).get('scores', {})
                            for user in GLOBAL_BATTLE_ROOMS[room_name]:
                                if user not in old_scores:
                                    old_scores[user] = 0
                            GLOBAL_BATTLE_QUESTIONS[room_name] = {
                                'title': title,
                                'image_url': img_url,
                                'answered_users': set(),
                                'scores': old_scores
                            }
                            break
                else:
                    GLOBAL_BATTLE_QUESTIONS[room_name] = {
                        'title': None,
                        'image_url': None,
                        'answered_users': set(),
                        'scores': {username: 0 for username in GLOBAL_BATTLE_ROOMS[room_name]}
                    }
            question = GLOBAL_BATTLE_QUESTIONS[room_name]
        elif 'answer' in request.POST:
            username = request.user.username
            user_answer = request.POST.get('answer', '').strip()
            correct_title = question['title']
            is_correct = user_answer.lower() == (correct_title or '').lower()
            question['answered_users'].add(username)
            show_feedback = True
            if 'scores' not in question:
                question['scores'] = {u: 0 for u in GLOBAL_BATTLE_ROOMS[room_name]}
            if is_correct:
                question['scores'][username] = question['scores'].get(username, 0) + 2
        elif 'finish' in request.POST:
            # Játék vége, nyertes meghatározása
            game_finished = True
            scores = question.get('scores', {})
            if scores:
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_scores) > 1 and sorted_scores[0][1] == sorted_scores[1][1]:
                    is_draw = True
                    winner = None
                    winner_score = sorted_scores[0][1]
                else:
                    winner = sorted_scores[0][0]
                    winner_score = sorted_scores[0][1]
            # Állapotot is elmentjük, hogy mindenkinél vége legyen
            question['game_finished'] = True
            question['winner'] = winner
            question['winner_score'] = winner_score
            question['is_draw'] = is_draw
        elif 'start_over' in request.POST:
            # Játék újraindítása: új kérdés, pontok nullázása
            MOVIE_LIST = get_random_movies(3)
            for title in MOVIE_LIST:
                movie_id = search_movie(title)
                if movie_id:
                    img_url = get_movie_backdrop(movie_id)
                    if img_url:
                        GLOBAL_BATTLE_QUESTIONS[room_name] = {
                            'title': title,
                            'image_url': img_url,
                            'answered_users': set(),
                            'scores': {user: 0 for user in GLOBAL_BATTLE_ROOMS[room_name]}
                        }
                        break
            else:
                GLOBAL_BATTLE_QUESTIONS[room_name] = {
                    'title': None,
                    'image_url': None,
                    'answered_users': set(),
                    'scores': {user: 0 for user in GLOBAL_BATTLE_ROOMS[room_name]}
                }
            # Töröljük a game_finished flag-et, ha volt
            question = GLOBAL_BATTLE_QUESTIONS[room_name]
            question.pop('game_finished', None)
            question.pop('winner', None)
            question.pop('winner_score', None)
            question.pop('is_draw', None)
        else:
            user_answer = ''
            is_correct = None
            show_feedback = False

    # Szoba információ
    room_players = GLOBAL_BATTLE_ROOMS[room_name]
    other_player = next((p for p in room_players if p != request.user.username), None)
    all_answered = len(question['answered_users']) >= 2
    
    your_score = question['scores'].get(request.user.username, 0)
    opponent_score = question['scores'].get(other_player, 0) if other_player else 0
    
    # Ha már vége a játéknak, context-be rakjuk
    if question.get('game_finished'):
        game_finished = True
        winner = question.get('winner')
        winner_score = question.get('winner_score')
        is_draw = question.get('is_draw')

    return render(request, 'quiz/battle_room.html', {
        'room_name': room_name,
        'username': request.user.username,
        'other_player': other_player,
        'image_url': question['image_url'],
        'correct_title': question['title'],
        'has_answered': request.user.username in question['answered_users'],
        'all_answered': all_answered,
        'show_feedback': show_feedback,
        'is_correct': is_correct,
        'user_answer': user_answer,
        'your_score': your_score,
        'opponent_score': opponent_score,
        'game_finished': game_finished,
        'winner': winner,
        'winner_score': winner_score,
        'is_draw': is_draw,
    })

@login_required
def challenge_mode(request):
    import time
    from django.utils import timezone
    
    # Session kulcsok
    SCORE_KEY = 'challenge_score'
    START_KEY = 'challenge_start_time'
    
    # Indításkor vagy új játék esetén
    if request.method == 'GET' and (SCORE_KEY not in request.session or START_KEY not in request.session):
        request.session[SCORE_KEY] = 0
        request.session[START_KEY] = int(time.time())
    
    # Idő számítása
    start_time = request.session.get(START_KEY, int(time.time()))
    elapsed = int(time.time()) - start_time
    time_left = max(0, 60 - elapsed)
    score = request.session.get(SCORE_KEY, 0)
    
    # Ha lejárt az idő, eredményképernyő
    if time_left <= 0:
        # Töröljük a session kulcsokat, hogy új játék indítható legyen
        request.session.pop(SCORE_KEY, None)
        request.session.pop(START_KEY, None)
        return render(request, 'quiz/challenge_mode.html', {
            'question': None,
            'score': score
        })
    
    # POST: válasz feldolgozása
    if request.method == 'POST':
        selected_choice = request.POST.get('selected_choice')
        correct_answer = request.POST.get('correct_answer')
        if selected_choice and correct_answer:
            is_correct = (selected_choice.strip().lower() == correct_answer.strip().lower())
            if is_correct:
                score += 2
                request.session[SCORE_KEY] = score
                # Profil pontszám is növelhető, ha szeretnéd:
                request.user.profile.score += 2
                request.user.profile.save()
    
    # Új kérdés generálása
    movie_titles = get_random_movies(3)
    correct_movie = random.choice(movie_titles)
    movie_id = search_movie(correct_movie)
    if movie_id:
        image_url = get_movie_backdrop(movie_id)
        if image_url:
            # Nem mentünk DB-be, csak a kérdést adjuk át
            class DummyQuestion:
                pass
            question = DummyQuestion()
            question.content = image_url
            question.correct_answer = correct_movie
            return render(request, 'quiz/challenge_mode.html', {
                'question': question,
                'choices': movie_titles,
                'score': score,
                'time_left': time_left
            })
    # Ha nem sikerült kérdést generálni
    return redirect('profile')

@login_required
def challenge_question_api(request):
    import time
    # Session kulcsok
    SCORE_KEY = 'challenge_score'
    START_KEY = 'challenge_start_time'
    # Indításkor vagy új játék esetén
    if SCORE_KEY not in request.session or START_KEY not in request.session:
        request.session[SCORE_KEY] = 0
        request.session[START_KEY] = int(time.time())
    # Idő számítása (mindig a session-beli start_time alapján!)
    start_time = request.session.get(START_KEY, int(time.time()))
    elapsed = int(time.time()) - start_time
    time_left = max(0, 60 - elapsed)
    score = request.session.get(SCORE_KEY, 0)
    # Ha POST: válasz feldolgozása (csak a pontszámot növeljük, start_time-ot NEM!)
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        is_correct = data.get('is_correct', False)
        if is_correct:
            score += 2
            request.session[SCORE_KEY] = score
            request.user.profile.score += 2
            request.user.profile.save()
    # Ha lejárt az idő, session kulcsokat töröljük és eredményképernyő
    if time_left <= 0:
        request.session.pop(SCORE_KEY, None)
        request.session.pop(START_KEY, None)
        return JsonResponse({
            'question': None,
            'choices': [],
            'score': score,
            'time_left': 0
        })
    # Új kérdés generálása
    movie_titles = get_random_movies(3)
    correct_movie = random.choice(movie_titles)
    movie_id = search_movie(correct_movie)
    if movie_id:
        image_url = get_movie_backdrop(movie_id)
        if image_url:
            return JsonResponse({
                'question': image_url,
                'correct_answer': correct_movie,
                'choices': movie_titles,
                'score': score,
                'time_left': time_left
            })
    return JsonResponse({'question': None, 'choices': [], 'score': score, 'time_left': time_left})

@csrf_exempt
@login_required
def challenge_finish_api(request):
    import json
    from django.utils import timezone
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        score = data.get('score', 0)
        QuizResult.objects.create(
            user=request.user,
            quiz_type='challenge',
            score=score,
            max_score=score,
            started_at=timezone.now(),
            ended_at=timezone.now(),
            is_challenge=True,
            time_limit=60
        )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'msg': 'POST only'})