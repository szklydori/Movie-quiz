from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('moviequiz/', views.movie_quiz, name='movie_quiz'),
    path('emoji-quiz/', views.emoji_quiz, name='emoji_quiz'),
    path('actor-quiz/', views.actor_quiz, name='actor_quiz'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('moviequiz/select-difficulty/', views.select_movie_quiz_difficulty, name='select_movie_quiz_difficulty'),
    path('actor-quiz/select-difficulty/', views.select_actor_quiz_difficulty, name='select_actor_quiz_difficulty'),
    path('emoji-quiz/select-difficulty/', views.select_emoji_quiz_difficulty, name='select_emoji_quiz_difficulty'),
    path('rank/', views.rank, name='rank'),
    path('battle/', views.battle, name='battle'),
    path('battle/<str:room_name>/', views.battle_room, name='battle_room'),
    path('challenge/', views.challenge_mode, name='challenge_mode'),
    path('challenge/question/', views.challenge_question_api, name='challenge_question_api'),
    path('challenge/finish/', views.challenge_finish_api, name='challenge_finish_api'),
]