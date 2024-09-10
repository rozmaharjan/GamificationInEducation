from django.urls import path
from student import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('studentclick', views.studentclick_view, name='studentclick'),
    path('studentlogin', LoginView.as_view(template_name='student/studentlogin.html'), name='studentlogin'),
    path('studentsignup', views.student_signup_view, name='studentsignup'),
    path('student-dashboard', views.student_dashboard_view, name='student-dashboard'),
    path('student-exam', views.student_exam_view, name='student-exam'),
    path('take-exam/<int:pk>', views.take_exam_view, name='take-exam'),
    path('start-exam/<int:pk>', views.start_exam_view, name='start-exam'),
    path('save_answers_view/<int:pk>/', views.save_answers_view, name='save_answers_view'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('coupons/', views.coupons, name='coupons'),
    path('calculate-marks', views.calculate_marks_view, name='calculate-marks'),
    path('view-result', views.view_result_view, name='view-result'),
    path('check-marks/<int:pk>', views.check_marks_view, name='check-marks'),
    path('student-marks', views.student_marks_view, name='student-marks'),
    path('view-exam-results/<int:pk>/', views.view_exam_results, name='view_exam_results'),
     path('recommendation/<int:user_id>/<int:question_id>/', views.recommendation, name='recommendation'),
]
