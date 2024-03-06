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
from mapbender_plugin.mapbender import mapbenderUpload

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

    def openDialogAddNewConfigSection(self):
        new_server_section_dialog = AddServerSectionDialog()
        new_server_section_dialog.exec()

    def openDialogEditConfigSection(self):
        edit_server_section_dialog = EditServerSectionDialog()
        edit_server_section_dialog.exec()

    def openDialogRemoveConfigSection(self):
        remove_server_section_dialog = RemoveServerSectionDialog()
        remove_server_section_dialog.exec()

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
                            if uploadProjectZipFile(self.host, self.username, self.port, self.password, self.plugin_dir,
                                                 source_project_zip_dir_path, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                                 qgis_project_folder_name):
                                if unzipProjectFolderOnServer(self.host, self.username, self.port, self.password,
                                                              qgis_project_folder_name, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH):
                                    # checkUploadedFiles(self.host, self.username, self.port, self.password,
                                    #                    source_project_dir_path, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH)
                                    wms_getcapabilities_url = getGetCapabilitiesUrl(self.host, self.plugin_dir,
                                                                                    server_project_dir_path, qgis_project_name)
                                    # mapbenderValidateUrl(self.host, self.username, self.port, self.password,
                                    #                      wms_getcapabilities_url)
                                    # mapbenderWmsShow(self.host, self.username, self.port, self.password,
                                    #                  wms_getcapabilities_url)
                else:
                    # if return = False (folder does not exist yet on the server)
                    if uploadProjectZipFile(self.host, self.username, self.port, self.password, self.plugin_dir,
                                         source_project_zip_dir_path, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                         qgis_project_folder_name):
                        if unzipProjectFolderOnServer(self.host, self.username, self.port, self.password,
                                                              qgis_project_folder_name, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH):
                            # checkUploadedFiles(self.host, self.username, self.port, self.password,source_project_dir_path,
                            #                            SERVER_QGIS_PROJECTS_FOLDER_REL_PATH)
                            wms_getcapabilities_url = getGetCapabilitiesUrl(self.host, self.plugin_dir,server_project_dir_path, qgis_project_name)
                            # mapbenderValidateUrl(self.host, self.username, self.port, self.password,
                            #                      wms_getcapabilities_url)
                            # if mapbenderWmsShow(self.host, self.username, self.port, self.password,
                            #                      wms_getcapabilities_url):
                            #     # reload source
                            #     print('reload source')
                            #
                            # else:
                            #     #add new source
                            #     print('add new source')

    def tempTestMapbenderConsole(self):
        iface.messageBar().pushMessage("", "Validating WMS ULR, checking if WMS URL is already set as Mapbender source, ...", level=Qgis.Info, duration=5)
        # variable hard coded only for tests
        wms_getCapabiltities_url = 'http://mapbender-qgis.wheregroup.lan/cgi-bin/qgis_mapserv.fcgi?VERSION=1.3.0&service=WMS&Request=GetCapabilities&map=/data/qgis-projects/source_ordner/test_project.qgz'

        mapbenderUpload.wms_parse_url_validate(wms_getCapabiltities_url)
        mapbenderUpload.wms_show(wms_getCapabiltities_url)

        return
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







