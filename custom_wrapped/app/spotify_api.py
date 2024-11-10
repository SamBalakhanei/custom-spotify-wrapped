# spotify_api.py

import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from django.utils import timezone
import datetime

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8000/spotify/callback/'
SCOPES = 'user-top-read user-read-playback-state user-modify-playback-state streaming'

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'


def get_auth_url():
    """
    Constructs the Spotify authorization URL.
    """
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
    }
    url = f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
    return url


def exchange_code_for_token(code):
    """
    Exchanges the authorization code for access and refresh tokens.
    """
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

    response = requests.post(SPOTIFY_TOKEN_URL, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def refresh_access_token(refresh_token):
    """
    Refreshes the access token using the refresh token.
    """
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = requests.post(SPOTIFY_TOKEN_URL, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_user_profile(access_token):
    """
    Retrieves the Spotify user profile.
    """
    url = f'{SPOTIFY_API_BASE_URL}/me'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_top_tracks(access_token, limit=10, time_range='medium_term'):
    """
    Retrieves the user's top tracks.
    """
    url = f'{SPOTIFY_API_BASE_URL}/me/top/tracks'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    params = {
        'limit': limit,
        'time_range': time_range
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_top_artists(access_token, limit=10, time_range='medium_term'):
    """
    Retrieves the user's top artists.
    """
    url = f'{SPOTIFY_API_BASE_URL}/me/top/artists'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    params = {
        'limit': limit,
        'time_range': time_range
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_track_features(access_token, track_id):
    url = f'{SPOTIFY_API_BASE_URL}/audio-features/{track_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_related_artists(access_token, artist_id, limit=5):
    """
    Retrieves related artists for a given artist ID.

    Args:
        access_token (str): Spotify API access token.
        artist_id (str): Spotify artist ID.
        limit (int): Number of related artists to retrieve.

    Returns:
        list: A list of related artists with their names and Spotify URLs.
    """
    url = f'{SPOTIFY_API_BASE_URL}/artists/{artist_id}/related-artists'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        related_artists = data.get('artists', [])[:limit]
        return [
            {
                'name': artist['name'],
                'artist_link': artist['external_urls']['spotify']
            }
            for artist in related_artists
        ]
    else:
        response.raise_for_status()
