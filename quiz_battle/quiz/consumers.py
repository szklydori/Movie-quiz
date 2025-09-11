import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import QuizResult, Profile
import random
import requests

BATTLE_STATE = {}
API_KEY = '65ac317aa28e9852f0dd9c6145b376e8'

# Helper: random movie with image
async def get_random_movie_with_image():
    url = f'https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}&language=en-US&sort_by=vote_average.desc&vote_count.gte=1000'
    response = requests.get(url)
    data = response.json()
    total_pages = min(data.get('total_pages', 1), 500)
    for _ in range(10):
        page = random.randint(1, total_pages)
        page_url = url + f'&page={page}'
        resp = requests.get(page_url)
        d = resp.json()
        results = d.get('results', [])
        if results:
            movie = random.choice(results)
            title = movie.get('title')
            movie_id = movie.get('id')
            if title and movie_id:
                img_url = await get_movie_backdrop(movie_id)
                if img_url:
                    return title, img_url
    return None, None

async def get_movie_backdrop(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}/images?api_key={API_KEY}'
    response = requests.get(url)
    data = response.json()
    backdrops = data.get('backdrops', [])
    if backdrops:
        image_url = 'https://image.tmdb.org/t/p/original' + backdrops[0]['file_path']
        return image_url
    return None

class BattleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'battle_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        if self.room_name not in BATTLE_STATE:
            title, img_url = await get_random_movie_with_image()
            BATTLE_STATE[self.room_name] = {
                'players': {},  # username -> {'score': 0, 'answered': False}
                'current_question': {'title': title, 'image_url': img_url},
                'finished': False
            }

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        username = data.get('user')
        state = BATTLE_STATE[self.room_name]

        if message_type == 'join':
            # Limit szoba 2 főre
            if username not in state['players'] and len(state['players']) >= 2:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'This room is full!'
                }))
                return
            if username not in state['players']:
                state['players'][username] = {'score': 0, 'answered': False}
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'battle_message',
                    'message': {
                        'type': 'join',
                        'user': username
                    }
                }
            )
            await self.send(text_data=json.dumps({
                'type': 'question',
                'image_url': state['current_question']['image_url'],
                'correct_title': state['current_question']['title'],
                'your_score': state['players'][username]['score'],
                'opponent_score': self._get_opponent_score(state, username),
                'finished': state['finished']
            }))
        elif message_type == 'answer' and not state['finished']:
            answer = data['answer']
            is_correct = data['is_correct']
            if not state['players'][username]['answered']:
                if is_correct:
                    state['players'][username]['score'] += 2
                state['players'][username]['answered'] = True
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'battle_message',
                    'message': {
                        'type': 'answer',
                        'user': username,
                        'answer': answer,
                        'is_correct': is_correct,
                        'scores': {u: p['score'] for u, p in state['players'].items()}
                    }
                }
            )
            print('PLAYERS:', state['players'])
            print('ALL ANSWERED:', all(p['answered'] for p in state['players'].values()))
            print('USERNAMES:', list(state['players'].keys()))
            # Csak akkor jöjjön új kérdés, ha pontosan 2 játékos van és mindkettő válaszolt
            if len(state['players']) == 2 and all(p['answered'] for p in state['players'].values()):
                title, img_url = await get_random_movie_with_image()
                state['current_question'] = {'title': title, 'image_url': img_url}
                for p in state['players'].values():
                    p['answered'] = False
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'battle_message',
                        'message': {
                            'type': 'question',
                            'image_url': img_url,
                            'correct_title': title
                        }
                    }
                )
        elif message_type == 'finish':
            state['finished'] = True
            winner = max(state['players'].items(), key=lambda x: x[1]['score'])[0]
            winner_score = state['players'][winner]['score']
            scores = {u: p['score'] for u, p in state['players'].items()}
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'battle_message',
                    'message': {
                        'type': 'finish',
                        'winner': winner,
                        'winner_score': winner_score,
                        'scores': scores
                    }
                }
            )

    async def battle_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    def _get_opponent_score(self, state, username):
        for u, p in state['players'].items():
            if u != username:
                return p['score']
        return 0

GLOBAL_BATTLE_ROOMS = {}  # room_name -> set of usernames
GLOBAL_BATTLE_QUESTIONS = {}  # room_name -> question data
