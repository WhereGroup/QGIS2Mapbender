import configparser
import os
from PyQt5 import uic

from mapbender_plugin.helpers import list_qgs_settings_child_groups, show_succes_box_ok, \
    show_fail_box_ok, validate_no_spaces
from mapbender_plugin.server_config import ServerConfig

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/server_config_dialog.ui'))

class serverConfigDialog(BASE, WIDGET):
    def __init__(self, server_config_is_new, selected_server_config, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setupConnections(server_config_is_new)
        if not server_config_is_new:
            self.getSavedServerConfig(selected_server_config)

    def setupConnections(self, server_config_is_new):
        if not server_config_is_new:
            self.dialogButtonBox.accepted.connect(self.saveEditedServerConfig)
        else:
            self.dialogButtonBox.accepted.connect(self.saveNewServerConfig)
        self.dialogButtonBox.rejected.connect(self.reject)

    def getSavedServerConfig(self, selected_server_config):
        self.selected_server_config = selected_server_config
        server_config = ServerConfig.getParamsFromSettings(selected_server_config)
        self.authcfg = server_config.authcfg

        self.serverConfigNameLineEdit.setText(selected_server_config)
        self.serverPortLineEdit.setText(server_config.port)
        self.serverAddressLineEdit.setText(server_config.url)
        self.userNameLineEdit.setText(server_config.username)
        self.passwordLineEdit.setText(server_config.password)
        self.qgisProjectPathLineEdit.setText(server_config.projects_path)
        self.qgisServerPathLineEdit.setText(server_config.qgis_server_path)
        self.mbPathLineEdit.setText(server_config.mb_app_path)
        self.mbBasisUrlLineEdit.setText(server_config.mb_basis_url)

    def saveEditedServerConfig(self):
        serverConfig = self.getEditedServerConfig()
        self.checkConfig(serverConfig)

    def saveNewServerConfig(self):
        serverConfig = self.getNewServerConfigFromFormular()
        self.checkConfig(serverConfig)

    def getNewServerConfigFromFormular(self) -> ServerConfig:
        new_server_config_name = self.serverConfigNameLineEdit.text()
        new_server_address = self.serverAddressLineEdit.text()
        new_port = self.serverPortLineEdit.text()
        new_user_name = self.userNameLineEdit.text()
        new_password = self.passwordLineEdit.text()
        new_server_qgis_projects_path = self.qgisProjectPathLineEdit.text()
        new_qgis_server_path = self.qgisServerPathLineEdit.text()
        new_server_mb_app_path = self.mbPathLineEdit.text()
        new_mb_basis_url = self.mbBasisUrlLineEdit.text()
        authcfg = ''

        return ServerConfig(
            name=new_server_config_name,
            url=new_server_address,
            port=new_port,
            username=new_user_name,
            password=new_password,
            projects_path=new_server_qgis_projects_path,
            qgis_server_path=new_qgis_server_path,
            mb_app_path=new_server_mb_app_path,
            mb_basis_url=new_mb_basis_url,
            authcfg=authcfg
        )

    def getEditedServerConfig(self) -> ServerConfig:
        edit_server_config_name = self.serverConfigNameLineEdit.text()
        edit_server_address = self.serverAddressLineEdit.text()
        edit_port = self.serverPortLineEdit.text()
        edit_user_name = self.userNameLineEdit.text()
        edit_password = self.passwordLineEdit.text()
        edit_server_qgis_projects_path = self.qgisProjectPathLineEdit.text()
        edit_qgis_server_path = self.qgisServerPathLineEdit.text()
        edit_server_mb_app_path = self.mbPathLineEdit.text()
        edit_mb_basis_url = self.mbBasisUrlLineEdit.text()
        return ServerConfig(
            name=edit_server_config_name,
            url=edit_server_address,
            port=edit_port,
            username=edit_user_name,
            password=edit_password,
            projects_path=edit_server_qgis_projects_path,
            qgis_server_path=edit_qgis_server_path,
            mb_app_path=edit_server_mb_app_path,
            mb_basis_url=edit_mb_basis_url,
            authcfg=self.authcfg
        )

    def checkConfig(self, serverConfig: ServerConfig) -> None:
        mandatoryFields = [serverConfig.name, serverConfig.url, serverConfig.projects_path, serverConfig.qgis_server_path, serverConfig.mb_app_path,
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





