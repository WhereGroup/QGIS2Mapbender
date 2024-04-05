import os

from PyQt5.QtCore import QSettings, Qt

from PyQt5 import uic

from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QHeaderView

from qgis._core import Qgis, QgsSettings, QgsMessageLog

from qgis.utils import iface

from mapbender_plugin.dialogs.add_server_config_dialog import AddServerConfigDialog
from mapbender_plugin.dialogs.edit_server_config_dialog import EditServerConfigDialog
from mapbender_plugin.helpers import get_plugin_dir, get_project_layers, \
    check_if_qgis_project, get_paths, zip_local_project_folder, upload_project_zip_file, \
    remove_project_folder_from_server, \
    check_if_project_folder_exists_on_server, unzip_project_folder_on_server, check_uploaded_files, \
    get_get_capabilities_url, show_fail_box_ok, show_fail_box_yes_no, show_succes_box_ok, \
    list_qgs_settings_child_groups, show_question_box, \
    update_mb_slug_in_settings, delete_local_project_zip_file, waitCursor, open_connection, upload
from mapbender_plugin.mapbender import MapbenderUpload
from mapbender_plugin.server_config import ServerConfig
from mapbender_plugin.settings import SERVER_TABLE_HEADERS, PLUGIN_SETTINGS_SERVER_CONFIG_KEY, TAG

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialogs/ui/main_dialog.ui'))


class MainDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

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
        if show_question_box(
                f"Are you sure you want to remove the server configuration '{selected_server_config}'?") != QMessageBox.Yes:
            return
        try:
            s = QSettings()
            s.remove(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{selected_server_config}")
            show_succes_box_ok('Success', 'Server configuration successfully removed')
            self.update_server_table()
            self.update_server_combo_box()
        except Exception as e:
            show_fail_box_ok('Failed', "Server configuration could not be deleted (see log)")
            QgsMessageLog.logMessage(f"Server configuration could not be deleted ({e})", TAG,
                                     Qgis.Warning)
            raise

    def publish_project(self) -> None:
        if not check_if_qgis_project():
            return
        # Check Mapbender params:
        if self.mbSlugComboBox.currentText() == '':
            show_fail_box_ok("Please complete Mapbender parameters",
                             "Please enter a valid Mapbender URL title")
            return
        with waitCursor():
            self.upload_project_qgis_server()


    def update_project(self):
        if not check_if_qgis_project():
            return
        with waitCursor():
            self.upload_project_qgis_server()

    def upload_project_qgis_server(self):
        # Get config params
        selected_server_config = self.serverConfigComboBox.currentText()
        server_config = ServerConfig.getParamsFromSettings(selected_server_config)

        # Get paths
        paths = get_paths(server_config.projects_path)
        source_project_dir_path = paths.get('source_project_dir_path')
        source_project_zip_dir_path = paths.get('source_project_zip_dir_path')
        qgis_project_folder_name = paths.get('qgis_project_folder_name')
        qgis_project_name = paths.get('qgis_project_name')
        server_project_dir_path = paths.get('server_project_dir_path')

        # Check "http://"
        wms_getcapabilities_url = (
                "http://" + server_config.url + "/cgi-bin/qgis_mapserv.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&map="
                + server_config.projects_path + qgis_project_folder_name + '/' + qgis_project_name)

        # getProjectLayers

        # Open connection
        c = open_connection(server_config.url, server_config.username, server_config.port, server_config.password)
        if not c:
            return
        with c:
            project_folder_exists_on_server = check_if_project_folder_exists_on_server(c,
                                                          server_config.projects_path,
                                                          qgis_project_folder_name)
            if project_folder_exists_on_server and self.publishRadioButton.isChecked():
                if (show_fail_box_yes_no("Failed",
                                         f"Project directory already exists on the server. \n \nDo you want to"
                                         f" overwrite the existing project directory '{qgis_project_folder_name},' "
                                         f"update the WMS as source in Mapbender and add it to the given "
                                         f"application?")) == QMessageBox.No:
                    return
                else:
                    remove_project_folder_from_server(c, server_config.projects_path, qgis_project_folder_name)
                    upload(c, server_config.projects_path, qgis_project_folder_name,
                           source_project_dir_path,
                           source_project_zip_dir_path)
                    self.mb_publish(wms_getcapabilities_url)
            if project_folder_exists_on_server and self.updateRadioButton.isChecked():
                remove_project_folder_from_server(c, server_config.projects_path, qgis_project_folder_name)
                upload(c, server_config.projects_path, qgis_project_folder_name,
                       source_project_dir_path,
                       source_project_zip_dir_path)
                self.mb_update(wms_getcapabilities_url)
            if not project_folder_exists_on_server and self.publishRadioButton.isChecked():
                upload(c, server_config.projects_path, qgis_project_folder_name,
                       source_project_dir_path,
                       source_project_zip_dir_path)
                self.mb_publish(wms_getcapabilities_url)
            if not project_folder_exists_on_server and self.updateRadioButton.isChecked():
                show_fail_box_ok("Failed",
                                 "Project directory " + qgis_project_folder_name + " does not exist on the server and therefore "
                                                                                   "can not be updated. \n \nIf you want to upload a new"
                                                                                   " QGIS-Project please select the option 'Publish "
                                                                                   " in Mapbender app'")

    # TEST MB PUBLISH AND UPDATE WITH opened "c"
    def mb_publish(self, wms_getcapabilities_url):
        # Mapbender params:
        if self.cloneTemplateRadioButton.isChecked():
            clone_app = True
        if self.addToAppRadioButton.isChecked():
            clone_app = False
        # Template slug:
        layer_set = self.layerSetLineEdit.text()

        QgsMessageLog.logMessage("Validating WMS ULR, checking if WMS URL is already set as Mapbender source, ...", TAG,
                                 level=Qgis.Info)

        mapbender_uploader = MapbenderUpload(self.host, self.username, self.mb_app_path)  # other parameters?

        exit_status_wms_show, sources_ids = mapbender_uploader.wms_show(wms_getcapabilities_url)
        if exit_status_wms_show == 0:  # success
            # Reload source if it already exists
            if len(sources_ids) > 0:
                for source_id in sources_ids:
                    exit_status_wms_reload = mapbender_uploader.wms_reload(source_id, wms_getcapabilities_url)
                source_id = sources_ids[-1]
            else:
                # Add source to Mapbender if it does not exist
                exit_status_wms_add, source_id = mapbender_uploader.wms_add(wms_getcapabilities_url)

                # Depending on user's input (duplicate template or use existing application):
            # if exit_status_wms_reload == 0 or exit_status_wms_add == 0:
            if clone_app:
                template_slug = self.mbSlugComboBox.currentText()
                exit_status_app_clone, slug, error = mapbender_uploader.app_clone(template_slug)
                if exit_status_app_clone == 0:
                    exit_status_wms_assign, output_wms_assign, error_wms_assign = (
                        mapbender_uploader.wms_assign(slug, source_id, layer_set))
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

    def mb_update(self, wms_getcapabilities_url):
        QgsMessageLog.logMessage(f"Mapbender update get capabilitites: {wms_getcapabilities_url}", TAG,
                                 level=Qgis.Info)
        mapbender_uploader = MapbenderUpload(self.host, self.username, self.mb_app_path)
        QgsMessageLog.logMessage("Mapbender uploader instanced", TAG,
                                 level=Qgis.Info)
        exit_status_wms_show, sources_ids = mapbender_uploader.wms_show(wms_getcapabilities_url)
        QgsMessageLog.logMessage(f"Output wms_show: {exit_status_wms_show}, {sources_ids}", TAG,
                                 level=Qgis.Info)
        if exit_status_wms_show == 0:  # Success
            # Reload source if it already exists
            if len(sources_ids) > 0:
                for source_id in sources_ids:
                    exit_status_wms_reload, output, error_output = mapbender_uploader.wms_reload(source_id,
                                                                                                 wms_getcapabilities_url)
                    if exit_status_wms_reload == 0:  # Success
                        show_succes_box_ok("Success report",
                                           "WMS succesfully updated:\n \n" + wms_getcapabilities_url +
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
