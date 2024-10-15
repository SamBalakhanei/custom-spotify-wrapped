from django.shortcuts import render, redirect
import urllib.parse
import os
from dotenv import load_dotenv
import requests
from django.conf import settings



load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8000/spotify/callback/'
SCOPES = 'user-top-read user-read-playback-state user-modify-playback-state streaming'
def index(request):
    template_name = 'index.html'
    return render(request, template_name)


def spotify_login(request):
    spotify_auth_url = "https://accounts.spotify.com/authorize"
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
    }
    url = f"{spotify_auth_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)

def spotify_callback(request):
    code = request.GET.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = requests.post(token_url, data=payload, headers=headers)
    token_data = response.json()

    request.session['spotify_access_token'] = token_data['access_token']
    request.session['spotify_refresh_token'] = token_data['refresh_token']

    return redirect('index')

def logout(request):
    request.session.flush()
    return redirect('index')

