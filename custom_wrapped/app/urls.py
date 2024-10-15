from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),
    path('logout/', views.logout, name='logout'),

]