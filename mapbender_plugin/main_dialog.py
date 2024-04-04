import os
from itertools import count

from PyQt5.QtCore import QSettings, Qt
from fabric2 import Connection
import paramiko

from PyQt5 import uic
import configparser

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QHeaderView, QWidget, QVBoxLayout, QApplication, QDockWidget, \
    QLabel

from qgis._core import Qgis, QgsProject, QgsSettings, QgsMessageLog
from qgis._gui import QgsMessageBar
from qgis.utils import iface

from mapbender_plugin.dialogs.add_server_config_dialog import AddServerConfigDialog
from mapbender_plugin.dialogs.edit_server_config_dialog import EditServerConfigDialog
from mapbender_plugin.helpers import check_if_config_file_exists, get_plugin_dir, get_project_layers, \
    check_if_qgis_project, get_paths, zip_local_project_folder, upload_project_zip_file, \
    remove_project_folder_from_server, \
    check_if_project_folder_exists_on_server, unzip_project_folder_on_server, check_uploaded_files, \
    get_get_capabilities_url, show_fail_box_ok, show_fail_box_yes_no, show_succes_box_ok, \
    list_qgs_settings_child_groups, show_question_box, show_new_info_message_bar, \
    update_mb_slug_in_settings, delete_local_project_zip_file
from mapbender_plugin.mapbender import MapbenderUpload
from mapbender_plugin.server_config import ServerConfig
from mapbender_plugin.settings import SERVER_TABLE_HEADERS, PLUGIN_SETTINGS_SERVER_CONFIG_KEY

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialogs/ui/main_dialog.ui'))


class MainDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.previous_message_bars = []

        self.plugin_dir = get_plugin_dir()

        self.setup()
        self.setupConnections()

    def setup(self):
        # Tabs
        self.tabWidget.setCurrentIndex(0)

        # Tab1
        self.update_server_combo_box()
        self.publishRadioButton.setChecked(True)
        self.update_slug_combo_box()
        self.mbSlugComboBox.setCurrentIndex(-1)

        self.cloneTemplateRadioButton.setChecked(True)
        self.updateButton.setEnabled(False)

        # Tab2
        # Server table
        serverTableHeaders = SERVER_TABLE_HEADERS
        self.serverTableWidget.setColumnCount(len(serverTableHeaders))
        self.serverTableWidget.setHorizontalHeaderLabels(serverTableHeaders)
        self.serverTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.update_server_table()

        # Buttons
        self.addServerConfigButton.setToolTip("Add server")
        self.editServerConfigButton.setToolTip("Edit server")
        self.removeServerConfigButton.setToolTip("Remove server")
        self.buttonBoxTab2.rejected.connect(self.reject)

    def setupConnections(self):
        self.tabWidget.currentChanged.connect(self.update_server_combo_box)
        self.publishRadioButton.clicked.connect(self.enable_publish_parameters)
        self.updateRadioButton.clicked.connect(self.disable_publish_parameters)
        self.publishButton.clicked.connect(self.publish_project)
        self.updateButton.clicked.connect(self.update_project)
        self.buttonBoxTab1.rejected.connect(self.reject)
        self.addServerConfigButton.clicked.connect(self.open_dialog_add_new_server_config)
        self.editServerConfigButton.clicked.connect(self.open_dialog_edit_server_config)
        self.removeServerConfigButton.clicked.connect(self.remove_server_config)

    def update_server_table(self):
        server_config_list = list_qgs_settings_child_groups("mapbender-plugin/connection")
        self.serverTableWidget.setRowCount(len(server_config_list))
        for i, (name) in enumerate(server_config_list):
            item_name = QTableWidgetItem(name)
            item_name.setText(server_config_list[i])
            self.serverTableWidget.setItem(i, 0, item_name)

            server_config = ServerConfig.getParamsFromSettings(name)

            item_url = QTableWidgetItem()
            item_url.setText(server_config.url)
            self.serverTableWidget.setItem(i, 1, item_url)

            item_path_qgis_projects = QTableWidgetItem()
            item_path_qgis_projects.setText(server_config.projects_path)
            self.serverTableWidget.setItem(i, 2, item_path_qgis_projects)

            item_mb_app_path = QTableWidgetItem()
            item_mb_app_path.setText(server_config.mb_app_path)
            self.serverTableWidget.setItem(i, 3, item_mb_app_path)

            item_mb_basis_url = QTableWidgetItem()
            item_mb_basis_url.setText(server_config.mb_basis_url)
            self.serverTableWidget.setItem(i, 4, item_mb_basis_url)

        self.update_server_combo_box()


    def update_server_combo_box(self) -> None:
        """ Updates the server configuration dropdown menu """
        # Read server configurations
        server_config_list = list_qgs_settings_child_groups(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection")
        if len(server_config_list) == 0:
            self.warningFirstServerLabel.show()
            self.serverComboBoxLabel.setText("Please add a server")
            self.serverConfigComboBox.clear()

        else:
            # Update server configuration-combobox
            self.serverComboBoxLabel.setText("Server")
            self.warningFirstServerLabel.hide()
            self.serverConfigComboBox.clear()
            self.serverConfigComboBox.addItems(server_config_list)

    def update_slug_combo_box(self):
        s = QgsSettings()
        if not s.contains(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/mb_templates"):
            return
        s.beginGroup(PLUGIN_SETTINGS_SERVER_CONFIG_KEY)
        mb_slugs = s.value('mb_templates')
        s.endGroup()
        if isinstance(mb_slugs, str):
            mb_slugs_list = mb_slugs.split(", ")
        else:
            mb_slugs_list = mb_slugs
        self.mbSlugComboBox.clear()
        if len(mb_slugs) > 0:
            self.mbSlugComboBox.addItems(mb_slugs_list)
            self.mbSlugComboBox.setCurrentIndex(-1)

    def disable_publish_parameters(self):
        self.mbParamsFrame.setEnabled(False)
        self.updateButton.setEnabled(True)
        self.publishButton.setEnabled(False)

    def enable_publish_parameters(self):
        self.mbParamsFrame.setEnabled(True)
        self.updateButton.setEnabled(False)
        self.publishButton.setEnabled(True)

    def open_dialog_add_new_server_config(self):
        new_server_config_dialog = AddServerConfigDialog()
        new_server_config_dialog.exec()
        self.update_server_table()
        self.update_server_combo_box()

    def open_dialog_edit_server_config(self):
        selected_row = self.serverTableWidget.currentRow()
        if selected_row == -1:
            return
        selected_server_config = self.serverTableWidget.item(selected_row, 0).text()
        edit_server_config_dialog = EditServerConfigDialog(selected_server_config)
        edit_server_config_dialog.exec()
        self.update_server_table()
        self.update_server_combo_box()

    def remove_server_config(self):
        selected_row = self.serverTableWidget.currentRow()
        if selected_row == -1:
            return
        selected_server_config = self.serverTableWidget.item(selected_row, 0).text()
        if show_question_box(f"Are you sure you want to remove the server configuration '{selected_server_config}'?") != QMessageBox.Yes:
            return
        try:
            s = QSettings()
            s.remove(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{selected_server_config}")
            show_succes_box_ok('Success', 'Server configuration successfully removed')
            self.update_server_table()
            self.update_server_combo_box()
        except Exception as e:
            show_fail_box_ok('Failed', "Server configuration could not be deleted (see log)")
            QgsMessageLog.logMessage(f"Server configuration could not be deleted ({e})", 'MapbenderPlugin', Qgis.Warning)
            raise

    def publish_project(self) -> None:
        # Check Mapbender params:
        if ((self.cloneTemplateRadioButton.isChecked() or self.addToAppRadioButton.isChecked()) and
                self.mbSlugComboBox.currentText() != ''):
            self.upload_project_qgis_server()
        else:
            show_fail_box_ok("Please complete Mapbender Parameters",
                                         "Please select clone template / add to existing application and enter a "
                                         "valid URL title")
            return

    def update_project(self):
        self.upload_project_qgis_server()

    def upload_project_qgis_server(self):
        # Config params:
        # Check config params / check connection
        selected_server_config = self.serverConfigComboBox.currentText()
        server_config = ServerConfig.getParamsFromSettings(selected_server_config)
        self.host = server_config.url
        self.port = server_config.port
        self.username = server_config.username
        self.password = server_config.password
        self.server_qgis_projects_folder_rel_path = server_config.projects_path
        self.mb_app_path = server_config.mb_app_path

        self.previous_message_bars = show_new_info_message_bar("Getting information from QGIS-Project ...", self.previous_message_bars)
        # iface.messageBar().pushMessage("", "Getting information from QGIS-Project ...", level=Qgis.Info, duration=2)
        if check_if_qgis_project(self.plugin_dir):
            # paths = get_paths(SERVER_QGIS_PROJECTS_FOLDER_REL_PATH)
            paths = get_paths(self.server_qgis_projects_folder_rel_path)
            source_project_dir_path = paths.get('source_project_dir_path')
            source_project_zip_dir_path = paths.get('source_project_zip_dir_path')
            qgis_project_folder_name = paths.get('qgis_project_folder_name')
            qgis_project_name = paths.get('qgis_project_name')
            server_project_dir_path = paths.get('server_project_dir_path')

            # getProjectLayers
            # Then check if folder exists on the server:
            self.previous_message_bars = show_new_info_message_bar("Connecting to server ...",
                                                                   self.previous_message_bars)
            # CHECK IF CONNECTION IS SUCCESSFUL AND THEN EXECUTE...
            if check_if_project_folder_exists_on_server(self.host, self.username, self.port, self.password,
                                                        self.plugin_dir, source_project_zip_dir_path,
                                                        self.server_qgis_projects_folder_rel_path, qgis_project_folder_name):
                # if return = True (folder already exists on server)
                if self.publishRadioButton.isChecked():
                    # project is supposed to be new and publish for the first time
                    if (show_fail_box_yes_no("Failed",
                                             f"Project directory already exists on the server. \n \nDo you want to"
                                             f" overwrite the existing project directory '{qgis_project_folder_name},' "
                                             f"update the WMS as source in Mapbender and add it to the given "
                                             f"application?")) == QMessageBox.Yes:
                        if remove_project_folder_from_server(self.host, self.username, self.port, self.password,
                                                             self.plugin_dir, self.server_qgis_projects_folder_rel_path,
                                                             qgis_project_folder_name):

                            zip_local_project_folder(self.plugin_dir, source_project_dir_path,
                                                     source_project_zip_dir_path, qgis_project_folder_name)

                            if upload_project_zip_file(self.host, self.username, self.port, self.password, self.plugin_dir,
                                                       source_project_zip_dir_path, self.server_qgis_projects_folder_rel_path,
                                                       qgis_project_folder_name):
                                self.previous_message_bars = show_new_info_message_bar("QGIS-Project folder successfully uploaded",
                                                                                       self.previous_message_bars)
                                # delete local zip folder
                                delete_local_project_zip_file(source_project_zip_dir_path)

                                if unzip_project_folder_on_server(self.host, self.username, self.port, self.password,
                                                                  qgis_project_folder_name, self.server_qgis_projects_folder_rel_path):
                                    # check "http://"
                                    wms_getcapabilities_url = (
                                            "http://" + self.host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                                            + self.server_qgis_projects_folder_rel_path + qgis_project_folder_name + '/' + qgis_project_name)

                                    self.previous_message_bars = show_new_info_message_bar(
                                        "WMS successfully created. Adding WMS as Mapbender source ...",
                                        self.previous_message_bars)
                                    # iface.messageBar().pushMessage("", "WMS successfully created. Adding WMS as "
                                    #                                    "Mapbender source ...",level=Qgis.Info, duration=2)

                                    self.mapbender_publish(wms_getcapabilities_url)
                else:
                    # Project is supposed to exist on the server and will not be published for the first time,
                    # but reloaded as a source in Mapbender
                    if remove_project_folder_from_server(self.host, self.username, self.port, self.password,
                                                         self.plugin_dir, self.server_qgis_projects_folder_rel_path,
                                                         qgis_project_folder_name):
                        self.previous_message_bars = show_new_info_message_bar(
                            "Updating QGIS project and data on server ...",
                            self.previous_message_bars)
                        # iface.messageBar().pushMessage("", "Updating QGIS project and data on server ...",
                        #                                level=Qgis.Info, duration=2)

                        zip_local_project_folder(self.plugin_dir, source_project_dir_path,
                                                 source_project_zip_dir_path, qgis_project_folder_name)

                        if upload_project_zip_file(self.host, self.username, self.port, self.password, self.plugin_dir,
                                                   source_project_zip_dir_path, self.server_qgis_projects_folder_rel_path,
                                                   qgis_project_folder_name):
                            if unzip_project_folder_on_server(self.host, self.username, self.port, self.password,
                                                              qgis_project_folder_name,
                                                              self.server_qgis_projects_folder_rel_path):
                                # check "http://"
                                wms_getcapabilities_url = (
                                        "http://" + self.host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                                        + self.server_qgis_projects_folder_rel_path + qgis_project_folder_name + '/' + qgis_project_name)
                                self.mb_update_wms(wms_getcapabilities_url)


            else:
                # if return = False (folder does not exist yet on the server)
                if self.publishRadioButton.isChecked(): # project is indeed new and will be uploaded to the server
                    iface.messageBar().pushMessage("", "Uploading QGIS project and data to server ...",
                                                   level=Qgis.Info, duration=2)
                    zip_local_project_folder(self.plugin_dir, source_project_dir_path,
                                             source_project_zip_dir_path, qgis_project_folder_name)
                    if upload_project_zip_file(self.host, self.username, self.port, self.password, self.plugin_dir,
                                               source_project_zip_dir_path, self.server_qgis_projects_folder_rel_path,
                                               qgis_project_folder_name):
                        if unzip_project_folder_on_server(self.host, self.username, self.port, self.password,
                                                          qgis_project_folder_name, self.server_qgis_projects_folder_rel_path):
                            wms_getcapabilities_url = (
                                    "http://" + self.host + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                                    + self.server_qgis_projects_folder_rel_path + qgis_project_folder_name + '/' + qgis_project_name)
                            self.mapbender_publish(wms_getcapabilities_url)
                # FAILBOX SHOWED NOT ONLY UNDER THIS CONDITION, ALSO IF NO CONNECTION IS SET
                else:
                    # project is supposed to exist on the server, and it does not -> user must select the option
                    # "Publish in Mapbender app"
                    show_fail_box_ok("Failed",
                        "Project directory " + qgis_project_folder_name + " does not exist on the server and therefore "
                                                                         "can not be updated. \n \nIf you want to upload a new"
                                                                         " QGIS-Project please select the option 'Publish "
                                                                         " in Mapbender app'")

    def mapbender_publish(self, wms_getcapabilities_url):
        # Mapbender params:
        if self.cloneTemplateRadioButton.isChecked():
            clone_app = True
        if self.addToAppRadioButton.isChecked():
            clone_app = False
        # Template slug:
        layer_set = self.layerSetLineEdit.text()

        iface.messageBar().pushMessage("", "Validating WMS ULR, checking if WMS URL is already set as Mapbender source, ...", level=Qgis.Info, duration=2)

        mapbender_uploader = MapbenderUpload(self.host, self.username, self.mb_app_path) # other parameters?

        exit_status_wms_show, sources_ids = mapbender_uploader.wms_show(wms_getcapabilities_url)
        if exit_status_wms_show == 0: # success
            # Reload source if it already exists
            if len(sources_ids)>0:
                for source_id in sources_ids:
                    exit_status_wms_reload = mapbender_uploader.wms_reload(source_id, wms_getcapabilities_url)
                source_id = sources_ids[-1]
            else:
                # Add source to Mapbender if it does not exist
                exit_status_wms_add, source_id = mapbender_uploader.wms_add(wms_getcapabilities_url)

                # Depending on user's input (duplicate template or use existing application):
            #if exit_status_wms_reload == 0 or exit_status_wms_add == 0:
            if clone_app:
                template_slug = self.mbSlugComboBox.currentText()
                exit_status_app_clone, slug, error = mapbender_uploader.app_clone(template_slug)
                if exit_status_app_clone == 0:
                    exit_status_wms_assign, output_wms_assign, error_wms_assign = (
                        mapbender_uploader.wms_assign(slug, source_id, layer_set))
                    print(exit_status_wms_assign, output_wms_assign, error_wms_assign)
                    update_mb_slug_in_settings(template_slug, is_mb_slug=True)
                    self.update_slug_combo_box()

                else:
                    show_fail_box_ok("Failed",
                                     f"Application could not be cloned.\n \n Error:  {error}")
                    update_mb_slug_in_settings(template_slug, is_mb_slug=False)
                    self.update_slug_combo_box()
                    return
            else:
                slug = self.mbSlugComboBox.currentText()
                exit_status_wms_assign, output_wms_assign, error_wms_assign = (
                    mapbender_uploader.wms_assign(slug, source_id, layer_set))
                print(exit_status_wms_assign, output_wms_assign, error_wms_assign)

            if exit_status_wms_assign == 0:
                show_succes_box_ok("Success report",
                                                "WMS succesfully created:\n \n" + wms_getcapabilities_url +
                                                "\n \n And added to mapbender application: \n \n" + "http://" +
                                                self.host + "/mapbender/application/" + slug)
                self.close()

            else:
                show_fail_box_ok("Failed",
                                 f"WMS could not be assigend to Mapbender application.\n{output_wms_assign}")

        mapbender_uploader.close_connection()

    def mb_update_wms(self, wms_getcapabilities_url):
        print('Mapbender update get capabilitites:')
        print(wms_getcapabilities_url)
        mapbender_uploader = MapbenderUpload(self.host, self.username, self.mb_app_path)
        print("mapbender_uploader instanziert")
        exit_status_wms_show, sources_ids = mapbender_uploader.wms_show(wms_getcapabilities_url)
        print("output wms_show")
        print(exit_status_wms_show, sources_ids)
        if exit_status_wms_show == 0:  # Success
            # Reload source if it already exists
            if len(sources_ids) > 0:
                for source_id in sources_ids:
                    exit_status_wms_reload, output, error_output = mapbender_uploader.wms_reload(source_id, wms_getcapabilities_url)
                    if exit_status_wms_reload == 0:  # Success
                        show_succes_box_ok("Success report" ,
                                               "WMS succesfully updated:\n \n"+ wms_getcapabilities_url +
                                               "\n \non Mapbender source(s): " + str(sources_ids))
                        self.close()
                    else:
                        show_fail_box_ok("Failed",
                                         f"WMS could not be reloaded. Reason {output} and {error_output}")
            else:
                show_fail_box_ok("Failed",
                                 f"WMS is not an existing source in Mapbender and could not be updated")
        else:  # Failed
            show_fail_box_ok("Failed",
                             f"No information for the given WMS could be displayed")
        mapbender_uploader.close_connection()










