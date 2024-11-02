from datetime import date
from django.shortcuts import render, redirect
import urllib.parse
import os
from dotenv import load_dotenv
import requests
from django.http import JsonResponse
from .forms import RegisterForm
from django.contrib.auth import login, authenticate
from .models import SpotifyToken, Wrapped
import datetime
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .utils.spotify_utils import process_top_tracks, process_top_artists
import google.generativeai as genai
import os
from collections import Counter
from django.utils.formats import date_format

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8000/spotify/callback/'
SCOPES = 'user-top-read user-read-playback-state user-modify-playback-state streaming'
genai.configure(api_key=os.environ["API_KEY"])

def save_wrapped(user, time_period, data):
    user = user
    now = datetime.datetime.now()

    Wrapped.objects.create(
        user=user,
        date_created=now,
        time_period=time_period,
        data=data
    )
    
    
def get_past_wrappeds(request):
    if request.method == 'GET':
        user = request.user

        wrapped_objs = Wrapped.objects.all().filter(user=user)

        wrappeds = {}
        
        i = 0
        
        for wrapped_obj in wrapped_objs:
            wrapped = {
                'date_created': wrapped_obj.date_created,
                'date_formatted': date_format(wrapped_obj.date_created),
                'time_period': wrapped_obj.time_period,
                'data': wrapped_obj.data,
            }
            print(wrapped['date_formatted'])
            wrappeds[i] = wrapped
            i += 1

        return render(request, 'past_wraps.html', {'past_wraps' : wrappeds})

def view_past_wrap(request, date):
    wrap = Wrapped.objects.get(date_created=date)  # Fetches the object with `id=1`
    return wrap


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


def delete_account(request):
    user = request.user
    user.delete()
    return redirect('index')

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

    # Calculate the expiration time for the token
    expires_in_seconds = token_data['expires_in']
    expires_at = timezone.now() + datetime.timedelta(seconds=expires_in_seconds)

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


@login_required
def logout(request):
    request.session.flush()
    return redirect('index')



def profile(request):
    user = request.user
    template_name = 'profile.html'
    context = {
        'user': user,
    }
    return render(request, template_name, context)



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

def show_top_tracks(request):
    return render(request, 'top_tracks.html')

def contact_us(request):
    return render(request, 'contact_us.html')

def get_top_tracks(request, limit, period):
    endpoint = 'https://api.spotify.com/v1/me/top/tracks'
    user = request.user
    token = SpotifyToken.objects.get(user=user)

    try:
        headers = {
            'Authorization': f'Bearer {token.access_token}',
        }

        params = {
            "limit": limit,
            "time_range": period
        }

        response = requests.get(endpoint, headers=headers, params=params)
        data = response.json()

        # Process the top tracks using the utility function
        top_tracks = process_top_tracks(data)

        # Render the processed data in a template
        return render(request, 'top_tracks.html', {'top_tracks': top_tracks})

    except Exception as e:
        error_data = {
            "message": "Operation failed",
            "error": str(e)
        }
        return JsonResponse(error_data, status=500)

def show_top_artists(request):
    return render(request, 'top_artists.html')

def get_top_artists(request, limit, period):
    endpoint = 'https://api.spotify.com/v1/me/top/artists'
    user = request.user
    token = SpotifyToken.objects.get(user=user)

    try:
        headers = {
            'Authorization': f'Bearer {token.access_token}',
        }

        params = {
            "limit": limit,
            "time_range": period
        }

        response = requests.get(endpoint, headers=headers, params=params)
        data = response.json()

        # Process the top artists using the utility function
        top_artists = process_top_artists(data)
        desc = generate_desc(request, top_artists)

        # Render the processed data in a template
        return render(request, 'top_artists.html', {'top_artists': top_artists, 'desc': desc})

    except Exception as e:
        error_data = {
            "message": "Operation failed",
            "error": str(e)
        }
        return JsonResponse(error_data, status=500)

def generate_desc(request, top_artists):
    model = genai.GenerativeModel("gemini-1.5-flash")
    # top 5 genres?
    top_5_genres = get_top_genres(top_artists)
    response = model.generate_content("Generate me the MBTI, zodiac sign, and favorite drink/coffee order of "
                                      "someone who listens to: " + top_5_genres + " in the format of " +
                                    "'People who listen to these genres are...")
    return "Your top genres are: " + top_5_genres + "." + response

def get_top_genres(top_artists):
    genres = []
    for artist_num, artist in top_artists.items:
        genres.extend(artist.genres)

    genre_counts = Counter(genres)
    top_5_genres = genre_counts.most_common(5)
    top_genres_string = ""
    for item in top_5_genres:
        top_genres_string += item
        top_genres_string += ", "
    return top_genres_string

def generate_wrapped(user, limit, period):
    artist_endpoint = 'https://api.spotify.com/v1/me/top/artists'
    tracks_endpoint = 'https://api.spotify.com/v1/me/top/tracks'

    token = SpotifyToken.objects.get(user=user)
    
    headers = {
        'Authorization': f'Bearer {token.access_token}',
    }

    params = {
        "limit": limit,
        "time_range": period
    }

    artists = requests.get(artist_endpoint, headers=headers, params=params)
    artists_data = artists.json()
    
    # Process the top artists using the utility function
    top_artists = process_top_artists(artists_data)
    
    tracks = requests.get(tracks_endpoint, headers=headers, params=params)
    tracks_data = tracks.json()
    top_tracks = process_top_tracks(tracks_data)


    wrapped = {}
    wrapped["artists"] = top_artists
    wrapped["tracks"] = top_tracks
    
    return wrapped

def create_new_wrapped(request, limit, period):
    wrapped = generate_wrapped(request.user, limit, period)
    
    save_wrapped(request.user, period, wrapped)
    context = {'top_artists': wrapped["artists"], 'top_tracks': wrapped["tracks"]}
    return render(request, 'wrapped.html', context)


