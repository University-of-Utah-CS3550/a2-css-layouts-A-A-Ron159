from django.shortcuts import redirect, render, get_object_or_404
from . import models
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.db.models import F

# Create your views here.
def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, "index.html", {
        'Assignments' : assignments
    })

def assignment(request, assignment_id):
    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    submissions_assigned_to_g = assignment.submission_set.filter(grader__username='g').count()
    assignment_data = {
        'assignment_id' : assignment_id,
        'title' : assignment.title,
        'description' : assignment.description,
        'deadline' : assignment.deadline,
        'weight' : assignment.weight,
        'points' : assignment.points,
        'submissions' : assignment.submission_set.count(),
        'submissions_assigned' : submissions_assigned_to_g,
        'student_count' : models.Group.objects.get(name="Students").user_set.count()
    }
    return render(request, "assignment.html", assignment_data)

def submissions(request, assignment_id):
    if request.method == "POST":
        return redirect(f"/{assignment_id}/submissions/")
    assignment = models.Assignment.objects.get(id=assignment_id)
    grader = User.objects.get(username='g')  # Assuming 'g' is the username of the grader
    submissions = models.Submission.objects.filter(assignment=assignment, grader=grader).order_by('author__username')
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
        'points': assignment.points
    }
    return render(request, "submissions.html", context)

def profile(request):
    assignments = models.Assignment.objects.annotate(
        submission_count=Count('submission'),
        submissions_graded=Count('submission', filter=Q(submission__score__isnull=False)),
    )
    grader_name = User.objects.get(username='g')

    profile_info = {
        'Assignments': assignments,
        'grader_name': grader_name
    }

    return render(request, "profile.html", profile_info)

def login_form(request):
    return render(request, "login.html")