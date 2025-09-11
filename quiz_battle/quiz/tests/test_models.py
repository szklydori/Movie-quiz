import pytest
from django.contrib.auth.models import User
from quiz.models import Profile, QuizResult, Answer, Film, EmojiMovie, Question

@pytest.mark.django_db
def test_profile_auto_created():
    user = User.objects.create_user(username='user1', password='pw')
    profile = Profile.objects.get(user=user)
    assert profile.score == 0

@pytest.mark.django_db
def test_quizresult_creation():
    user = User.objects.create_user(username='user2', password='pw')
    result = QuizResult.objects.create(user=user, quiz_type='emoji', score=3)
    assert result.quiz_type == 'emoji'
    assert result.score == 3

@pytest.mark.django_db
def test_answer_linking():
    user = User.objects.create_user(username='user3', password='pw')
    result = QuizResult.objects.create(user=user, quiz_type='image', score=1)
    film = Film.objects.create(title='Test Movie')
    question = Question.objects.create(
        quiz_result=result,
        type='image',
        content='Test content',
        correct_answer='A',
        difficulty=1,
        film=film
    )
    answer = Answer.objects.create(quiz_result=result, question=question, selected_option='A', is_correct=True)
    assert answer.quiz_result == result
    assert answer.is_correct

@pytest.mark.django_db
def test_film_and_emoji_movie():
    film = Film.objects.create(title='Test Film', year=2020, genre='Comedy')
    emoji = EmojiMovie.objects.create(title='Test Emoji', emoji_representation='🎬')
    assert film.title == 'Test Film'
    assert emoji.emoji_representation == '🎬' 