import os
from dataclasses import dataclass

from qgis.core import QgsProject


@dataclass
class Paths:
    source_project_dir_path: str
    source_project_dir_name: str
    source_project_file_name: str
    source_project_zip_file_path: str
    server_project_parent_dir_path: str
    server_project_dir_path: str

    @staticmethod
    def get_paths(server_project_parent_dir_path: str):
        source_project_dir_path = QgsProject.instance().absolutePath()
        source_project_dir_name = os.path.basename(source_project_dir_path)
        source_project_file_name = os.path.basename(QgsProject.instance().fileName())
        source_project_zip_file_path = source_project_dir_path + '.zip'
        server_project_dir_path = server_project_parent_dir_path + source_project_dir_name
        return Paths(source_project_dir_path, source_project_dir_name, source_project_file_name,
                     source_project_zip_file_path, server_project_parent_dir_path, server_project_dir_path)
