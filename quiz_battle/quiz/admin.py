from django.contrib import admin
from .models import EmojiMovie, EmojiMovieDatabase, QuizResult, Question, Answer, Film

@admin.register(EmojiMovie)
class EmojiMovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'emoji_representation', 'year', 'genre', 'difficulty')
    list_filter = ('genre', 'year', 'difficulty')
    search_fields = ('title', 'emoji_representation')
    ordering = ('title',)

@admin.register(EmojiMovieDatabase)
class EmojiMovieDatabaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'emoji_representation')
    search_fields = ('title', 'emoji_representation')
    ordering = ('title',)

admin.site.register(QuizResult)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Film) 