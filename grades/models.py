from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied

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

    # Checks if the user is allowed to change the grade
    def change_grade(self, user, new_grade) :
        if user.groups.filter(name='Student').exists():
            raise PermissionDenied("You do not have permission to change this grade.")
        grade = new_grade

    def view_submission(self, user):
        # Check if the user is authorized to view the submission
        if user == self.author or user == self.grader or user.is_superuser:
            return self.file  # Return the file field if authorized
        raise PermissionDenied("You do not have permission to view this submission.")

