# api/serializers.py

from rest_framework import serializers
from .models import (
    User, Group, GroupMember, Subject, Block, Lesson, Test, Question, Answer,
    TestResult, StudentCluster, TestDifficulty, ScorePrediction, Recommendation,
    VideoType, Video, UserAnswer, TrainingSession, TrainingQuestion
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class GroupMemberSerializer(serializers.ModelSerializer):
    # Android шлёт user_id / group_id — принимаем их явно
    user_id  = serializers.UUIDField(write_only=True)
    group_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = GroupMember
        fields = ["id", "user_id", "group_id"]

    def to_representation(self, instance):
        return {
            "id":       str(instance.id),
            "user_id":  str(instance.user_id),
            "group_id": str(instance.group_id),
        }

    def create(self, validated_data):
        user_id  = validated_data.pop("user_id")
        group_id = validated_data.pop("group_id")
        validated_data["user_id"]  = user_id
        validated_data["group_id"] = group_id
        return GroupMember.objects.create(**validated_data)


class TestSerializer(serializers.ModelSerializer):
    # Убрали 'subject' из полей
    class Meta:
        model = Test
        fields = ["id", "title", "description", "duration", "is_published"] # Добавлены новые поля
        # exclude = ['subject'] # Альтернативный способ исключения поля 'subject'


# --- Циклическая зависимость: определяем в нужном порядке или используем PrimaryKeyRelatedField ---
# Сначала определяем TestSerializer, затем LessonSerializer, затем BlockSerializer

class LessonSerializer(serializers.ModelSerializer):
    # Вложенный тест урока (опционально) - используем PrimaryKeyRelatedField, чтобы избежать циклической зависимости на этом уровне
    # Если вы хотите вложить *весь* объект Test, используйте TestSerializer(read_only=True) как раньше,
    # но тогда нужно определить TestSerializer *до* этого места или использовать lazy-инициализацию.
    # В данном случае, для простоты, используем PrimaryKeyRelatedField.
    # Если вложенность нужна, см. альтернативу ниже.
    test = serializers.PrimaryKeyRelatedField(queryset=Test.objects.all(), allow_null=True, required=False)
    # test = TestSerializer(read_only=True) # <--- Альтернатива: вложенная сериализация, но требует осторожного обращения с циклом

    # Вложенный блок (опционально) - PrimaryKeyRelatedField для той же причины
    block = serializers.PrimaryKeyRelatedField(queryset=Block.objects.all())

    class Meta:
        model = Lesson
        fields = "__all__" # Или перечислите явно: ['id', 'summary', 'block', 'test', 'video_link', 'duration', 'position', 'is_published']


class BlockSerializer(serializers.ModelSerializer):
    # Вложенные уроки (опционально) - используем LessonSerializer, но т.к. LessonSerializer уже знает про Block (как FK),
    # это создаст цикл при полной вложенности. Используем PrimaryKeyRelatedField или SlugRelatedField.
    # lessons = LessonSerializer(many=True, read_only=True) # <-- Цикл!
    lessons = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source='lessons.all') # <-- Только IDs уроков
    # Или, если хотите только ID урока как список строк:
    # lessons = serializers.SlugRelatedField(many=True, read_only=True, slug_field='id')

    # Вложенный финальный тест (опционально) - PrimaryKeyRelatedField
    final_test = serializers.PrimaryKeyRelatedField(queryset=Test.objects.all(), allow_null=True, required=False)
    # final_test = TestSerializer(read_only=True) # <-- Альтернатива: вложенная сериализация

    # Вложенный предмет (опционально) - PrimaryKeyRelatedField
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    # subject = SubjectSerializer(read_only=True) # <-- Альтернатива: вложенная сериализация

    class Meta:
        model = Block
        fields = "__all__" # Или перечислите явно: ['id', 'title', 'subject', 'final_test', 'lessons', 'description', ...]


class SubjectSerializer(serializers.ModelSerializer):
    # Вложенные блоки (опционально) - PrimaryKeyRelatedField для избежания цикла, если BlockSerializer включает Subject
    # blocks = BlockSerializer(many=True, read_only=True) # <-- Цикл!
    blocks = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source='blocks.all') # <-- Только IDs блоков
    # blocks = serializers.SlugRelatedField(many=True, read_only=True, slug_field='id') # <-- Альтернатива

    class Meta:
        model = Subject
        fields = "__all__" # Или ['id', 'name', 'blocks']


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"


class QuestionWithAnswersSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    # test = TestSerializer(read_only=True) # Опционально: включить информацию о тесте

    class Meta:
        model = Question
        fields = ["id", "text", "answers"] # Убрали "test", если не нужно
        # fields = ["id", "text", "test", "answers"] # Если нужно включить тест


# --- Обновим TestResultSerializer, чтобы он работал с новым Test ---
# Текущий TestResultSerializer уже использует test_id, что хорошо.
# Но если вы хотите получить *вложенную* информацию о тесте, можно добавить:
class TestResultSerializer(serializers.ModelSerializer):
    # Поля для записи — принимаем user_id / test_id / completed_at как от Android
    user_id      = serializers.UUIDField(write_only=True)
    test_id      = serializers.IntegerField(write_only=True)
    completed_at = serializers.DateTimeField(required=False, allow_null=True, write_only=False)

    class Meta:
        model = TestResult
        fields = ["id", "user_id", "test_id", "score", "started_at", "completed_at"]

    def to_representation(self, instance):
        """Format dates as yyyy-MM-dd'T'HH:mm:ss for Android SimpleDateFormat."""
        def fmt(dt):
            return dt.strftime("%Y-%m-%dT%H:%M:%S") if dt else None

        return {
            "id":           str(instance.id),
            "user_id":      str(instance.user_id) if instance.user_id else None,
            "test_id":      instance.test_id if instance.test_id else None,
            "score":        instance.score,
            "started_at":   fmt(instance.started_at),
            "completed_at": fmt(instance.completed_at),
        }

    def create(self, validated_data):
        from datetime import datetime
        user_id = validated_data.pop("user_id")
        test_id = validated_data.pop("test_id")
        validated_data["user_id"] = user_id
        validated_data["test_id"] = test_id
        if not validated_data.get("completed_at"):
            validated_data["completed_at"] = datetime.now()
        if not validated_data.get("started_at"):
            validated_data["started_at"] = validated_data["completed_at"]
        return TestResult.objects.create(**validated_data)

class TestResultWithTestDetailsSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)
    test_id = serializers.IntegerField(write_only=True)
    # Вложенная информация о тесте
    test_details = TestSerializer(source='test', read_only=True)

    class Meta:
        model = TestResult
        fields = ["id", "user_id", "test_id", "score", "started_at", "completed_at", "test_details"]

    # Наследуем to_representation и create от TestResultSerializer, если логика одинакова
    # иначе, переопределите их здесь.


# ── ML serializers ──────────────────────────────────

class StudentClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentCluster
        fields = "__all__"


class TestDifficultySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestDifficulty
        fields = "__all__"


class ScorePredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScorePrediction
        fields = "__all__"


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = "__all__"

class VideoTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoType
        fields = "__all__"


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = "__all__"


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = "__all__"

class TrainingQuestionSerializer(serializers.ModelSerializer):
    question_details = QuestionWithAnswersSerializer(source='question', read_only=True)

    class Meta:
        model = TrainingQuestion
        fields = ['id', 'session', 'question_details', 'status', 'position']

class TrainingSessionSerializer(serializers.ModelSerializer):
    training_questions = TrainingQuestionSerializer(many=True, read_only=True)
    class Meta:
        model = TrainingSession
        fields = ['id', 'user', 'status', 'source_test_result', 'training_questions', 'created_at']

