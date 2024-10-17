from django.shortcuts import render, redirect
import urllib.parse
import os
from dotenv import load_dotenv
import requests
from django.conf import settings
from django.http import JsonResponse


load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8000/spotify/callback/'
SCOPES = 'user-top-read user-read-playback-state user-modify-playback-state streaming'


def index(request):
    access_token = request.session.get('spotify_access_token')
    template_name = 'index.html'
    if access_token:

        user_profile = get_spotify_user_profile(access_token)

        if user_profile:
            username = user_profile.get('display_name')
        else:
            username = "Unknown User"
    else:
        username = None
    context = {
        'username': username,
    }

    return render(request, template_name, context)


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


    try:
        headers = {
            'Authorization': f'Bearer {request.session['spotify_access_token'] }',
        }
        
        params = {
            "limit": limit,
            "time_range" : period
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        
        data = response.json()
        top_tracks = {}
        numTracks = 1
        
        for datum in data["items"]:   
            artists = []
            for artist in datum["artists"]:
                artists.append({
                    "name": artist["name"],
                    "artist_link": artist["href"]
                })  
                                  
            top_tracks[numTracks] = {
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
            
            numTracks += 1
            
        return JsonResponse(top_tracks, status=200)
    except Exception as e:
        error_data = {
            "message": "Operation failed",
            "error": str(e)
        }
            
        return JsonResponse(error_data, status=500)

