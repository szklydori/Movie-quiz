import pytest
from django.contrib.auth.models import User
from django.urls import reverse

@pytest.mark.django_db
def test_challenge_mode_get(client):
    user = User.objects.create_user(username='viewuser', password='pw')
    client.force_login(user)
    response = client.get('/challenge/')
    assert response.status_code == 200
    assert b'Challenge Mode' in response.content

@pytest.mark.django_db
def test_challenge_question_api_get(client):
    user = User.objects.create_user(username='apiget', password='pw')
    client.force_login(user)
    response = client.get('/challenge/question/')
    assert response.status_code == 200
    data = response.json()
    assert 'question' in data
    assert 'choices' in data

@pytest.mark.django_db
def test_challenge_question_api_post(client):
    user = User.objects.create_user(username='apipost', password='pw')
    client.force_login(user)
    # First GET to set session
    client.get('/challenge/question/')
    response = client.post('/challenge/question/', data='{"is_correct": true}', content_type='application/json')
    assert response.status_code == 200
    data = response.json()
    assert 'score' in data

@pytest.mark.django_db
def test_challenge_finish_api(client):
    user = User.objects.create_user(username='finishuser', password='pw')
    client.force_login(user)
    response = client.post('/challenge/finish/', data='{"score": 5}', content_type='application/json')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

@pytest.mark.django_db
def test_profile_page(client):
    user = User.objects.create_user(username='profileuser', password='pw')
    client.force_login(user)
    response = client.get('/profile/')
    assert response.status_code == 200
    assert b'Profile' in response.content

@pytest.mark.django_db
def test_login_logout(client):
    user = User.objects.create_user(username='loginuser', password='pw')
    login = client.login(username='loginuser', password='pw')
    assert login
    response = client.get('/logout/')
    assert response.status_code in (200, 302) 