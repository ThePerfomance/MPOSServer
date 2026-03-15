from django.urls import path
from django.http import HttpResponse
from . import views


def index(request):
    return HttpResponse("Hello, World!")


urlpatterns = [
    # Root
    path("", index),

    # Users
    path("users", views.users_list),
    path("users/<uuid:pk>", views.user_detail),
    path("users/by-email/<str:email>", views.user_by_email),
    path("users/<uuid:user_id>/groups", views.groups_for_user),
    path("users/<uuid:user_id>/results", views.results_for_user),

    # Groups
    path("groups", views.groups_list),
    path("groups/<uuid:pk>", views.group_detail),
    path("groups/by-name/<str:name>", views.group_by_name),
    path("groups/<uuid:group_id>/users", views.users_for_group),

    # Group Members
    path("group-members", views.group_members_list),
    path("group-members/<uuid:pk>", views.group_member_detail),

    # Subjects
    path("subjects", views.subjects_list),
    path("subjects/<uuid:pk>", views.subject_detail),
    path("subjects/by-name/<str:name>", views.subject_by_name),

    # Tests
    path("tests", views.tests_list),
    path("tests/<int:pk>", views.test_detail),
    path("tests/<int:test_id>/questions", views.questions_for_test),

    # Test Results
    path("test-results", views.test_results_list),
    path("test-results/<uuid:pk>", views.test_result_detail),

    # Questions
    path("questions", views.questions_list),
    path("questions/<int:pk>", views.question_detail),

    # Answers
    path("answers", views.answers_list),
    path("answers/<int:pk>", views.answer_detail),

    # ML
    path("ml/cluster-students", views.ml_cluster_students),
    path("ml/cluster-group/<uuid:group_id>", views.ml_cluster_group),
    path("ml/segment-tests", views.ml_segment_tests),
    path("ml/predict-result", views.ml_predict_result),
    path("ml/recommendations/<uuid:user_id>", views.ml_recommendations),
    path("ml/clusters/<uuid:user_id>", views.ml_student_cluster),
    path("ml/test-difficulty/<int:test_id>", views.ml_test_difficulty),
]