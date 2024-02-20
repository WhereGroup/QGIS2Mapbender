import os
import shutil
import sys

from PyQt5 import uic
#from configparser import ConfigParser
import configparser

from PyQt5.QtWidgets import QMessageBox
from qgis._core import Qgis, QgsProject

from mapbender_plugin.add_server_section_dialog import AddServerSectionDialog
from mapbender_plugin.edit_server_section_dialog import EditServerSectionDialog
from mapbender_plugin.remove_server_section_dialog import RemoveServerSectionDialog

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'resources/ui/main_dialog.ui'))

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
            self.sectionComboBox.clear()
            self.sectionComboBox.addItems(config_sections)
            self.sectionComboBoxLabel.show()
            self.sectionComboBox.show()
            # config management
            self.warningAddServiceText.hide()

    def validateConfigParams(self):
        selected_section = self.sectionComboBox.currentText()
        server_url = self.config.get(selected_section, 'url')
        server_username = self.config.get(selected_section, 'username')
        server_password = self.config.get(selected_section, 'password')
        if server_url == '' or len(server_url)<5:
            print('Please provide a value for URL')
        print(server_url, server_username, server_password)
        self.uploadProject()

    def uploadProject(self):
        self.source_project_dir_path = QgsProject.instance().readPath("./")
        self.source_project_file_path = QgsProject.instance().fileName()

        self.server_dir_path = '/home/cviesca/Projekte/Plugin_QGIS-QGIS-Server_Mapbender/'
        self.server_project_dir_name = 'project_ordner_COPY'
        self.server_project_dir_path = self.server_dir_path + self.server_project_dir_name
        # The destination directory, must not already exist; it will be created
        # as well as missing parent directories. Permissions and times of directories are copied
        # with copystat(), individual files are copied using shutil.copy2().
        try:
            shutil.copytree(self.source_project_dir_path, self.server_project_dir_path)
            successBox = QMessageBox()
            successBox.setIcon(QMessageBox.Information)
            successBox.setWindowTitle("Success")
            successBox.setText("Project directory successfully uploaded")
            successBox.setStandardButtons(QMessageBox.Ok)
            result = successBox.exec_()
            if result == QMessageBox.Ok:
                self.close()
        except FileExistsError:
            failBox = QMessageBox()
            failBox.setIcon(QMessageBox.Warning)
            failBox.setWindowTitle("Failed")
            failBox.setText("Project directory could not be uploaded: Project directory already exists")
            failBox.setStandardButtons(QMessageBox.Ok)
            result = failBox.exec_()
            if result == QMessageBox.Ok:
                self.close()


    def openDialogAddNewConfigSection(self):
        new_server_section_dialog = AddServerSectionDialog()
        new_server_section_dialog.exec()

    def openDialogEditConfigSection(self):
        edit_server_section_dialog = EditServerSectionDialog()
        edit_server_section_dialog.exec()

    def openDialogRemoveConfigSection(self):
        remove_server_section_dialog = RemoveServerSectionDialog()
        remove_server_section_dialog.exec()







