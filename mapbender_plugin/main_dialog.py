import os

from fabric2 import Connection
import paramiko

from PyQt5 import uic
import configparser

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMessageBox

from qgis._core import Qgis, QgsProject
from qgis.utils import iface

from mapbender_plugin.dialogs.add_server_section_dialog import AddServerSectionDialog
from mapbender_plugin.dialogs.edit_server_section_dialog import EditServerSectionDialog
from mapbender_plugin.dialogs.remove_server_section_dialog import RemoveServerSectionDialog
from mapbender_plugin.helpers import checkIfConfigFileExists, getPluginDir, getProjectLayers, \
    checkIfQgisProject, getPaths, zipLocalProjectFolder, uploadProjectZipFile, removeProjectFolderFromServer, \
    checkIfProjectFolderExistsOnServer, unzipProjectFolderOnServer, checkUploadedFiles, getGetCapabilitiesUrl
from mapbender_plugin.mapbender import MapbenderUpload

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
        self.uploadButton.clicked.connect(self.uploadProject)
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

    def openDialogAddNewConfigSection(self):
        new_server_section_dialog = AddServerSectionDialog()
        new_server_section_dialog.exec()

    def openDialogEditConfigSection(self):
        edit_server_section_dialog = EditServerSectionDialog()
        edit_server_section_dialog.exec()

    def openDialogRemoveConfigSection(self):
        remove_server_section_dialog = RemoveServerSectionDialog()
        remove_server_section_dialog.exec()

    def uploadProject(self):
        iface.messageBar().pushMessage("", "Connecting to server ...", level=Qgis.Info, duration=5)

        # config params:
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
            if checkIfQgisProject(self.plugin_dir):
                source_project_dir_path = getPaths(SERVER_QGIS_PROJECTS_FOLDER_REL_PATH).get('source_project_dir_path')
                source_project_zip_dir_path = getPaths(SERVER_QGIS_PROJECTS_FOLDER_REL_PATH).get('source_project_zip_dir_path')
                qgis_project_folder_name = getPaths(SERVER_QGIS_PROJECTS_FOLDER_REL_PATH).get('qgis_project_folder_name')
                qgis_project_name = getPaths(SERVER_QGIS_PROJECTS_FOLDER_REL_PATH).get('qgis_project_name')
                server_project_dir_path = getPaths(SERVER_QGIS_PROJECTS_FOLDER_REL_PATH).get('server_project_dir_path')
                #getProjectLayers
                # if success...
                zipLocalProjectFolder(self.plugin_dir, source_project_dir_path,
                                      source_project_zip_dir_path, qgis_project_folder_name)
                # then check if folder exists on the server:
                if checkIfProjectFolderExistsOnServer(self.host, self.username, self.port, self.password,
                                                      self.plugin_dir, source_project_zip_dir_path,
                                                      SERVER_QGIS_PROJECTS_FOLDER_REL_PATH, qgis_project_folder_name):
                    # if return = Ture (folder already exists in server)
                    failBox = QMessageBox()
                    failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                    failBox.setWindowTitle("Failed")
                    failBox.setText(
                        "Project directory could not be uploaded: Project directory already exists on the server. Do you want to "
                        "overwrite the existing project directory '" + qgis_project_folder_name + "'?")
                    failBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    result = failBox.exec_()
                    if result == QMessageBox.Yes:
                        self.close()
                        if removeProjectFolderFromServer(self.host, self.username, self.port, self.password,
                                                         self.plugin_dir, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                                         qgis_project_folder_name):
                            iface.messageBar().pushMessage("", "Uploading QGIS project and data to server ...",
                                                           level=Qgis.Info, duration=5)

                            if uploadProjectZipFile(self.host, self.username, self.port, self.password, self.plugin_dir,
                                                 source_project_zip_dir_path, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                                 qgis_project_folder_name):
                                if unzipProjectFolderOnServer(self.host, self.username, self.port, self.password,
                                                              qgis_project_folder_name, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH):
                                    wms_getcapabilities_url = (
                                            "http://" + self.host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                                            + SERVER_QGIS_PROJECTS_FOLDER_REL_PATH + qgis_project_folder_name + '/' + qgis_project_name)
                                    self.tempTestMapbenderConsole(wms_getcapabilities_url)
                else:
                    # if return = False (folder does not exist yet on the server)
                    iface.messageBar().pushMessage("", "Uploading QGIS project and data to server ...",
                                                   level=Qgis.Info, duration=5)
                    if uploadProjectZipFile(self.host, self.username, self.port, self.password, self.plugin_dir,
                                         source_project_zip_dir_path, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                         qgis_project_folder_name):
                        if unzipProjectFolderOnServer(self.host, self.username, self.port, self.password,
                                                              qgis_project_folder_name, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH):
                            wms_getcapabilities_url = (
                                    "http://" + self.host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                                    + SERVER_QGIS_PROJECTS_FOLDER_REL_PATH + qgis_project_folder_name + '/' + qgis_project_name)
                            self.tempTestMapbenderConsole(wms_getcapabilities_url)

    def tempTestMapbenderConsole(self, wms_getcapabilities_url):
        # mapbender params:
        if self.cloneTemplateRadioButton.isChecked():
            clone_app = True
        if self.addToAppRadioButton.isChecked():
            clone_app = False
        # template slug:
        layer_set = self.layerSetLineEdit.text()

        iface.messageBar().pushMessage("", "Validating WMS ULR, checking if WMS URL is already set as Mapbender source, ...", level=Qgis.Info, duration=5)
        # variable hard coded only for tests
        #wms_url = 'http://mapbender-qgis.wheregroup.lan/cgi-bin/qgis_mapserv.fcgi?VERSION=1.3.0&service=WMS&Request=GetCapabilities&map=/data/qgis-projects/source_ordner/test_project.qgz'
        wms_url = wms_getcapabilities_url

        #mapbender_uploader = MapbenderUpload('mapbender-qgis.wheregroup.lan', 'root')
        mapbender_uploader = MapbenderUpload(self.host, self.username)

        # Optional
        # wms_is_valid = mapbender_uploader.wms_parse_url_validate(wms_url)
        # if wms_is_valid:
        #...

        exit_status_wms_show, sources_ids = mapbender_uploader.wms_show(wms_url)
        if exit_status_wms_show == 0: # success
            # reload source if it already exists
            if len(sources_ids)>0:
                for source_id in sources_ids:
                    exit_status_wms_reload = mapbender_uploader.wms_reload(source_id, wms_url)
                source_id = sources_ids[-1]
            else:
                # add source to mapbender if it does not exist
                exit_status_wms_add, source_id = mapbender_uploader.wms_add(wms_url)

                # depending on user's input (duplicate template or use existing application):
            #if exit_status_wms_reload == 0 or exit_status_wms_add == 0:
            if clone_app:
                template_slug = self.mapbenderCustomAppSlugLineEdit.text()
                exit_status_app_clone, slug = mapbender_uploader.app_clone(template_slug)
                if exit_status_app_clone == 0:
                    exit_status_wms_assign = mapbender_uploader.wms_assign(slug, source_id, layer_set)
            else:
                slug = self.mapbenderCustomAppSlugLineEdit.text()
                exit_status_wms_assign = mapbender_uploader.wms_assign(slug, source_id, layer_set)

            if exit_status_wms_assign == 0:
                successBox = QMessageBox()
                successBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconSuccess.svg'))
                successBox.setWindowTitle("Success report")
                successBox.setText("WMS succesfully created:\n \n" + wms_getcapabilities_url +
                                   "\n \n And added to mapbender application: \n \n" + "http://" + self.host
                                   + "/mapbender/application/"+ slug
                                   )
                successBox.setStandardButtons(QMessageBox.Ok)
                result = successBox.exec_()
                if result == QMessageBox.Ok:
                    self.close()

                else:
                    failBox = QMessageBox()
                    failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                    failBox.setWindowTitle("Failed")
                    failBox.setText("WMS could not be added to mapbender application")
                    failBox.setStandardButtons(QMessageBox.Ok)
                    failBox.exec_()
            else:
                failBox = QMessageBox()
                failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
                failBox.setWindowTitle("Failed")
                failBox.setText("Application could not be cloned")
                failBox.setStandardButtons(QMessageBox.Ok)
                failBox.exec_()

        mapbender_uploader.close_connection()








