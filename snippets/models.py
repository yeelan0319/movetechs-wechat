from __future__ import unicode_literals

import json

from django.db import models

class Snippet(models.Model):
  user = models.CharField(max_length=20)
  date = models.DateTimeField('date published')
  content = models.CharField(max_length=500)
  content_type = models.IntegerField(default=0)

  def __str__(self):
    return json.dumps({
        'user': self.user,
        'date': self.date.isoformat(),
        'content': self.content,
        'content_type': self.content_type
    })
