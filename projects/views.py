from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Project, ProjectsMember
from .serializers import ProjectSerializer, ProjectMemberWriteSerializer, ProjectsMemberSerializer


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
def _ensure_project_admin_or_owner(user, project: Project):
    if not user.is_authenticated:
        raise PermissionDenied("باید لاگین باشی.")
    # owner همیشه دسترسی داره
    if project.owner == user:
        return
    # بررسی اینکه توی پروژه admin هست یا نه
    membership = ProjectsMember.objects.filter(project=project, user=user).first()
    if not membership or membership.role not in (
        ProjectsMember.Role.ADMIN,
        ProjectsMember.Role.OWNER,
    ):
        raise PermissionDenied("فقط مالک یا ادمین‌های پروژه می‌توانند این عملیات را انجام دهند.")

class ProjectMemberListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, id=project_id)

        # هر عضوی از پروژه می‌تونه لیست اعضا رو ببینه
        if not ProjectsMember.objects.filter(project=project, user=user).exists() and project.owner != user:
            raise PermissionDenied("شما عضو این پروژه نیستید.")

        # فرض: related_name = 'memberships'
        return ProjectsMember.objects.filter(project=project)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectMemberWriteSerializer
        return ProjectsMemberSerializer

    def perform_create(self, serializer):
        user = self.request.user
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, id=project_id)

        # فقط owner/admin اجازه invite دارد
        _ensure_project_admin_or_owner(user, project)

        # جلوگیری از اضافه‌شدن دوباره‌ی عضو
        target_user = serializer.validated_data["user"]
        if ProjectsMember.objects.filter(project=project, user=target_user).exists():
            raise PermissionDenied("این کاربر قبلاً عضو این پروژه است.")

        serializer.save(project=project)


class ProjectMemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, id=project_id)

        # هر عضوی که دسترسی به پروژه دارد، می‌تواند جزئیات اعضا را ببیند
        if not ProjectsMember.objects.filter(project=project, user=user).exists() and project.owner != user:
            raise PermissionDenied("شما عضو این پروژه نیستید.")

        return ProjectsMember.objects.filter(project=project)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProjectMemberWriteSerializer
        return ProjectsMemberSerializer

    def perform_update(self, serializer):
        user = self.request.user
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, id=project_id)

        _ensure_project_admin_or_owner(user, project)

        membership = self.get_object()
        # نمی‌گذاریم کسی نقش OWNER خودش را از پروژه حذف کند از اینجا
        if membership.user == project.owner and serializer.validated_data.get("role") != ProjectsMember.Role.OWNER:
            raise PermissionDenied("نقش مالک پروژه را نمی‌توان تغییر داد.")

        serializer.save(project=project, user=serializer.validated_data["user"])

    def perform_destroy(self, instance):
        user = self.request.user
        project = instance.project

        _ensure_project_admin_or_owner(user, project)

        # مالک پروژه را از اعضا پاک نکن
        if instance.user == project.owner:
            raise PermissionDenied("نمی‌توان مالک پروژه را حذف کرد.")

        instance.delete()