from .views import (
    UploadFileView,
    ListFilesView,
    DeleteFileView,
    MoveFileView,
    MoveFolderView,
)
from django.urls import path
from .views import DeleteFileView, MoveFileView, MoveFolderView #Added Imports
urlpatterns = [

    path(
        'files/upload/',
        UploadFileView.as_view(),
        name='upload-file'
    ),

    path(
        'files/',
        ListFilesView.as_view(),
        name='list-files'
    ),

    # Pass the file_id dynamically through the endpoint URL
    path('files/<int:file_id>/delete/', DeleteFileView.as_view(), name='delete-file'),

#New Endpoints for moving items
    path('files/<int:file_id>/move/', MoveFileView.as_view(), name='move-file'),
    path('folders/<int:folder_id>/move/', MoveFolderView.as_view(), name='move-folder'),
]