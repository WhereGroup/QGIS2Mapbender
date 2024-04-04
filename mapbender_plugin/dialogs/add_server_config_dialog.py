import configparser
import os
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from PyQt5.uic.properties import QtGui
from qgis._core import QgsApplication, QgsSettings
from qgis.utils import iface

from mapbender_plugin.helpers import show_succes_box_ok, show_fail_box_ok, validate_no_spaces, validate_no_spaces
from mapbender_plugin.server_config import ServerConfig

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/add_server_config_dialog.ui'))


class AddServerConfigDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setupConnections()

    def setupConnections(self):
        self.addServerConfigDialogButtonBox.accepted.connect(self.saveNewServerConfig)
        self.addServerConfigDialogButtonBox.rejected.connect(self.reject)

    def saveNewServerConfig(self):
        serverConfig = self.getNewServerConfig()
        self.checkConfig(serverConfig)

    def getNewServerConfig(self) -> ServerConfig:
        new_server_config_name = self.newServerConfigNameLineEdit.text()
        new_server_address = self.newServerAddressLineEdit.text()
        new_port = self.newServerPortLineEdit.text()
        new_user_name = self.newUserNameLineEdit.text()
        new_password = self.newPasswordLineEdit.text()
        new_server_qgis_projects_path = self.newQgisProjectPathLineEdit.text()
        new_server_mb_app_path = self.newMbPathLineEdit.text()
        new_mb_basis_url = self.newMbBasisUrlLineEdit.text()
        return ServerConfig(
            name=new_server_config_name,
            url=new_server_address,
            port=new_port,
            username=new_user_name,
            password=new_password,
            projects_path=new_server_qgis_projects_path,
            mb_app_path=new_server_mb_app_path,
            mb_basis_url=new_mb_basis_url
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