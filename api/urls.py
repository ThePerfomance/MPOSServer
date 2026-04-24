# api/urls.py
from django.urls import path
from . import views # <-- Импортируйте views из текущей директории (api)

# Убираем определение index и корневой urlpatterns из этого файла

urlpatterns = [
    # Root (если нужен, но обычно не нужен внутри api/)
    # path("", views.index), # <-- Лучше убрать или сделать внутреннюю точку входа

    # Users
    path("users/", views.users_list, name='users-list'), # <-- Добавил слэши
    path("users/<uuid:pk>/", views.user_detail, name='user-detail'),
    path("users/by-email/<str:email>/", views.user_by_email, name='user-by-email'),
    path("users/<uuid:user_id>/groups/", views.groups_for_user, name='user-groups-for-user'),
    path("users/<uuid:user_id>/results/", views.results_for_user, name='user-results-for-user'),
    #path('auth/login/', views.authenticate_user, name='authenticate_user'),

    # Groups
    path("groups/", views.groups_list, name='groups-list'), # <-- Добавил слэш
    path("groups/<uuid:pk>/", views.group_detail, name='group-detail'),
    path("groups/by-name/<str:name>/", views.group_by_name, name='group-by-name'),
    path("groups/<uuid:group_id>/users/", views.users_for_group, name='users-for-group'),

    # Group Members
    path("group-members/", views.group_members_list, name='group-members-list'),
    path("group-members/<uuid:pk>/", views.group_member_detail, name='group-member-detail'),

    # Subjects
    path("subjects/", views.subjects_list, name='subjects-list'), # <-- Добавил слэш
    path("subjects/<uuid:pk>/", views.subject_detail, name='subject-detail'),
    path("subjects/by-name/<str:name>/", views.subject_by_name, name='subject-by-name'),

    # Blocks (NEW)
    path("blocks/", views.blocks_list, name='blocks-list'),
    path("blocks/<uuid:pk>/", views.block_detail, name='block-detail'),
    path("subjects/<uuid:subject_id>/blocks/", views.blocks_by_subject, name='blocks-by-subject-via-subject'), # <-- Уникальное имя для одного из них
    # path('subjects/<uuid:subject_id>/blocks/', views.blocks_by_subject, name='blocks-by-subject'), # <-- Удалил дубль

    # Lessons (NEW)
    path("lessons/", views.lessons_list, name='lessons-list'),
    path("lessons/<uuid:pk>/", views.lesson_detail, name='lesson-detail'),
    path("blocks/<uuid:block_id>/lessons/", views.lessons_by_block, name='lessons-by-block'),

    # Tests (Updated: remove subject filter if needed, add block/lesson filters)
    path("tests/", views.tests_list, name='tests-list'), # <-- Добавил слэш
    path("tests/<int:pk>/", views.test_detail, name='test-detail'),
    path("lessons/<uuid:lesson_id>/test/", views.test_by_lesson, name='test-by-lesson'), # <-- Добавил слэш
    path("blocks/<uuid:block_id>/final-test/", views.final_test_by_block, name='final-test-by-block'), # <-- Добавил слэш
    path("tests/<int:test_id>/questions/", views.questions_for_test, name='questions-for-test'),

    # Test Results (Unchanged)
    path("test-results/", views.test_results_list, name='test-results-list'),
    path("test-results/<uuid:pk>/", views.test_result_detail, name='test-result-detail'),

    # Questions (Unchanged)
    path("questions/", views.questions_list, name='questions-list'),
    path("questions/<int:pk>/", views.question_detail, name='question-detail'),

    # Answers (Unchanged)
    path("answers/", views.answers_list, name='answers-list'),
    path("answers/<int:pk>/", views.answer_detail, name='answer-detail'),

    # Video
    path("video-types/", views.video_types_list, name='video-types-list'),
    path("videos/", views.videos_list, name='videos-list'),

    # Trainer / User Answers
    path("test-results/<uuid:result_id>/user-answers/", views.user_answers_for_result, name='user-answers-for-result'),
    path("training-sessions/", views.training_sessions_list, name='training-sessions-list'),
    path("training-sessions/<uuid:pk>/", views.training_session_detail, name='training-session-detail'),
    path("training-sessions/from-result/<uuid:result_id>/", views.create_training_from_result, name='create-training-from-result'),
    path("training-questions/<int:pk>/answer/", views.answer_training_question, name='answer-training-question'),

    # ML - СТАРЫЕ ENDPOINTS (отключены, но сохранены для сравнения)
    # path("ml/cluster-students/", views.ml_cluster_students, name='ml-cluster-students'),
    # path("ml/cluster-group/<uuid:group_id>/", views.ml_cluster_group, name='ml-cluster-group'),
    # path("ml/segment-tests/", views.ml_segment_tests, name='ml-segment-tests'),
    # path("ml/predict-result/", views.ml_predict_result, name='ml-predict-result'),
    # path("ml/recommendations/<uuid:user_id>/", views.ml_recommendations, name='ml-recommendations'),
    # path("ml/clusters/<uuid:user_id>/", views.ml_student_cluster, name='ml-student-cluster'),
    # path("ml/test-difficulty/<int:test_id>/", views.ml_test_difficulty, name='ml-test-difficulty'),
    
    # ML - НОВЫЕ ENDPOINTS ДЛЯ ДИПЛОМА (персонализированные рекомендации)
    path("ml/analyze-weak-topics/<uuid:user_id>/", views.ml_analyze_weak_topics, name='ml-analyze-weak-topics'),
    path("ml/personalized-recommendations/<uuid:user_id>/", views.ml_personalized_recommendations, name='ml-personalized-recommendations'),
    path("ml/learning-path/<uuid:user_id>/", views.ml_learning_path, name='ml-learning-path'),
]

# Уберите определение index и внешний urlpatterns из этого файла