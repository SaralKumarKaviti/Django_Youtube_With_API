from django.db import models
from oauth2client.contrib.django_util.models import CredentialsField


# Create your models here.

class CredentialsModel(models.Model):
    credential = CredentialsField()