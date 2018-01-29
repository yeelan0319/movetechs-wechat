from __future__ import unicode_literals

import datetime
import json

from django.db import models

class Person(models.Model):
  name = models.CharField(max_length=50)
  name_pinyin = models.CharField(max_length=50)
  open_id = models.CharField(max_length=50)

class Snippet(models.Model):
  user = models.CharField(max_length=50)
  date = models.DateTimeField('date published')
  week = models.IntegerField(default=0)
  content = models.CharField(max_length=500)
  content_type = models.IntegerField(default=0)
  has_read = models.BooleanField(default=False)
  has_star = models.BooleanField(default=False)

  def __str__(self):
    return json.dumps({
        'user': self.user,
        'date': self.date.isoformat(),
        'week': self.week,
        'content': self.content,
        'content_type': self.content_type,
        'has_read': self.has_read,
        'has_star': self.has_star
    })
