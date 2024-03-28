import configparser
import os
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from qgis._core import QgsSettings

from mapbender_plugin.helpers import list_qgs_settings_child_groups, list_qgs_settings_values, show_succes_box_ok, \
    show_fail_box_ok
from mapbender_plugin.server_config import ServerConfig

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/edit_server_section_dialog.ui'))

class EditServerConfigDialog(BASE, WIDGET):
    def __init__(self, selected_section, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.editDialogButtonBox.accepted.connect(self.saveEditedServerConfig)
        self.editDialogButtonBox.rejected.connect(self.reject)

        self.getServerConfig(selected_section)

        server_config_sections = list_qgs_settings_child_groups("mapbender-plugin/connection")

    #def get...
    def getServerConfig(self, selected_section):
        self.selected_section = selected_section
        server_config = ServerConfig.getParamsFromSettings(selected_section)

        self.editServiceNameLineEdit.setText(selected_section)
        self.editPortLineEdit.setText(server_config.port)
        self.editServerAddressLineEdit.setText(server_config.url)
        self.editUserNameLineEdit.setText(server_config.username)
        self.editPasswordLineEdit.setText(server_config.password)
        self.editQgisProjectPathLineEdit.setText(server_config.projects_path)
        self.editMbPathLineEdit.setText(server_config.mb_app_path)
        self.editMbBasisUrlLineEdit.setText(server_config.mb_basis_url)

    def saveEditedServerConfig(self):
        # get edited values
        edit_section_name = self.editServiceNameLineEdit.text()
        edit_server_address = self.editServerAddressLineEdit.text()
        edit_port = self.editPortLineEdit.text()
        edit_user_name = self.editUserNameLineEdit.text()
        edit_password = self.editPasswordLineEdit.text()
        edit_server_qgis_projects_path = self.editQgisProjectPathLineEdit.text()
        edit_server_mb_app_path = self.editMbPathLineEdit.text()
        edit_mb_basis_url = self.editMbBasisUrlLineEdit.text()

        # check mandatory values
        if (not edit_section_name or not edit_server_address or not edit_server_qgis_projects_path
                or not edit_server_mb_app_path or not edit_mb_basis_url):
            show_fail_box_ok('Failed', 'Please fill in the mandatory fields')
        else:
            ServerConfig.saveToSettings(edit_section_name, edit_server_address, edit_port, edit_user_name, edit_password, edit_server_qgis_projects_path, edit_server_mb_app_path, edit_mb_basis_url)

            if (show_succes_box_ok('Success', 'Section successfully updated')) == QMessageBox.Ok:
                self.close()

            # if (show_fail_box_ok('Failed', 'Section could not be successfully updated')) == QMessageBox.Ok:
            #     self.close()




