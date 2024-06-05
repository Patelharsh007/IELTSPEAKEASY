from django.db import models
from django.contrib.auth.models import User

class PracticeHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    response = models.TextField()
    score = models.FloatField()
    feedback = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
