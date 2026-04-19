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
        fields = ["id", "title", "description", "duration", "is_published"]

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = "__all__"

class LessonSerializer(serializers.ModelSerializer):
    test = serializers.PrimaryKeyRelatedField(queryset=Test.objects.all(), allow_null=True, required=False)
    block = serializers.PrimaryKeyRelatedField(queryset=Block.objects.all())

    video = VideoSerializer(read_only=True)

    video_id = serializers.PrimaryKeyRelatedField(
        queryset=Video.objects.all(),
        source='video',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Lesson
        fields = [
            'id', 'title','summary','duration', 'position',
             'is_published', 'block', 'test', 'video', 'video_id',
        ]


class BlockSerializer(serializers.ModelSerializer):
    lessons = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source='lessons.all')

    final_test = serializers.PrimaryKeyRelatedField(queryset=Test.objects.all(), allow_null=True, required=False)

    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())

    class Meta:
        model = Block
        fields = "__all__"


class SubjectSerializer(serializers.ModelSerializer):

    blocks = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source='blocks.all')

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

    class Meta:
        model = Question
        fields = ["id", "text", "answers"]

class TestResultSerializer(serializers.ModelSerializer):
    user_id      = serializers.UUIDField(write_only=True)
    test_id      = serializers.IntegerField(write_only=True)
    completed_at = serializers.DateTimeField(required=False, allow_null=True, write_only=False)

    class Meta:
        model = TestResult
        fields = ["id", "user_id", "test_id", "score", "started_at", "completed_at"]

    def to_representation(self, instance):
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

