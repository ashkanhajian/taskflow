from django.contrib import admin
from .models import Project, ProjectsMember


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "is_archived", "created_at")
    list_filter = ("is_archived", "created_at")
    search_fields = ("name", "owner__username")


@admin.register(ProjectsMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "user", "role", "joined_at")
    list_filter = ("role", "project")
    search_fields = ("project__name", "user__username")