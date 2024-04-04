import configparser
import os
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from qgis._core import QgsSettings

from mapbender_plugin.helpers import list_qgs_settings_child_groups, show_succes_box_ok, \
    show_fail_box_ok, validate_no_spaces
from mapbender_plugin.server_config import ServerConfig

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/edit_server_config_dialog.ui'))

class EditServerConfigDialog(BASE, WIDGET):
    def __init__(self, selected_server_config, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setupConnections()

        self.getServerConfig(selected_server_config)

    def setupConnections(self):
        self.editDialogButtonBox.accepted.connect(self.saveEditedServerConfig)
        self.editDialogButtonBox.rejected.connect(self.reject)

    #def get...
    def getServerConfig(self, selected_server_config):
        self.selected_server_config = selected_server_config
        server_config = ServerConfig.getParamsFromSettings(selected_server_config)

        self.editServerConfigNameLineEdit.setText(selected_server_config)
        self.editPortLineEdit.setText(server_config.port)
        self.editServerAddressLineEdit.setText(server_config.url)
        self.editUserNameLineEdit.setText(server_config.username)
        self.editPasswordLineEdit.setText(server_config.password)
        self.editQgisProjectPathLineEdit.setText(server_config.projects_path)
        self.editMbPathLineEdit.setText(server_config.mb_app_path)
        self.editMbBasisUrlLineEdit.setText(server_config.mb_basis_url)

    def saveEditedServerConfig(self):
        serverConfig = self.getEditedServerConfig()
        self.checkConfig(serverConfig)

    def getEditedServerConfig(self) -> ServerConfig:
        edit_server_config_name = self.editServerConfigNameLineEdit.text()
        edit_server_address = self.editServerAddressLineEdit.text()
        edit_port = self.editPortLineEdit.text()
        edit_user_name = self.editUserNameLineEdit.text()
        edit_password = self.editPasswordLineEdit.text()
        edit_server_qgis_projects_path = self.editQgisProjectPathLineEdit.text()
        edit_server_mb_app_path = self.editMbPathLineEdit.text()
        edit_mb_basis_url = self.editMbBasisUrlLineEdit.text()
        return ServerConfig(
            name=edit_server_config_name,
            url=edit_server_address,
            port=edit_port,
            username=edit_user_name,
            password=edit_password,
            projects_path=edit_server_qgis_projects_path,
            mb_app_path=edit_server_mb_app_path,
            mb_basis_url=edit_mb_basis_url
        )

    def checkConfig(self, serverConfig: ServerConfig) -> None:
        mandatoryFields = [serverConfig.name, serverConfig.url, serverConfig.projects_path, serverConfig.mb_app_path,
                           serverConfig.mb_basis_url]

        if not all(mandatoryFields):
            show_fail_box_ok('Failed', 'Please fill in the mandatory fields')
            return

        if not serverConfig.isValid():
            show_fail_box_ok('Failed', 'Fields should not have blank spaces')
            return

        serverConfig.save()

        show_succes_box_ok('Success', 'Server configuration successfully updated')
        self.close()
        return





