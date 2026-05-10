# api/services/personalization.py
from django.db.models import Avg, Sum, Q, F, Avg, ExpressionWrapper, fields
from django.utils import timezone
from api.models import Test, TestResult, TestDifficulty, User, StudentCluster, Question, TrainingSession, \
    TrainingQuestion, Lesson
import random

def update_test_segmentation():
    """Математическая сегментация тестов по уровню сложности"""
    tests = Test.objects.annotate(
        avg_score=Avg('results__earned_points')
    )

    for test in tests:
        # Считаем максимальный балл за тест
        max_points = test.questions.aggregate(total=Sum('points'))['total'] or 0
        if max_points == 0:
            continue

        avg_score = test.avg_score or 0

        # Математический расчет сложности D
        difficulty_coef = 1 - (avg_score / max_points)

        if difficulty_coef <= 0.3:
            diff_label = 'easy'
        elif difficulty_coef <= 0.6:
            diff_label = 'medium'
        else:
            diff_label = 'hard'

        TestDifficulty.objects.update_or_create(
            test=test,
            defaults={
                'difficulty': diff_label,
                'avg_score_all': avg_score
            }
        )


def update_student_clusters():
    students = User.objects.filter(role='student')

    # 1. Предрасчет времени (как делали ранее)
    test_avg_times = {}
    tests_with_time = TestResult.objects.filter(completed_at__isnull=False).values('test_id').annotate(
        avg_duration=Avg(ExpressionWrapper(F('completed_at') - F('started_at'), output_field=fields.DurationField()))
    )
    for t in tests_with_time:
        test_avg_times[t['test_id']] = t['avg_duration'].total_seconds()

    for student in students:
        # Сортируем по времени, чтобы правильно считать номера попыток
        results = TestResult.objects.filter(
            user=student,
            completed_at__isnull=False
        ).select_related('test__difficulty').order_by('started_at')

        if not results.exists():
            continue

        weighted_earned = 0
        weighted_total = 0
        tests_taken = results.count()

        # Словари для расчетов
        attempt_counts = {}  # Для расчета K_att
        active_dates = set()  # Для расчета K_reg

        for res in results:
            # Трекинг дат для регулярности
            active_dates.add(res.completed_at.date())

            # Трекинг попыток для K_att
            t_id = res.test_id
            attempt_counts[t_id] = attempt_counts.get(t_id, 0) + 1
            current_attempt = attempt_counts[t_id]

            # --- РАСЧЕТ КОЭФФИЦИЕНТОВ ---

            # 1. Сложность
            diff_obj = getattr(res.test, 'difficulty', None)
            d = 0.2 if getattr(diff_obj, 'difficulty', '') == 'easy' else (
                0.8 if getattr(diff_obj, 'difficulty', '') == 'hard' else 0.5)
            k_diff = 1 + d

            # 2. Время (K_time)
            user_duration = (res.completed_at - res.started_at).total_seconds()
            avg_duration = test_avg_times.get(t_id)
            k_time = 1.0
            if avg_duration and avg_duration > 0:
                k_time = max(0.9, min(1.1, 1 + 0.1 * (1 - (user_duration / avg_duration))))

            # 3. Попытки (K_att)
            k_att = max(0.7, 1.0 - 0.1 * (current_attempt - 1))

            # Начисляем баллы
            weighted_earned += res.earned_points * k_diff * k_time * k_att
            weighted_total += res.total_points * k_diff

        if weighted_total == 0:
            continue

        # --- 4. РЕГУЛЯРНОСТЬ (K_reg) ---
        k_reg = 1.0
        sorted_dates = sorted(list(active_dates))
        if len(sorted_dates) > 1:
            total_days = (sorted_dates[-1] - sorted_dates[0]).days
            avg_gap = total_days / (len(sorted_dates) - 1)

            if avg_gap <= 3:
                k_reg = 1.05  # Бонус +5%
            elif avg_gap >= 7:
                k_reg = 0.95  # Штраф -5%

        # Итоговый расчет кластера
        performance = min((weighted_earned / weighted_total) * 100 * k_reg, 100.0)

        if performance >= 80:
            c_id, c_label = 1, 'Отличники'
        elif performance >= 50:
            c_id, c_label = 2, 'Хорошисты'
        else:
            c_id, c_label = 3, 'Нужна помощь'

        StudentCluster.objects.update_or_create(
            user=student,
            defaults={
                'cluster_id': c_id,
                'cluster_label': c_label,
                'avg_score': performance,
                'tests_taken': tests_taken
            }
        )


def generate_adaptive_session(user, lesson_id=None, total_questions=10):
        """
        Создает адаптивную сессию тренажера на основе кластера студента.
        Можно привязать к конкретному уроку (lesson_id) или сделать глобальной.
        """
        # 1. Определяем кластер студента (по умолчанию считаем "Хорошистом", если данных еще нет)
        cluster = StudentCluster.objects.filter(user=user).first()
        cluster_id = cluster.cluster_id if cluster else 2

        # 2. Устанавливаем квоты вопросов (easy, medium, hard) в зависимости от кластера
        if cluster_id == 3:  # Нужна помощь
            quotas = {'easy': int(total_questions * 0.7), 'medium': int(total_questions * 0.3), 'hard': 0}
        elif cluster_id == 2:  # Хорошисты
            quotas = {'easy': int(total_questions * 0.2), 'medium': int(total_questions * 0.6),
                      'hard': int(total_questions * 0.2)}
        else:  # Отличники
            quotas = {'easy': 0, 'medium': int(total_questions * 0.3), 'hard': int(total_questions * 0.7)}

        # Корректируем возможные потери при округлении
        quotas['medium'] += total_questions - sum(quotas.values())

        # 3. Собираем базу доступных вопросов
        base_query = Q()
        if lesson_id:
            # Если тренируем конкретный урок, берем вопросы из его теста
            base_query &= Q(test__lesson_for__id=lesson_id)

        # Исключаем вопросы, на которые студент уже ответил ПРАВИЛЬНО в тренажере
        answered_correctly = TrainingQuestion.objects.filter(
            session__user=user,
            is_correct=True
        ).values_list('question_id', flat=True)

        base_query &= ~Q(id__in=answered_correctly)

        selected_questions = []

        # 4. Выбираем вопросы по квотам
        for diff_level, count in quotas.items():
            if count <= 0:
                continue

            # Ищем вопросы нужной сложности
            q_pool = list(Question.objects.filter(
                base_query & Q(test__difficulty__difficulty=diff_level)
            ))

            # Если вопросов нужной сложности не хватает, берем сколько есть
            if len(q_pool) > count:
                selected_questions.extend(random.sample(q_pool, count))
            else:
                selected_questions.extend(q_pool)

        # 5. Если вопросов все равно меньше 10 (например, мало базы), добираем любые случайные
        if len(selected_questions) < total_questions:
            shortage = total_questions - len(selected_questions)
            exclude_ids = [q.id for q in selected_questions] + list(answered_correctly)
            fallback_pool = list(Question.objects.filter(base_query).exclude(id__in=exclude_ids))

            if len(fallback_pool) > shortage:
                selected_questions.extend(random.sample(fallback_pool, shortage))
            else:
                selected_questions.extend(fallback_pool)

        # Перемешиваем итоговый пул
        random.shuffle(selected_questions)

        # 6. Создаем сессию и привязываем вопросы
        if not selected_questions:
            return None  # Нет вопросов для генерации

        session = TrainingSession.objects.create(
            user=user,
            lesson_id=lesson_id,
            status='active'
        )

        training_questions = [
            TrainingQuestion(
                session=session,
                question=q,
                position=idx,
                status='pending'
            ) for idx, q in enumerate(selected_questions)
        ]
        TrainingQuestion.objects.bulk_create(training_questions)

        return session


def get_learning_path(user):
    """
    Формирует список шагов на основе недавних ошибок пользователя.
    """
    # 1. Находим последние результаты тестов с низким баллом
    low_results = TestResult.objects.filter(user=user).order_by('-completed_at')[:5]

    learning_steps = []
    step_counter = 1

    for result in low_results:
        # Если процент правильных ответов меньше 70%
        score_percent = (result.earned_points / result.total_points * 100) if result.total_points > 0 else 0

        if score_percent < 70:
            # Находим блок или урок, связанный с этим тестом
            # (Логика зависит от того, как тесты привязаны к контенту в вашей модели)
            test = result.test
            lesson = Lesson.objects.filter(test=test).first() or Lesson.objects.filter(block__final_test=test).first()

            if lesson:
                # Шаг 1: Посмотреть видео
                if hasattr(lesson, 'video') and lesson.video:
                    learning_steps.append({
                        "step": step_counter,
                        "action": "watch",
                        "topic": lesson.title,
                        "content": f"Посмотрите видеоматериал к уроку: {lesson.title}"
                    })
                    step_counter += 1

                # Шаг 2: Изучить теорию
                learning_steps.append({
                    "step": step_counter,
                    "action": "study",
                    "topic": lesson.title,
                    "content": "Повторите теоретический материал урока."
                })
                step_counter += 1

                # Шаг 3: Практика (тренажер)
                learning_steps.append({
                    "step": step_counter,
                    "action": "practice",
                    "topic": lesson.title,
                    "content": "Пройдите адаптивный тренажер по этой теме."
                })
                step_counter += 1

    return learning_steps if learning_steps else None