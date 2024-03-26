import os

from PyQt5.QtCore import QSettings
from fabric2 import Connection
import paramiko

from PyQt5 import uic
import configparser

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem

from qgis._core import Qgis, QgsProject
from qgis.utils import iface

from mapbender_plugin.dialogs.add_server_section_dialog import AddServerSectionDialog
from mapbender_plugin.dialogs.edit_server_section_dialog import EditServerSectionDialog
from mapbender_plugin.helpers import check_if_config_file_exists, get_plugin_dir, get_project_layers, \
    check_if_qgis_project, get_paths, zip_local_project_folder, upload_project_zip_file, \
    remove_project_folder_from_server, \
    check_if_project_folder_exists_on_server, unzip_project_folder_on_server, check_uploaded_files, \
    get_get_capabilities_url, show_fail_box_ok, show_fail_box_yes_no, show_succes_box_ok, \
    list_qgs_settings_child_groups, list_qgs_settings_values, show_question_box
from mapbender_plugin.mapbender import MapbenderUpload

from mapbender_plugin.settings import (
    SERVER_QGIS_PROJECTS_FOLDER_REL_PATH, CONFIG_FILE_NAME,
)

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialogs/ui/main_dialog.ui'))

class MainDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.server_qgis_projects_folder_rel_path = SERVER_QGIS_PROJECTS_FOLDER_REL_PATH

        self.plugin_dir = get_plugin_dir()
        self.config_path = self.plugin_dir + "/" + CONFIG_FILE_NAME
        # check if config file exists
        if not check_if_config_file_exists(self.config_path):
            self.iface.messageBar().pushMessage("No config file is available. Failed creating a new"
                                                "config file", "Please contact", level=Qgis.Critical)

        # tabs
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.currentChanged.connect(self.update_section_combo_box)

        # tab1
        self.update_section_combo_box()
        self.publishRadioButton.setChecked(True)

        self.publishRadioButton.clicked.connect(self.enable_publish_parameters)
        self.cloneTemplateRadioButton.setChecked(True)
        self.updateButton.setEnabled(False)
        self.updateRadioButton.clicked.connect(self.disable_publish_parameters)

        self.publishButton.clicked.connect(self.publish_project)
        self.updateButton.clicked.connect(self.update_project)

        #tmp, for testing
        self.tmpMapbenderConsoleButton.clicked.connect(self.test_console)
        self.tmpMapbenderConsoleButton.hide()
        # tmp, for testing


        # tab2
        # server table
        self.serverTableWidget.setColumnCount(2)
        self.serverTableWidget.setHorizontalHeaderLabels(["Name", "URL"])
        self.update_server_table()
        #self.serverTableWidget.table.setRowCount
        # buttons
        self.addServerConfigButton.clicked.connect(self.open_dialog_add_new_config_section)
        self.editServerConfigButton.clicked.connect(self.open_dialog_edit_config_section)
        self.removeServerConfigButton.clicked.connect(self.remove_config_section)
        self.buttonBoxTab1.rejected.connect(self.reject)
        self.buttonBoxTab2.rejected.connect(self.reject)


    def update_server_table(self):
        server_config_sections = list_qgs_settings_child_groups("mapbender-plugin/connection")
        self.serverTableWidget.setRowCount(len(server_config_sections))
        for i, (name) in enumerate(server_config_sections):
            item_name = QTableWidgetItem(name)
            item_name.setText(server_config_sections[i])
            self.serverTableWidget.setItem(i, 0, item_name)

            con_params = list_qgs_settings_values(server_config_sections[i])
            item_url = QTableWidgetItem()
            item_url.setText(con_params['url'])
            self.serverTableWidget.setItem(i, 1, item_url)

    def update_section_combo_box(self) -> None:
        """ Updates the server configuration sections dropdown menu """
        # # parse config file
        # try:
        #     # As the documentation makes clear, any number of filenames can be passed to the read method,
        #     # and it will silently ignore the ones that cannot be opened.
        #     self.config = configparser.ConfigParser()
        #     self.config.read(self.config_path)
        # except configparser.Error as error:
        #     self.iface.messageBar().pushMessage("Error: Could not parse config file ", error, level=Qgis.Critical)

        # read config sections
        config_sections = list_qgs_settings_child_groups("mapbender-plugin/connection")
        if len(config_sections) == 0:
            #self.warningAddServiceText.show()
            self.serverComboBoxLabel.hide()
            self.sectionComboBox.hide()
            self.publishButton.hide()
            self.editServerConfigButton.hide()
            self.removeServerConfigButton.hide()

        else:
            # update sections-combobox
            #self.warningAddServiceText.hide()
            self.sectionComboBox.clear()
            self.sectionComboBox.addItems(config_sections)
            self.serverComboBoxLabel.show()
            self.sectionComboBox.show()
            self.publishButton.show()
            # config management
            self.editServerConfigButton.show()
            self.removeServerConfigButton.show()


    def disable_publish_parameters(self):
        self.mbParamsFrame.setEnabled(False)
        self.updateButton.setEnabled(True)
        self.publishButton.setEnabled(False)

    def enable_publish_parameters(self):
        self.mbParamsFrame.setEnabled(True)
        self.publishButton.setEnabled(True)
        self.updateButton.setEnabled(False)

    def open_dialog_add_new_config_section(self):
        new_server_section_dialog = AddServerSectionDialog()
        new_server_section_dialog.exec()
        self.update_server_table()

    def open_dialog_edit_config_section(self):
        edit_server_section_dialog = EditServerSectionDialog()
        edit_server_section_dialog.exec()
        self.update_server_table()

    def remove_config_section(self):
        selected_row = self.serverTableWidget.currentRow()
        selected_section = self.serverTableWidget.item(selected_row, 0).text()
        if (
        show_question_box(f"""Are you sure you want to remove the section '{selected_section}'?""")) == QMessageBox.Yes:
            try:
                s = QSettings()
                s.remove(f"mapbender-plugin/connection/{selected_section}")
                if (show_succes_box_ok('Success', 'Section successfully removed')) == QMessageBox.Ok:
                    self.update_server_table()
            except:
                show_fail_box_ok('Failed', "Section could not be deleted")


    def publish_project(self):
        # check mapbender params:
        if ((self.cloneTemplateRadioButton.isChecked() or self.addToAppRadioButton.isChecked()) and
                self.mapbenderCustomAppSlugLineEdit.text() != ''):
            self.upload_project()
        else:
            if (show_fail_box_ok("Please complete Mapbender Parameters",
                                         "Please select clone template / add to existing application and enter a "
                                         "valid URL title")) == QMessageBox.Ok:
                return

    def update_project(self):
        self.upload_project()

    def upload_project(self):
        # config params:
        # check config params / check connection
        selected_section = self.sectionComboBox.currentText()
        con_params = list_qgs_settings_values(selected_section)
        self.host = con_params['url']
        self.port = con_params['port']
        self.username = con_params['username']
        self.password = con_params['password']
        print(self.host, self.port, self.username, self.password)

        # self.host = self.config.get(selected_section, 'url')
        # self.port = self.config.get(selected_section, 'port')
        # self.username = self.config.get(selected_section, 'username')
        # self.password = self.config.get(selected_section, 'password')

        iface.messageBar().pushMessage("", "Checking QGIS-Project ...", level=Qgis.Info, duration=2)
        if check_if_qgis_project(self.plugin_dir):
            paths = get_paths(SERVER_QGIS_PROJECTS_FOLDER_REL_PATH)
            source_project_dir_path = paths.get('source_project_dir_path')
            source_project_zip_dir_path = paths.get('source_project_zip_dir_path')
            qgis_project_folder_name = paths.get('qgis_project_folder_name')
            qgis_project_name = paths.get('qgis_project_name')
            server_project_dir_path = paths.get('server_project_dir_path')

            #getProjectLayers
            # if success...
            # then check if folder exists on the server:
            if check_if_project_folder_exists_on_server(self.host, self.username, self.port, self.password,
                                                        self.plugin_dir, source_project_zip_dir_path,
                                                        SERVER_QGIS_PROJECTS_FOLDER_REL_PATH, qgis_project_folder_name):
                # if return = True (folder already exists on server)
                if self.publishRadioButton.isChecked():
                    if (show_fail_box_yes_no("Failed",
                                             f"Project directory already exists on the server. \n \nDo you want to"
                                             f" overwrite the existing project directory '{qgis_project_folder_name}' "
                                             f"and update the WMS?")) == QMessageBox.Yes:
                        if remove_project_folder_from_server(self.host, self.username, self.port, self.password,
                                                             self.plugin_dir, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                                             qgis_project_folder_name):
                            iface.messageBar().pushMessage("", "Uploading QGIS project and data to server ...",
                                                           level=Qgis.Info, duration=5)

                            zip_local_project_folder(self.plugin_dir, source_project_dir_path,
                                                     source_project_zip_dir_path, qgis_project_folder_name)

                            if upload_project_zip_file(self.host, self.username, self.port, self.password, self.plugin_dir,
                                                       source_project_zip_dir_path, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                                       qgis_project_folder_name):
                                if unzip_project_folder_on_server(self.host, self.username, self.port, self.password,
                                                                  qgis_project_folder_name, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH):
                                    # check "http://"
                                    wms_getcapabilities_url = (
                                            "http://" + self.host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                                            + SERVER_QGIS_PROJECTS_FOLDER_REL_PATH + qgis_project_folder_name + '/' + qgis_project_name)
                                    self.mapbender_upload(wms_getcapabilities_url)
                else:
                    if remove_project_folder_from_server(self.host, self.username, self.port, self.password,
                                                         self.plugin_dir, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                                         qgis_project_folder_name):
                        iface.messageBar().pushMessage("", "Updating QGIS project and data on server ...",
                                                       level=Qgis.Info, duration=5)

                        zip_local_project_folder(self.plugin_dir, source_project_dir_path,
                                                 source_project_zip_dir_path, qgis_project_folder_name)

                        if upload_project_zip_file(self.host, self.username, self.port, self.password, self.plugin_dir,
                                                   source_project_zip_dir_path, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                                   qgis_project_folder_name):
                            if unzip_project_folder_on_server(self.host, self.username, self.port, self.password,
                                                              qgis_project_folder_name,
                                                              SERVER_QGIS_PROJECTS_FOLDER_REL_PATH):
                                # check "http://"
                                wms_getcapabilities_url = (
                                        "http://" + self.host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                                        + SERVER_QGIS_PROJECTS_FOLDER_REL_PATH + qgis_project_folder_name + '/' + qgis_project_name)
                                self.mapbender_update(wms_getcapabilities_url)


            else:
                # if return = False (folder does not exist yet on the server)
                if self.publishRadioButton.isChecked():
                    iface.messageBar().pushMessage("", "Uploading QGIS project and data to server ...",
                                                   level=Qgis.Info, duration=5)
                    zip_local_project_folder(self.plugin_dir, source_project_dir_path,
                                             source_project_zip_dir_path, qgis_project_folder_name)
                    if upload_project_zip_file(self.host, self.username, self.port, self.password, self.plugin_dir,
                                               source_project_zip_dir_path, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH,
                                               qgis_project_folder_name):
                        if unzip_project_folder_on_server(self.host, self.username, self.port, self.password,
                                                          qgis_project_folder_name, SERVER_QGIS_PROJECTS_FOLDER_REL_PATH):
                            wms_getcapabilities_url = (
                                    "http://" + self.host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                                    + SERVER_QGIS_PROJECTS_FOLDER_REL_PATH + qgis_project_folder_name + '/' + qgis_project_name)
                            self.mapbender_upload(wms_getcapabilities_url)
                else:
                    show_fail_box_ok("Failed",

                        "Project directory " + qgis_project_folder_name + " does not exist on the server and therefore "
                                                                         "can not be updated. \n \nIf you want to upload a new"
                                                                         " QGIS-Project please select the option 'Publish "
                                                                         " in Mapbender app'")

    def test_console(self):
        self.mapbender_upload("http://mapbender-qgis.wheregroup.lan/cgi-bin/qgis_mapserv.fcgi?VERSION=1.3.0&map=/data/qgis-projects/source_ordner/test_project.qgz")
        #self.mapbender_update()

    def mapbender_upload(self, wms_getcapabilities_url):
        # mapbender params:
        if self.cloneTemplateRadioButton.isChecked():
            clone_app = True
        if self.addToAppRadioButton.isChecked():
            clone_app = False
        # template slug:
        layer_set = self.layerSetLineEdit.text()

        iface.messageBar().pushMessage("", "Validating WMS ULR, checking if WMS URL is already set as Mapbender source, ...", level=Qgis.Info, duration=5)

        mapbender_uploader = MapbenderUpload(self.host, self.username) # other parameters?
        # TEST CONSOLE:
        #host= "mapbender-qgis.wheregroup.lan"
        #user = "root"
        #mapbender_uploader = MapbenderUpload( host, user)

        # Optional
        # wms_is_valid = mapbender_uploader.wms_parse_url_validate(wms_getcapabilities_url)
        # if wms_is_valid:
        #...

        exit_status_wms_show, sources_ids = mapbender_uploader.wms_show(wms_getcapabilities_url)
        if exit_status_wms_show == 0: # success
            # reload source if it already exists
            if len(sources_ids)>0:
                for source_id in sources_ids:
                    exit_status_wms_reload = mapbender_uploader.wms_reload(source_id, wms_getcapabilities_url)
                source_id = sources_ids[-1]
            else:
                # add source to Mapbender if it does not exist
                exit_status_wms_add, source_id = mapbender_uploader.wms_add(wms_getcapabilities_url)

                # depending on user's input (duplicate template or use existing application):
            #if exit_status_wms_reload == 0 or exit_status_wms_add == 0:
            if clone_app:
                template_slug = self.mapbenderCustomAppSlugLineEdit.text()
                exit_status_app_clone, slug, error = mapbender_uploader.app_clone(template_slug)
                if exit_status_app_clone == 0:
                    exit_status_wms_assign, output_wms_assign, error_wms_assign = (
                        mapbender_uploader.wms_assign(slug, source_id, layer_set))
                    print(exit_status_wms_assign, output_wms_assign, error_wms_assign)

                else:
                    show_fail_box_ok("Failed",
                                     f"Application could not be cloned.\n \n Error:  {error}")
                    return
            else:
                slug = self.mapbenderCustomAppSlugLineEdit.text()
                exit_status_wms_assign, output_wms_assign, error_wms_assign = (
                    mapbender_uploader.wms_assign(slug, source_id, layer_set))
                print(exit_status_wms_assign, output_wms_assign, error_wms_assign)

            if exit_status_wms_assign == 0:
                if (show_succes_box_ok("Success report",
                                                "WMS succesfully created:\n \n" + wms_getcapabilities_url +
                                                "\n \n And added to mapbender application: \n \n" + "http://" +
                                                self.host + "/mapbender/application/" + slug)) == QMessageBox.Ok:
                    self.close()

            else:
                show_fail_box_ok("Failed",
                                 f"WMS could not be assigend to Mapbender application.\n{output_wms_assign}")

        mapbender_uploader.close_connection()

    def mapbender_update(self, wms_getcapabilities_url):
        mapbender_uploader = MapbenderUpload(self.host, self.username)
        exit_status_wms_show, sources_ids = mapbender_uploader.wms_show(wms_getcapabilities_url)
        if exit_status_wms_show == 0:  # success
            # reload source if it already exists
            if len(sources_ids) > 0:
                for source_id in sources_ids:
                    exit_status_wms_reload = mapbender_uploader.wms_reload(source_id, wms_getcapabilities_url)
                    if exit_status_wms_reload == 0:  # success
                        if (show_succes_box_ok("Success report" ,
                                               "WMS succesfully updated:\n \n"+ wms_getcapabilities_url +
                                               "\n \non Mapbender source(s): " + str(sources_ids))) == QMessageBox.Ok:
                            self.close()
            else:
                show_fail_box_ok("Failed",
                                 f"WMS is not an existing source in Mapbender and could not be updated")
        mapbender_uploader.close_connection()










