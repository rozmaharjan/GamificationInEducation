import os
import django

# Set up Django settings module and initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlinequiz.settings')
django.setup()

from quiz.models import UserAnswer, Course, Student

def print_user_answers():
    # Retrieve all user answers
    user_answers = UserAnswer.objects.select_related('course', 'user').all()

    for answer in user_answers:
        course_name = answer.course.name  # Adjust if the field name is different
        user_id = answer.user.id
        course_id = answer.course.id
        print(f"User ID: {user_id}, Course ID: {course_id}, Course Name: {course_name}, Answer: {answer.answer}")

if __name__ == "__main__":
    print_user_answers()
