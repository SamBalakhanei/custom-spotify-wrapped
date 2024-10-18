from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),
    path('logout/', views.logout, name='logout'),
    path('spotify/get_top_tracks/<int:limit>/<str:period>/', views.get_top_tracks, name='spotify_get_top_tracks'),
    path('spotify/get_top_artists/<int:limit>/<str:period>/', views.get_top_artists, name='spotify_get_top_artists')

]