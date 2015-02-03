from django.core.cache import cache
from django.db import models
from django.contrib.auth.models import User

from airmozilla.main.models import Event, SuggestedEvent


class Starred(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(User, null=True)
    added = models.DateTimeField(auto_now_add = True)


    @property
    def anonymous(self):
        return not self.user_id
