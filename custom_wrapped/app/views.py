from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
import urllib.parse
import os
from dotenv import load_dotenv
import requests
from django.http import JsonResponse
from .forms import RegisterForm
from django.contrib.auth import login, authenticate
from .models import SpotifyToken, Wrapped, Friend
import datetime
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .utils.spotify_utils import process_top_tracks, process_top_artists
import google.generativeai as genai
from collections import Counter
from django.utils.formats import date_format
from django.contrib.auth.models import User
from django.db.models import Q
from .spotify_api import (
    get_auth_url,
    exchange_code_for_token,
    refresh_access_token,
    get_user_profile,
    get_top_tracks,
    get_top_artists,
    get_related_artists,
    get_user_top_genre
)

genai.configure(api_key=os.environ["API_KEY"])

def save_wrapped(user, time_period, data, desc):
    """
    Saves wrap, unless there is an existing wrap with the same data.
    :param user:
    :param time_period:
    :param data:
    :param desc:
    :return: nothing
    """
    user = user
    now = datetime.datetime.now()

    if Wrapped.objects.filter(date_created=now, time_period=time_period, user=user).exists():
        return

    Wrapped.objects.create(
        user=user,
        date_created=now,
        time_period=time_period,
        desc=desc,
        data=data
    )


def get_past_wrappeds(request):
    """
    Fetches basic information of past wraps to display in a list on past_wraps.html
    :param request:
    :return: render request for past_wraps.html
    """
    if request.method == 'GET':
        user = request.user

        wrapped_objs = Wrapped.objects.all().filter(user=user)
        wrappeds = {}

        i = 0

        for wrapped_obj in wrapped_objs:
            wrapped = {
                'id': wrapped_obj.id,
                'date_created': wrapped_obj.date_created,
                'date_formatted': date_format(wrapped_obj.date_created),
                'time_period': wrapped_obj.time_period,
                'image_url': wrapped_obj.data['tracks'].get('1')['album_image']
            }
            wrappeds[i] = wrapped
            i += 1

        return render(request, 'past_wraps.html', {'past_wraps': wrappeds})


def register(request):
    """
    This function allows the user to register for the platform

    If user is making a registration attempt:
        If the user's information is valid, it will redirect to the home page

    Otherwise, it just sends them to the register page
    """
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
    """
    Deletes the account of the user who called the function (request.user)
    """
    user = request.user
    user.delete()
    return redirect('index')


def login_view(request):
    """
    This function allows the user to log into the platform

    If user is making a login attempt:
        If the user's information is valid, it will redirect to the home page

    Otherwise, it just sends them to the login page
    """
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
    """
    Directs the user to the homepage
    The user's spotify access token is sent as context
        If the user hasn't logged in with spotify, the homepage will tell them to
    """
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
def spotify_login_view(request):
    """
    Redirects the user to Spotify's authorization URL.
    """
    auth_url = get_auth_url()
    return redirect(auth_url)


@login_required
def spotify_callback(request):
    """
    Creates an access token for the user when they log in with spotify
    Assigns the access token to the user
    """
    code = request.GET.get('code')

    try:
        token_data = exchange_code_for_token(code)
    except requests.exceptions.HTTPError as e:
        error_data = {
            "message": "Failed to exchange code for token",
            "error": str(e)
        }
        return JsonResponse(error_data, status=400)

    # Calculate the expiration time for the token
    expires_in_seconds = token_data['expires_in']
    expires_at = timezone.now() + datetime.timedelta(seconds=expires_in_seconds)

    # Get or create the SpotifyToken object for the current user
    user = request.user
    spotify_token, created = SpotifyToken.objects.get_or_create(
        user=user,
        defaults={
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_in': expires_at
        }
    )

    if not created:
        # Update the token fields if the object already exists
        spotify_token.access_token = token_data['access_token']
        if 'refresh_token' in token_data:
            spotify_token.refresh_token = token_data['refresh_token']
        spotify_token.expires_in = expires_at
        spotify_token.save()

    return redirect('index')


@login_required
def logout_view(request):
    """
    Allows the user to logout from the platform
    """
    request.session.flush()
    return redirect('index')


@login_required
def profile(request):
    """
    Directs the user to their profile
    Outgoing requests are outgoing friend requests
    Incoming requests are the incoming friend requests
    friends are the friends the user already has added
    """
    # Outgoing requests initiated by the current user
    outgoing_requests = Friend.objects.filter(user=request.user, status='sent')

    # Incoming requests received by the current user
    incoming_requests = Friend.objects.filter(friend=request.user, status='sent')

    # Confirmed friends where the current user is either the sender or the recipient
    friends = Friend.objects.filter(
        Q(user=request.user, status='accepted') | Q(friend=request.user, status='accepted')
    )

    context = {
        'outgoing_requests': outgoing_requests,
        'incoming_requests': incoming_requests,
        'friends': friends
    }
    return render(request, 'profile.html', context)


@login_required
def send_friend_request(request):
    """
    If the user sends a friend request, it will only be sent if not already sent/added
    """
    if request.method == "POST":
        # Get the username from the form input
        username = request.POST.get('username')
        print(f"Username received: {username}")  # Debugging

        # Check if the user with this username exists
        friend = get_object_or_404(User, username=username)

        # Check if a friend request already exists to prevent duplicates
        existing_request = Friend.objects.filter(user=request.user, friend=friend).exists() or \
                           Friend.objects.filter(user=friend, friend=request.user).exists()

        print(f"Existing request found: {existing_request}")  # Debugging

        if not existing_request:
            # Create a friend request entry where request.user is the sender and friend is the recipient
            Friend.objects.create(user=request.user, friend=friend, status='sent')
            print("Friend request created successfully")  # Debugging
        else:
            print("Friend request already exists, not creating another.")  # Debugging

    return redirect('profile')


@login_required
def accept_friend_request(request, friend_id):
    """
    Allows the user to accept an incoming friend request
    Sets the friend request status to accepted
    """
    # Find the friend request sent to the current user
    friend_request = get_object_or_404(Friend, id=friend_id, friend=request.user, status='sent')

    # Update the friend request to accepted status
    friend_request.status = 'accepted'
    friend_request.save()

    return redirect('profile')


@login_required
def deny_friend_request(request, friend_id):
    """
    Allows the user to deny an incoming friend request
    Deletes the request
    """
    # Remove the incoming friend request from the database
    Friend.objects.filter(id=friend_id, friend=request.user, status='sent').delete()
    return redirect('profile')


@login_required
def cancel_friend_request(request, friend_id):
    """
    Allows the user to cancel an outgoing friend request
    Deletes the request
    """
    # Remove the outgoing friend request from the database
    Friend.objects.filter(id=friend_id, user=request.user, status='sent').delete()
    return redirect('profile')


@login_required
def remove_friend(request, friend_id):
    """
    Allows the user to remove an existing friend from their friends list
    Finds the friend object with status 'accepted' to ensure proper deletion
    """


    # Find and delete the friendship from both directions (if it exists)
    friend_relation = Friend.objects.filter(
        (Q(user=request.user, friend__id=friend_id) | Q(friend=request.user, user__id=friend_id)),
        status='accepted'
    )

    if friend_relation.exists():
        friend_relation.delete()
        print("Friend removed successfully")  # Debugging

    return redirect('profile')


def contact_us(request):
    return render(request, 'contact_us.html')


@login_required
def get_top_tracks_view(request, limit=10, period='medium_term'):
    """
    Fetches and displays the user's top tracks.
    """
    user = request.user
    try:
        spotify_token = SpotifyToken.objects.get(user=user)
        if spotify_token.is_expired():
            if spotify_token.refresh_token:
                token_data = refresh_access_token(spotify_token.refresh_token)
                spotify_token.access_token = token_data['access_token']
                if 'refresh_token' in token_data:
                    spotify_token.refresh_token = token_data['refresh_token']
                spotify_token.expires_in = timezone.now() + datetime.timedelta(seconds=token_data['expires_in'])
                spotify_token.save()
            else:
                return redirect('spotify_login')
        access_token = spotify_token.access_token

        # Retrieve top tracks and pass access_token to process features
        data = get_top_tracks(access_token, limit, period)
        top_tracks = process_top_tracks(data, access_token)

        return render(request, 'top_tracks.html', {'top_tracks': top_tracks})

    except SpotifyToken.DoesNotExist:
        return redirect('spotify_login')
    except Exception as e:
        error_data = {
            "message": "Operation failed",
            "error": str(e)
        }
        return JsonResponse(error_data, status=500)


@login_required
def get_top_artists_view(request, limit=10, period='medium_term'):
    """
    Fetches and displays the user's top artists.
    """
    user = request.user
    try:
        spotify_token = SpotifyToken.objects.get(user=user)
        if spotify_token.is_expired():
            if spotify_token.refresh_token:
                token_data = refresh_access_token(spotify_token.refresh_token)
                spotify_token.access_token = token_data['access_token']
                if 'refresh_token' in token_data:
                    spotify_token.refresh_token = token_data['refresh_token']
                spotify_token.expires_in = timezone.now() + datetime.timedelta(seconds=token_data['expires_in'])
                spotify_token.save()
            else:
                return redirect('spotify_login')
        access_token = spotify_token.access_token

        data = get_top_artists(access_token, limit, period)
        top_artists = process_top_artists(data, access_token)
        desc = generate_desc(request, top_artists)

        return render(request, 'top_artists.html', {'top_artists': top_artists, 'desc': desc})

    except SpotifyToken.DoesNotExist:
        return redirect('spotify_login')
    except Exception as e:
        error_data = {
            "message": "Operation failed",
            "error": str(e)
        }
        return JsonResponse(error_data, status=500)

      
def generate_desc(top_artists):
    """
    Generates a description of a user from their top genres.

    Args:
        top_artists : top artists the user listens to.

    Returns:
        string: Description of the user.
    """


    model = genai.GenerativeModel("gemini-1.5-flash")
    # top 5 genres:
    top_5_genres = get_top_genres(top_artists)
    response = model.generate_content("In 100 words or under, generate me the MBTI, zodiac sign, favorite drink/coffee, " +
                                      "and colors describing someone who listens to: " + top_5_genres +
                                      "Start with 'People who listen to these genres are often'. Evaluate all the genres together. Make the sentences flow, and don't use Markdown or add asterisks.")
    return response.text


def get_top_genres(top_artists):
    genres = []

    for key, artist in top_artists.items():
        if not artist.get('genres') == '':
            genres.append(artist.get('genres'))

    genre_counts = Counter(genres)
    top_5_genres = genre_counts.most_common(5)
    top_genres_string = ""
    for item in top_5_genres:
        top_genres_string += str(item)
        top_genres_string += ", "

    return top_genres_string


def generate_wrapped(user, limit=10, period='medium_term'):
    """
    Generates a wrapped summary of the user's top artists and tracks.
    """
    try:
        spotify_token = SpotifyToken.objects.get(user=user)
        if spotify_token.is_expired():
            if spotify_token.refresh_token:
                token_data = refresh_access_token(spotify_token.refresh_token)
                spotify_token.access_token = token_data['access_token']
                if 'refresh_token' in token_data:
                    spotify_token.refresh_token = token_data['refresh_token']
                spotify_token.expires_in = timezone.now() + datetime.timedelta(seconds=token_data['expires_in'])
                spotify_token.save()
            else:
                return None

        access_token = spotify_token.access_token

        # Process top artists with access_token
        artists_data = get_top_artists(access_token, limit, period)
        top_artists = process_top_artists(artists_data, access_token)

        # Process top tracks as before
        tracks_data = get_top_tracks(access_token, limit, period)
        top_tracks = process_top_tracks(tracks_data, access_token)

        wrapped = {"artists": top_artists, "tracks": top_tracks}
        desc = generate_desc(wrapped['artists'])
        save_wrapped(user, period, wrapped, desc)
        return wrapped

    except SpotifyToken.DoesNotExist:
        return None
    except Exception as e:
        print(f"Error generating wrapped: {e}")
        return None


def display_wrapped(request, limit, period):
    """
    Creates and saves a new wrapped summary for the user.
    """
    now = datetime.datetime.now()

    access_token = SpotifyToken.objects.get(user=request.user).access_token
    user_profile = get_user_profile(access_token)
    top_genre = get_user_top_genre(access_token, limit, period)

    if Wrapped.objects.filter(date_created=now, time_period=period, user=request.user).exists():
        wrapped = Wrapped.objects.get(date_created=now, time_period=period, user=request.user)
        context = {'top_artists': wrapped.data["artists"],
                   'top_tracks': wrapped.data["tracks"],
                   'desc': wrapped.desc,
                   'top_genre': top_genre,
                   'user_profile': user_profile,
                   }
    else:
        wrapped = generate_wrapped(request.user, limit, period)
        if wrapped:
            desc = generate_desc(wrapped['artists'])
            save_wrapped(request.user, period, wrapped, desc)
            context = {'top_artists': wrapped["artists"],
                       'top_tracks': wrapped["tracks"],
                       'desc': desc,
                       'top_genre': top_genre,
                       'user_profile': user_profile,
                       }
        else:
            error_data = {
                "message": "Failed to generate wrapped summary."
            }
            return JsonResponse(error_data, status=500)

    return render(request, 'wrapped.html', context)




def delete_wrapped(request, item_id):
    """
    Deletes selected saved wrap.
    :param request:
    :param item_id:
    :return:
    """
    Wrapped.objects.get(id=item_id).delete()
    return get_past_wrappeds(request)


def select_period(request):
    """
    Renders page for selection time period
    :param request:
    :return:
    """
    return render(request, 'select_period.html')

