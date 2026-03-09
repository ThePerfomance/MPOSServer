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
    class Meta:
        model = GroupMember
        fields = "__all__"


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
    class Meta:
        model = TestResult
        fields = "__all__"


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
