from django.core.cache import cache
from django.db import models
from django.contrib.auth.models import User
from airmozilla.main.models import Event


class StarredEvent(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "user")


