from django.template.context_processors import request
from rest_framework import serializers
from django.contrib.auth import get_user_model

from accounts.serializers import UserSerializer
from .models import Board, Column, Task, TaskComment, Label
from projects.models import Project, ProjectsMember

User = get_user_model()

class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = [
            'id',
            'project',
            'name',
            'description',
            'is_default',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_project(self, value,data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError('You must login first')
        is_owner = value.owner == user
        is_member = ProjectsMember.objects.filter(project=value, user=user).exists()

        if not (is_owner or is_member):
            raise serializers.ValidationError("شما عضو این پروژه نیستید.")

        return value
class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ["id", "project", "name", "color", "created_at"]
        read_only_fields = ["id", "created_at"]

class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = "__all__"
        read_only_fields = ['id']

class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    assignee = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(),
                                            required=False, allow_null=True)
    class Meta:
        model = Task
        fields = [
            "id",
            "column",
            "title",
            "description",
            "created_by",
            "assignee",
            "priority",
            "due_date",
            "labels",
            "is_complete",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

class TaskCommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = TaskComment
        fields = [
            "id",
            "task",
            "author",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at", "task"]

    def validate_labels(self, value):
        """

        """
        column_id = self.initial_data.get("column")
        project = None

        from .models import Column

        if column_id:
            try:
                column = Column.objects.select_related("board").get(pk=column_id)
                project = column.board
            except Column.DoesNotExist:
                raise serializers.ValidationError("ستون نامعتبر است.")
        elif self.instance:

            project = self.instance.column.board

        if project is None:
            return value

        for label in value:
            if label.project != project:
                raise serializers.ValidationError(
                    f"لیبل «{label.name}» متعلق به این پروژه نیست."
                )
        return value