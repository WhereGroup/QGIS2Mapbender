import os
import shutil

from qgis._core import QgsMessageLog, Qgis

from mapbender_plugin.helpers import show_fail_box_ok
from mapbender_plugin.settings import TAG


class Upload:
    def __init__(self, source_project_dir_path, source_project_dir_name, source_project_zip_file_path,
                 server_projects_dir_path):
        self.source_project_dir_path = source_project_dir_path
        self.source_project_dir_name = source_project_dir_name
        self.source_project_zip_file_path = source_project_zip_file_path
        self.server_projects_dir_path = server_projects_dir_path

    def check_if_project_folder_exists_on_server(self, connection) -> bool:
        try:
            if connection.run('test -d {}'.format(self.server_projects_dir_path + self.source_project_dir_name),
                              warn=True).failed:  # Without .zip (if it exists, is unzipped)
                return False
            else:
                return True
        except OSError as e:
            show_fail_box_ok("Failed",
                             f"Reason: {e}")
            return False
        except Exception as e:
            show_fail_box_ok("Failed",
                             f"Could not check if project directory exists already on the server. Reason: {e}")
            return False

    def remove_project_folder_from_server(self, connection) -> bool:
        try:
            connection.run(
                f'cd ..; cd {self.server_projects_dir_path}; rm -r {self.source_project_dir_name};')
            # Check success:
            if os.path.isdir(f'{self.server_projects_dir_path}{self.source_project_dir_name}'):
                show_fail_box_ok("Failed", f"Could not remove existing project folder from server.")
                return False
            else:
                QgsMessageLog.logMessage("Existing project folder successfully removed from server", TAG,
                                         level=Qgis.Info)
                return True

        except Exception as e:
            show_fail_box_ok("Failed", f"Could not remove existing project folder from server. Reason: {e}")
            return False

    def zip_upload_unzip_clean(self, connection):
        QgsMessageLog.logMessage("Updating QGIS project and data on server ...", TAG, level=Qgis.Info)
        self.zip_local_project_dir()
        self.upload_project_zip_file(connection)
        QgsMessageLog.logMessage("QGIS-Project folder successfully uploaded", TAG, level=Qgis.Info)
        self.delete_local_project_zip_file()
        self.unzip_and_remove_project_dir_on_server(connection)

    def zip_local_project_dir(self):
        try:
            # Copy directory and remove unwanted files
            if os.path.isdir(f'{self.source_project_dir_path}_copy_tmp'):
                shutil.rmtree(f'{self.source_project_dir_path}_copy_tmp')
            os.mkdir(f'{self.source_project_dir_path}_copy_tmp')
            shutil.copytree(self.source_project_dir_path, f'{self.source_project_dir_path}_copy_tmp/'
                                                     f'{self.source_project_dir_name}')
            try:
                for folder_name, subfolders, filenames in os.walk(f'{self.source_project_dir_path}_copy_tmp'):
                    for filename in filenames:
                        file_path = os.path.join(folder_name, filename)
                        if filename.split(".")[-1] in ('gpkg-wal', 'gpkg-shm'):
                            os.remove(file_path)
                try:
                    # Compress tmp copy of project folder
                    shutil.make_archive(self.source_project_dir_path, 'zip', f'{self.source_project_dir_path}_copy_tmp')
                    # Check
                    if os.path.isfile(self.source_project_zip_file_path):
                        QgsMessageLog.logMessage("Zip-project folder successfully created", TAG, level=Qgis.Info)
                    # Remove tmp copy of project folder
                    shutil.rmtree(f'{self.source_project_dir_path}_copy_tmp')
                except Exception as e:
                    show_fail_box_ok("Failed", f"Could not compress copy of project folder. Reason: {e}")
            except Exception as e:
                show_fail_box_ok("Failed", f"Could not remove unwanted files. Reason: {e}")
        except Exception as e:
            show_fail_box_ok("Failed", f"Could not copy project folder. Reason: {e}")

    def delete_local_project_zip_file(self):
        if os.path.isfile(self.source_project_zip_file_path):
            os.remove(self.source_project_zip_file_path)

    def upload_project_zip_file(self, connection) -> bool:
        try:
            connection.put(local=self.source_project_zip_file_path, remote=self.server_projects_dir_path)
            # Check upload success
            if connection.run('test {}'.format(self.server_projects_dir_path + self.source_project_dir_name + ".zip"),
                              warn=True).failed:
                # Upload not successful: Folder does not exist in server
                show_fail_box_ok("Failed", "Project directory could not be uploaded")
                return False
            else:
                # Upload successful: Folder exists  in server
                QgsMessageLog.logMessage("QGIS-Project folder successfully uploaded", TAG, level=Qgis.Info)
                return True
        except Exception as e:
            show_fail_box_ok("Failed", f"Project directory could not be uploaded. Reason: {e}")

    def unzip_and_remove_project_dir_on_server(self, connection) -> None:
        """
        Unzips project folder on the server
        :param source_project_dir_name:
        :param server_qgis_projects_folder_path:
        """
        connection.run(f'cd ..; cd {self.server_projects_dir_path}/; unzip {self.source_project_dir_name}.zip;')
        QgsMessageLog.logMessage("Unzipping files on the server...", TAG, level=Qgis.Info)
        connection.run(f'cd ..; cd /data/qgis-projects/; rm {self.source_project_dir_name}.zip;')