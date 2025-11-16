from django.contrib import admin
from .models import Board, Column, Task


from django.contrib import admin
from .models import Board, Column, Task


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "project", "is_default", "created_at")
    list_filter = ("project",)
    search_fields = ("name", "project__name")


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "board", "order")
    list_filter = ("board",)
    search_fields = ("name", "board__name")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "column",
        "assignee",
        "priority",
        "is_complete",
        "due_date",
    )

    list_filter = ("priority", "is_complete", "column")
    search_fields = ("title", "description")

