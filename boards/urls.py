from django.urls import path

from .views import (
    BoardListCreateView,
    BoardDetailView,
    ColumnListCreateView,
    ColumnDetailView,
    TaskListCreateView,
    TaskDetailView,
    TaskCommentListCreateView,
    TaskCommentDetailView,
)

urlpatterns = [
    path("boards/", BoardListCreateView.as_view(), name="board-list-create"),
    path("boards/<int:pk>/", BoardDetailView.as_view(), name="board-detail"),

    path("columns/", ColumnListCreateView.as_view(), name="column-list-create"),
    path("columns/<int:pk>/", ColumnDetailView.as_view(), name="column-detail"),

    path("tasks/", TaskListCreateView.as_view(), name="task-list-create"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path(
        "tasks/<int:task_id>/comments/",
        TaskCommentListCreateView.as_view(),
        name="task-comment-list-create",
    ),
    path(
        "tasks/<int:task_id>/comments/<int:pk>/",
        TaskCommentDetailView.as_view(),
        name="task-comment-detail",
    ),

]
