# urls.py

from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # Updated view name

    # Spotify Authentication URLs
    path('spotify/login/', views.spotify_login_view, name='spotify_login'),  # Updated view name
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),

    # Spotify Data Retrieval URLs
    path('spotify/get_top_tracks/<int:limit>/<str:period>/', views.get_top_tracks_view, name='spotify_get_top_tracks'),
    # Updated view name
    path('spotify/get_top_artists/<int:limit>/<str:period>/', views.get_top_artists_view,
         name='spotify_get_top_artists'),  # Updated view name

    # General Data Retrieval URLs
    path('get-top-tracks/<int:limit>/<str:period>/', views.get_top_tracks_view, name='get_top_tracks'),
    # Updated view name
    path('get-top-artists/<int:limit>/<str:period>/', views.get_top_artists_view, name='get_top_artists'),
    # Updated view name

    # Wrapped Data URLs
    path('wrapped/<int:limit>/<str:period>/', views.create_new_wrapped, name='wrapped'),
    path('view_wrap/<int:item_id>/', views.view_past_wrap, name='view_wrap'),
    path('get-past-wrappeds/', views.get_past_wrappeds, name='past_wraps'),

    # Contact and Profile URLs
    path('contact-us/', views.contact_us, name='contact_us'),
    path('profile/', views.profile, name='profile'),

    # Friend Management URLs
    path('send_friend_request/', views.send_friend_request, name='send_friend_request'),
    path('accept_friend_request/<int:friend_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('deny_friend_request/<int:friend_id>/', views.deny_friend_request, name='deny_friend_request'),
    path('cancel_friend_request/<int:friend_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('remove_friend/<int:friend_id>/', views.remove_friend, name='remove_friend'),

    # Duo-Wrapped URL
    path('duo_wrapped/<int:friend_id>/', views.duo_wrapped, name='duo_wrapped'),

    # Account Management URL
    path('delete_account/', views.delete_account, name='delete_account'),
    path('delete_wrapped/<int:item_id>/', views.delete_wrapped, name='delete_wrapped'),
    path('past_duo_wrappeds/', views.view_past_duo_wrappeds, name='past_duo_wrappeds'),
    path('duo_wrapped/<int:duo_wrapped_id>/', views.view_duo_wrapped_detail, name='view_duo_wrapped_detail'),
]
