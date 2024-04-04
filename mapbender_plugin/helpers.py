import os
import shutil

from PyQt5.QtCore import Qt
from decorator import contextmanager
from fabric2 import Connection
import paramiko

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from qgis._core import QgsApplication, QgsProject, QgsSettings, QgsMessageLog, Qgis
from qgis.utils import iface

from mapbender_plugin.settings import TAG


def get_plugin_dir() -> str:
    """Returns the plugin directory"""
    plugin_dir = os.path.dirname(__file__)
    return plugin_dir


def get_project_layers() -> list:
    """ Returns project layers
    :return: layers_names
    """
    project = QgsProject.instance()
    project.read()
    layers_names = []
    for layer in project.mapLayers().values():
        layers_names.append(layer.name())
    return layers_names


def check_if_qgis_project() -> bool:
    """
        Checks if plugin is used within a QGIS-Project
        :return: bool
        """
    # Get and check .qgz project path
    source_project_dir_path = QgsProject.instance().readPath("./")
    source_project_file_path = QgsProject.instance().fileName()
    if source_project_dir_path == "./" or source_project_file_path == "":
        show_fail_box_ok('Failed',
                                     "Please use the Mapbender Plugin from a saved QGIS-Project")
        return False
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
        # Copy directory and remove unwanted files
        if os.path.isdir(f'{source_project_dir_path}_copy_tmp'):
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
                # Compress tmp copy of project folder
                shutil.make_archive(source_project_dir_path, 'zip', f'{source_project_dir_path}_copy_tmp')
                # Check
                if os.path.isfile(source_project_zip_dir_path):
                    QgsMessageLog.logMessage("Zip-project folder successfully created", TAG, level=Qgis.Info)
                # remove tmp copy of project folder
                shutil.rmtree(f'{source_project_dir_path}_copy_tmp')
                #uploadProjectZipFile(server_qgis_projects_folder_rel_path)

            except Exception as e:
                show_fail_box_ok("Failed", f"Could not compress copy of project folder. Reason: {e}")
        except Exception as e:
            show_fail_box_ok("Failed", f"Could not remove unwanted files. Reason: {e}")
    except Exception as e:
        show_fail_box_ok("Failed", f"Could not copy project folder. Reason: {e}")


def delete_local_project_zip_file(source_project_zip_dir_path):
    if os.path.isfile(source_project_zip_dir_path):
        os.remove(source_project_zip_dir_path)
    else:
        return

def open_connection(host: str, username: str, port: str, password: str):
    sftpConnection = Connection(host=host, user=username, port=port, connect_kwargs={
        "password": password})
    with sftpConnection as c:
        try:
            c.open()
            QgsMessageLog.logMessage("Connection to server opened", TAG, level=Qgis.Info)
            return c
        except OSError as e:
            QgsMessageLog.logMessage("Connection to server failed", TAG, level=Qgis.Warning)
            show_fail_box_ok("Failed", f"Could not create connection. Reason: {e}")
            return

def check_if_project_folder_exists_on_server_2(c,plugin_dir: str, source_project_zip_dir_path: str,
                                             server_qgis_projects_folder_rel_path: str, qgis_project_folder_name: str) -> bool:
    """
    Checks if project folder already exists on server
    :param plugin_dir:
    :param source_project_zip_dir_path:
    :param server_qgis_projects_folder_rel_path:
    :param qgis_project_folder_name:
    :return: bool
    """

    try:
        # Check if project folder already exists on the server
        if c.run('test -d {}'.format(server_qgis_projects_folder_rel_path + qgis_project_folder_name),
                 warn=True).failed:  # without .zip
            # If it exists, is unzipped, -d option to test if the file exist and is a directory
            # Folder does not exist yet in server: upload project folder
            print('c run successfully')
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

    sftpConnection = Connection(host=host, user=username, port=port, connect_kwargs={
        "password": password})
    with sftpConnection as c:
        try:
            # Check if project folder already exists on the server
            if c.run('test -d {}'.format(server_qgis_projects_folder_rel_path + qgis_project_folder_name),
                     warn=True).failed:  # without .zip
                # If it exists, is unzipped, -d option to test if the file exist and is a directory
                # Folder does not exist yet in server: upload project folder
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
                # Check upload success
                if c.run('test {}'.format(server_qgis_projects_folder_rel_path + qgis_project_folder_name + ".zip"),
                         warn=True).failed:  # with .zip (if exists, is zipped), wihout -d option (to test if
                    # The file exist, not a directory
                    # Upload not successful:: Folder does not exist in server
                    show_fail_box_ok("Failed", "Project directory could not be uploaded")
                    return False
                else:
                    # Upload was successful: Folder exists now in server
                    #iface.messageBar().pushMessage("", "QGIS-Project folder successfully uploaded", level=Qgis.Info, duration=2)
                    return True
                        #self.unzipProjectFolderInServer(server_qgis_projects_folder_rel_path)
            except Exception as e:
                show_fail_box_ok("Failed", f"Project directory could not be uploaded. Reason: {e}")
    except Exception as e:
        show_fail_box_ok("Failed", f"Could not create connection. Reason: {e}")

def remove_project_folder_from_server_2(c, plugin_dir: str,
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
        c.run(
            f'cd ..; cd {server_qgis_projects_folder_rel_path}; rm -r {qgis_project_folder_name};')
        # Check
        if os.path.isdir(f'{server_qgis_projects_folder_rel_path}{qgis_project_folder_name}'):
            show_fail_box_ok("Failed", f"Could not remove existing project folder from server.")
            return False
        else:
            QgsMessageLog.logMessage("Existing project folder successfully removed from server", TAG, level=Qgis.Info)
            return True

    except Exception as e:
        show_fail_box_ok("Failed", f"Could not remove existing project folder from server. Reason: {e}")


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
        # Login
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #ssh_client.connect(hostname=host, username=username, port=port, password=password) # fails because of "port"
        ssh_client.connect(hostname=host, username=username, password=password)
        try:
            # Remove folder from server
            stdin, stdout, stderr = ssh_client.exec_command(
                f'cd ..; cd {server_qgis_projects_folder_rel_path}; rm -r {qgis_project_folder_name};')
            # Check
            out = stdout.readlines()
            if os.path.isdir(f'{server_qgis_projects_folder_rel_path}{qgis_project_folder_name}'):
                show_fail_box_ok("Failed", f"Could not remove existing project folder from server.")
                return False
            else:
                QgsMessageLog.logMessage("Existing project folder successfully removed from server", TAG, level=Qgis.Info)
                return True

        except Exception as e:
            show_fail_box_ok("Failed", f"Could not remove existing project folder from server. Reason: {e}")
    except Exception as e:
        show_fail_box_ok("Failed", f"Could not connect to server. Reason: {e}")


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
        # Login
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #ssh_client.connect(hostname=host, username=username, port=port, password=password) # fails because of "port"
        ssh_client.connect(hostname=host, username=username, password=password)
        try:
            # Unzip
            stdin, stdout, stderr = ssh_client.exec_command(f'cd ..; '
                                                            f'cd {server_qgis_projects_folder_rel_path}/;'
                                                            f'unzip {qgis_project_folder_name}.zip;')
            QgsMessageLog.logMessage("Unzipping files on the server...", TAG, level=Qgis.Info)

            # List files with: stdout.read().decode())
            # Access files
            stdin, stdout, stderr = ssh_client.exec_command(f'cd {server_qgis_projects_folder_rel_path}/{qgis_project_folder_name}/; ls')
            try:
                # Remove zip file from server
                stdin, stdout, stderr = ssh_client.exec_command(
                    f'cd ..; cd /data/qgis-projects/; rm {qgis_project_folder_name}.zip;')
                return True
            except Exception as e:
                QgsMessageLog.logMessage(f"Could not remove zip file from server. Reason: {e}", TAG, level=Qgis.Warning)
        except Exception as e:
            QgsMessageLog.logMessage(f"Could not unzip file. Reason: {e}", TAG, level=Qgis.Warning)
    except Exception as e:
        QgsMessageLog.logMessage(f"Could not create connection. Reason: {e}", TAG, level=Qgis.Warning)


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
    # If success:
    successBox = QMessageBox()
    successBox.setIconPixmap(QPixmap(plugin_dir + '/resources/icons/mIconSuccess.svg'))
    successBox.setWindowTitle("Success")
    successBox.setText("WMS succesfully created:\n" + wms_getcapabilities_url)
    successBox.setStandardButtons(QMessageBox.Ok)
    successBox.exec_()
    return wms_getcapabilities_url

def create_fail_box(title, text):
    failBox = QMessageBox()
    failBox.setIconPixmap(QPixmap(":/images/themes/default/mIconWarning.svg"))
    failBox.setWindowTitle(title)
    failBox.setText(text)
    return failBox

def show_fail_box_ok(title, text):
    failBox = create_fail_box(title, text)
    failBox.setStandardButtons(QMessageBox.Ok)
    return failBox.exec_()

def show_fail_box_yes_no(title, text):
    failBox = create_fail_box(title, text)
    failBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    return failBox.exec_()

def show_succes_box_ok(title, text):
    plugin_dir = get_plugin_dir()
    successBox = QMessageBox()
    successBox.setIconPixmap(QPixmap(plugin_dir + '/resources/icons/mIconSuccess.svg'))
    successBox.setWindowTitle(title)
    successBox.setText(text)
    successBox.setStandardButtons(QMessageBox.Ok)
    return successBox.exec_()


def show_question_box(text):
    questionBox = QMessageBox()
    questionBox.setIcon(QMessageBox.Question)
    questionBox.setText(text)
    questionBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    return questionBox.exec_()

def get_plugin_dir():
    file = os.path.dirname(__file__)
    plugin_dir = os.path.dirname(file) + '/mapbender_plugin'
    return plugin_dir

def list_qgs_settings_child_groups(key):
    s = QgsSettings()
    s.beginGroup(key)
    subkeys = s.childGroups()
    s.endGroup
    return subkeys

def show_new_info_message_bar(text, previous_message_bars):
    #previous_message_bars = delete_previous_messages(previous_message_bars) # FEHLER
    message_bar = iface.messageBar().createMessage(text)
    iface.messageBar().pushWidget(message_bar, duration=3)
    previous_message_bars.append(message_bar)
    return previous_message_bars

@contextmanager
def waitCursor():
    try:
        QgsApplication.setOverrideCursor(Qt.WaitCursor)
        yield
    except Exception as ex:
        raise ex
    finally:
        QgsApplication.restoreOverrideCursor()


def delete_previous_messages(previous_message_bars):
    for message_bar in previous_message_bars:
        iface.messageBar().popWidget(message_bar)
    previous_message_bars = []
    return previous_message_bars


def validate_no_spaces(*variables):
    for var in variables:
        if " " in var:
            return False
    return True


def update_mb_slug_in_settings(mb_slug, is_mb_slug):
    s = QgsSettings()
    if s.contains("mapbender-plugin/mb_templates"):
        s.beginGroup('mapbender-plugin/')
        mb_slugs = s.value('mb_templates')
        s.endGroup()
        if isinstance(mb_slugs, str):
            mb_slugs_list = mb_slugs.split(", ")
        else:
            mb_slugs_list = mb_slugs

        if is_mb_slug:
            if mb_slug in mb_slugs_list:
                return
            else:
                mb_slugs_list.append(mb_slug)
                updated_mb_slugs = ", ".join(mb_slugs_list)
                s.setValue('mapbender-plugin/mb_templates', updated_mb_slugs)
        else:
            if mb_slug in mb_slugs_list:
                mb_slugs_list.remove(mb_slug)
                updated_mb_slugs = ", ".join(mb_slugs_list)
                s.setValue('mapbender-plugin/mb_templates', updated_mb_slugs)
            else:
                return
    else:
        if is_mb_slug:
            s.setValue('mapbender-plugin/mb_templates', mb_slug)
        else:
            return






