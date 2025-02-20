from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User, Group

# Create your models here.

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(default="")
    deadline = models.DateTimeField(default=timezone.now)
    weight = models.IntegerField(default=0)
    points = models.IntegerField(default=100)
    
    def __str__(self):
        return self.title

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    grader = models.ForeignKey(User, related_name='graded_set', on_delete=models.CASCADE)
    file = models.FileField(default="")
    score = models.DecimalField(decimal_places=2, max_digits=5, null=True)