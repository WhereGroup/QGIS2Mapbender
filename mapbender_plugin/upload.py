import os
import shutil

from qgis._core import QgsMessageLog, Qgis
from qgis.utils import iface

from mapbender_plugin.helpers import show_fail_box_ok, waitCursor
from mapbender_plugin.settings import TAG, WMS_SERVICE_VERSION_REQUEST


class Upload:
    def __init__(self, connection, paths):
        self.connection = connection
        self.source_project_dir_path = paths.source_project_dir_path
        self.source_project_dir_name = paths.source_project_dir_name
        self.source_project_file_name = paths.source_project_file_name
        self.source_project_zip_file_path = paths.source_project_zip_file_path
        self.server_projects_dir_path = paths.server_projects_dir_path

    def get_wms_url(self, server_config) -> str:
        protocol_is_http = True
        # Check "http://"
        if protocol_is_http:
            protocol = 'http://'
            wms_url = (f'{protocol}{server_config.url}{server_config.qgis_server_path}{WMS_SERVICE_VERSION_REQUEST}'
                       f'{server_config.projects_path}{self.source_project_dir_name}/'
                       f'{self.source_project_file_name}')
            return wms_url

    def check_if_project_folder_exists_on_server(self) -> bool:
        with waitCursor():
            if self.connection.run('test -d {}'.format(self.server_projects_dir_path + self.source_project_dir_name),
                              warn=True).failed:  # Without .zip (if it exists, is unzipped)
                return False
        return True

    def remove_project_folder_from_server(self) -> bool:
        with waitCursor():
            result = self.connection.run(
                f'cd ..; cd {self.server_projects_dir_path}; rm -r {self.source_project_dir_name};')
            # Check success:
            if os.path.isdir(f'{self.server_projects_dir_path}{self.source_project_dir_name}'):
                show_fail_box_ok("Failed",
                                 f"Could not remove existing project folder from server. Reason {result.return_code}.")
                return False
            QgsMessageLog.logMessage("Existing project folder successfully removed from server", TAG,
                                     level=Qgis.Info)
            return True

    def zip_upload_unzip_clean(self) -> bool:
        QgsMessageLog.logMessage("Updating QGIS project and data on server ...", TAG, level=Qgis.Info)
        if self.zip_local_project_dir():
            if self.upload_project_zip_file():
                QgsMessageLog.logMessage("QGIS-Project folder successfully uploaded", TAG, level=Qgis.Info)
                self.delete_local_project_zip_file()
                if self.unzip_and_remove_project_dir_on_server():
                    return True
        return False

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

    def upload_project_zip_file(self) -> bool:
        with waitCursor():
            try:
                self.connection.put(local=self.source_project_zip_file_path, remote=self.server_projects_dir_path)
                QgsMessageLog.logMessage("QGIS-Project folder successfully uploaded", TAG, level=Qgis.Info)
                return True
            except Exception as e:
                show_fail_box_ok("Failed", f"Project directory could not be uploaded. Reason {e}")
                return False

    def unzip_and_remove_project_dir_on_server(self) -> bool:
        with waitCursor():
            result = self.connection.run(
                f'cd ..; cd {self.server_projects_dir_path}/; unzip {self.source_project_dir_name}.zip;',
                warn=True)
            if result.ok:
                QgsMessageLog.logMessage("Files unzipped on server", TAG, level=Qgis.Info)
                self.connection.run(f'cd ..; cd /data/qgis-projects/; rm {self.source_project_dir_name}.zip;')
                return True
            show_fail_box_ok("Failed", f"Could not unzip project directory on server. Reason {result.return_code}")
            return False
