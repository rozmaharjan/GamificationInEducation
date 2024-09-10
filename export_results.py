# export_results.py
import os
import django
import csv

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlinequiz.settings')
django.setup()

from quiz.models import Result, UserAnswer

def export_data():
    # Define path for the data folder
    data_folder = 'data'

    # Ensure the data folder exists
    os.makedirs(data_folder, exist_ok=True)

    # Export results
    results = Result.objects.all().values('student_id', 'exam_id', 'marks')
    results_path = os.path.join(data_folder, 'quiz_results.csv')
    with open(results_path, 'w', newline='') as csvfile:
        fieldnames = ['student_id', 'exam_id', 'marks']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow({
                'student_id': result['student_id'],
                'exam_id': result['exam_id'],
                'marks': result['marks']
            })

    # Export user answers
    user_answers = UserAnswer.objects.all().values('user_id', 'course_id', 'question_id', 'answer')
    answers_path = os.path.join(data_folder, 'user_answers.csv')
    with open(answers_path, 'w', newline='') as csvfile:
        fieldnames = ['user_id', 'course_id', 'question_id', 'answer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for answer in user_answers:
            writer.writerow({
                'user_id': answer['user_id'],
                'course_id': answer['course_id'],
                'question_id': answer['question_id'],
                'answer': answer['answer']
            })

if __name__ == "__main__":
    export_data()
