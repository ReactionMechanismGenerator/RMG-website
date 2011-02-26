from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """
    A model containing user profile information. Some of the information is
    stored in the :class:`User` class built into Django; this class provides
    extra custom information.
    """
    user = models.ForeignKey(User, unique=True)
    