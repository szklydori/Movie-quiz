import pytest
from django.contrib.auth.models import User
from django.test import Client
from quiz.models import QuizResult, Answer, Profile, Question, Film
from quiz.forms import CustomUserCreationForm

@pytest.mark.django_db
def test_profile_created():
    user = User.objects.create_user(username='testuser', password='testpass')
    profile = Profile.objects.get(user=user)
    assert profile.score == 0

@pytest.mark.django_db
def test_quizresult_challenge():
    user = User.objects.create_user(username='testuser2', password='testpass')
    result = QuizResult.objects.create(user=user, quiz_type='challenge', score=5, is_challenge=True)
    assert result.is_challenge
    assert result.score == 5

@pytest.mark.django_db
def test_challenge_mode_session(client):
    user = User.objects.create_user(username='testuser3', password='testpass')
    client.force_login(user)
    response = client.get('/challenge/')
    assert response.status_code == 200
    # Session keys set
    session = client.session
    session['challenge_score'] = 4
    session['challenge_start_time'] = 1234567890
    session.save()
    # POST right answer
    response = client.post('/challenge/question/', data='{"is_correct": true}', content_type='application/json')
    assert response.status_code == 200
    data = response.json()
    assert 'score' in data

@pytest.mark.django_db
def test_challenge_finish_api(client):
    user = User.objects.create_user(username='testuser4', password='testpass')
    client.force_login(user)
    response = client.post('/challenge/finish/', data='{"score": 7}', content_type='application/json')
    assert response.status_code == 200
    assert QuizResult.objects.filter(user=user, is_challenge=True, score=7).exists()

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
def test_custom_user_creation_form_valid():
    form = CustomUserCreationForm(data={
        'username': 'formuser',
        'password1': 'StrongPass123',
        'password2': 'StrongPass123',
        'email': 'test@example.com',
    })
    assert form.is_valid()
    user = form.save()
    assert User.objects.filter(username='formuser').exists() 