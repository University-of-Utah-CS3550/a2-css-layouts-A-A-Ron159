from datetime import timezone
from decimal import Decimal
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from . import models
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def is_student(user):
    return user.groups.filter(name="Students").exists()

def is_ta(user):
    return user.groups.filter(name="Teaching Assistants").exists()

def is_admin(user):
    return user.is_superuser


# Create your views here.
@login_required
def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, "index.html", {
        'Assignments' : assignments
    })

@login_required
def assignment(request, assignment_id):
    request.user
    error_message = None
    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    user_submissions = assignment.submission_set.filter(author=request.user)
    print(user_submissions)
    # alice_submissions = assignment.submission_set.filter(author__username='a')
    submissions_assigned_to_user = assignment.submission_set.filter(grader__username=request.user).count()
    # submissions_assigned_to_g = assignment.submission_set.filter(grader__username='g').count()

    assignment.grade_status = None
    assignment.due_status = None

    if not request.user.is_authenticated:  # Anonymous users are treated as students
        user_role = "student"
    elif is_admin(request.user):  # Admin user
        user_role = "admin"
        total_available_points = None
        total_earned_points = None
        assignment.score = None
        assignment.status = None

    elif is_ta(request.user):  # TA user
        user_role = "ta"
        total_available_points = None
        total_earned_points = None
        assignment.score = None
        
    elif is_student(request.user):  # Student user
        user_role = "student"
        user = User.objects.get(username=request.user)
        total_available_points = 0
        total_earned_points = 0
        assignment.score = None
        submission = models.Submission.objects.filter(assignment=assignment, author=user).first()
        if submission:
            # Graded submission 
            if submission.score is not None:  
                assignment.score = (submission.score / assignment.points) * 100
                total_available_points += assignment.weight
                total_earned_points += (submission.score / assignment.points) * assignment.weight
                assignment.grade_status = 'Graded'
            # Submitted but not yet graded
            else:  
                assignment.grade_status = 'Ungraded'
        else:
            if assignment.deadline < timezone.now():  # Overdue and no submission
                assignment.grade_status = 'Missing'
                assignment.score = 0
            else:  # Not Due and no submission
                assignment.grade_status = None
                assignment.score = None

        assignment.due_status = 'Overdue' if assignment.deadline < timezone.now() else 'Not Due'

    #     # Past due with no submission
    #     if assignment.deadline < timezone.now():  
    #         total_available_points += assignment.weight
    #         # assignment.grade_status = 'Ungraded'
    #         assignment.due_status = 'Overdue'
    #         assignment.score = 0
    #     # Not due yet
    #     else:
    #         assignment.due_status = 'Not Due'
    #         assignment.score = None
    # else:
    #     user_role = "unknown"
    
    if request.method == "POST":
        file = request.FILES.get('file')
        if file:
        # Validate the file name ends with ".pdf"
            if not file.name.lower().endswith('.pdf'):
                error_message = "The uploaded file must be a PDF (with a .pdf extension)."
            else:
                try:
                    # Check that the file starts with "%PDF-"
                    if not next(file.chunks()).startswith(b'%PDF-'):
                        error_message = "The uploaded file is not a valid PDF."
                except Exception as e:
                    error_message = "An error occurred while validating the file. Please try again."
            if not error_message:
                max_file_size = 64 * 1024 * 1024  # 64 MiB in bytes
                if file.size > max_file_size:
                    error_message = "The uploaded file exceeds the maximum size of 64 MiB."
                else:
                    user = get_object_or_404(User, username=request.user)
                    try:
                        submission = models.Submission.objects.get(assignment=assignment, author=user)
                        submission.file = file
                    except models.Submission.DoesNotExist:
                        grader = pick_grader(assignment)
                        submission = models.Submission(
                            assignment=assignment,
                            author=user,
                            grader=grader,
                            file=file,
                            score=None
                        )
                    submission.save()
                    return redirect('assignment', assignment_id=assignment_id)



    # if request.method == "POST":
    #     file = request.FILES.get('file')
    #     if file:
    #         user = get_object_or_404(User, username=request.user)
    #         try:
    #             submission = models.Submission.objects.get(assignment=assignment, author=user)
    #             submission.file = file
    #         except models.Submission.DoesNotExist:
    #             grader = pick_grader(assignment)
    #             submission = models.Submission(assignment=assignment, author=user, grader=grader, file=file, score=None)
    #         submission.save()
    #         return redirect('assignment', assignment_id=assignment_id)

    assignment_data = {
        'assignment_id' : assignment_id,
        'title' : assignment.title,
        'description' : assignment.description,
        'deadline' : assignment.deadline,
        'weight' : assignment.weight,
        'points' : assignment.points,
        'submissions' : assignment.submission_set.count(),
        'user_submissions' : user_submissions,
        "earned_points": total_earned_points,
        "available_points": total_available_points,
        "score": assignment.score,
        "grade_status": assignment.grade_status,
        "due_status": assignment.due_status,
        'submissions_assigned' : submissions_assigned_to_user,
        'student_count' : models.Group.objects.get(name="Students").user_set.count(),
        "user_role": user_role,
        "error_message": error_message,
    }
    return render(request, "assignment.html", assignment_data)

def pick_grader(Assignment):
    ta_group = Group.objects.get(name="Teaching Assistants")
    ta_users = ta_group.user_set.annotate(
        total_assigned=Count('graded_set', filter=Q(graded_set__assignment=Assignment))
    ).order_by('total_assigned')
    return ta_users.first()

@login_required
@user_passes_test(is_ta)
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
                        try:
                            submission.change_grade(request.user, grade)
                            submission.save()  # Save changes after grade modification
                        except PermissionDenied:
                            if submission_id not in errors:
                                errors[submission_id] = []
                            errors[submission_id].append("You do not have permission to change this grade.")
         
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

@login_required
def profile(request):
    if not request.user.is_authenticated:  # Anonymous users are treated as students and log in as Alice Algorithmer
        user_role = "student"
        user = User.objects.get(username='a')
        assignments = models.Assignment.objects.annotate(
            submission_count=Count('submission'),
            submissions_graded=Count('submission', filter=Q(submission__score__isnull=False)),
        )
        current_grade = None
    elif is_admin(request.user):  # Admin user
        user_role = "admin"
        user = User.objects.get(username=request.user)
        assignments = models.Assignment.objects.annotate(
            submission_count=Count('submission'),
            submissions_graded=Count('submission', filter=Q(submission__score__isnull=False)),
        )
    elif is_ta(request.user):  # TA user
        user_role = "ta"
        user = User.objects.get(username=request.user)
        assignments = models.Assignment.objects.annotate(
            submission_count=Count('submission', filter=Q(submission__grader=user)),
            submissions_graded=Count('submission', filter=Q(submission__grader=user, submission__score__isnull=False)),
        )
    elif is_student(request.user):  # Student user
        user_role = "student"
        user = User.objects.get(username=request.user)
         # Get all assignments for this student
        assignments = models.Assignment.objects.all()

        # Initialize grade points
        total_available_points = 0
        total_earned_points = 0

        for assignment in assignments:
            submission = models.Submission.objects.filter(assignment=assignment, author=user).first()
            if submission:
                # Graded submission 
                if submission.score is not None:  
                    assignment.score = (submission.score / assignment.points) * 100
                    total_available_points += assignment.weight
                    total_earned_points += (submission.score / assignment.points) * assignment.weight
                    assignment.status = 'Graded'
                # Submitted but not yet graded
                else:  
                    assignment.status = 'Ungraded'
            # Past due with no submission
            elif assignment.deadline < timezone.now():  
                total_available_points += assignment.weight
                assignment.status = 'Missing'
            # Not due yet
            else:
                assignment.status = 'Not Due'

        # Calculate the current grade
        if total_available_points > 0:
            current_grade = (total_earned_points / total_available_points) * 100
        else:
            current_grade = 100  # No assignments due yet

    else:
        user_role = "unknown"
        assignments = models.Assignment.objects.none()
        current_grade = None

    profile_info = {
        'assignments': assignments,
        'user': request.user,
        'user_role': user_role,
        'current_grade': round(current_grade, 2) if user_role == "student" else None,
    }


    return render(request, "profile.html", profile_info)

def login_form(request):
    next_url = request.GET.get('next', 'profile')
    errors = {}

    if request.method == "POST":
        next_url = request.POST.get('next', 'profile')
        inputted_username = request.POST.get("username", "")
        inputted_password = request.POST.get("password", "")
        user = authenticate(username = inputted_username, password = inputted_password)
        if user is not None:
            login(request, user)
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
                return redirect(next_url)
            else:
                return redirect('/')  # Redirect to home page if URL is unsafe
        else:
            errors[0] = "Username and password do not match"
            return render(request, "login.html", {"next":next_url, "errors":errors})
    return render(request, "login.html", {"next":next_url, "errors":errors})

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

@login_required
def show_upload(request, filename):
    submission = get_object_or_404(models.Submission, file=filename)

    try:
        # Enforce the security policy using the `view_submission` method
        file_field = submission.view_submission(request.user)
        # Return the file as a response
        return HttpResponse(file_field.open())
    except PermissionDenied:
        # Return a proper error response if permission is denied
        return HttpResponse("You do not have permission to view this file.", status=403)