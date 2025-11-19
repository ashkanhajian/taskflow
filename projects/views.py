from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Project, ProjectsMember
from .serializers import ProjectSerializer


class ProjectListCreateView(generics.ListCreateAPIView):

    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Project.objects.none()


        return Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("برای ساخت پروژه باید لاگین باشی.")


        project = serializer.save(owner=user)

        ProjectsMember.objects.create(
            project=project,
            user=user,
            role=ProjectsMember.Role.OWNER,
        )


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Project.objects.none()


        return Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct()

    def perform_update(self, serializer):
        project = self.get_object()
        if project.owner != self.request.user:
            raise PermissionDenied("فقط سازنده پروژه می‌تواند آن را ویرایش کند.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("فقط سازنده پروژه می‌تواند آن را حذف کند.")
        instance.delete()
