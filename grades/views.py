from django.shortcuts import render, get_object_or_404
from . import models


# Create your views here.
def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, "index.html", {
        'Assignments' : assignments
    })

def assignment(request, assignment_id):
    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    assignment_data = {
        'assignment_id' : assignment_id,
        'title' : assignment.title,
        'description' : assignment.description,
        'deadline' : assignment.deadline,
        'weight' : assignment.weight,
        'points' : assignment.points,
        'submissions' : assignment.submission_set.count(),
        'student_count' : models.Group.objects.get(name="Students").user_set.count()
    }
    return render(request, "assignment.html", assignment_data)

def submissions(request, assignment_id):
    return render(request, "submissions.html")

def profile(request):
    return render(request, "profile.html")

def login_form(request):
    return render(request, "login.html")