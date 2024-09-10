import logging
from django.shortcuts import get_object_or_404, render,redirect,reverse
import requests
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from quiz import models as QMODEL
from teacher import models as TMODEL
from quiz import models as QMODEL
from django.http import JsonResponse
import pickle
from surprise import Dataset, Reader
from django.views.decorators.csrf import csrf_exempt
import json

#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'student/studentclick.html')

def student_signup_view(request):
    userForm=forms.StudentUserForm()
    studentForm=forms.StudentForm()
    mydict={'userForm':userForm,'studentForm':studentForm}
    if request.method=='POST':
        userForm=forms.StudentUserForm(request.POST)
        studentForm=forms.StudentForm(request.POST,request.FILES)
        if userForm.is_valid() and studentForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            student=studentForm.save(commit=False)
            student.user=user
            student.save()
            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)
        return HttpResponseRedirect('studentlogin')
    return render(request,'student/studentsignup.html',context=mydict)

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_dashboard_view(request):
    dict={
    
    'total_course':QMODEL.Course.objects.all().count(),
    'total_question':QMODEL.Question.objects.all().count(),
    }
    return render(request,'student/student_dashboard.html',context=dict)

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_exam_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_exam.html',{'courses':courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def take_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    total_questions=QMODEL.Question.objects.all().filter(course=course).count()
    questions=QMODEL.Question.objects.all().filter(course=course)
    total_marks=0
    for q in questions:
        total_marks=total_marks + q.marks
    
    return render(request,'student/take_exam.html',{'course':course,'total_questions':total_questions,'total_marks':total_marks})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def start_exam_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)

    # Check if the student has already taken the quiz
    result_exists = QMODEL.Result.objects.filter(exam=course, student=student).exists()
    
    if result_exists:
        return render(request, 'student/already_attempted.html', {'course': course})

    # If not attempted, proceed with starting the exam
    questions = QMODEL.Question.objects.filter(course=course)
    return render(request, 'student/start_exam.html', {'course': course, 'questions': questions})



@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def calculate_marks_view(request):
    if request.COOKIES.get('course_id') is not None:
        course_id = request.COOKIES.get('course_id')
        course = QMODEL.Course.objects.get(id=course_id)
        student = models.Student.objects.get(user_id=request.user.id)
        
        # Check if the student has already taken the exam
        result_exists = QMODEL.Result.objects.filter(exam=course, student=student).exists()
        
        if result_exists:
            return HttpResponseRedirect('already_attempted')

        total_marks = 0
        questions = QMODEL.Question.objects.filter(course=course)
        for i, question in enumerate(questions):
            selected_ans = request.COOKIES.get(str(i + 1))
            if selected_ans == question.answer:
                total_marks += question.marks

        # Save the result if not already present
        result = QMODEL.Result()
        result.marks = total_marks
        result.exam = course
        result.student = student
        result.save()

        return HttpResponseRedirect('view-result')
    else:
        return HttpResponseRedirect('student-dashboard')




@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_result_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/view_result.html',{'courses':courses})
    

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_marks_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_marks.html',{'courses':courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def check_marks_view(request, pk):
    if not pk:
        raise ValueError("PK is empty")
    course = QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    user_answers = QMODEL.UserAnswer.objects.filter(course=course, user=student)
    
    if user_answers.count() == 0 or user_answers.first().user.user != request.user:
     return HttpResponseForbidden("You are not authorized to view these results.")
    
    total_marks_obtained = 0
    for user_answer in user_answers:
        question = user_answer.question
        if user_answer.answer == question.answer:
            total_marks_obtained += question.marks

    results = QMODEL.Result.objects.filter(student=student, exam=course)


    return render(request, 'student/check_marks.html', {
        'user_answers': user_answers,
        'total_marks_obtained': total_marks_obtained,
        'view_exam_results_url': pk and reverse('view_exam_results', args=[pk]),
        'results': results,
    })

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_exam_results(request, pk):
    student = get_object_or_404(QMODEL.Student, user=request.user)
    course = get_object_or_404(QMODEL.Course, id=pk)
    
    # Check if the student has completed the exam
    result_exists = QMODEL.Result.objects.filter(student=student, exam=course).exists()
    if not result_exists:
        return HttpResponseForbidden("You have not completed this exam or do not have access to it.")
    
    user_answers = QMODEL.UserAnswer.objects.filter(user=student, course=course)
    questions = QMODEL.Question.objects.filter(course=course)
    
    results = []
    total_marks_obtained = 0
    
    for question in questions:
        user_answer = user_answers.filter(question=question).first()
        if user_answer and user_answer.answer == question.answer:
            total_marks_obtained += question.marks  # Add marks for correct answers
        results.append({
            'question': question.question,
            'options': [question.option1, question.option2, question.option3, question.option4],
            'your_answer': user_answer.answer if user_answer else 'Not Answered',
            'correct_answer': question.answer
        })
    
    context = {
        'results': results,
        'course': course,
        'total_marks_obtained': total_marks_obtained
    }
    
    return render(request, 'student/view_exam_results.html', context)

    
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def save_answers_view(request, pk):
    course = get_object_or_404(QMODEL.Course, id=pk)
    student = get_object_or_404(models.Student, user_id=request.user.id)
    
    if request.method == 'POST':
        # Process and save user answers
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = int(key.split('_')[1])
                answer = value
                
                QMODEL.UserAnswer.objects.update_or_create(
                    user=student,
                    course=course,
                    question_id=question_id,
                    defaults={'answer': answer}
                )

        # Create or update Result entry
        # For simplicity, assuming all answers are provided and marked as complete
        total_marks = sum(QMODEL.Question.objects.filter(course=course).values_list('marks', flat=True))
        result, created = QMODEL.Result.objects.update_or_create(
            student=student,
            exam=course,
            defaults={'marks': total_marks}
        )
        
        return HttpResponseRedirect(reverse('view_exam_results', args=[pk]))
    else:
        return HttpResponseRedirect(reverse('student_dashboard'))


@login_required
def leaderboard_view(request):
    # Fetch all students and their total marks
    students = models.Student.objects.all()
    student_results = []

    for student in students:
        total_marks = QMODEL.Result.objects.filter(student=student).aggregate(Sum('marks'))['marks__sum'] or 0
        student_name = f"{student.user.first_name} {student.user.last_name}"
        student_results.append({
            'student_name': student_name,
            'marks_obtained': total_marks,
            'student': student
        })

    # Sort students by marks obtained in descending order
    student_results = sorted(student_results, key=lambda x: x['marks_obtained'], reverse=True)

    # Assign ranks and discounts
    for idx, result in enumerate(student_results):
        result['rank'] = idx + 1
        if result['rank'] <= 3:
            result['discount'] = f"{100 - (result['rank'] - 1) * 25}%"  
            result['reward_link'] = '' 
        else:
            result['discount'] = 'Recommendation'
            result['reward_link'] = f"/student/recommendation/{result['student'].user.id}/1/" 

    # Calculate the rank of the current student
    current_student = models.Student.objects.get(user_id=request.user.id)
    total_marks_current = QMODEL.Result.objects.filter(student=current_student).aggregate(Sum('marks'))['marks__sum'] or 0
    
    rank = 1
    for result in student_results:
        if result['student'] == current_student:
            break
        rank += 1
    
    # Assign rewards
    if rank == 1:
        discount_current = '100%'
    elif rank == 2:
        discount_current = '50%'
    elif rank == 3:
        discount_current = '25%'
    else:
        discount_current = 'Recommendation'
    
    return render(request, 'student/leaderboard.html', {'quiz_results': student_results, 'rank': rank, 'total_marks': total_marks_current, 'discount': discount_current})


@login_required(login_url='studentlogin')
def coupons(request):
    discount = request.GET.get('discount')
    if discount:
        discount_value = discount
    else:
        discount_value = "No discount provided"

    # Fetch book data from Google Books API
    api_url = 'https://www.googleapis.com/books/v1/volumes'
    params = {
        'q': 'computer science OR programming OR software engineering OR algorithms OR data structures',
        'maxResults': 10,
        'printType': 'books'
    }
    
    response = requests.get(api_url, params=params)
    books = response.json().get('items', [])
    
    return render(request, 'student/coupons.html', {'books': books, 'discount': discount_value})

# Load the model
with open('svd_model.pkl', 'rb') as f:
    algo = pickle.load(f)

# YouTube API settings
YOUTUBE_API_KEY = 'AIzaSyDaRS1e-NgFlogsNNr1ilAxEhr3nU_T5AM'  
YOUTUBE_API_URL = 'https://www.googleapis.com/youtube/v3/search'

def fetch_youtube_videos(subject):
    # Query the YouTube Data API
    params = {
        'part': 'snippet',
        'q': subject + ' tutorial',
        'type': 'video',
        'key': YOUTUBE_API_KEY,
        'maxResults': 5
    }
    response = requests.get(YOUTUBE_API_URL, params=params)
    data = response.json()
    video_recommendations = []
    for item in data.get('items', []):
        video_url = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        thumbnail_url = item['snippet']['thumbnails']['default']['url']
        video_recommendations.append({
            'url': video_url,
            'thumbnail': thumbnail_url
        })
    return video_recommendations

@csrf_exempt
def recommendation(request, user_id, question_id):
    if request.method == 'GET':
        try:
            student = models.Student.objects.get(user_id=user_id)

            # Make prediction
            prediction = algo.predict(student.id, question_id)
            predicted_score = prediction.est

            # Determine weak subjects
            weak_subjects = analyze_weak_subjects(student.id)

            # Fetch video recommendations
            video_recommendations = {}
            for subject in weak_subjects:
                video_recommendations[subject] = fetch_youtube_videos(subject)

            return render(request, 'student/recommendation.html', {
                'predicted_score': predicted_score,
                'recommended_videos': video_recommendations
            })
        except models.Student.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def analyze_weak_subjects(user_id):
    WEAK_SUBJECT_THRESHOLD = 60.0

    # Fetch the student object using user_id
    try:
        student = models.Student.objects.get(user_id=user_id)
    except models.Student.DoesNotExist:
        return []

    # Filter results using the student id
    student_results = QMODEL.Result.objects.filter(student=student)

    subject_scores = {}
    for result in student_results:
        course = result.exam
        if course.course_name not in subject_scores:
             subject_scores[course.course_name] = []
        subject_scores[course.course_name].append(result.marks)

    weak_subjects = []
    for course_name, scores in subject_scores.items():
        average_score = sum(scores) / len(scores)
        if average_score < WEAK_SUBJECT_THRESHOLD:
            weak_subjects.append(course_name)

    return weak_subjects

