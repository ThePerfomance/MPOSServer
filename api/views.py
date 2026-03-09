from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    User, Group, GroupMember, Subject, Test, Question, Answer, TestResult,
    StudentCluster, TestDifficulty, ScorePrediction, Recommendation,
)
from .serializers import (
    UserSerializer, GroupSerializer, GroupMemberSerializer, SubjectSerializer,
    TestSerializer, QuestionSerializer, QuestionWithAnswersSerializer,
    AnswerSerializer, TestResultSerializer,
    StudentClusterSerializer, TestDifficultySerializer,
    ScorePredictionSerializer, RecommendationSerializer,
)
from ml.engine import cluster_students, segment_tests, predict_score, build_recommendations


# ═══════════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def users_list(request):
    if request.method == "GET":
        return Response(UserSerializer(User.objects.all(), many=True).data)
    s = UserSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "GET":
        return Response(UserSerializer(user).data)
    if request.method == "PUT":
        s = UserSerializer(user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)
    user.delete()
    return Response({"detail": "User deleted"})


@api_view(["GET"])
def user_by_email(request, email):
    user = get_object_or_404(User, email=email)
    return Response(UserSerializer(user).data)


@api_view(["GET"])
def groups_for_user(request, user_id):
    memberships = GroupMember.objects.filter(user_id=user_id).values_list("group_id", flat=True)
    groups = Group.objects.filter(id__in=memberships)
    return Response(GroupSerializer(groups, many=True).data)


@api_view(["GET"])
def results_for_user(request, user_id):
    results = TestResult.objects.filter(user_id=user_id)
    return Response(TestResultSerializer(results, many=True).data)


# ═══════════════════════════════════════════════════════════════════════
# GROUPS
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def groups_list(request):
    if request.method == "GET":
        return Response(GroupSerializer(Group.objects.all(), many=True).data)
    s = GroupSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == "GET":
        return Response(GroupSerializer(group).data)
    if request.method == "PUT":
        s = GroupSerializer(group, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)
    group.delete()
    return Response({"detail": "Group deleted"})


@api_view(["GET"])
def group_by_name(request, name):
    group = get_object_or_404(Group, name=name)
    return Response(GroupSerializer(group).data)


@api_view(["GET"])
def users_for_group(request, group_id):
    user_ids = GroupMember.objects.filter(group_id=group_id).values_list("user_id", flat=True)
    users = User.objects.filter(id__in=user_ids)
    return Response(UserSerializer(users, many=True).data)


# ═══════════════════════════════════════════════════════════════════════
# GROUP MEMBERS
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def group_members_list(request):
    if request.method == "GET":
        return Response(GroupMemberSerializer(GroupMember.objects.all(), many=True).data)
    s = GroupMemberSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def group_member_detail(request, pk):
    gm = get_object_or_404(GroupMember, pk=pk)
    if request.method == "GET":
        return Response(GroupMemberSerializer(gm).data)
    if request.method == "PUT":
        s = GroupMemberSerializer(gm, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)
    gm.delete()
    return Response({"detail": "Group member deleted"})


# ═══════════════════════════════════════════════════════════════════════
# SUBJECTS
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def subjects_list(request):
    if request.method == "GET":
        return Response(SubjectSerializer(Subject.objects.all(), many=True).data)
    s = SubjectSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == "GET":
        return Response(SubjectSerializer(subject).data)
    if request.method == "PUT":
        s = SubjectSerializer(subject, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)
    subject.delete()
    return Response({"detail": "Subject deleted"})


@api_view(["GET"])
def subject_by_name(request, name):
    subject = get_object_or_404(Subject, name=name)
    return Response(SubjectSerializer(subject).data)


# ═══════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def tests_list(request):
    if request.method == "GET":
        return Response(TestSerializer(Test.objects.all(), many=True).data)
    s = TestSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def test_detail(request, pk):
    test = get_object_or_404(Test, pk=pk)
    if request.method == "GET":
        return Response(TestSerializer(test).data)
    if request.method == "PUT":
        s = TestSerializer(test, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)
    test.delete()
    return Response({"detail": "Test deleted"})


@api_view(["GET"])
def questions_for_test(request, test_id):
    questions = Question.objects.filter(test_id=test_id)
    return Response(QuestionWithAnswersSerializer(questions, many=True).data)


# ═══════════════════════════════════════════════════════════════════════
# TEST RESULTS
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def test_results_list(request):
    if request.method == "GET":
        return Response(TestResultSerializer(TestResult.objects.all(), many=True).data)
    s = TestResultSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def test_result_detail(request, pk):
    tr = get_object_or_404(TestResult, pk=pk)
    if request.method == "GET":
        return Response(TestResultSerializer(tr).data)
    if request.method == "PUT":
        s = TestResultSerializer(tr, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)
    tr.delete()
    return Response({"detail": "Test result deleted"})


# ═══════════════════════════════════════════════════════════════════════
# QUESTIONS
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def questions_list(request):
    if request.method == "GET":
        return Response(QuestionSerializer(Question.objects.all(), many=True).data)
    s = QuestionSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def question_detail(request, pk):
    q = get_object_or_404(Question, pk=pk)
    if request.method == "GET":
        return Response(QuestionSerializer(q).data)
    if request.method == "PUT":
        s = QuestionSerializer(q, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)
    q.delete()
    return Response({"detail": "Question deleted"})


# ═══════════════════════════════════════════════════════════════════════
# ANSWERS
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def answers_list(request):
    if request.method == "GET":
        return Response(AnswerSerializer(Answer.objects.all(), many=True).data)
    s = AnswerSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def answer_detail(request, pk):
    a = get_object_or_404(Answer, pk=pk)
    if request.method == "GET":
        return Response(AnswerSerializer(a).data)
    if request.method == "PUT":
        s = AnswerSerializer(a, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)
    a.delete()
    return Response({"detail": "Answer deleted"})


# ═══════════════════════════════════════════════════════════════════════
# ML ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@api_view(["POST"])
def ml_cluster_students(request):
    """
    POST /ml/cluster-students
    Кластеризует всех студентов по средним баллам и числу пройденных тестов.
    Сохраняет результаты в StudentCluster.
    Тело запроса (опционально): {"n_clusters": 3}
    """
    n_clusters = request.data.get("n_clusters", 3)
    students = User.objects.filter(role="student")

    stats = []
    for student in students:
        qs = TestResult.objects.filter(user=student)
        agg = qs.aggregate(avg=Avg("score"), cnt=Count("id"))
        stats.append({
            "user_id": str(student.id),
            "avg_score": float(agg["avg"] or 0),
            "tests_taken": int(agg["cnt"] or 0),
        })

    clusters = cluster_students(stats, n_clusters=n_clusters)

    saved = []
    for c in clusters:
        obj, _ = StudentCluster.objects.update_or_create(
            user_id=c["user_id"],
            defaults={
                "cluster_id": c["cluster_id"],
                "cluster_label": c["cluster_label"],
                "avg_score": c["avg_score"],
                "tests_taken": c["tests_taken"],
            },
        )
        saved.append(StudentClusterSerializer(obj).data)

    return Response({"clusters": saved})


@api_view(["POST"])
def ml_segment_tests(request):
    """
    POST /ml/segment-tests
    Сегментирует все тесты по уровню сложности на основе средних баллов.
    Сохраняет результаты в TestDifficulty.
    """
    tests = Test.objects.all()
    stats = []
    for test in tests:
        qs = TestResult.objects.filter(test=test)
        agg = qs.aggregate(avg=Avg("score"), cnt=Count("id"))
        if agg["cnt"]:
            stats.append({
                "test_id": test.id,
                "avg_score": float(agg["avg"] or 0),
                "attempt_count": int(agg["cnt"]),
            })

    segmented = segment_tests(stats)

    saved = []
    for seg in segmented:
        obj, _ = TestDifficulty.objects.update_or_create(
            test_id=seg["test_id"],
            defaults={
                "difficulty": seg["difficulty"],
                "avg_score_all": seg["avg_score"],
            },
        )
        saved.append(TestDifficultySerializer(obj).data)

    return Response({"test_difficulties": saved})


@api_view(["POST"])
def ml_predict_result(request):
    """
    POST /ml/predict-result
    Прогнозирует балл студента для указанного теста.
    Тело: {"user_id": "<uuid>", "test_id": <int>}
    """
    user_id = request.data.get("user_id")
    test_id = request.data.get("test_id")
    if not user_id or not test_id:
        return Response({"error": "user_id and test_id are required"}, status=400)

    user = get_object_or_404(User, pk=user_id)
    test = get_object_or_404(Test, pk=test_id)

    # История результатов студента с агрегированными средними по тестам
    history_qs = TestResult.objects.filter(user=user).select_related("test")
    history = []
    for r in history_qs:
        test_avg = TestResult.objects.filter(test=r.test).aggregate(avg=Avg("score"))["avg"] or 0
        history.append({"score": r.score, "test_avg": float(test_avg)})

    target_avg = TestResult.objects.filter(test=test).aggregate(avg=Avg("score"))["avg"] or 50.0
    predicted = predict_score(history, float(target_avg))

    obj, _ = ScorePrediction.objects.update_or_create(
        user=user,
        test=test,
        defaults={"predicted_score": predicted},
    )
    return Response(ScorePredictionSerializer(obj).data)


@api_view(["GET"])
def ml_recommendations(request, user_id):
    """
    GET /ml/recommendations/<user_id>
    Возвращает персонализированные рекомендации для студента.
    Требует предварительного запуска /ml/cluster-students и /ml/segment-tests.
    """
    user = get_object_or_404(User, pk=user_id)

    try:
        cluster = StudentCluster.objects.get(user=user)
    except StudentCluster.DoesNotExist:
        return Response({"error": "Сначала выполните /ml/cluster-students"}, status=400)

    difficulties = TestDifficulty.objects.all()
    if not difficulties.exists():
        return Response({"error": "Сначала выполните /ml/segment-tests"}, status=400)

    tests_with_diff = [
        {"test_id": td.test_id, "difficulty": td.difficulty} for td in difficulties
    ]
    recs = build_recommendations(cluster.cluster_label, tests_with_diff)

    # Сохраняем рекомендации в БД
    Recommendation.objects.filter(user=user).delete()
    saved = []
    for r in recs:
        obj = Recommendation.objects.create(
            user=user,
            test_id=r["test_id"],
            text=r["text"],
            priority=r["priority"],
        )
        saved.append(RecommendationSerializer(obj).data)

    return Response({
        "user_id": str(user_id),
        "cluster_label": cluster.cluster_label,
        "recommendations": saved,
    })


@api_view(["GET"])
def ml_student_cluster(request, user_id):
    """
    GET /ml/clusters/<user_id>
    Возвращает кластер конкретного студента.
    """
    cluster = get_object_or_404(StudentCluster, user_id=user_id)
    return Response(StudentClusterSerializer(cluster).data)


@api_view(["GET"])
def ml_test_difficulty(request, test_id):
    """
    GET /ml/test-difficulty/<test_id>
    Возвращает уровень сложности конкретного теста.
    """
    diff = get_object_or_404(TestDifficulty, test_id=test_id)
    return Response(TestDifficultySerializer(diff).data)
