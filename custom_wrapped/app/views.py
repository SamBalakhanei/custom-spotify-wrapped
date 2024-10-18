from django.shortcuts import render, redirect
import urllib.parse
import os
from dotenv import load_dotenv
import requests
from django.http import JsonResponse
from .forms import RegisterForm
from django.contrib.auth import login, authenticate
from .models import SpotifyToken
import datetime
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8000/spotify/callback/'
SCOPES = 'user-top-read user-read-playback-state user-modify-playback-state streaming'

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = RegisterForm()
    context = {
        'form': form
    }
    template_name = 'register.html'
    return render(request, template_name, context)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    template_name = 'login.html'
    context = {
        'form': form
    }
    return render(request, template_name, context)


def index(request):
    access_token = None
    if request.user.is_authenticated:
        try:
            spotify_token = SpotifyToken.objects.get(user=request.user)
            if not spotify_token.is_expired():
                access_token = spotify_token.access_token
        except SpotifyToken.DoesNotExist:
            pass
    template_name = 'index.html'
    context = {
        'access_token': access_token
    }
    return render(request, template_name, context)


@login_required
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


@login_required
def spotify_callback(request):
    code = request.GET.get('code')

    # Spotify token URL
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

    # Make a request to get the access token
    response = requests.post(token_url, data=payload, headers=headers)
    token_data = response.json()
    print("GOT JSON")

    # Calculate the expiration time for the token
    expires_in_seconds = token_data['expires_in']
    print(f"EXPIRES IN SECONDS = {expires_in_seconds}")
    expires_at = timezone.now() + datetime.timedelta(seconds=expires_in_seconds)
    print(f"EXPIRES AT = {expires_at}")

    # Get or create the SpotifyToken object for the current user
    user = request.user
    spotify_token, created = SpotifyToken.objects.get_or_create(
        user=user,
        defaults={
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'expires_in': expires_at
        }
    )

    if not created:
        # Update the token fields if the object already exists
        spotify_token.access_token = token_data['access_token']
        spotify_token.refresh_token = token_data['refresh_token']
        spotify_token.expires_in = expires_at
        spotify_token.save()

    return redirect('index')


def logout(request):
    request.session.flush()
    return redirect('index')


def get_spotify_user_profile(access_token):
    url = 'https://api.spotify.com/v1/me'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_top_tracks(request, limit, period):
    endpoint = 'https://api.spotify.com/v1/me/top/tracks'
    user = request.user
    token = SpotifyToken.objects.get(user=user)

    try:
        headers = {
            'Authorization': f'Bearer { token.access_token }',
        }
        
        params = {
            "limit": limit,
            "time_range" : period
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        
        data = response.json()
        top_tracks = {}
        num_tracks = 1
        
        for datum in data["items"]:   
            artists = []
            for artist in datum["artists"]:
                artists.append({
                    "name": artist["name"],
                    "artist_link": artist["href"]
                })  
                                  
            top_tracks[num_tracks] = {
                "track_name" : datum["name"],
                "mp3_preview_url": datum["preview_url"],
                "track_url" : datum["external_urls"]["spotify"],
                "duration_ms": datum["duration_ms"],
                "artists": artists,
                "album_name": datum["album"]["name"],
                "album_link": datum["album"]["external_urls"]["spotify"],
                "album_image": datum["album"]["images"][0]["url"],
                "release_date": datum["album"]["release_date"],
            }
            
            num_tracks += 1
            
        return JsonResponse(top_tracks, status=200)
    except Exception as e:
        error_data = {
            "message": "Operation failed",
            "error": str(e)
        }
            
        return JsonResponse(error_data, status=500)

def get_top_artists(request, limit, period):
    endpoint = 'https://api.spotify.com/v1/me/top/artists'
    user = request.user
    token = SpotifyToken.objects.get(user=user)

    try:
        headers = {
            'Authorization': f'Bearer { token.access_token }',
        }
        
        params = {
            "limit": limit,
            "time_range" : period
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        
        data = response.json()
        top_artists = {}
        num_artists = 1
        
        for datum in data["items"]:                    
            top_artists[num_artists] = {
                "name": datum["name"],
                "artist_url": datum["external_urls"]["spotify"],
                "genres": datum["genres"],
                "image_url": datum["images"][0]["url"]
            }
            
            num_artists += 1
            
        return JsonResponse(top_artists, status=200)
    except Exception as e:
        error_data = {
            "message": "Operation failed",
            "error": str(e)
        }
            
        return JsonResponse(error_data, status=500)


