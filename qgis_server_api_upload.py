import os
import shutil
import requests

from qgis.core import QgsMessageLog, Qgis

from .helpers import show_fail_box_ok, waitCursor
from .server_config import ServerConfig
from .settings import TAG

class QgisServerApiUpload:
    def __init__(self, paths):
        self.source_project_dir_path = paths.source_project_dir_path
        self.source_project_dir_name = paths.source_project_dir_name
        self.source_project_file_name = paths.source_project_file_name
        self.source_project_zip_file_path = paths.source_project_zip_file_path
        self.server_project_parent_dir_path = paths.server_project_parent_dir_path

    def get_wms_url(self, server_config: ServerConfig) -> str:
        wms_service_version_request = "?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
        wms_url = (f'{server_config.qgis_server_protocol}{server_config.qgis_server_path}'
                   f'{wms_service_version_request}{server_config.projects_path}{self.source_project_dir_name}/'
                   f'{self.source_project_file_name}')
        return wms_url

    def zip_local_project_dir(self) -> bool:
        # Copy source directory and remove unwanted files
        if os.path.isdir(f'{self.source_project_dir_path}_copy_tmp'):
            shutil.rmtree(f'{self.source_project_dir_path}_copy_tmp')
        os.mkdir(f'{self.source_project_dir_path}_copy_tmp')
        shutil.copytree(self.source_project_dir_path, f'{self.source_project_dir_path}_copy_tmp/'
                                                      f'{self.source_project_dir_name}')
        for folder_name, subfolders, filenames in os.walk(f'{self.source_project_dir_path}_copy_tmp'):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                if filename.split(".")[-1] in ('gpkg-wal', 'gpkg-shm'):
                    os.remove(file_path)
        # Compress tmp copy of project folder
        shutil.make_archive(self.source_project_dir_path, 'zip', f'{self.source_project_dir_path}_copy_tmp')
        # Remove temporary copy of source directory
        shutil.rmtree(f'{self.source_project_dir_path}_copy_tmp')
        # Check
        if os.path.isfile(self.source_project_zip_file_path):
            QgsMessageLog.logMessage("Zip-project folder successfully created", TAG, level=Qgis.Info)
            return True
        else:
            return False

    def delete_local_project_zip_file(self) -> None:
        with waitCursor():
            if os.path.isfile(self.source_project_zip_file_path):
                os.remove(self.source_project_zip_file_path)

    def api_upload(self, server_config: ServerConfig):

        # POST request
        # Uploads a ZIP file to the server and extracts its contents into the upload directory,
        # which is configured using the 'api_upload_dir' parameter.
        # Users must have the 'access api' and 'upload files' permissions
        print('api upload')
        api_url = "http://" + server_config.url + "/mapbender/api"
        # credentials
        payload = {
            "username": server_config.username,
            "password": server_config.password
        }
        response_login_check = requests.post(api_url + "/login_check", json=payload)
        print(f"response login: {response_login_check}")
        # check response
        if response_login_check.status_code == 200:
            # Token
            token = response_login_check.json().get("token")
        elif response_login_check.status_code == 404:
            return (f"Error: {response_login_check.status_code}: URL is invalid, please check your details.\n"
                    f"Server address is correct?\n")
        else:
            return (
                f"Error: {response_login_check.status_code}: Unable to validate credentials, please check your details.\n"
                f"Login, password are correct? \n")

        with open(self.source_project_zip_file_path, 'rb') as file:
            print(self.source_project_zip_file_path)
            header = {"Authorization": f"Bearer {token}"}
            files = {'file': file}
            response_upload = requests.post(api_url + "/upload/zip" , files=files, headers=header)
            print(f"response upload: {response_upload}, success: {response_upload.json().get('success')}, "
                  f"error: {response_upload.json().get('error')}")
            print(response_upload.json())
        if response_upload.status_code == 200:
            print('ZIP file uploaded and extracted successfully')
        elif response_upload.status_code == 400:
            return (f"Error {response_upload.status_code}: Invalid request, e.g., no file uploaded or wrong file type.\n"
                    f"Message: {response_upload.json().get('message')}.\n")
        elif response_upload.status_code == 401: #JWT Tocken not found
            return (f"Error {response_upload.status_code}: Unauthorized.\n"
                    f"Message: {response_upload.json().get('message')}.")
        elif response_upload.status_code == 403:
            return (f"Error {response_upload.status_code}: Unauthorized.\n"
                    f"Error: {response_upload.json().get('error')}. Access Denied: Missing permissions - Upload Files.\n")
        elif response_upload.status_code == 500: # Warning: mkdir(): Permission denied (500 Internal Server Error
            # (user: carmen, root)
            return (f"Error {response_upload.status_code}: Server error, e.g., failed to move or extract the file.\n"
                    f"Message: {response_upload.json().get('message')}.\n")
        else:
            return f"Error {response_upload.status_code}"