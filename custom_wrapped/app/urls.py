from django.urls import path, include

from . import views
from .views import show_top_tracks, get_top_tracks
from .views import show_top_artists, get_top_artists
from .views import contact_us

urlpatterns = [
    path('', views.index, name='index'),
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),
    path('logout/', views.logout, name='logout'),
    path('spotify/get_top_tracks/<int:limit>/<str:period>/', views.get_top_tracks, name='spotify_get_top_tracks'),
    path('spotify/get_top_artists/<int:limit>/<str:period>/', views.get_top_artists, name='spotify_get_top_artists'),
    path('top-tracks/', show_top_tracks, name='top_tracks'),
    path('get-top-tracks/<int:limit>/<str:period>/', get_top_tracks, name='get_top_tracks'),
    path('top-artists/', show_top_artists, name='top_artists'),
    path('get-top-artists/<int:limit>/<str:period>/', get_top_artists, name='get_top_artists'),
    path('contact-us/', contact_us, name='contact_us'),
    path('profile/', views.profile, name='profile'),
    path('delete_account/', views.delete_account, name='delete_account'),


]