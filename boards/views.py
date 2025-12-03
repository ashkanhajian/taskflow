from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
import projects
from .models import Board, Column, Task, TaskComment
from .serializers import BoardSerializer, ColumnSerializer, TaskSerializer, TaskCommentSerializer
from projects.models import Project, ProjectsMember
from django.contrib.auth import get_user_model

User = get_user_model()

def user_projects_queryset(user:User):
    return Project.objects.filter(
        Q(owner=user) | Q(memberships__user=user)
    ).distinct()

class BoardListCreateView(generics.ListAPIView):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        projects = user_projects_queryset(user)
        return Project.objects.filter(projects__in=projects)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to create a new board")
        board = serializer.save()
        return board

class BoardDetailView(generics.RetrieveAPIView):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        projects = user_projects_queryset(user)
        return Project.objects.filter(projects__in=projects)
    def perform_update(self, serializer):
        board = self.get_object()
        if board.project.owner != self.request.user:
            raise PermissionDenied("You must be logged in to update a board")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.project.owner != self.request.user:
            raise PermissionDenied("You must be logged in to delete a board")
        instance.delete()

class ColumnListCreateView(generics.ListAPIView):
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        projects = user_projects_queryset(user)
        return Column.objects.filter(projects__in=projects)


    def perform_create(self, serializer):
        board = serializer.validated_data["board"]
        user = self.request.user
        projects = user_projects_queryset(user)
        if board.project not in projects:
            raise PermissionDenied("شما به این برد دسترسی ندارید.")
        serializer.save()
class ColumnDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        projects = user_projects_queryset(user)
        return Column.objects.filter(projects__in=projects)

class TaskListCreateView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        projects = user_projects_queryset(user)
        return Task.objects.filter(column__board__project__in=projects)
    def perform_create(self, serializer):
        user = self.request.user
        column = serializer.validated_data["column"]
        project = user_projects_queryset(user)
        if column.project not in projects:
            raise PermissionDenied('شما به این ستون/برد دسترسی ندارید')
        serializer.save(created_by=user)

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        projects = user_projects_queryset(user)
        return Task.objects.filter(column__board__project__in=projects)

class TaskCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        task_id = self.kwargs["task_id"]
        projects = user_projects_queryset(user)
        qs = TaskComment.objects.select_related(
            "author",
            "task__column__board__project",
        ).filter(task_id=task_id)
        # فقط اعضای پروژه مربوط اجازه دسترسی دارن
        return qs.filter(task__column__board__project__in=projects)

    def perform_create(self, serializer):
        user = self.request.user
        task_id = self.kwargs["task_id"]
        task = get_object_or_404(
            Task.objects.select_related("column__board__project"),
            id=task_id,
        )
        projects = user_projects_queryset(user)
        if task.column.board.project not in projects:
            raise PermissionDenied("شما به این تسک دسترسی ندارید.")
        serializer.save(author=user, task=task)


class TaskCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        task_id = self.kwargs["task_id"]
        projects = user_projects_queryset(user)
        qs = TaskComment.objects.select_related(
            "author",
            "task__column__board__project",
        ).filter(task_id=task_id)
        return qs.filter(task__column__board__project__in=projects)

    def perform_update(self, serializer):
        comment = self.get_object()
        if comment.author != self.request.user:
            raise PermissionDenied("فقط نویسنده کامنت می‌تواند آن را ویرایش کند.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("فقط نویسنده کامنت می‌تواند آن را حذف کند.")
        instance.delete()