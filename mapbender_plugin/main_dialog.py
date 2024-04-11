import os

from PyQt5.QtCore import QSettings, Qt, QRegExp

from PyQt5 import uic
from PyQt5.QtGui import QRegExpValidator

from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QHeaderView
from fabric2 import Connection

from qgis.core import Qgis, QgsSettings, QgsMessageLog

from mapbender_plugin.dialogs.server_config_dialog import serverConfigDialog
from mapbender_plugin.helpers import get_plugin_dir, \
    qgis_project_is_saved, \
    show_fail_box_ok, show_fail_box_yes_no, show_succes_box_ok, \
    list_qgs_settings_child_groups, show_question_box, \
    update_mb_slug_in_settings
from mapbender_plugin.mapbender import MapbenderUpload
from mapbender_plugin.paths import Paths
from mapbender_plugin.server_config import ServerConfig
from mapbender_plugin.settings import SERVER_TABLE_HEADERS, PLUGIN_SETTINGS_SERVER_CONFIG_KEY, TAG
from mapbender_plugin.upload import Upload

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

    def setup(self) -> None:
        # Tabs
        self.tabWidget.setCurrentIndex(0)

        # Tab1
        self.update_server_combo_box()
        self.publishRadioButton.setChecked(True)
        self.update_slug_combo_box()
        self.mbSlugComboBox.setCurrentIndex(-1)
        self.cloneTemplateRadioButton.setChecked(True)
        self.publishButton.setEnabled(False)  # Enabled only if mbSlugComboBox has a value
        self.updateButton.setEnabled(False)
        # QLineValidator for slug:
        regex_slug_layer_set = QRegExp("[^\\s;\\\\/]*")
        regex_slug_layer_set_validator = QRegExpValidator(regex_slug_layer_set)
        self.mbSlugComboBox.setValidator(regex_slug_layer_set_validator)
        self.layerSetLineEdit.setValidator(regex_slug_layer_set_validator)

        # Tab2
        server_table_headers = SERVER_TABLE_HEADERS
        self.serverTableWidget.setColumnCount(len(server_table_headers))
        self.serverTableWidget.setHorizontalHeaderLabels(server_table_headers)
        self.serverTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.update_server_table()

        # Buttons
        self.addServerConfigButton.setToolTip("Add server")
        self.editServerConfigButton.setToolTip("Edit server")
        self.removeServerConfigButton.setToolTip("Remove server")
        self.buttonBoxTab2.rejected.connect(self.reject)

    def setupConnections(self) -> None:
        self.tabWidget.currentChanged.connect(self.update_server_combo_box)
        self.publishRadioButton.clicked.connect(self.enable_publish_parameters)
        self.updateRadioButton.clicked.connect(self.disable_publish_parameters)
        self.mbSlugComboBox.lineEdit().textChanged.connect(self.validate_slug_not_empty)
        self.mbSlugComboBox.currentIndexChanged.connect(self.validate_slug_not_empty)
        self.publishButton.clicked.connect(self.publish_project)
        self.updateButton.clicked.connect(self.update_project)
        self.buttonBoxTab1.rejected.connect(self.reject)
        self.addServerConfigButton.clicked.connect(self.open_dialog_add_new_server_config)
        self.editServerConfigButton.clicked.connect(self.open_dialog_edit_server_config)
        self.removeServerConfigButton.clicked.connect(self.remove_server_config)

    def update_server_table(self) -> None:
        server_config_list = list_qgs_settings_child_groups(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection")
        self.serverTableWidget.setRowCount(len(server_config_list))
        for i, (name) in enumerate(server_config_list):
            item_name = QTableWidgetItem(name)
            item_name.setText(server_config_list[i])
            self.serverTableWidget.setItem(i, 0, item_name)

            server_config = ServerConfig.getParamsFromSettings(name)

            item_url = QTableWidgetItem()
            item_url.setText(server_config.url)
            self.serverTableWidget.setItem(i, 1, item_url)

            # Further columns (see settings.py SERVER_TABLE_HEADERS)
            # item_path_qgis_projects = QTableWidgetItem()
            # item_path_qgis_projects.setText(server_config.projects_path)
            # self.serverTableWidget.setItem(i, 2, item_path_qgis_projects)
            #
            # item_qgis_server_path = QTableWidgetItem()
            # item_qgis_server_path.setText(server_config.qgis_server_path)
            # self.serverTableWidget.setItem(i, 3, item_qgis_server_path)
            #
            # item_mb_app_path = QTableWidgetItem()
            # item_mb_app_path.setText(server_config.mb_app_path)
            # self.serverTableWidget.setItem(i, 4, item_mb_app_path)
            #
            # item_mb_basis_url = QTableWidgetItem()
            # item_mb_basis_url.setText(server_config.mb_basis_url)
            # self.serverTableWidget.setItem(i, 5, item_mb_basis_url)

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

    def update_slug_combo_box(self) -> None:
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

    def disable_publish_parameters(self) -> None:
        self.mbParamsFrame.setEnabled(False)
        self.updateButton.setEnabled(True)
        self.publishButton.setEnabled(False)

    def enable_publish_parameters(self) -> None:
        self.mbParamsFrame.setEnabled(True)
        self.updateButton.setEnabled(False)
        self.publishButton.setEnabled(True)

    def validate_slug_not_empty(self) -> None:
        """
        Enable the publish button only "URL Title" has a value
        :return:
        """
        self.publishButton.setEnabled(self.mbSlugComboBox.currentText() != '')
    def open_dialog_add_new_server_config(self) -> None:
        server_config_is_new = True
        new_server_config_dialog = serverConfigDialog(server_config_is_new, '')
        new_server_config_dialog.exec()
        self.update_server_table()
        self.update_server_combo_box()

    def open_dialog_edit_server_config(self) -> None:
        server_config_is_new = False
        selected_row = self.serverTableWidget.currentRow()
        if selected_row == -1:
            return
        selected_server_config = self.serverTableWidget.item(selected_row, 0).text()
        edit_server_config_dialog = serverConfigDialog(server_config_is_new, selected_server_config)
        edit_server_config_dialog.exec()
        self.update_server_table()
        self.update_server_combo_box()

    def remove_server_config(self) -> None:
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
        if not qgis_project_is_saved():
            return
        # Check Mapbender params:
        if self.mbSlugComboBox.currentText() == '':
            show_fail_box_ok("Please complete Mapbender parameters",
                             "Please enter a valid Mapbender URL title")
            return
        self.upload_project_qgis_server()

    def update_project(self) -> None:
        if not qgis_project_is_saved():
            return
        self.upload_project_qgis_server()

    def upload_project_qgis_server(self) -> None:
        # Get server config params and project paths
        server_config = ServerConfig.getParamsFromSettings(self.serverConfigComboBox.currentText())
        paths = Paths.get_paths(server_config.projects_path)

        if server_config.windows_pk_path == '':
            connect_kwargs = {"password": server_config.password}
        else:
            connect_kwargs = {"password": server_config.password,
                              "key_filename": server_config.windows_pk_path}

        with Connection(host=server_config.url, user=server_config.username, port=server_config.port,
                        connect_kwargs=connect_kwargs) as connection:
            try:
                connection.open()
            except Exception as e:
                show_fail_box_ok("Connection failed", f"Connection failed. Reason: {e}")
                return

            upload = Upload(connection, paths)
            wms_url = upload.get_wms_url(server_config)
            project_folder_exists_on_server = upload.check_if_project_folder_exists_on_server()
            # User's input = publish
            if project_folder_exists_on_server and self.publishRadioButton.isChecked():
                if show_fail_box_yes_no("Failed",
                                        f"Project directory already exists on the server. \n \nDo you want to"
                                        f" overwrite the existing project directory '{paths.source_project_dir_name},' "
                                        f"update the WMS as source in Mapbender and add it to the given "
                                        f"application?") == QMessageBox.No:
                    return
                if not upload.remove_project_folder_from_server():
                    return
                if not upload.zip_upload_unzip_clean():
                    return
                QgsMessageLog.logMessage(f"WMS get capabilitites URL: {wms_url}", TAG,
                                         level=Qgis.Info)
                self.mb_publish(connection, server_config, wms_url)
            # User's input = update
            if project_folder_exists_on_server and self.updateRadioButton.isChecked():
                if not upload.remove_project_folder_from_server():
                    return
                if not upload.zip_upload_unzip_clean():
                    return
                self.mb_update(connection, server_config, wms_url)
            if not project_folder_exists_on_server and self.publishRadioButton.isChecked():
                if not upload.zip_upload_unzip_clean():
                    return
                QgsMessageLog.logMessage(f"WMS get capabilitites URL: {wms_url}", TAG,
                                         level=Qgis.Info)
                self.mb_publish(connection, server_config, wms_url)
            if not project_folder_exists_on_server and self.updateRadioButton.isChecked():
                show_fail_box_ok("Failed",
                                 "Project directory " + paths.source_project_dir_name + " does not exist on the server and therefore "
                                                                                        "can not be updated. \n \nIf you want to upload a new"
                                                                                        " QGIS-Project please select the option 'Publish "
                                                                                        " in Mapbender app'")

    def mb_publish(self, connection, server_config, wms_url):
        # Get Mapbender params:
        if self.cloneTemplateRadioButton.isChecked():
            clone_app = True
        if self.addToAppRadioButton.isChecked():
            clone_app = False
        # Template slug:
        layer_set = self.layerSetLineEdit.text()

        mapbender_uploader = MapbenderUpload(connection, server_config, wms_url)

        exit_status_wms_show, sources_ids = mapbender_uploader.wms_show()
        if exit_status_wms_show == 1:  ## Failed
            show_fail_box_ok("Failed",
                             f"WMS layer information could not be displayed. "
                             f"Mapbender upload will be interrupted.")
            return

        if len(sources_ids) > 0:  # URL exists one or multiple times as Mapbender source: reload
            exit_status_wms_reload_list = []
            for source_id in sources_ids:
                exit_status_wms_reload, output, error = mapbender_uploader.wms_reload(source_id)
                exit_status_wms_reload_list.append(exit_status_wms_reload)
            if not all(exit_status_wms_reload == 0 for exit_status_wms_reload in exit_status_wms_reload_list):
                show_fail_box_ok("Failed",
                                 f"QGIS-Project is successfuly uploaded to the server but WMS could not be reloaded in Mapbender.")
                return
            # Default: source (or source with higher ID, if multiple IDs) will be selected be added to the given Mapbender application
            source_id = sources_ids[-1]
        else:
            # Source does not exist yet in Mapbender: add
            exit_status_wms_add, source_id, error = mapbender_uploader.wms_add()
            if exit_status_wms_add != 0:
                show_fail_box_ok("Failed",
                                 f"QGIS-Project is successfuly uploaded to the server but WMS could not be added to "
                                 f"Mapbender. Reason: {error}")
                return

        if clone_app:  # The given Mapbender's template app will be cloned and the WMS will be assigned to the cloned
            # app
            template_slug = self.mbSlugComboBox.currentText()
            exit_status_app_clone, slug, error = mapbender_uploader.app_clone(template_slug)
            if exit_status_app_clone != 0:
                show_fail_box_ok("Failed",
                                 f"Application could not be cloned.\n \n Error:  {error}")
                update_mb_slug_in_settings(template_slug, is_mb_slug=False)
                self.update_slug_combo_box()
                return
            update_mb_slug_in_settings(template_slug, is_mb_slug=True)
            self.update_slug_combo_box()

            exit_status_wms_assign, output_wms_assign, error_wms_assign = (
                mapbender_uploader.wms_assign(slug, source_id, layer_set))

        else:  # The WMS will be assigned to the given Mapbender app
            slug = self.mbSlugComboBox.currentText()
            exit_status_wms_assign, output_wms_assign, error_wms_assign = (
                mapbender_uploader.wms_assign(slug, source_id, layer_set))

        if exit_status_wms_assign != 0:
            show_fail_box_ok("Failed",
                             f"WMS could not be assigned to Mapbender application.\nReason: Exit status: {exit_status_wms_assign} \n"
                             f"Output: {output_wms_assign}.\n Error: {error_wms_assign}")
            return

        show_succes_box_ok("Success report",
                           "WMS successfully created:\n \n" + wms_url +
                           "\n \n And added to Mapbender application: \n \n" + "http://" +
                           server_config.url + "/mapbender/application/" + slug)
        self.close()

    def mb_update(self, connection, server_config, wms_url):
        mapbender_uploader = MapbenderUpload(connection, server_config, wms_url)
        exit_status_wms_show, sources_ids = mapbender_uploader.wms_show()
        QgsMessageLog.logMessage(f"Output wms_show: {exit_status_wms_show}, {sources_ids}", TAG,
                                 level=Qgis.Info)
        if exit_status_wms_show != 0:
            show_fail_box_ok("Failed",
                             f"WMS layer information could not be displayed. "
                             f"Mapbender upload will be interrupted.")
            return
        if len(sources_ids) == 0:
            show_fail_box_ok("Failed",
                             f"WMS is not an existing source in Mapbender and could not be updated")
        # URL exists one or multiple times as Mapbender source: reload
        exit_status_wms_reload_list = []
        for source_id in sources_ids:
            exit_status_wms_reload, output, error = mapbender_uploader.wms_reload(source_id)
            exit_status_wms_reload_list.append(exit_status_wms_reload)
        if not all(exit_status_wms_reload == 0 for exit_status_wms_reload in exit_status_wms_reload_list):
            show_fail_box_ok("Failed",
                             f"QGIS-Project is successfuly uploaded to the server but WMS could not be reloaded in Mapbender. "
                             f"Reason {output} and {error}. "
                             f"Mapbender upload will be interrupted.")
            return
        show_succes_box_ok("Success report",
                           "WMS succesfully updated:\n \n" + wms_url +
                           "\n \non Mapbender source(s): " + str(sources_ids))
        self.close()


