import os
from dataclasses import dataclass

from qgis._core import QgsProject


@dataclass
class Paths:
    source_project_dir_path: str
    source_project_dir_name: str
    source_project_file_path: str
    source_project_file_name: str
    source_project_zip_dir_path: str
    source_project_parent_dir_path: str
    server_project_dir_path: str

    @staticmethod
    def get_paths(server_projects_dir_path: str):
        source_project_dir_path = QgsProject.instance().absolutePath()
        source_project_dir_name = os.path.basename(source_project_dir_path)
        source_project_file_path = QgsProject.instance().fileName()
        source_project_file_name = os.path.basename(source_project_file_path)
        source_project_zip_dir_path = source_project_dir_path + '.zip'
        source_project_parent_dir_path = os.path.abspath(os.path.join(source_project_dir_path, os.pardir))
        server_project_dir_path = server_projects_dir_path + source_project_dir_name
