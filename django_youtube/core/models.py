from django.db import models
from oauth2client.contrib.django_util.models import CredentialsField
from embed_video.fields import EmbedVideoField


# Create your models here.

class CredentialsModel(models.Model):
    credential = CredentialsField()


