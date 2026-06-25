from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Folder, File
import os

class MediaAPITests(APITestCase):

    def setUp(self):
        # Create two distinct users
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')

        # Create base folders for User 1
        self.folder1 = Folder.objects.create(name="Folder 1", owner=self.user1)
        self.subfolder1 = Folder.objects.create(name="Subfolder 1", parent=self.folder1, owner=self.user1)

        # Create an isolated mock file in memory for testing
        mock_file = SimpleUploadedFile("test_file.txt", b"file_content", content_type="text/plain")
        self.file1 = File.objects.create(name="Test File", file=mock_file, folder=self.folder1, owner=self.user1)

    def test_delete_file_success(self):
        """Ensure an owner can successfully delete their file."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('delete-file', kwargs={'file_id': self.file1.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(File.objects.filter(id=self.file1.id).exists())

    def test_delete_file_permission_denied(self):
        """Ensure a user cannot delete another user's file."""
        self.client.force_authenticate(user=self.user2) # Authenticate as unauthorized user
        url = reverse('delete-file', kwargs={'file_id': self.file1.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(File.objects.filter(id=self.file1.id).exists())

    def test_move_file_success(self):
        """Ensure an owner can move their file to a valid destination folder."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('move-file', kwargs={'file_id': self.file1.id})
        
        data = {'target_folder_id': self.subfolder1.id}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.file1.refresh_from_db()
        self.assertEqual(self.file1.folder, self.subfolder1)

    def test_move_folder_recursion_block(self):
        """Ensure a folder cannot be moved into itself or its own child subfolder."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('move-folder', kwargs={'folder_id': self.folder1.id})

        data = {'target_folder_id': self.subfolder1.id}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_upload_file_success(self):
        """Ensure an authenticated user can upload a file."""

        self.client.force_authenticate(user=self.user1)

        upload_file = SimpleUploadedFile(
            "upload_test.txt",
            b"Hello Upload",
            content_type="text/plain"
        )

        response = self.client.post(
            reverse('upload-file'),
            {
                "name": "Uploaded File",
                "file": upload_file,
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(File.objects.count(), 2)

    def test_list_files_success(self):
        """Ensure an authenticated user can view their files."""

        self.client.force_authenticate(user=self.user1)

        response = self.client.get(
            reverse('list-files')
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)