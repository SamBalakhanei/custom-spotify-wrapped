from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('', include('django.contrib.auth.urls')),  # Django auth
    path('spotify/', include('social_django.urls', namespace='social')),  # Spotify login and callback

]