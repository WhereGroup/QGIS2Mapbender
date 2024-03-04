import os

import paramiko
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from qgis._core import QgsProject


def getPluginDir() -> str:
    """Returns the plugin directory"""
    plugin_dir = os.path.dirname(__file__)
    return plugin_dir

def checkIfConfigFileExists(config_path: str) -> bool:
    """Checks if configuration file exists in Plugin folder and creates it if
    it did not exist

        Args:
            config_path (str): the path to the config file
            """

    if not os.path.isfile(config_path):
        try:
            # create the config file if not existing
            open(config_path, 'a').close()
            return True
        except OSError as e:
            print(f"Error {e}. Could not create config file. Please contact")
            return False
    else:
        return True

def getProjectLayers() -> list:
    """ Returns project layers"""
    project = QgsProject.instance()
    project.read()
    layers_names = []
    for layer in project.mapLayers().values():
        layers_names.append(layer.name())
    return layers_names

def checkQgisProjectAndGetPaths(server_qgis_projects_folder_rel_path, plugin_dir):
    # get and check .qgz project path
    source_project_dir_path = QgsProject.instance().readPath("./")
    source_project_file_path = QgsProject.instance().fileName()
    qgis_project_name = source_project_file_path.split("/")[-1]
    if source_project_dir_path == "./" or source_project_file_path == "":
        failBox = QMessageBox()
        failBox.setIconPixmap(QPixmap(plugin_dir + '/resources/icons/mIconWarning.svg'))
        failBox.setWindowTitle("Failed")
        failBox.setText("Please use the Mapbender Plugin from a valid QGIS-Project with QGIS-Server configurations")
        failBox.setStandardButtons(QMessageBox.Ok)
        failBox.exec_()
    else:
        paths = {'source_project_dir_path': QgsProject.instance().readPath("./"),
                 'source_project_file_path': QgsProject.instance().fileName(),
                 'qgis_project_name': source_project_file_path.split("/")[-1],
                 'source_project_zip_dir_path': source_project_dir_path + '.zip',
                 'qgis_project_folder_name': source_project_dir_path.split("/")[-1],
                 'qgis_project_folder_parent': os.path.abspath(os.path.join(source_project_dir_path, os.pardir)),
                 'server_project_dir_path': server_qgis_projects_folder_rel_path + source_project_dir_path.split("/")[-1]
                 }
        return (paths)