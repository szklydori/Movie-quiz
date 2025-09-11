import pytest
from django.contrib.auth.forms import AuthenticationForm
from quiz.forms import CustomUserCreationForm
from django.contrib.auth.models import User

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

@pytest.mark.django_db
def test_authentication_form():
    user = User.objects.create_user(username='authuser', password='pw12345')
    form = AuthenticationForm(None, data={'username': 'authuser', 'password': 'pw12345'})
    assert form.is_valid() 