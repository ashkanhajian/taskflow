from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

import projects
from .models import Board, Column, Task
from .serializers import BoardSerializer, ColumnSerializer, TaskSerializer
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
