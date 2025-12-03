from django.db import transaction
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

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

def _ensure_user_in_project(user, project):
    if not user.is_authenticated:
        raise PermissionDenied("باید لاگین باشی.")
    if project.owner == user:
        return
    if ProjectsMember.objects.filter(project=project, user=user).exists():
        return
    raise PermissionDenied("شما به این پروژه دسترسی ندارید.")


class ColumnReorderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, board_id):
        user = request.user
        board = get_object_or_404(
            Board.objects.select_related("project"),
            id=board_id,
        )

        _ensure_user_in_project(user, board.project)

        column_ids = request.data.get("column_ids")
        if not isinstance(column_ids, list) or not column_ids:
            return Response(
                {"detail": "فیلد column_ids باید یک لیست از شناسه ستون‌ها باشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ستون‌هایی که واقعاً متعلق به این برد هستند
        columns = list(Column.objects.filter(board=board, id__in=column_ids))

        if len(columns) != len(column_ids):
            return Response(
                {"detail": "بعضی از ستون‌ها یافت نشدند یا متعلق به این برد نیستند."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        columns_by_id = {c.id: c for c in columns}

        with transaction.atomic():
            for index, cid in enumerate(column_ids):
                col = columns_by_id[cid]
                col.order = index
                col.save(update_fields=["order"])

        serialized = ColumnSerializer(
            Column.objects.filter(board=board).order_by("order", "id"),
            many=True,
        )
        return Response(serialized.data, status=status.HTTP_200_OK)

class TaskReorderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, column_id):
        user = request.user
        column = get_object_or_404(
            Column.objects.select_related("board__project"),
            id=column_id,
        )

        _ensure_user_in_project(user, column.board.project)

        task_ids = request.data.get("task_ids")
        if not isinstance(task_ids, list) or not task_ids:
            return Response(
                {"detail": "فیلد task_ids باید یک لیست از شناسه تسک‌ها باشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tasks = list(Task.objects.filter(column=column, id__in=task_ids))

        if len(tasks) != len(task_ids):
            return Response(
                {"detail": "بعضی از تسک‌ها یافت نشدند یا متعلق به این ستون نیستند."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tasks_by_id = {t.id: t for t in tasks}

        with transaction.atomic():
            for index, tid in enumerate(task_ids):
                task = tasks_by_id[tid]
                task.order = index
                task.save(update_fields=["order"])

        serialized = TaskSerializer(
            Task.objects.filter(column=column).order_by("order", "id"),
            many=True,
        )
        return Response(serialized.data, status=status.HTTP_200_OK)