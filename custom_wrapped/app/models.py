from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class SpotifyToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    expires_in = models.DateTimeField()

    def is_expired(self):
        """
        Check if the token is expired.
        """
        return timezone.now() >= self.expires_in

    def refresh(self, new_access_token, new_expires_in):
        """
        Refresh the token with a new access token and expiration time.
        """
        self.access_token = new_access_token
        self.expires_in = timezone.now() + datetime.timedelta(seconds=new_expires_in)
        self.save()
        
class Wrapped(models.Model):
    date_created = models.DateField()
    time_period = models.CharField(max_length=10, default='')
    type = models.CharField(max_length=10, default='')
    data = models.JSONField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
