from django.urls import path
from . import views

app_name = "assess"

urlpatterns = [
    # Dashboard & resume
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_resume, name="upload_resume"),

    # Tests
    path("test/aptitude/", views.aptitude_test, name="aptitude_test"),
    path("test/coding/", views.coding_test, name="coding_test"),

    # Interviews
    path("interview/tech/", views.tech_interview, name="tech_interview"),
    path("tech/questions/", views.get_tech_questions, name="get_tech_questions"),

    path("interview/hr/", views.hr_interview, name="hr_interview"),
    path("interview/hr/", views.hr_interview_page, name="hr_interview"),
    path("hr/questions/", views.get_hr_questions, name="get_hr_questions"),

    path("hr/submit/", views.submit_hr_interview, name="submit_hr_interview"),
    path("tech/questions/", views.get_tech_questions, name="get_tech_questions"),
    path("tech/submit/", views.submit_tech_interview, name="submit_tech_interview"),
    path("log/violation/", views.log_violation, name="log_violation"),





    # Status pages
    path("wait/", views.wait_page, name="wait"),
    path("rejected/", views.rejection_report, name="rejected"),
    path("result/", views.final_result, name="result"),

]
