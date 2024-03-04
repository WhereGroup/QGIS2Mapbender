import os
import shutil

from fabric2 import Connection
import paramiko

from PyQt5 import uic
import configparser

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMessageBox

from qgis._core import Qgis, QgsProject

from mapbender_plugin.dialogs.add_server_section_dialog import AddServerSectionDialog
from mapbender_plugin.dialogs.edit_server_section_dialog import EditServerSectionDialog
from mapbender_plugin.dialogs.remove_server_section_dialog import RemoveServerSectionDialog
from mapbender_plugin.helpers import checkIfConfigFileExists, getPluginDir, getProjectLayers, \
    checkQgisProjectAndGetPaths

from mapbender_plugin.settings import (
    SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
    TEMPLATE_APPLICATION_NAME, CONFIG_FILE_NAME,
)

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialogs/ui/main_dialog.ui'))

class MainDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.server_qgis_projects_folder_rel_path = SERVER_QGIS_PROJECTS_FOLDER_REL_PATH
        templateApplicationName = TEMPLATE_APPLICATION_NAME

        self.plugin_dir = getPluginDir()
        self.config_path = self.plugin_dir + "/" + CONFIG_FILE_NAME
        # check if config file exists
        if not checkIfConfigFileExists(self.config_path):
            self.iface.messageBar().pushMessage("No config file is available. Failed creating a new"
                                                "config file", "Please contact", level=Qgis.Critical)

        # tabs
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.currentChanged.connect(self.updateSectionComboBox)

        # tab1
        self.updateSectionComboBox()
        self.uploadButton.clicked.connect(self.validateConfigParams)
        self.tmpMapbenderConsoleButton.clicked.connect(self.tempTestMapbenderConsole)

        # tab2
        self.addServerConfigButton.clicked.connect(self.openDialogAddNewConfigSection)
        self.editServerConfigButton.clicked.connect(self.openDialogEditConfigSection)
        self.removeServerConfigButton.clicked.connect(self.openDialogRemoveConfigSection)
        self.buttonBoxTab1.rejected.connect(self.reject)
        self.buttonBoxTab2.rejected.connect(self.reject)


    def updateSectionComboBox(self) -> None:
        """ Updates the server configuration sections dropdown menu """
        # parse config file
        try:
            # As the documentation makes clear, any number of filenames can be passed to the read method,
            # and it will silently ignore the ones that cannot be opened.
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)
        except configparser.Error as error:
            self.iface.messageBar().pushMessage("Error: Could not parse config file ", error, level=Qgis.Critical)

        # read config sections
        config_sections = self.config.sections()
        if len(config_sections) == 0:
            self.warningAddServiceText.show()
            self.sectionComboBoxLabel.hide()
            self.sectionComboBox.hide()
            self.uploadButton.hide()
            self.editServerConfigButton.hide()
            self.editServiceConfigLabel.hide()
            self.removeServerConfigButton.hide()
            self.removeServiceConfigLabel.hide()
            self.exportServiceConfigFileButton.hide()
            self.exportServiceConfigFileLabel.hide()
        else:
            # sections-combobox
            self.warningAddServiceText.hide()
            self.sectionComboBox.clear()
            self.sectionComboBox.addItems(config_sections)
            self.sectionComboBoxLabel.show()
            self.sectionComboBox.show()
            self.uploadButton.show()
            # config management
            self.editServerConfigButton.show()
            self.editServiceConfigLabel.show()
            self.removeServerConfigButton.show()
            self.removeServiceConfigLabel.show()
            self.exportServiceConfigFileButton.show()
            self.exportServiceConfigFileLabel.show()

    def validateConfigParams(self):
        selected_section = self.sectionComboBox.currentText()
        self.host = self.config.get(selected_section, 'url')
        self.port = self.config.get(selected_section, 'port')
        self.username = self.config.get(selected_section, 'username')
        self.password = self.config.get(selected_section, 'password')
        if self.host == '' or len(self.host)<5:
            failBox = QMessageBox()
            failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
            failBox.setWindowTitle("Failed")
            failBox.setText("Server URL is not valid. Please select a valid section or edit the selected section under"
                            " 'Server configuration management'")
            failBox.setStandardButtons(QMessageBox.Ok)
            failBox.exec_()
        else:
            source_project_zip_dir_paths = checkQgisProjectAndGetPaths(SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                                                      self.plugin_dir)
            source_project_dir_path = source_project_zip_dir_paths.get('source_project_dir_path')

            # getProjectLayers
            # zipProjectFolder

    # def checkQgisProjectAndGetPaths(self, server_qgis_projects_folder_rel_path):
    #     # get and check .qgz project path
    #     self.source_project_dir_path = QgsProject.instance().readPath("./")
    #     self.source_project_file_path = QgsProject.instance().fileName()
    #     self.qgis_project_name = self.source_project_file_path.split("/")[-1]
    #     if self.source_project_dir_path == "./" or self.source_project_file_path == "":
    #         failBox = QMessageBox()
    #         failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
    #         failBox.setWindowTitle("Failed")
    #         failBox.setText("Please use the Mapbender Plugin from a valid QGIS-Project with QGIS-Server configurations")
    #         failBox.setStandardButtons(QMessageBox.Ok)
    #         failBox.exec_()
    #     else:
    #         # get project layers
    #         #source_project_layers = getProjectLayers()
    #         #print(source_project_layers)
    #
    #         # project folder name (with .qgz and data) as in local
    #         self.source_project_zip_dir_path = self.source_project_dir_path + '.zip'
    #         self.qgis_project_folder_name = self.source_project_dir_path.split("/")[-1]
    #         self.qgis_project_folder_parent = os.path.abspath(os.path.join(self.source_project_dir_path, os.pardir))
    #         self.server_project_dir_path = server_qgis_projects_folder_rel_path + self.qgis_project_folder_name
    #
    #         self.zipProjectFolder(server_qgis_projects_folder_rel_path)
    def zipProjectFolder(self, server_qgis_projects_folder_rel_path):
        try:
            # copy directory and remove unwanted files
            if os.path.isdir(f'{self.source_project_dir_path}_copy_tmp'):
                print("copy already exists... removing it")
                shutil.rmtree(f'{self.source_project_dir_path}_copy_tmp')
            os.mkdir(f'{self.source_project_dir_path}_copy_tmp')
            shutil.copytree(self.source_project_dir_path, f'{self.source_project_dir_path}_copy_tmp/'
                                                          f'{self.qgis_project_folder_name}')
            try:
                for folder_name, subfolders, filenames in os.walk(f'{self.source_project_dir_path}_copy_tmp'):
                    for filename in filenames:
                        file_path = os.path.join(folder_name, filename)
                        if filename.split(".")[-1] in ('gpkg-wal', 'gpkg-shm'):
                            os.remove(file_path)
                try:
                    # compress tmp copy of project folder
                    shutil.make_archive(self.source_project_dir_path, 'zip', f'{self.source_project_dir_path}_copy_tmp')
                    # check
                    if os.path.isfile(self.source_project_zip_dir_path):
                        print('Zip-project folder successfully created')
                    # remove tmp copy of project folder
                    shutil.rmtree(f'{self.source_project_dir_path}_copy_tmp')
                    self.uploadProjectZipFile(server_qgis_projects_folder_rel_path)

                except Exception as e:
                    failBox = QMessageBox()
                    failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                    failBox.setWindowTitle("Failed")
                    failBox.setText(f"Could not compress copy of project folder. Reason: {e}")
                    failBox.setStandardButtons(QMessageBox.Ok)
                    failBox.exec_()
            except Exception as e:
                failBox = QMessageBox()
                failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                failBox.setWindowTitle("Failed")
                failBox.setText(f"Could not remove unwanted files. Reason: {e}")
                failBox.setStandardButtons(QMessageBox.Ok)
                failBox.exec_()
        except Exception as e:
            failBox = QMessageBox()
            failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
            failBox.setWindowTitle("Failed")
            failBox.setText(f"Could not copy project folder. Reason: {e}")
            failBox.setStandardButtons(QMessageBox.Ok)
            failBox.exec_()

    def uploadProjectZipFile(self, server_qgis_projects_folder_rel_path):
        # Alternative 1 - OSError: Failure
        # login
        #ssh_client = paramiko.SSHClient()
        #ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #ssh_client.connect(hostname=self.host, username=self.username, password=self.password)

        # upload
        #ftp_client = ssh_client.open_sftp()
        #ftp_client.put('/home/cviesca/Projekte/Plugin_QGIS-QGIS-Server_Mapbender/source_ordner.zip', '/data/qgis-projects')
        #ftp_client.close()

        # unzip
        #stdin, stdout, stderr = ssh_client.exec_command('unzip source_ordner.zip')
        #print(stdout.read().decode())

        # access files
        #stdin, stdout, stderr = ssh_client.exec_command('ls')
        #print(stdout.read().decode())

        # Alternative 2
        sftpConnection = Connection(host=self.host, user=self.username, port=self.port, connect_kwargs={
            "password": self.password})
        try:
            with sftpConnection as c:
                try:
                    # check if project folder already exists
                    if c.run('test -d {}'.format(server_qgis_projects_folder_rel_path + self.qgis_project_folder_name), warn=True).failed: # without .zip
                        # (if exists, is unzipped), -d option to test if the file exist and is a directory
                        # Folder doesn't exist yet in server: upload project folder
                        c.put(local=self.source_project_zip_dir_path,
                              remote= server_qgis_projects_folder_rel_path)
                        # check upload success
                        if c.run('test {}'.format(server_qgis_projects_folder_rel_path + self.qgis_project_folder_name + ".zip"),
                                 warn=True).failed:  # with .zip (if exists, is zipped), wihout -d option (to test if
                            # the file exist, not a directory)
                            # Upload not successful:: Folder does not exist in server
                            failBox = QMessageBox()
                            failBox.setIconPixmap(
                                QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                            failBox.setWindowTitle("Failed")
                            failBox.setText("Project directory could not be uploaded")
                            failBox.setStandardButtons(QMessageBox.Ok)
                            failBox.exec_()
                        else:
                            # Upload was successful: Folder exists now in server
                            print('zip folder successfully uploaded')
                            self.unzipProjectFolderInServer(server_qgis_projects_folder_rel_path)
                    else:
                        # Folder already exists in server
                        failBox = QMessageBox()
                        failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                        failBox.setWindowTitle("Failed")
                        failBox.setText(
                            "Project directory could not be uploaded: Project directory already exists. Do you want to "
                            "overwrite the existing project directory '" + self.qgis_project_folder_name + "'?")
                        failBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        result = failBox.exec_()
                        if result == QMessageBox.Yes:
                            self.close()
                            self.overwriteProject(server_qgis_projects_folder_rel_path)
                except Exception as e:
                    failBox = QMessageBox()
                    failBox.setIconPixmap(
                        QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                    failBox.setWindowTitle("Failed")
                    failBox.setText(f"Project directory could not be uploaded. Reason: {e}")
                    failBox.setStandardButtons(QMessageBox.Ok)
                    failBox.exec_()
        except Exception as e:
            failBox = QMessageBox()
            failBox.setIconPixmap(
                QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
            failBox.setWindowTitle("Failed")
            failBox.setText(f"Could not create connection. Reason: {e}")
            failBox.setStandardButtons(QMessageBox.Ok)
            failBox.exec_()

    def overwriteProject(self, server_qgis_projects_folder_rel_path):
        print('overwrite project')
        try:
            # login
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=self.host, username=self.username, password=self.password)
            try:
                # remove folder from server
                stdin, stdout, stderr = ssh_client.exec_command(
                    f'cd ..; cd {server_qgis_projects_folder_rel_path}; rm -r {self.qgis_project_folder_name};')
                #check
                out = stdout.readlines()
                if os.path.isdir(f'{server_qgis_projects_folder_rel_path}{self.qgis_project_folder_name}'):
                    failBox = QMessageBox()
                    failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                    failBox.setWindowTitle("Failed")
                    failBox.setText(f"Could not remove existing project folder from server.")
                    failBox.setStandardButtons(QMessageBox.Ok)
                    failBox.exec_()
                else:
                    try:
                        self.uploadProjectZipFile(server_qgis_projects_folder_rel_path)
                    except Exception as e:
                        failBox = QMessageBox()
                        failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                        failBox.setWindowTitle("Failed")
                        failBox.setText(f"Could not overwrite project folder. Reason: {e}")
                        failBox.setStandardButtons(QMessageBox.Ok)
                        failBox.exec_()

            except Exception as e:
                failBox = QMessageBox()
                failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                failBox.setWindowTitle("Failed")
                failBox.setText(f"Could not remove existing project folder from server. Reason: {e}")
                failBox.setStandardButtons(QMessageBox.Ok)
                failBox.exec_()

        except Exception as e:
            failBox = QMessageBox()
            failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
            failBox.setWindowTitle("Failed")
            failBox.setText(f"Could not overwrite project folder. Reason: {e}")
            failBox.setStandardButtons(QMessageBox.Ok)
            failBox.exec_()

    def unzipProjectFolderInServer(self, server_qgis_projects_folder_rel_path):
        try:
            # login
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=self.host, username=self.username, password=self.password)
            try:
                # unzip
                stdin, stdout, stderr = ssh_client.exec_command(f'cd ..; '
                                                                f'cd {server_qgis_projects_folder_rel_path}/;'
                                                                f'unzip {self.qgis_project_folder_name}.zip;')
                print(stdout.read().decode())

                # access files
                stdin, stdout, stderr = ssh_client.exec_command(f'cd {server_qgis_projects_folder_rel_path}/{self.qgis_project_folder_name}/; ls')
                print(stdout.read().decode())

                try:
                    # remove zip file from server
                    stdin, stdout, stderr = ssh_client.exec_command(
                        f'cd ..; cd /data/qgis-projects/; rm {self.qgis_project_folder_name}.zip;')
                except Exception as e:
                    print(f"Could not remove zip file from server. Reason: {e}")

            except Exception as e:
                print(f"Could not unzip file. Reason: {e}")

            #self.checkUploadedFiles()
            self.getGetCapabilitiesUrl()
        except Exception as e:
            print(f"Could not create connection. Reason: {e}")


    def checkUploadedFiles(self):
        sftpConnection = Connection(host=self.host, user=self.username, port=self.port, connect_kwargs={
            "password": self.password}) 
        # check upload:
        files_uploaded = []
        files_not_uploaded = []
        try:
            with sftpConnection as c:
                try:
                    sftpClient = c.sftp()
                    # this only checks ls in self.source_project_dir_path
                    # for filename in os.listdir(self.source_project_dir_path):
                    #     if filename.split(".")[-1] not in ('gpkg-wal', 'gpkg-shm') and filename in sftpClient.listdir(
                    #             self.server_project_dir_path):
                    #         files_uploaded.append(filename)
                    #     elif filename.split(".")[-1] not in ('gpkg-wal', 'gpkg-shm') and filename not in sftpClient.listdir(
                    #             self.server_project_dir_path):
                    #         files_not_uploaded.append(filename)

                    # use os.walk instead for listing all files in source file
                    source_tree = []
                    for root, _, files in os.walk(self.source_project_dir_path):
                        source_tree.append(root)
                        for f in files:
                            source_tree.append(os.path.join(root, f))
                    for path in source_tree:
                        filename = path.split("/")[-1]
                        file_extension = filename.split(".")[-1]
                        if os.path.isfile(path):
                            if file_extension not in ('gpkg-wal', 'gpkg-shm') and filename in sftpClient.listdir_attr(
                                        self.server_project_dir_path):
                                files_uploaded.append(filename)
                            elif file_extension not in ('gpkg-wal', 'gpkg-shm') and filename not in sftpClient.listdir(
                                        self.server_project_dir_path):
                                files_not_uploaded.append(filename)

                    # succes:
                    successBox = QMessageBox()
                    successBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconSuccess.svg'))
                    successBox.setWindowTitle("Success")
                    if len(files_not_uploaded) == 0:
                        successBox.setText(
                            "Project directory '" + self.qgis_project_folder_name + "' successfully uploaded. \nFiles uploaded: " + ', '.join(
                                files_uploaded))
                    else:
                        successBox.setText(
                            "Project directory " + self.qgis_project_folder_name + " successfully uploaded. \nFiles uploaded: " + ', '.join(
                                files_uploaded)
                            + ".\nFiles not uploaded: " + ', '.join(files_not_uploaded))

                    successBox.setStandardButtons(QMessageBox.Ok)
                    result = successBox.exec_()
                    if result == QMessageBox.Ok:
                        self.close()
                    # wms getCapabilities
                    self.wms_getcapabilities_url = ("http://" + self.host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                                                    + self.server_project_dir_path + "/" + self.qgis_project_name)
                    print(self.wms_getcapabilities_url)
                except Exception as e:
                    print(f"Could not.... Reason: {e}")
        except Exception as e:
                print(f"Could not.... Reason: {e}")

    def getGetCapabilitiesUrl(self):
        self.wms_getcapabilities_url = (
                    "http://" + self.host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                    + self.server_project_dir_path + "/" + self.qgis_project_name)
        # 1) test in mapbender console
        # if succes:
        successBox = QMessageBox()
        successBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconSuccess.svg'))
        successBox.setWindowTitle("Success")
        successBox.setText("WMS succesfully created:\n" + self.wms_getcapabilities_url)
        successBox.setStandardButtons(QMessageBox.Ok)
        successBox.exec_()
        print(self.wms_getcapabilities_url)

    def tempTestMapbenderConsole(self):
        print("connecting to mapbender console")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #client.connect(hostname=self.host, username=self.username, password=self.password) # use when function is correctly executed after upload
        client.connect('mapbender-qgis.wheregroup.lan', username='root', password='')
        # paramiko creates an instance of shell and all the commands have to be given in that instance of shell only
        # 0) Validate url: bin/console mapbender:wms:validate:url
        # Command to check the accessibility of the WMS data source. The available layers are listed, if the service is accessible.
        try:
            stdin, stdout, stderr = client.exec_command(
                #f'cd ..; cd /data/mapbender/application/; bin/console mapbender:wms:validate:url "{self.wms_getcapabilities_url}";')
                f'cd ..; cd /data/mapbender/application/; bin/console mapbender:wms:validate:url '
                f'"http://mapbender-qgis.wheregroup.lan/cgi-bin/qgis_mapserv.fcgi?VERSION=1.3.0'
                f'&map=/data/qgis-projects/source_ordner/test_project.qgz";')
            out_wms_validate_url = []
            for line in stdout:
                print(line.strip('\n'))
                out_wms_validate_url.append(line.strip('\n'))
            print('out_wms_validate_url')
            print(out_wms_validate_url)
            # if len(out_application_clone) == 0:
            #    print('WMS {self.wms_getcapabilities_url} could not be validated')
            # else:
            #    print(f' {self.wms_getcapabilities_url} was successfully validated ({out_wms_validate_url})')

            # 1) Check if WMS is already available as source in Mapbender (pending: based on url and not on id)
            try:
                stdin, stdout, stderr = client.exec_command(
                    f'cd ..; cd /data/mapbender/application/; bin/console mapbender:wms:show 4;') # with id: test with existing and not existing ids
                    #f'cd ..; cd /data/mapbender/application/; bin/console mapbender:wms:show {self.wms_getcapabilities_url} ;')
                out_wms_show = []
                for line in stdout:
                    print(line.strip('\n'))
                    out_wms_show.append(line.strip('\n'))
                print(out_wms_show)
                if len(out_wms_show) == 0:
                    print(f'WMS not available yet as Mapbender source. WMS will be added as Mapbender source...')
                    #print(f'WMS {self.wms_getcapabilities_url} not available yet as Mapbender source. WMS will be added as Mapbender source...') # use when function is correctly executed after upload
                    try:
                        # 2) If WMS not available as mapbender source yet: Adds a new WMS Source to your Mapbender Service rep
                        stdin, stdout, stderr = client.exec_command(
                            #f'cd ..; cd /data/mapbender/application/; bin/console mapbender:wms:add {self.wms_getcapabilities_url} ;') # use when function is correctly executed after upload
                            f'cd ..; cd /data/mapbender/application/; bin/console mapbender:wms:add http://mapbender-qgis.wheregroup.lan/cgi-bin/qgis_mapserv.fcgi?VERSION=1.3.0&map=/data/qgis-projects/source_ordner/test_project.qgz')
                        out_wms_add = []
                        for line in stdout:
                            print(line.strip('\n'))
                            out_wms_add.append(line.strip('\n'))
                        print(out_wms_add)
                        print(f'wms successfully added to Mapbender sources ({out_wms_add[-1]})')
                    except Exception as e:
                        print(f'Error: Could not add WMS to Mapbender sources. Reason {e}')
                else:
                    print('WMS already available as Mapbender source')
                    try:
                        # 3) If WMS already available as Mapbender source: update (bin/console mapbender:wms:reload:url (arguments: source id, serviceUrl))
                        stdin, stdout, stderr = client.exec_command(
                            #f'cd ..; cd /data/mapbender/application/; bin/console mapbender:wms:reload:url {id} {self.wms_getcapabilities_url} ;') # use when function is correctly executed after upload
                            f'cd ..; cd /data/mapbender/application/; bin/console mapbender:wms:reload:url 4 "http://mapbender-qgis.wheregroup.lan/cgi-bin/qgis_mapserv.fcgi?VERSION=1.3.0&map=/data/qgis-projects/source_ordner/test_project.qgz"')
                        out_wms_reaload_url = []
                        for line in stdout:
                            print(line.strip('\n'))
                            out_wms_reaload_url.append(line.strip('\n'))
                        print(out_wms_reaload_url)
                        if len(out_wms_reaload_url) == 0:
                            print('WMS could not be updated WMS as Mapbender source')
                        else:
                            print('WMS was successfully updated WMS as Mapbender source')
                    except Exception as e:
                        print(f'Error: Could not update WMS as Mapbender source. Reason {e}')

                # 4) Clone template application: This will create a new application with a _imp suffix as application name.
                try:
                    stdin, stdout, stderr = client.exec_command(
                        f'cd ..; cd /data/mapbender/application/; bin/console mapbender:application:clone {self.templateApplicationName};')
                    out_application_clone = []
                    for line in stdout:
                        print(line.strip('\n'))
                        out_application_clone.append(line.strip('\n'))
                    print(out_application_clone)
                    if len(out_application_clone) == 0:
                        print('WMS could not be updated WMS as Mapbender source')
                    else:
                        print(f'Application {self.templateApplicationName} was successfully cloned ({out_application_clone[0]})')
                except Exception as e:
                    print(f'Error: Could not clone application. Reason {e}')

                # 5) Add source to application: mapbender:wms:assign (Arguments:
                # application: id or slug of the application
                # source: id of the wms source
                # layerset (optional): id or name of the layerset. Defaults to 'main' or the first layerset in the application.)
                self.mapbenderSourceId = 15
                try:
                    stdin, stdout, stderr = client.exec_command(
                        f'cd ..; cd /data/mapbender/application/; bin/console mapbender:wms:assign {self.templateApplicationName}_imp {self.mapbenderSourceId};')
                    out_wms_assign = []
                    for line in stdout:
                        print(line.strip('\n'))
                        out_wms_assign.append(line.strip('\n'))
                    print(out_wms_assign)
                    #if len(out_application_clone) == 0:
                    #    print('WMS could not be updated WMS as Mapbender source')
                    #else:
                    #    print(f'Mapbender source was successfully assigned')
                except Exception as e:
                    print(f'Error: Could not assign Mapbender source to application {self.templateApplicationName}_imp. Reason {e}')

            except Exception as e:
                print(f'Error: Could not check if WMS is already available as source in Mapbender. Reason {e}')
            client.close()
        except Exception as e:
            print(f'Error: Could not validate application. Reason {e}')


    def openDialogAddNewConfigSection(self):
        new_server_section_dialog = AddServerSectionDialog()
        new_server_section_dialog.exec()

    def openDialogEditConfigSection(self):
        edit_server_section_dialog = EditServerSectionDialog()
        edit_server_section_dialog.exec()

    def openDialogRemoveConfigSection(self):
        remove_server_section_dialog = RemoveServerSectionDialog()
        remove_server_section_dialog.exec()







