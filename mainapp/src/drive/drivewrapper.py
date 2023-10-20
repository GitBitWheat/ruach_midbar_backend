import os
from googleapiclient.http import MediaFileUpload
from mainapp.src.drive.service import build_drive_service
from django.core.files.uploadedfile import InMemoryUploadedFile

class DriveWrapper:

    def __init__(self, service=None):
        if service:
            self.service = service
        else:
            self.service = build_drive_service()

    def create_dir(self, dir_name : str, parent_id : str) -> str:
        file_metadata = {
            'name': dir_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        dir = self.service.files().create(body=file_metadata).execute()
        return dir['id']
    
    def list_files(self, dir_id : str) -> list[dict]:
        return self.service.files().list(
                q=f"'{dir_id}' in parents and trashed=false",
                fields='files(id, name, webViewLink)'
            ).execute().get('files', [])

    def list_subdirectories(self, dir_id : str) -> list[dict]:
        return self.service.files().list(
                q=f"mimeType='application/vnd.google-apps.folder' and '{dir_id}' in parents and trashed=false"
            ).execute().get('files', [])

    # Get the id of the subdirectory of directory with id dir_id titled by the contents of subdir_name.
    # If no such subdirectory exists, create it.
    def get_subdirectory(self, subdir_name : str, dir_id : str) -> str:
        subdirs_list = self.list_subdirectories(dir_id)
        filtered_subdirs_list = list(filter(lambda dir: dir['name'] == subdir_name, subdirs_list))
        if len(filtered_subdirs_list) > 0:
            subdir_id = filtered_subdirs_list[0]['id']
        else:
            subdir_id = self.create_dir(subdir_name, dir_id)
        return subdir_id

    def upload_file(self, file : InMemoryUploadedFile, parent_dir_id : str) -> tuple[str, str]:
        upload_path = rf'mainapp\tmp\{file.name}'
        with open(upload_path, 'wb+') as dest:
            for chunk in file.chunks():  
                dest.write(chunk)

        media = MediaFileUpload(upload_path)
        file_metadata = {
            'name': file.name,
            'parents': [parent_dir_id],
        }
        response = self.service.files() \
        .create(body=file_metadata, media_body=media, fields='id, webViewLink') \
        .execute()

        media.stream().close()
        os.remove(upload_path)

        return (response['id'], response['webViewLink'])
    
    def delete_file(self, file_id : str):
        self.service.files().delete(fileId=file_id).execute()