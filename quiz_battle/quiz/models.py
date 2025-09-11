from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    

class EmojiMovie(models.Model):
    title = models.CharField(max_length=200)
    emoji_representation = models.CharField(max_length=100)
    year = models.IntegerField(null=True, blank=True)
    genre = models.CharField(max_length=100, null=True, blank=True)
    difficulty = models.IntegerField(default=1)  
    
    def __str__(self):
        return f"{self.title} ({self.emoji_representation})"
    
    class Meta:
        ordering = ['title']

class EmojiMovieDatabase(models.Model):
    title = models.CharField(max_length=200)
    emoji_representation = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.title} ({self.emoji_representation})"
    
    class Meta:
        ordering = ['title']
        db_table = 'emoji_movie_database'  

class Film(models.Model):
    title = models.CharField(max_length=200)
    year = models.IntegerField(null=True, blank=True)
    genre = models.CharField(max_length=100, null=True, blank=True)
    emoji_hint = models.CharField(max_length=100, null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    actors = models.TextField(null=True, blank=True)  # vesszővel elválasztva

    def __str__(self):
        return self.title

class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz_type = models.CharField(max_length=50)
    score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    period = models.CharField(max_length=50, null=True, blank=True)
    is_challenge = models.BooleanField(default=False)
    time_limit = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz_type} - {self.score}"

class Question(models.Model):
    QUIZ_TYPES = [
        ('image', 'Image'),
        ('emoji', 'Emoji'),
        ('actor', 'Actor'),

    ]
    quiz_result = models.ForeignKey(QuizResult, on_delete=models.CASCADE, related_name='questions')
    type = models.CharField(max_length=20, choices=QUIZ_TYPES)
    content = models.TextField()
    correct_answer = models.TextField()
    difficulty = models.IntegerField(default=1)
    film = models.ForeignKey(Film, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.type} - {self.content[:30]}..."

class Answer(models.Model):
    quiz_result = models.ForeignKey(QuizResult, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.TextField()
    is_correct = models.BooleanField()

    def __str__(self):
        return f"{self.quiz_result.user.username} - {self.selected_option} - {'Correct' if self.is_correct else 'Wrong'}"


