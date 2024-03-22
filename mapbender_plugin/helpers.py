import os
import shutil

from fabric2 import Connection
import paramiko

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from qgis._core import QgsProject, Qgis, QgsMessageLog
from qgis.utils import iface

from mapbender_plugin.settings import SERVER_MB_CD_APPLICATION_PATH
from mapbender_plugin.mapbender import TAG


def get_plugin_dir() -> str:
    """Returns the plugin directory"""
    plugin_dir = os.path.dirname(__file__)
    return plugin_dir


def check_if_config_file_exists(config_path: str) -> bool:
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


def get_project_layers() -> list:
    """ Returns project layers"""
    project = QgsProject.instance()
    project.read()
    layers_names = []
    for layer in project.mapLayers().values():
        layers_names.append(layer.name())
    return layers_names


def check_if_qgis_project(plugin_dir: str) -> bool:
    """
        Checks if plugin is used within a QGIS-Project
        :param plugin_dir:
        :return: bool
        """
    # get and check .qgz project path
    source_project_dir_path = QgsProject.instance().readPath("./")
    source_project_file_path = QgsProject.instance().fileName()
    if source_project_dir_path == "./" or source_project_file_path == "":
        show_fail_box_ok('', "Failed",
                                     "Please use the Mapbender Plugin from a valid QGIS-Project with QGIS-Server configurations")
        return False
    else:
        return True


def get_paths(server_qgis_projects_folder_rel_path: str):
    """
    Check if plugin is used within a QGIS-Project and get the paths if true
    :param server_qgis_projects_folder_rel_path:
    :param plugin_dir:
    :return: paths
    """
    source_project_dir_path = QgsProject.instance().readPath("./")
    source_project_file_path = QgsProject.instance().fileName()
    qgis_project_name = source_project_file_path.split("/")[-1]
    source_project_dir_path = QgsProject.instance().readPath("./")
    paths = {'source_project_dir_path': QgsProject.instance().readPath("./"),
                 'source_project_file_path': QgsProject.instance().fileName(),
                 'qgis_project_name': source_project_file_path.split("/")[-1],
                 'source_project_zip_dir_path': source_project_dir_path + '.zip',
                 'qgis_project_folder_name': source_project_dir_path.split("/")[-1],
                 'qgis_project_folder_parent': os.path.abspath(os.path.join(source_project_dir_path, os.pardir)),
                 'server_project_dir_path': server_qgis_projects_folder_rel_path + source_project_dir_path.split("/")[-1]
                 }
    return (paths)


def zip_local_project_folder(plugin_dir: str, source_project_dir_path: str,
                             source_project_zip_dir_path: str, qgis_project_folder_name: str):
    """
    Copies project directory and removes unwanted files. Zips local project folder
    :param server_qgis_projects_folder_rel_path:
    :param plugin_dir:
    :param source_project_dir_path:
    :param source_project_zip_dir_path:
    :param qgis_project_folder_name:
    :return:
    """
    try:
        # copy directory and remove unwanted files
        if os.path.isdir(f'{source_project_dir_path}_copy_tmp'):
            print("copy already exists... removing it")
            shutil.rmtree(f'{source_project_dir_path}_copy_tmp')
        os.mkdir(f'{source_project_dir_path}_copy_tmp')
        shutil.copytree(source_project_dir_path, f'{source_project_dir_path}_copy_tmp/'
                                                      f'{qgis_project_folder_name}')
        try:
            for folder_name, subfolders, filenames in os.walk(f'{source_project_dir_path}_copy_tmp'):
                for filename in filenames:
                    file_path = os.path.join(folder_name, filename)
                    if filename.split(".")[-1] in ('gpkg-wal', 'gpkg-shm'):
                        os.remove(file_path)
            try:
                # compress tmp copy of project folder
                shutil.make_archive(source_project_dir_path, 'zip', f'{source_project_dir_path}_copy_tmp')
                # check
                if os.path.isfile(source_project_zip_dir_path):
                    print('Zip-project folder successfully created')
                # remove tmp copy of project folder
                shutil.rmtree(f'{source_project_dir_path}_copy_tmp')
                #uploadProjectZipFile(server_qgis_projects_folder_rel_path)

            except Exception as e:
                show_fail_box_ok('', "Failed", f"Could not compress copy of project folder. Reason: {e}")
        except Exception as e:
            show_fail_box_ok('', "Failed", f"Could not remove unwanted files. Reason: {e}")
    except Exception as e:
        show_fail_box_ok('', "Failed", f"Could not copy project folder. Reason: {e}")

def check_if_project_folder_exists_on_server(host: str, username: str, port: str, password: str, plugin_dir: str, source_project_zip_dir_path: str,
                                             server_qgis_projects_folder_rel_path: str, qgis_project_folder_name: str) -> bool:
    """
    Checks if project folder already exists on server
    :param host:
    :param username:
    :param port:
    :param password:
    :param plugin_dir:
    :param source_project_zip_dir_path:
    :param server_qgis_projects_folder_rel_path:
    :param qgis_project_folder_name:
    :return: bool
    """
    iface.messageBar().pushMessage("", "Connecting to server ...", level=Qgis.Info, duration=2)

    sftpConnection = Connection(host=host, user=username, port=port, connect_kwargs={
        "password": password})
    try:
        with sftpConnection as c:
            try:
                # check if project folder already exists on the server
                if c.run('test -d {}'.format(server_qgis_projects_folder_rel_path + qgis_project_folder_name),
                         warn=True).failed:  # without .zip
                    # (if exists, is unzipped), -d option to test if the file exist and is a directory
                    # Folder does not exist yet in server: upload project folder
                    print("Folder does not exist yet in server: upload project folder")
                    return False
                else:
                    print('Folder already exists in server')
                    return True
            except Exception as e:
                show_fail_box_ok('', "Failed",
                                             f"Could not check if project directory exists already on the server. Reason: {e}")
    except Exception as e:
        show_fail_box_ok('', "Failed", f"Could not create connection. Reason: {e}")

def upload_project_zip_file(host: str, username: str, port: str, password: str, plugin_dir: str, source_project_zip_dir_path: str,
                            server_qgis_projects_folder_rel_path: str, qgis_project_folder_name: str) -> bool:
    """
    Uploads project zip file to the server
    :param host:
    :param username:
    :param port:
    :param password:
    :param plugin_dir:
    :param source_project_zip_dir_path:
    :param server_qgis_projects_folder_rel_path:
    :param qgis_project_folder_name:
    :return: bool (True = success, False = failed)
    """

    sftpConnection = Connection(host=host, user=username, port=port, connect_kwargs={
        "password": password})
    try:
        with sftpConnection as c:
            try:
                c.put(local=source_project_zip_dir_path, remote= server_qgis_projects_folder_rel_path)
                # check upload success
                if c.run('test {}'.format(server_qgis_projects_folder_rel_path + qgis_project_folder_name + ".zip"),
                         warn=True).failed:  # with .zip (if exists, is zipped), wihout -d option (to test if
                    # the file exist, not a directory)
                    # Upload not successful:: Folder does not exist in server
                    show_fail_box_ok('', "Failed", "Project directory could not be uploaded")
                    return False
                else:
                    # Upload was successful: Folder exists now in server
                    iface.messageBar().pushMessage("", "QGIS-Project folder successfully uploaded", level=Qgis.Info, duration=2)
                    return True
                        #self.unzipProjectFolderInServer(server_qgis_projects_folder_rel_path)
            except Exception as e:
                show_fail_box_ok('', "Failed", f"Project directory could not be uploaded. Reason: {e}")
    except Exception as e:
        show_fail_box_ok('', "Failed", f"Could not create connection. Reason: {e}")


def remove_project_folder_from_server(host: str, username: str, port: str, password: str, plugin_dir: str,
                                      server_qgis_projects_folder_rel_path: str, qgis_project_folder_name: str):
    """
    Removes a project folder from server
    :param host:
    :param username:
    :param port:
    :param password:
    :param plugin_dir:
    :param server_qgis_projects_folder_rel_path:
    :param qgis_project_folder_name:
    :return: (True = success, False = failed)
    """
    try:
        # login
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #ssh_client.connect(hostname=host, username=username, port=port, password=password) # fails because of "port"
        ssh_client.connect(hostname=host, username=username, password=password)
        try:
            # remove folder from server
            stdin, stdout, stderr = ssh_client.exec_command(
                f'cd ..; cd {server_qgis_projects_folder_rel_path}; rm -r {qgis_project_folder_name};')
            #check
            out = stdout.readlines()
            if os.path.isdir(f'{server_qgis_projects_folder_rel_path}{qgis_project_folder_name}'):
                show_fail_box_ok('', "Failed", f"Could not remove existing project folder from server.")
                return False
            else:
                print('Existing project folder successfully removed from server')
                return True

        except Exception as e:
            show_fail_box_ok('', "Failed", f"Could not remove existing project folder from server. Reason: {e}")
    except Exception as e:
        show_fail_box_ok('', "Failed", f"Could not connect to server. Reason: {e}")

def unzip_project_folder_on_server(host: str, username: str, port: str, password: str, qgis_project_folder_name: str,
                                   server_qgis_projects_folder_rel_path: str) -> bool:
    """
    Unzips project folder on the server
    :param host:
    :param username:
    :param port:
    :param password:
    :param qgis_project_folder_name:
    :param server_qgis_projects_folder_rel_path:
    :return: True if success
    """
    try:
        # login
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #ssh_client.connect(hostname=host, username=username, port=port, password=password) # fails because of "port"
        ssh_client.connect(hostname=host, username=username, password=password)
        try:
            # unzip
            stdin, stdout, stderr = ssh_client.exec_command(f'cd ..; '
                                                            f'cd {server_qgis_projects_folder_rel_path}/;'
                                                            f'unzip {qgis_project_folder_name}.zip;')
            print('Unzipping files on the server...')
            print(stdout.read().decode())
            # access files
            stdin, stdout, stderr = ssh_client.exec_command(f'cd {server_qgis_projects_folder_rel_path}/{qgis_project_folder_name}/; ls')
            print('Accessing files on the server...')
            print(stdout.read().decode())
            try:
                # remove zip file from server
                stdin, stdout, stderr = ssh_client.exec_command(
                    f'cd ..; cd /data/qgis-projects/; rm {qgis_project_folder_name}.zip;')
                return True
            except Exception as e:
                print(f"Could not remove zip file from server. Reason: {e}")
        except Exception as e:
            print(f"Could not unzip file. Reason: {e}")
    except Exception as e:
        print(f"Could not create connection. Reason: {e}")


def check_uploaded_files(host: str, username: str, port: str, password: str, plugin_dir, qgis_project_folder_name,
                         source_project_dir_path: str, server_project_dir_path: str):
    """
    Checks uploaded files to the server
    :param host:
    :param username:
    :param port:
    :param password:
    :param source_project_dir_path:
    :param server_project_dir_path:
    :return:
    """
    pass
#     sftpConnection = Connection(host=host, user=username, port=port, connect_kwargs={
#         "password": password})
#     # check upload:
#     files_uploaded = []
#     files_not_uploaded = []
#     try:
#         with sftpConnection as c:
#             try:
#                 sftpClient = c.sftp()
#                 # this only checks ls in self.source_project_dir_path
#                 # for filename in os.listdir(self.source_project_dir_path):
#                 #     if filename.split(".")[-1] not in ('gpkg-wal', 'gpkg-shm') and filename in sftpClient.listdir(
#                 #             self.server_project_dir_path):
#                 #         files_uploaded.append(filename)
#                 #     elif filename.split(".")[-1] not in ('gpkg-wal', 'gpkg-shm') and filename not in sftpClient.listdir(
#                 #             self.server_project_dir_path):
#                 #         files_not_uploaded.append(filename)
#
#                 # use os.walk instead for listing all files in source file
#                 source_tree = []
#                 for root, _, files in os.walk(source_project_dir_path):
#                     source_tree.append(root)
#                     for f in files:
#                         source_tree.append(os.path.join(root, f))
#                 for path in source_tree:
#                     filename = path.split("/")[-1]
#                     file_extension = filename.split(".")[-1]
#                     if os.path.isfile(path):
#                         if file_extension not in ('gpkg-wal', 'gpkg-shm') and filename in sftpClient.listdir_attr(
#                                 server_project_dir_path):
#                             files_uploaded.append(filename)
#                         elif file_extension not in ('gpkg-wal', 'gpkg-shm') and filename not in sftpClient.listdir(
#                                 server_project_dir_path):
#                             files_not_uploaded.append(filename)
#
#                 # succes:
#                 successBox = QMessageBox()
#                 successBox.setIconPixmap(QPixmap(plugin_dir + '/resources/icons/mIconSuccess.svg'))
#                 successBox.setWindowTitle("Success")
#                 if len(files_not_uploaded) == 0:
#                     successBox.setText(
#                         "Project directory '" + qgis_project_folder_name + "' successfully uploaded. \nFiles uploaded: " + ', '.join(
#                             files_uploaded))
#                 else:
#                     successBox.setText(
#                         "Project directory " + qgis_project_folder_name + " successfully uploaded. \nFiles uploaded: " + ', '.join(
#                             files_uploaded)
#                         + ".\nFiles not uploaded: " + ', '.join(files_not_uploaded))
#
#                 successBox.setStandardButtons(QMessageBox.Ok)
#                 result = successBox.exec_()
#                 if result == QMessageBox.Ok:
#                     self.close()
#             except Exception as e:
#                 print(f"Could not.... Reason: {e}")
#     except Exception as e:
#         print(f"Could not connect to server. Reason: {e}")


def get_get_capabilities_url(host: str, plugin_dir, server_project_dir_path, qgis_project_name) -> str:
    """
    Returns the getCapabilities Url for the created WMS
    :return:
    """
    wms_getcapabilities_url = (
            "http://" + host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
            + server_project_dir_path + "/" + qgis_project_name)
    # 1) test in mapbender console (Step 0)
    # if succes:
    successBox = QMessageBox()
    successBox.setIconPixmap(QPixmap(plugin_dir + '/resources/icons/mIconSuccess.svg'))
    successBox.setWindowTitle("Success")
    successBox.setText("WMS succesfully created:\n" + wms_getcapabilities_url)
    successBox.setStandardButtons(QMessageBox.Ok)
    successBox.exec_()
    print(wms_getcapabilities_url)
    return wms_getcapabilities_url

def create_fail_box(plugin_dir, title, text):
    failBox = QMessageBox()
    failBox.setIconPixmap(QPixmap(plugin_dir + '/resources/icons/mIconWarning.svg'))
    failBox.setWindowTitle(title)
    failBox.setText(text)
    return failBox

def show_fail_box_ok(plugin_dir, title, text):
    failBox = create_fail_box(plugin_dir, title, text)
    failBox.setStandardButtons(QMessageBox.Ok)
    failBox.exec_()

def show_fail_box_yes_no(plugin_dir, title, text):
    failBox = create_fail_box(plugin_dir, title, text)
    failBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    failBox.exec_()

def show_succes_box_ok(plugin_dir, title, text):
    successBox = QMessageBox()
    successBox.setIconPixmap(QPixmap(plugin_dir + '/resources/icons/mIconSuccess.svg'))
    successBox.setWindowTitle(title)
    successBox.setText(text)
    successBox.setStandardButtons(QMessageBox.Ok)
    successBox.exec_()


