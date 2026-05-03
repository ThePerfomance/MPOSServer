from django.contrib.auth.hashers import check_password
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .models import (
    User, Group, GroupMember, Subject, Block, Lesson, Test, Question, Answer, TestResult,
    StudentCluster, TestDifficulty, ScorePrediction, Recommendation, VideoType, Video, UserAnswer, TrainingSession, TrainingQuestion,
    TeacherGroup, GroupSubject
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer, GroupSerializer, GroupMemberSerializer, SubjectSerializer,
    TestSerializer, BlockSerializer, LessonSerializer, QuestionSerializer, QuestionWithAnswersSerializer,
    AnswerSerializer, TestResultSerializer,
    StudentClusterSerializer, TestDifficultySerializer,
    ScorePredictionSerializer, RecommendationSerializer,VideoTypeSerializer, VideoSerializer, UserAnswerSerializer,
    TrainingSessionSerializer, TrainingQuestionSerializer,
    TeacherGroupSerializer, GroupSubjectSerializer # <--- ДОБАВЛЕНО
)
from .forms import (
    SubjectForm, BlockForm, LessonForm, VideoForm, TestForm, BlockFormSet, LessonFormSet,
    QuestionForm, AnswerFormSet
)
from ml.engine import (
    analyze_weak_topics,
    generate_personalized_recommendations,
    analyze_progress_over_time,
    build_learning_path
)


# ═══════════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def users_list(request):
    if request.method == "GET":
        return Response(UserSerializer(User.objects.all(), many=True).data)
    s = UserSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)

@api_view(["POST"])
@permission_classes([AllowAny])
def user_register(request):
    """
    Регистрация нового пользователя из мобильного приложения.

    Требуемые поля:
    - email: уникальный email пользователя
    - password: пароль (минимум 4 символа)
    - firstname: имя
    - lastname: фамилия
    - patronymic: отчество
    - role: роль ('student' или 'teacher')

    Возвращает данные созданного пользователя без пароля.
    """
    serializer = UserRegistrationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()

    response_data = {
        'id': str(user.id),
        'email': user.email,
        'firstname': user.firstname,
        'lastname': user.lastname,
        'patronymic': user.patronymic,
        'role': user.role,
        'is_active': user.is_active,
    }

    return Response({
        'message': 'Пользователь успешно зарегистрирован',
        'user': response_data
    }, status=status.HTTP_201_CREATED)


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
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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
# ПРЕПОДАВАТЕЛИ И ПРЕДМЕТЫ ГРУПП (NEW)
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET"])
def subjects_for_group(request, group_id):
    """Получить список предметов для конкретной группы"""
    subject_ids = GroupSubject.objects.filter(group_id=group_id).values_list("subject_id", flat=True)
    subjects = Subject.objects.filter(id__in=subject_ids)
    return Response(SubjectSerializer(subjects, many=True).data)


@api_view(["POST"])
def add_subject_to_group(request):
    """Привязать предмет к группе"""
    s = GroupSubjectSerializer(data=request.data)
    if s.is_valid():
        gs = s.save()
        return Response({
            "status": "success",
            "message": "Предмет успешно привязан к группе",
            "id": str(gs.id)
        }, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def teachers_for_group(request, group_id):
    """Получить список преподавателей конкретной группы"""
    teacher_ids = TeacherGroup.objects.filter(group_id=group_id).values_list("teacher_id", flat=True)
    teachers = User.objects.filter(id__in=teacher_ids)
    return Response(UserSerializer(teachers, many=True).data)


@api_view(["POST"])
def add_teacher_to_group(request):
    """Привязать преподавателя к группе"""
    s = TeacherGroupSerializer(data=request.data)
    if s.is_valid():
        tg = s.save()
        return Response({
            "status": "success",
            "message": "Преподаватель успешно привязан к группе",
            "id": str(tg.id)
        }, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def groups_for_teacher(request, teacher_id):
    """Получить все группы, которые ведет конкретный преподаватель"""
    group_ids = TeacherGroup.objects.filter(teacher_id=teacher_id).values_list("group_id", flat=True)
    groups = Group.objects.filter(id__in=group_ids)
    return Response(GroupSerializer(groups, many=True).data)

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

@api_view(["POST"])
def test_start(request, test_id):
    """
    Шаг 1: Создание объекта TestResult и получение вопросов.
    """
    test = get_object_or_404(Test, pk=test_id)
    user = request.user if request.user.is_authenticated else None

    # Если в мобильном приложении нет JWT, можно передавать user_id в теле
    if not user and 'user_id' in request.data:
        user = get_object_or_404(User, id=request.data.get('user_id'))

    # Создаем запись о начале теста
    test_result = TestResult.objects.create(
        user=user,
        test=test,
        started_at=timezone.now(),
        earned_points=0,
        total_points=0
    )

    # Получаем вопросы с ответами
    questions = Question.objects.filter(test=test)
    questions_data = QuestionWithAnswersSerializer(questions, many=True).data

    return Response({
        "result_id": test_result.id,
        "test": {
            "id": test.id,
            "title": test.title,
            "questions": questions_data
        }
    }, status=status.HTTP_201_CREATED)

@api_view(["POST"])
def test_submit(request, result_id):
    """
    Шаг 3: Прием ответов, расчет баллов и завершение теста.
    (ML-анализ отключен)
    """
    test_result = get_object_or_404(TestResult, pk=result_id)

    # Защита: если тест уже завершен, не даем перезаписать результаты
    if test_result.completed_at is not None:
        return Response({"detail": "Тест уже завершен."}, status=status.HTTP_400_BAD_REQUEST)

    answers_data = request.data.get("answers", [])

    # 1. Считаем max_points на основе ВСЕХ вопросов в тесте
    all_questions = Question.objects.filter(test=test_result.test)
    max_points = sum(q.points for q in all_questions)
    total_earned = 0

    # Преобразуем присланные ответы в словарь {question_id: answer_id} для быстрого поиска
    user_answers_dict = {ans.get("question"): ans.get("answer") for ans in answers_data}

    # 2. Проходим по всем вопросам теста
    for question in all_questions:
        chosen_answer_id = user_answers_dict.get(question.id)

        # Если ответ был предоставлен
        if chosen_answer_id:
            chosen_answer = Answer.objects.filter(pk=chosen_answer_id, question=question).first()
            if chosen_answer:
                is_correct = chosen_answer.is_correct
                points = question.points if is_correct else 0
            else:
                chosen_answer = None
                is_correct = False
                points = 0
        else:
            # Пользователь пропустил вопрос
            chosen_answer = None
            is_correct = False
            points = 0

        # Сохраняем результат ответа
        UserAnswer.objects.update_or_create(
            test_result=test_result,
            question=question,
            defaults={
                'chosen_answer': chosen_answer,
                'is_correct': is_correct,
                'points_earned': points
            }
        )

        total_earned += points

    # 3. Обновляем итоговый результат
    test_result.earned_points = total_earned
    test_result.total_points = max_points
    test_result.completed_at = timezone.now()
    test_result.save()

    # --- ЗДЕСЬ БЫЛ ML-АНАЛИЗ. СЕЙЧАС ОН ОТКЛЮЧЕН ---

    # Возвращаем детализированный результат
    user_answers = UserAnswer.objects.filter(test_result=test_result)

    return Response({
        "id": test_result.id,
        "user": str(test_result.user.id) if test_result.user else None,
        "test": {"id": test_result.test.id, "title": test_result.test.title},
        "earned_points": test_result.earned_points,
        "total_points": test_result.total_points,
        "started_at": test_result.started_at,
        "completed_at": test_result.completed_at,
        "user_answers": [
            {
                "question": ua.question_id,
                "chosen_answer": ua.chosen_answer_id,
                "is_correct": ua.is_correct,
                "points_earned": ua.points_earned
            } for ua in user_answers
        ]
    })

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

# views.py

@api_view(["GET", "POST"])
def test_results_list(request):
    """
    Список результатов тестирования.
    POST: Создание нового результата теста с ответами пользователя.
          После сохранения ответов автоматически запускается ML-анализ слабых тем.
    """
    if request.method == "GET":
        return Response(TestResultSerializer(TestResult.objects.all(), many=True).data)

    # 1. Сначала проверяем валидность основных данных результата
    data = request.data.copy()

    # Извлекаем список ответов отдельно, чтобы он не мешал базовому сериализатору
    answers_data = data.pop("answers", [])

    s = TestResultSerializer(data=data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    test_result = s.save()

    # 2. Сохраняем ответы UserAnswer
    try:
        for ans in answers_data:
            # Если флаг is_correct не передан, определяем его автоматически
            is_correct = ans.get("is_correct")
            if is_correct is None:
                question_id = ans.get("question_id")
                chosen_answer_id = ans.get("chosen_answer_id")
                if question_id and chosen_answer_id:
                    correct_answer = Answer.objects.filter(question_id=question_id, is_correct=True).first()
                    is_correct = (correct_answer and correct_answer.id == chosen_answer_id)
                else:
                    is_correct = False
            
            UserAnswer.objects.create(
                test_result=test_result,
                question_id=ans.get("question_id"),
                chosen_answer_id=ans.get("chosen_answer_id"),
                is_correct=is_correct
            )
    except Exception as e:
        # Если ответы не сохранились, лучше удалить сам результат, чтобы не было дублей при перезаписи
        test_result.delete()
        return Response({"error": f"Ошибка при сохранении ответов: {str(e)}"}, status=500)

    # 3. Запускаем ML-анализ слабых тем сразу после прохождения теста
    try:
        from ml.engine import analyze_weak_topics, generate_personalized_recommendations
        
        user_id = str(test_result.user.id) if test_result.user else None
        if user_id:
            # Анализируем слабые темы
            weak_topics = analyze_weak_topics(user_id)
            
            # Генерируем персонализированные рекомендации
            recommendations = generate_personalized_recommendations(user_id)
            
            # Логируем для отладки
            print(f"[ML] Анализ выполнен для пользователя {user_id}")
            print(f"[ML] Слабые темы: {weak_topics}")
            print(f"[ML] Рекомендации: {len(recommendations)} шт.")
    except Exception as e:
        # ML-ошибка не должна ломать основной поток
        print(f"[ML] Ошибка при анализе: {str(e)}")

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

def _collect_student_stats(students):
    """Собирает 5 признаков для каждого студента — как в Android KMeans.kt."""
    from datetime import datetime
    stats = []
    for student in students:
        qs = TestResult.objects.filter(user=student)
        agg = qs.aggregate(avg=Avg("score"), cnt=Count("id"))
        avg_score   = float(agg["avg"] or 0)
        tests_taken = int(agg["cnt"] or 0)

        # Среднее время выполнения (минуты)
        times = []
        for r in qs:
            if r.started_at and r.completed_at:
                delta = (r.completed_at - r.started_at).total_seconds() / 60.0
                if delta >= 0:
                    times.append(delta)
        avg_time = float(sum(times) / len(times)) if times else 0.0

        # Количество уникальных тестов
        test_count = qs.values("test").distinct().count()

        # Средневзвешенная сложность (test_id % 5 + 1 — как в Android)
        difficulty_vals = [((r.test_id or 1) % 5 + 1) for r in qs]
        weighted_diff = float(sum(difficulty_vals) / len(difficulty_vals)) if difficulty_vals else 0.0

        stats.append({
            "user_id":             str(student.id),
            "firstname":           student.firstname,
            "lastname":            student.lastname,
            "avg_score":           avg_score,
            "tests_taken":         tests_taken,
            "avg_time":            avg_time,
            "test_count":          test_count,
            "weighted_difficulty": weighted_diff,
        })
    return stats

# ═══════════════════════════════════════════════════════════════════════
# BLOCKS (NEW)
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def blocks_list(request):
    if request.method == "GET":
        blocks = Block.objects.all()
        # Фильтрация по subject_id, если передан
        subject_id = request.query_params.get('subject_id', None)
        if subject_id:
            blocks = blocks.filter(subject_id=subject_id)
        serializer = BlockSerializer(blocks, many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = BlockSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def block_detail(request, pk):
    block = get_object_or_404(Block, pk=pk)
    if request.method == "GET":
        serializer = BlockSerializer(block)
        return Response(serializer.data)
    elif request.method == "PUT":
        serializer = BlockSerializer(block, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == "DELETE":
        block.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["GET"])
def blocks_by_subject(request, subject_id):
    blocks = Block.objects.filter(subject_id=subject_id).order_by('position')
    serializer = BlockSerializer(blocks, many=True)
    return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════════════
# LESSONS (NEW)
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def lessons_list(request):
    if request.method == "GET":
        lessons = Lesson.objects.all()
        # Фильтрация по block_id, если передан
        block_id = request.query_params.get('block_id', None)
        if block_id:
            lessons = lessons.filter(block_id=block_id)
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = LessonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "PUT", "DELETE"])
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if request.method == "GET":
        serializer = LessonSerializer(lesson)
        return Response(serializer.data)
    elif request.method == "PUT":
        serializer = LessonSerializer(lesson, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == "DELETE":
        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["GET"])
def lessons_by_block(request, block_id):
    lessons = Lesson.objects.filter(block_id=block_id).order_by('position')
    serializer = LessonSerializer(lessons, many=True)
    return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════════════
# TESTS (UPDATED)
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def tests_list(request):
    if request.method == "GET":
        tests = Test.objects.all()
        # Фильтрация по block_id или lesson_id, если переданы
        lesson_id = request.query_params.get('lesson_id', None)
        block_id = request.query_params.get('block_id', None)
        if lesson_id:
            # Получаем тест по ID урока
            lesson = get_object_or_404(Lesson, pk=lesson_id)
            if lesson.test:
                serializer = TestSerializer([lesson.test], many=True)
                return Response(serializer.data)
            else:
                return Response([], status=status.HTTP_200_OK) # У урока нет теста
        elif block_id:
            # Получаем финальный тест по ID блока
            block = get_object_or_404(Block, pk=block_id)
            if block.final_test:
                serializer = TestSerializer([block.final_test], many=True)
                return Response(serializer.data)
            else:
                return Response([], status=status.HTTP_200_OK) # У блока нет финального теста
        else:
            # Просто список всех тестов (без фильтрации)
            serializer = TestSerializer(tests, many=True)
            return Response(serializer.data)

    elif request.method == "POST":
        # Создание теста возможно, но привязка к Lesson или Block должна быть отдельным действием
        # или через вьюхи создания Lesson/Block.
        serializer = TestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def test_by_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    if lesson.test:
        serializer = TestSerializer(lesson.test)
        return Response(serializer.data)
    else:
        return Response({"detail": "Lesson has no associated test"}, status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
def final_test_by_block(request, block_id):
    block = get_object_or_404(Block, pk=block_id)
    if block.final_test:
        serializer = TestSerializer(block.final_test)
        return Response(serializer.data)
    else:
        return Response({"detail": "Block has no associated final test"}, status=status.HTTP_404_NOT_FOUND)

# ═══════════════════════════════════════════════════════════════════════
# ML ENDPOINTS - ПЕРСОНАЛИЗИРОВАННЫЕ РЕКОМЕНДАЦИИ (НОВАЯ ВЕРСИЯ ДЛЯ ДИПЛОМА)
# ═══════════════════════════════════════════════════════════════════════

@api_view(["POST"])
def ml_analyze_weak_topics(request, user_id):
    """
    POST /ml/analyze-weak-topics/<user_id>/
    
    Анализирует ответы пользователя и определяет слабые темы.
    
    Body (опционально):
    {
        "limit_days": 30  // Анализировать только последние N дней (по умолчанию все)
    }
    
    Возвращает:
    {
        "weak_topics": [...],
        "topic_details": {...},
        "overall_stats": {...}
    }
    """
    user = get_object_or_404(User, pk=user_id)
    
    # Получаем все ответы пользователя
    user_answers_qs = UserAnswer.objects.filter(
        test_result__user=user
    ).select_related('test_result', 'question').order_by('-answered_at')
    
    limit_days = request.data.get('limit_days')
    if limit_days:
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=int(limit_days))
        user_answers_qs = user_answers_qs.filter(answered_at__gte=cutoff_date)
    
    # Преобразуем в список словарей
    user_answers = [
        {
            "question_id": ua.question_id,
            "is_correct": ua.is_correct,
            "answered_at": ua.answered_at.isoformat() if ua.answered_at else None,
            "test_id": ua.test_result.test_id if ua.test_result else None,
        }
        for ua in user_answers_qs
    ]
    
    # Получаем информацию о вопросах
    question_ids = set(ua["question_id"] for ua in user_answers if ua["question_id"])
    questions_qs = Question.objects.filter(id__in=question_ids)
    
    questions_map = {}
    for q in questions_qs:
        # Определяем тему вопроса через тест → урок → блок → предмет
        topic = "Общая тема"
        try:
            lesson = Lesson.objects.filter(test=q.test_id).first()
            if lesson:
                block = lesson.block
                topic = block.title  # Используем название блока как тему
        except:
            pass
        
        questions_map[q.id] = {
            "topic": topic,
            "block_id": str(lesson.block_id) if lesson else None,
            "lesson_id": str(lesson.id) if lesson else None,
            "recommendation_link": q.recommendation_link,
            "recommendation_video_link": q.recommendation_video_link,
        }
    
    # Анализируем слабые темы
    result = analyze_weak_topics(user_answers, questions_map)
    
    return Response(result)


@api_view(["GET"])
def ml_personalized_recommendations(request, user_id):
    """
    GET /ml/personalized-recommendations/<user_id>/
    
    Генерирует персонализированные рекомендации с ссылками на материалы.
    
    Query params:
    - limit_days: анализировать ответы за последние N дней
    - max_recommendations: максимальное количество рекомендаций (по умолчанию 10)
    
    Возвращает:
    {
        "user_id": str,
        "recommendations": [
            {
                "topic": str,
                "priority": int,
                "recommendation_text": str,
                "resources": [
                    {"type": "lesson", "title": str, "url": str},
                    {"type": "video", "title": str, "url": str},
                    ...
                ],
                "practice_questions": [int, ...]
            },
            ...
        ],
        "progress_analysis": {...}
    }
    """
    user = get_object_or_404(User, pk=user_id)
    
    limit_days = request.query_params.get('limit_days', None)
    max_recs = int(request.query_params.get('max_recommendations', 10))
    
    # 1. Получаем ответы пользователя
    user_answers_qs = UserAnswer.objects.filter(
        test_result__user=user
    ).select_related('test_result', 'question').order_by('-answered_at')
    
    if limit_days:
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=int(limit_days))
        user_answers_qs = user_answers_qs.filter(answered_at__gte=cutoff_date)
    
    user_answers = [
        {
            "question_id": ua.question_id,
            "is_correct": ua.is_correct,
            "answered_at": ua.answered_at.isoformat() if ua.answered_at else None,
            "test_id": ua.test_result.test_id if ua.test_result else None,
        }
        for ua in user_answers_qs
    ]
    
    # 2. Получаем информацию о вопросах
    question_ids = set(ua["question_id"] for ua in user_answers if ua["question_id"])
    questions_qs = Question.objects.filter(id__in=question_ids)
    
    questions_map = {}
    for q in questions_qs:
        topic = "Общая тема"
        lesson = Lesson.objects.filter(test=q.test_id).first()
        if lesson:
            topic = lesson.block.title
        
        questions_map[q.id] = {
            "topic": topic,
            "block_id": str(lesson.block_id) if lesson else None,
            "lesson_id": str(lesson.id) if lesson else None,
            "recommendation_link": q.recommendation_link,
            "recommendation_video_link": q.recommendation_video_link,
        }
    
    # 3. Анализируем слабые темы
    weak_topics_analysis = analyze_weak_topics(user_answers, questions_map)
    
    # 4. Получаем данные для рекомендаций
    lessons_map = {}
    for lesson in Lesson.objects.select_related('video').all():
        lessons_map[str(lesson.id)] = {
            "title": lesson.title or "",
            "summary": lesson.summary or "",
            "block_id": str(lesson.block_id),
            "video_id": str(lesson.video_id) if lesson.video_id else None,
        }
    
    videos_map = {}
    for video in Video.objects.all():
        videos_map[str(video.id)] = {
            "title": video.name,
            "link": video.link or "",
            "type": video.type.name if video.type else "",
        }
    
    blocks_map = {}
    for block in Block.objects.all():
        blocks_map[str(block.id)] = {
            "title": block.title,
            "subject_id": str(block.subject_id),
        }
    
    # 5. Генерируем рекомендации
    recommendations = generate_personalized_recommendations(
        weak_topics_analysis,
        lessons_map,
        videos_map,
        blocks_map,
        max_recommendations=max_recs
    )
    
    # 6. Строим структуру блоков
    blocks_structure = {
        "blocks": [
            {
                "id": str(b.id),
                "title": b.title,
                "subject": str(b.subject_id),
                "position": b.position,
            }
            for b in Block.objects.all()
        ],
        "lessons_by_block": {},
    }
    
    for block in Block.objects.all():
        block_id = str(block.id)
        lessons = Lesson.objects.filter(block=block).order_by('position')
        blocks_structure["lessons_by_block"][block_id] = [
            {
                "id": str(l.id),
                "title": l.title or "",
                "position": l.position,
            }
            for l in lessons
        ]
    
    # 7. Строим траекторию обучения
    learning_path = build_learning_path(
        weak_topics_analysis,
        recommendations,
        blocks_structure
    )
    
    total_time = sum(step.get("estimated_time_minutes", 0) for step in learning_path)
    
    return Response({
        "user_id": str(user_id),
        "learning_path": learning_path,
        "total_estimated_time_minutes": total_time,
    })


# ═══════════════════════════════════════════════════════════════════════
# СТАРЫЕ ML ENDPOINTS (ОТКЛЮЧЕНЫ, НО СОХРАНЕНЫ ДЛЯ СРАВНЕНИЯ)
# ═══════════════════════════════════════════════════════════════════════

# @api_view(["GET"])
# def ml_recommendations_old(request, user_id):
#     ...


# ═══════════════════════════════════════════════════════════════════════
# VIDEO & VIDEO TYPES
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
def video_types_list(request):
    if request.method == "GET":
        return Response(VideoTypeSerializer(VideoType.objects.all(), many=True).data)
    s = VideoTypeSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
def videos_list(request):
    if request.method == "GET":
        return Response(VideoSerializer(Video.objects.all(), many=True).data)
    s = VideoSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════════════
# TRAINER (USER ANSWERS & SESSIONS)
# ═══════════════════════════════════════════════════════════════════════

@api_view(["GET"])
def user_answers_for_result(request, result_id):
    """Возвращает все 'атомарные' ответы пользователя за одну попытку теста."""
    answers = UserAnswer.objects.filter(test_result_id=result_id)
    return Response(UserAnswerSerializer(answers, many=True).data)


@api_view(["GET", "POST"])
def training_sessions_list(request):
    if request.method == "GET":
        # Извлекаем user_id и lesson_id из параметров запроса (?user_id=...&lesson_id=...)
        user_id = request.query_params.get('user_id')
        lesson_id = request.query_params.get('lesson_id')

        if user_id:
            # Фильтруем сессии только для этого пользователя
            sessions = TrainingSession.objects.filter(user_id=user_id)
            
            # Если передан lesson_id, дополнительно фильтруем по уроку
            if lesson_id:
                sessions = sessions.filter(lesson_id=lesson_id)
        else:
            # Если id не передан, отдаем все (или пустой список для безопасности)
            sessions = TrainingSession.objects.all()

        serializer = TrainingSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    # Логика для POST остается прежней
    s = TrainingSessionSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT"])
def training_session_detail(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk)
    if request.method == "GET":
        return Response(TrainingSessionSerializer(session).data)
    s = TrainingSessionSerializer(session, data=request.data, partial=True)
    s.is_valid(raise_exception=True)
    s.save()
    return Response(s.data)


@api_view(["POST"])
def create_training_from_result(request, result_id):
    """
    Создаёт или обновляет сессию тренажёра по ошибкам из TestResult.
    
    ИЗМЕНЕНИЯ:
    - Сессии теперь привязываются к уроку (lesson) через Test -> Lesson
    - Если пользователь ответил на 4 вопроса из 10+, создаётся новая сессия 
      на оставшиеся вопросы, а старая удаляется
    """
    test_result = get_object_or_404(TestResult, pk=result_id)
    wrong_answers = test_result.user_answers.filter(is_correct=False)

    if not wrong_answers.exists():
        return Response({"detail": "Все ответы верны. Тренажёр не требуется."},
                        status=status.HTTP_400_BAD_REQUEST)

    # Определяем урок, к которому относится тест
    lesson = None
    try:
        # Пытаемся найти урок через связь Test -> Lesson
        lesson = Lesson.objects.get(test=test_result.test)
    except Lesson.DoesNotExist:
        # Если тест не привязан к уроку, оставляем lesson=None
        pass

    # 1. Ищем уже существующую активную сессию для этого пользователя и урока
    session_filters = {'user': test_result.user, 'status': 'active'}
    if lesson:
        session_filters['lesson'] = lesson
    
    session, created = TrainingSession.objects.get_or_create(
        **session_filters,
        defaults={'source_test_result': test_result}
    )

    # 2. Получаем ID вопросов, которые уже есть в этой сессии
    existing_question_ids = list(session.training_questions.values_list('question_id', flat=True))

    # 3. Определяем текущую максимальную позицию в списке
    last_position = session.training_questions.count()

    # 4. Добавляем новые вопросы из ошибок
    new_questions_added = 0
    for wa in wrong_answers:
        if wa.question_id not in existing_question_ids:
            TrainingQuestion.objects.create(
                session=session,
                question=wa.question,
                position=last_position + new_questions_added,
                status='pending'
            )
            new_questions_added += 1

    # 5. ЛОГИКА ЗАВЕРШЕНИЯ: если есть хотя бы один отвеченный вопрос, создаём новую сессию
    total_questions = session.training_questions.count()
    answered_count = session.training_questions.exclude(status='pending').count()
    
    # Если пользователь ответил хотя бы на один вопрос и есть неотвеченные
    if answered_count >= 1 and total_questions > answered_count:
        # Получаем ID вопросов, на которые даны правильные ответы в текущей сессии
        correct_question_ids = list(
            session.training_questions.filter(is_correct=True).values_list('question_id', flat=True)
        )
        
        # Фильтруем pending вопросы: исключаем те, на которые уже были даны правильные ответы
        pending_questions = session.training_questions.filter(
            status='pending'
        ).exclude(question_id__in=correct_question_ids)
        
        pending_count = pending_questions.count()
        
        if pending_count > 0:
            # Создаём новую сессию для оставшихся вопросов
            new_session = TrainingSession.objects.create(
                user=test_result.user,
                lesson=lesson,
                status='active',
                source_test_result=test_result
            )
            
            # Переносим неотвеченные вопросы (исключая уже правильно отвеченные) в новую сессию
            for idx, tq in enumerate(pending_questions):
                TrainingQuestion.objects.create(
                    session=new_session,
                    question=tq.question,
                    position=idx,
                    status='pending'
                )
            
            # Удаляем старые TrainingQuestion из старой сессии
            session.training_questions.all().delete()
            
            # Помечаем старую сессию как завершённую и удаляем её
            session.status = 'completed'
            session.completed_at = timezone.now()
            session.save()
            session.delete()
            
            # Возвращаем новую сессию
            session = new_session
            created = True

    return Response({
        "session": TrainingSessionSerializer(session).data,
        "added_count": new_questions_added,
        "is_new_session": created
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def answer_training_question(request, pk):
    """Принимает ответ пользователя внутри тренажёра."""
    tq = get_object_or_404(TrainingQuestion, pk=pk)
    chosen_answer_id = request.data.get('chosen_answer_id')

    if not chosen_answer_id:
        return Response({"detail": "chosen_answer_id обязателен"}, status=status.HTTP_400_BAD_REQUEST)

    answer = get_object_or_404(Answer, pk=chosen_answer_id)
    tq.chosen_answer = answer
    tq.is_correct = answer.is_correct
    tq.status = 'correct' if answer.is_correct else 'wrong'
    tq.answered_at = timezone.now()
    tq.save()

    # 1. Получаем сессию
    session = tq.session

    # 2. ИСПРАВЛЕНИЕ: Закрываем сессию ТОЛЬКО если НЕТ вопросов со статусом, отличным от 'correct'
    # То есть и 'pending', и 'wrong' будут удерживать сессию открытой
    if not session.training_questions.exclude(status='correct').exists():
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()
    else:
        # Защита: Если сессия случайно была закрыта раньше времени, открываем обратно
        if session.status == 'completed':
            session.status = 'active'
            session.completed_at = None
            session.save()

    return Response(TrainingQuestionSerializer(tq).data)

# ═══════════════════════════════════════════════════════════════════════
# COURSE CONSTRUCTOR VIEW
# ═══════════════════════════════════════════════════════════════════════

@login_required
def course_constructor_view(request):
    current_step = int(request.GET.get('step', 1))
    subject_id = request.GET.get('subject_id')
    block_id = request.GET.get('block_id')
    lesson_id = request.GET.get('lesson_id')

    user = request.user
    is_teacher = getattr(user, 'role', '') == 'teacher'

    selected_items = {}
    subject, block, lesson, test = None, None, None, None

    # Проверка прав доступа к объектам при их получении
    if subject_id:
        subject = get_object_or_404(Subject, id=subject_id)
        if is_teacher and subject.creator != user:
            return redirect('admin:index')  # Запрет доступа к чужому предмету
        selected_items[str(subject.id)] = subject.name
    if block_id:
        block = get_object_or_404(Block, id=block_id)
        selected_items[str(block.id)] = block.title
    if lesson_id:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        selected_items[str(lesson.id)] = lesson.title
        if lesson.test:
            test = lesson.test
            selected_items[f"test_{test.id}"] = test.title

    context = {
        'current_step': current_step,
        'subject_id': subject_id,
        'block_id': block_id,
        'lesson_id': lesson_id,
        'selected_items': selected_items,
        'test': test,
    }

    base_url = reverse('api:course-constructor')

    if current_step == 1:
        if request.method == 'POST':
            form = SubjectForm(request.POST)
            if form.is_valid():
                # БЫЛО: subject = form.save()
                # СТАЛО:
                subject = form.save(commit=False)
                subject.creator = request.user  # <--- ЗАПИСЫВАЕМ АВТОРА
                subject.save()

                query_string = f'?step=2&subject_id={subject.id}'
                return redirect(base_url + query_string)
        else:
            form = SubjectForm()

        context['form'] = form

        # ФИЛЬТРАЦИЯ: Преподаватель видит только свои предметы
        if getattr(request.user, 'role', '') == 'teacher':
            context['subjects'] = Subject.objects.filter(creator=request.user)
        else:
            context['subjects'] = Subject.objects.all()


    elif current_step == 2:

        if not subject_id: return redirect(base_url + '?step=1')

        if request.method == 'POST':

            formset = BlockFormSet(request.POST, prefix='blocks')

            if formset.is_valid():

                for form in formset:

                    # Убеждаемся, что форма реально заполнена (есть заголовок)

                    if form.has_changed() and form.cleaned_data.get('title'):
                        block_instance = form.save(commit=False)

                        block_instance.subject = subject

                        block_instance.save()

                # ИСПРАВЛЕНИЕ: Проверяем, есть ли теперь блоки у предмета

                if Block.objects.filter(subject=subject).exists():

                    return redirect(base_url + f'?step=3&subject_id={subject.id}')

                else:

                    # Если ни одного блока нет, не пускаем дальше

                    context['error_message'] = "Пожалуйста, заполните название хотя бы одного блока, чтобы продолжить."

            else:

                context['formset'] = formset

        else:

            context['formset'] = BlockFormSet(prefix='blocks')

        context['blocks'] = Block.objects.filter(subject=subject)

    elif current_step == 3:
        if not subject_id: return redirect(base_url + '?step=1')
        if not block_id:
            blocks_for_subject = Block.objects.filter(subject_id=subject_id)
            if blocks_for_subject.count() == 1:
                return redirect(base_url + f'?step=3&subject_id={subject_id}&block_id={blocks_for_subject.first().id}')
            context['blocks_to_select'] = blocks_for_subject
            return render(request, 'admin/course_constructor.html', context)

        if request.method == 'POST':
            formset = LessonFormSet(request.POST, prefix='lessons')
            if formset.is_valid():
                for form in formset:
                    if form.has_changed():
                        lesson_instance = form.save(commit=False)
                        lesson_instance.block = block
                        lesson_instance.save()
                if Lesson.objects.filter(block=block).exists():
                    return redirect(base_url + f'?step=3&subject_id={subject.id}&block_id={block.id}')
                else:
                    context['error_message'] = "Пожалуйста, заполните название хотя бы одного урока, чтобы продолжить."
            else:
                context['formset'] = formset
        else:
            context['formset'] = LessonFormSet(prefix='lessons')
        context['lessons'] = Lesson.objects.filter(block=block)


    elif current_step == 4:

        if not lesson_id: return redirect(base_url + f'?step=3&subject_id={subject_id}&block_id={block_id}')

        if request.method == 'POST':

            # --- ДОБАВЛЕН КОД ДЛЯ ОТКРЕПЛЕНИЯ ВИДЕО И ТЕСТА ---

            if 'unlink_video' in request.POST:

                lesson.video = None

                lesson.save()

                return redirect(request.get_full_path())


            elif 'unlink_test' in request.POST:

                lesson.test = None

                lesson.save()

                return redirect(request.get_full_path())

            # --------------------------------------------------

            elif 'submit_new_video' in request.POST:

                video_form = VideoForm(request.POST, request.FILES)

                if video_form.is_valid():
                    video = video_form.save(commit=False)

                    video.creator = request.user  # <--- ЗАПИСЫВАЕМ АВТОРА ВИДЕО

                    video.save()

                    lesson.video = video

                    lesson.save()

                    return redirect(request.get_full_path())

            elif 'submit_existing_video' in request.POST:

                video_id = request.POST.get('existing_video')

                if video_id:
                    lesson.video = get_object_or_404(Video, id=video_id)

                    lesson.save()

                    return redirect(request.get_full_path())

            elif 'submit_new_test' in request.POST:

                test_form = TestForm(request.POST)

                if test_form.is_valid():
                    test = test_form.save(commit=False)

                    test.creator = request.user  # <--- ЗАПИСЫВАЕМ АВТОРА ТЕСТА

                    test.save()

                    lesson.test = test

                    lesson.save()

                    query_string = f'?step=5&subject_id={subject.id}&block_id={block.id}&lesson_id={lesson.id}'

                    return redirect(base_url + query_string)

            elif 'submit_existing_test' in request.POST:

                test_id = request.POST.get('existing_test')

                if test_id:
                    lesson.test = get_object_or_404(Test, id=test_id)

                    lesson.save()

                    return redirect(

                        base_url + f'?step=5&subject_id={subject.id}&block_id={block.id}&lesson_id={lesson.id}')

        # Фильтруем свободные объекты только для текущего преподавателя

        unassigned_videos = Video.objects.filter(lessons__isnull=True)

        unassigned_tests = Test.objects.filter(lesson_for__isnull=True, final_block_of__isnull=True)

        if is_teacher:
            unassigned_videos = unassigned_videos.filter(creator=user)
            unassigned_tests = unassigned_tests.filter(creator=user)

        context['video_form'] = VideoForm()
        context['test_form'] = TestForm()
        context['lesson'] = lesson
        free_videos = Video.objects.filter(lessons__isnull=True)
        free_tests = Test.objects.filter(lesson_for__isnull=True, final_block_of__isnull=True)

        if getattr(request.user, 'role', '') == 'teacher':
            free_videos = free_videos.filter(creator=request.user)
            free_tests = free_tests.filter(creator=request.user)

        context['unassigned_videos'] = free_videos
        context['unassigned_tests'] = free_tests

    elif current_step == 5:
        if not test: return redirect(
            base_url + f'?step=4&subject_id={subject_id}&block_id={block_id}&lesson_id={lesson_id}')
        if request.method == 'POST':
            question_form = QuestionForm(request.POST)
            answer_formset = AnswerFormSet(request.POST, instance=Question())
            if question_form.is_valid() and answer_formset.is_valid():
                new_question = question_form.save(commit=False)
                new_question.test = test
                new_question.save()
                answer_formset.instance = new_question
                answer_formset.save()
                return redirect(request.get_full_path())
        else:
            context['question_form'] = QuestionForm()
            context['answer_formset'] = AnswerFormSet(instance=Question())
        context['questions'] = Question.objects.filter(test=test)

    return render(request, 'admin/course_constructor.html', context)
