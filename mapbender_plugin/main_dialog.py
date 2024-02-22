import os
import shutil

from PyQt5 import uic
import configparser

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMessageBox
from paramiko import sftp
from paramiko.client import SSHClient
from paramiko.sftp_client import SFTPClient
from fabric2 import Connection
from qgis._core import Qgis, QgsProject

from mapbender_plugin.dialogs.add_server_section_dialog import AddServerSectionDialog
from mapbender_plugin.dialogs.edit_server_section_dialog import EditServerSectionDialog
from mapbender_plugin.dialogs.remove_server_section_dialog import RemoveServerSectionDialog

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialogs/ui/main_dialog.ui'))

class MainDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # tabs
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.currentChanged.connect(self.updateSectionComboBox)

        # tab1
        self.updateSectionComboBox()
        self.uploadButton.clicked.connect(self.validateConfigParams)

        # tab2
        self.addServerConfigButton.clicked.connect(self.openDialogAddNewConfigSection)
        self.editServerConfigButton.clicked.connect(self.openDialogEditConfigSection)
        self.removeServerConfigButton.clicked.connect(self.openDialogRemoveConfigSection)
        self.buttonBoxTab1.rejected.connect(self.reject)
        self.buttonBoxTab2.rejected.connect(self.reject)

        self.server_qgis_projects_folder_rel_path = '/data/qgis-projects/'

    def updateSectionComboBox(self):
        # create an empty config file in plugin directory if not already existing
        self.plugin_dir = os.path.dirname(__file__)
        self.config_path = self.plugin_dir + '/server_config.cfg'

        # check if config file exists
        if not os.path.isfile(self.config_path):
            try:
                # create the config file if not existing
                open(self.config_path, 'a').close()
            except OSError:
                self.iface.messageBar().pushMessage("Failed creating the file", "Please contact", level=Qgis.Critical)

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
        self.username = self.config.get(selected_section, 'username')
        self.password = self.config.get(selected_section, 'password')
        if self.host == '' or len(self.host)<5:
            failBox = QMessageBox()
            # failBox.setIcon(QMessageBox.Warning)
            failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
            failBox.setWindowTitle("Failed")
            failBox.setText("Server URL is not valid. Please select a valid section or edit the selected section under"
                            " 'Server configuration management'")
            failBox.setStandardButtons(QMessageBox.Ok)
            result = failBox.exec_()
        else:
            self.uploadProject()


    def uploadProject(self):
        # get and check .qgz project path
        self.source_project_dir_path = QgsProject.instance().readPath("./")
        self.source_project_file_path = QgsProject.instance().fileName()
        if self.source_project_dir_path == "./" or self.source_project_file_path == "":
            failBox = QMessageBox()
            failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
            failBox.setWindowTitle("Failed")
            failBox.setText("Please use the Mapbender Plugin from a valid QGIS-Project with QGIS-Server configurations")
            failBox.setStandardButtons(QMessageBox.Ok)
            failBox.exec_()
        else:
            # get project layers
            source_project_layers = self.getProjectLayers()
            #print(source_project_layers)

            # QGIS Server folder
            self.server_qgis_projects_folder_abs_path = self.host + self.server_qgis_projects_folder_rel_path

            # project folder name (with .qgz and data) as in local
            self.qgis_project_folder_name = self.source_project_dir_path.split("/")[-1]
            self.server_project_dir_path = self.server_qgis_projects_folder_rel_path + self.qgis_project_folder_name

            try:
                # server connection and upload - WORKS, with VPN
                #sftpConnection = Connection(host=self.host, user=self.username) # does not work!  Der Name oder der Dienst ist nicht bekannt
                sftpPassword = ''
                sftpConnection = Connection(host='mapbender-qgis.wheregroup.lan', user='root', port='', connect_kwargs={"password": sftpPassword})
                with sftpConnection as c:
                     sftpClient = c.sftp()
                     # create qgis-project folder:
                     try:
                         sftpClient.mkdir(self.server_project_dir_path) # does not create parent directories if not exist!
                         # upload files:
                         for filename in os.listdir(self.source_project_dir_path):
                             # if filename is a file:
                             if filename.split(".")[-1] not in ('gpkg-wal', 'gpkg-shm'):
                                 c.put(local=self.source_project_dir_path + "/" + filename,
                                       remote=self.server_project_dir_path)
                     except Exception as e:
                        print(f"Could not mkdir!. Reason: {e}")

                                     # check upload:
                files_uploaded = []
                files_not_uploaded = []
                with sftpConnection as c:
                    sftpClient = c.sftp()
                    for filename in os.listdir(self.source_project_dir_path):
                         if filename.split(".")[-1] not in ('gpkg-wal', 'gpkg-shm') and filename in sftpClient.listdir(self.server_project_dir_path):
                             files_uploaded.append(filename)
                         elif filename.split(".")[-1] not in ('gpkg-wal', 'gpkg-shm') and filename not in sftpClient.listdir(self.server_project_dir_path):
                            files_not_uploaded.append(filename)
                # succes:
                successBox = QMessageBox()
                successBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconSuccess.svg'))
                successBox.setWindowTitle("Success")
                if len(files_not_uploaded) == 0:
                    successBox.setText("Project directory" + self.qgis_project_folder_name + "successfully uploaded. \nFiles uploaded: " + ', '.join(files_uploaded))
                else:
                    successBox.setText(
                        "Project directory" + self.qgis_project_folder_name + "successfully uploaded. \nFiles uploaded: " + ', '.join(files_uploaded)
                        + ".\nFiles not uploaded: " + ', '.join(files_not_uploaded))

                successBox.setStandardButtons(QMessageBox.Ok)
                result = successBox.exec_()
                if result == QMessageBox.Ok:
                    self.close()

            except FileExistsError:
                failBox = QMessageBox()
                failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                failBox.setWindowTitle("Failed")
                failBox.setText("Project directory could not be uploaded: Project directory already exists. Do you want to "
                                "overwrite the existing project directory '" + self.qgis_project_folder_name + "'?")
                failBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                result = failBox.exec_()
                if result == QMessageBox.Yes:
                    self.close()
                    self.overwriteProject()
            except shutil.Error: #convert to error
                failBox = QMessageBox()
                failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                failBox.setWindowTitle("Failed")
                failBox.setText("Project directory could not be uploaded")
                failBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                result = failBox.exec_()
                if result == QMessageBox.Yes:
                    self.close()
                    self.overwriteProject()

    def getProjectLayers(self):
        project = QgsProject.instance()
        project.read()
        layers_names = []
        for layer in project.mapLayers().values():
            layers_names.append(layer.name())
        return layers_names

    def overwriteProject(self): # local, for tests
        try:
            shutil.rmtree(self.server_project_dir_path)
            shutil.copytree(self.source_project_dir_path, self.server_project_dir_path)
            successBox = QMessageBox()
            successBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconSuccess.svg'))
            successBox.setWindowTitle("Success")
            successBox.setText("Project directory successfully overwritten")
            successBox.setStandardButtons(QMessageBox.Ok)
            result = successBox.exec_()
        except shutil.Error:
            failBox = QMessageBox()
            failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
            failBox.setWindowTitle("Failed")
            failBox.setText("An error occurred")
            failBox.setStandardButtons(QMessageBox.Ok)
            failBox.exec_()



    def openDialogAddNewConfigSection(self):
        new_server_section_dialog = AddServerSectionDialog()
        new_server_section_dialog.exec()

    def openDialogEditConfigSection(self):
        edit_server_section_dialog = EditServerSectionDialog()
        edit_server_section_dialog.exec()

    def openDialogRemoveConfigSection(self):
        remove_server_section_dialog = RemoveServerSectionDialog()
        remove_server_section_dialog.exec()







