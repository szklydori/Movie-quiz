import pytest
from django.contrib.auth.models import User
from quiz.models import QuizResult, Answer, Profile, Film, Question
from django.test import Client

@pytest.mark.django_db
def test_wrong_answer_does_not_increase_score(client):
    user = User.objects.create_user(username='wronguser', password='pw')
    client.force_login(user)
    client.get('/challenge/')
    session = client.session
    session['challenge_score'] = 5
    session['challenge_start_time'] = 1234567890
    session.save()
    response = client.post('/challenge/question/', data='{"is_correct": false}', content_type='application/json')
    data = response.json()
    assert data['score'] == 5  #score should not increase

@pytest.mark.django_db
def test_no_new_question_after_timeup(client):
    user = User.objects.create_user(username='timeoutuser', password='pw')
    client.force_login(user)
    #simulate expired session
    session = client.session
    session['challenge_score'] = 2
    session['challenge_start_time'] = 0  
    session.save()
    response = client.get('/challenge/question/')
    data = response.json()
    assert data['question'] is None
    assert data['time_left'] == 0

@pytest.mark.django_db
def test_leaderboard_only_own_challenge_results(client):
    user1 = User.objects.create_user(username='userA', password='pw')
    user2 = User.objects.create_user(username='userB', password='pw')
    QuizResult.objects.create(user=user1, quiz_type='challenge', score=10, is_challenge=True)
    QuizResult.objects.create(user=user2, quiz_type='challenge', score=99, is_challenge=True)
    client.force_login(user1)
    response = client.get('/profile/')
    assert b'userA' in response.content
    assert b'userB' not in response.content  # onyl your own resutl

@pytest.mark.django_db
def test_challenge_session_reset(client):
    user = User.objects.create_user(username='resetuser', password='pw')
    client.force_login(user)
    #start a challenge
    client.get('/challenge/')
    session = client.session
    session['challenge_score'] = 7
    session['challenge_start_time'] = 1234567890
    session.save()
    #time is up
    session['challenge_start_time'] = 0
    session.save()
    client.get('/challenge/question/') 
    #new challenge
    client.get('/challenge/')
    session = client.session
    assert session.get('challenge_score', None) == 0

@pytest.mark.django_db
def test_answer_quizresult_link_and_user_delete():
    user = User.objects.create_user(username='deluser', password='pw')
    result = QuizResult.objects.create(user=user, quiz_type='emoji', score=2)
    film = Film.objects.create(title='Test Film')
    question = Question.objects.create(
        quiz_result=result,
        type='emoji',
        content='Test content',
        correct_answer='A',
        difficulty=1,
        film=film
    )
    answer = Answer.objects.create(quiz_result=result, question=question, selected_option='A', is_correct=True)
    assert answer.quiz_result == result
    user.delete()
    # quizresult and answer are deleted (on_delete=models.CASCADE)
    assert not QuizResult.objects.filter(id=result.id).exists()
    assert not Answer.objects.filter(id=answer.id).exists() 