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
        self.setupConnections()
        self.server_config_is_new = server_config_is_new
        if not self.server_config_is_new:
            self.getSavedServerConfig(selected_server_config)

    def setupConnections(self):
        self.dialogButtonBox.accepted.connect(self.saveServerConfig)
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

    def getServerConfigFromFormular(self) -> ServerConfig:
        server_config_name = self.serverConfigNameLineEdit.text()
        server_address = self.serverAddressLineEdit.text()
        port = self.serverPortLineEdit.text()
        user_name = self.userNameLineEdit.text()
        password = self.passwordLineEdit.text()
        server_qgis_projects_path = self.qgisProjectPathLineEdit.text()
        qgis_server_path = self.qgisServerPathLineEdit.text()
        server_mb_app_path = self.mbPathLineEdit.text()
        mb_basis_url = self.mbBasisUrlLineEdit.text()
        if self.server_config_is_new:
            # authcfg will be set after saving the basic auth params in the auth_db
            self.authcfg = ''
        return ServerConfig(
            name=server_config_name,
            url=server_address,
            port=port,
            username=user_name,
            password=password,
            projects_path=server_qgis_projects_path,
            qgis_server_path=qgis_server_path,
            mb_app_path=server_mb_app_path,
            mb_basis_url=mb_basis_url,
            authcfg=self.authcfg
        )


    def checkConfig(self, serverConfig: ServerConfig) -> None:
        mandatoryFields = [serverConfig.name, serverConfig.url, serverConfig.projects_path,
                           serverConfig.qgis_server_path, serverConfig.mb_app_path,
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

    def saveServerConfig(self):
        serverConfig = self.getServerConfigFromFormular()
        self.checkConfig(serverConfig)




