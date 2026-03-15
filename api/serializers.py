from rest_framework import serializers
from .models import (
    User, Group, GroupMember, Subject, Test, Question, Answer, TestResult,
    StudentCluster, TestDifficulty, ScorePrediction, Recommendation,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


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


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


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
        fields = ["id", "test", "text", "answers"]


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = "__all__"


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