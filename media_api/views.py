import os
from django.conf import settings
from django.shortcuts import get_object_or_404  # Crucial import added here
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import File, Folder

class DeleteFileView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, file_id):
        try:
            file_obj = File.objects.get(id=file_id)
        except File.DoesNotExist:
            return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        if file_obj.owner != request.user:
            return Response(
                {"error": "You do not have permission to delete this file."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        file_path = os.path.abspath(file_obj.file.path)
        media_root = os.path.abspath(settings.MEDIA_ROOT)

        if not file_path.startswith(media_root):
            return Response(
                {"error": "Security Violation: Invalid or unsafe storage path detected."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if os.path.exists(file_path):
            file_obj.file.delete(save=False)
        
        file_obj.delete()

        return Response({"message": "File deleted successfully."}, status=status.HTTP_200_OK)


class MoveFileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, file_id):
        file_obj = get_object_or_404(File, id=file_id)
        
        if file_obj.owner != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        target_folder_id = request.data.get('target_folder_id')

        if target_folder_id is not None:
            target_folder = get_object_or_404(Folder, id=target_folder_id)
            if target_folder.owner != request.user:
                return Response({"error": "Target folder permission denied."}, status=status.HTTP_403_FORBIDDEN)
            file_obj.folder = target_folder
        else:
            file_obj.folder = None

        file_obj.save()
        return Response({"message": f"File moved successfully to folder {target_folder_id or 'Root'}."}, status=status.HTTP_200_OK)


class MoveFolderView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, folder_id):
        folder_obj = get_object_or_404(Folder, id=folder_id)

        if folder_obj.owner != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        target_folder_id = request.data.get('target_folder_id')

        if target_folder_id is not None:
            target_folder_id = int(target_folder_id)
            
            if target_folder_id == folder_obj.id:
                return Response({"error": "Cannot move a folder into itself."}, status=status.HTTP_400_BAD_REQUEST)

            target_folder = get_object_or_404(Folder, id=target_folder_id)
            
            if target_folder.owner != request.user:
                return Response({"error": "Target folder permission denied."}, status=status.HTTP_403_FORBIDDEN)

            current_parent = target_folder
            while current_parent is not None:
                if current_parent.id == folder_obj.id:
                    return Response({"error": "Cannot move a folder into one of its subfolders."}, status=status.HTTP_400_BAD_REQUEST)
                current_parent = current_parent.parent

            folder_obj.parent = target_folder
        else:
            folder_obj.parent = None

        folder_obj.save()
        return Response({"message": f"Folder moved successfully to folder {target_folder_id or 'Root'}."}, status=status.HTTP_200_OK)