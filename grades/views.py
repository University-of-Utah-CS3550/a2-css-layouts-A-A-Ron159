from decimal import Decimal
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from . import models
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.db.models import F
from django.contrib.auth import authenticate, login, logout

# Create your views here.
def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, "index.html", {
        'Assignments' : assignments
    })

def assignment(request, assignment_id):
    request.user
    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    user_submissions = assignment.submission_set.filter(author__username=request.user)
    # alice_submissions = assignment.submission_set.filter(author__username='a')
    submissions_assigned_to_user = assignment.submission_set.filter(grader__username=request.user).count()
    # submissions_assigned_to_g = assignment.submission_set.filter(grader__username='g').count()

    if not request.user.is_authenticated:  # Anonymous users are treated as students
        user_role = "student"
    elif is_admin(request.user):  # Admin user
        user_role = "admin"
    elif is_ta(request.user):  # TA user
        user_role = "ta"
    elif is_student(request.user):  # Student user
        user_role = "student"
    else:
        user_role = "unknown"  # Fallback, though this should not occur
    
    if request.method == "POST":
        file = request.FILES.get('file')
        if file:
            alice = get_object_or_404(User, username='a')
            try:
                submission = models.Submission.objects.get(assignment=assignment, author=alice)
                submission.file = file
            except models.Submission.DoesNotExist:
                garry_grader = get_object_or_404(User, username='g')
                submission = models.Submission(assignment=assignment, author=alice, grader=garry_grader, file=file, score=None)
            submission.save()
            return redirect('assignment', assignment_id=assignment_id)

    assignment_data = {
        'assignment_id' : assignment_id,
        'title' : assignment.title,
        'description' : assignment.description,
        'deadline' : assignment.deadline,
        'weight' : assignment.weight,
        'points' : assignment.points,
        'submissions' : assignment.submission_set.count(),
        'user_submissions' : user_submissions,
        # 'alice_submissions' : alice_submissions,
        'submissions_assigned' : submissions_assigned_to_user,
        # 'submissions_assigned' : submissions_assigned_to_g,
        'student_count' : models.Group.objects.get(name="Students").user_set.count(),
        "user_role": user_role,
    }
    return render(request, "assignment.html", assignment_data)

def submissions(request, assignment_id):
    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    if request.user.is_superuser:
        submissions = models.Submission.objects.filter(assignment=assignment).order_by('author__username')
    elif is_ta(request.user) :
        grader = get_object_or_404(User, username=request.user)
        submissions = models.Submission.objects.filter(assignment=assignment, grader=grader).order_by('author__username')

    errors = {}
    generic_errors = []

    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("grade-"):
                submission_id = key[6:]
                try:
                    submission_id = int(submission_id)
                    submission = models.Submission.objects.get(id=submission_id, assignment=assignment)
                    
                    try:
                        grade = float(value)
                        if grade < 0 or grade > assignment.points:
                            raise ValueError("Grade must be between 0 and the number of points offered on this assignment.")
                        submission.score = grade
                        submission.save()
                    except ValueError as e:
                        if submission_id not in errors:
                            errors[submission_id] = []
                        errors[submission_id].append(str(e))
                except (ValueError, models.Submission.DoesNotExist) as e:
                    generic_errors.append(f"Invalid submission ID: {submission_id}. {str(e)}")
        
        if not errors and not generic_errors:
            return redirect(f"/{assignment_id}/submissions/")

    context = {
        'assignment': assignment,
        'submissions': submissions,
        'points': assignment.points,
        'errors': errors,
        'generic_errors': generic_errors
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
        'grader_name': grader_name,
        'user' : request.user
    }

    return render(request, "profile.html", profile_info)

def login_form(request):
    if request.method == "POST":
        inputted_username = request.POST.get("username", "")
        inputted_password = request.POST.get("password", "")
        user = authenticate(username = inputted_username, password = inputted_password)
        if user is not None:
            login(request, user)
            return redirect("profile")
        else:
            return render(request, "login.html")
    return render(request, "login.html")

def logout_form(request):
    logout(request)
    return render(request, "login.html")

def process_grades(post_data, assignment, grader):
    submissions_to_update = []
    for key in post_data:
        if key.startswith('grade-'):
            submission_id = int(key.removeprefix('grade-'))
            try:
                submission = models.Submission.objects.get(id=submission_id, assignment=assignment, grader=grader)
                grade = post_data[key]
                if grade == '':
                    submission.score = None
                else:
                    submission.score = Decimal(grade)
                submissions_to_update.append(submission)
                print(f"Submission ID: {submission_id}, Score: {submission.score}")
            except models.Submission.DoesNotExist:
                continue
    models.Submission.objects.bulk_update(submissions_to_update, ['score'])
    print(f"Updated Submissions: {len(submissions_to_update)}")

def show_upload(request, filename):
    submission = get_object_or_404(models.Submission, file=filename)
    return HttpResponse(submission.file.open())

def is_student(user):
    return user.groups.filter(name="Students").exists()

def is_ta(user):
    return user.groups.filter(name="Teaching Assistants").exists()

def is_admin(user):
    return user.is_superuser
