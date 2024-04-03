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

        self.addServerConfigDialogButtonBox.accepted.connect(self.save_new_server_config)
        self.addServerConfigDialogButtonBox.rejected.connect(self.reject)

    def save_new_server_config(self):
        new_server_config_name = self.newServerConfigNameLineEdit.text()
        new_server_address = self.newServerAddressLineEdit.text()
        new_port = self.newServerPortLineEdit.text()
        new_user_name = self.newUserNameLineEdit.text()
        new_password = self.newPasswordLineEdit.text()
        new_server_qgis_projects_path = self.newQgisProjectPathLineEdit.text()
        new_server_mb_app_path = self.newMbPathLineEdit.text()
        new_mb_basis_url = self.newMbBasisUrlLineEdit.text()

        if (not new_server_config_name or not new_server_address or not new_server_qgis_projects_path
                or not new_server_mb_app_path or not new_mb_basis_url):
            show_fail_box_ok('Failed', 'Please fill in the mandatory fields (*)')
            return

        if not validate_no_spaces(new_server_config_name, new_server_address, new_port, new_user_name, new_password,
                                  new_server_qgis_projects_path, new_server_mb_app_path, new_mb_basis_url):
            show_fail_box_ok('Failed', 'Fields should not have blank spaces')
            return

        else:
        # check if name already exists and create a yes/no box (if existing: setValue: Sets the value of setting key to value. If the key already exists, the previous value is
        #             # # overwritten. An optional Section argument can be used to set a value to a specific Section.)

        # else:
            ServerConfig.saveToSettings(new_server_config_name, new_server_address, new_port, new_user_name, new_password, new_server_qgis_projects_path, new_server_mb_app_path, new_mb_basis_url)
            show_succes_box_ok('Success', 'New server configuration successfully added')
            self.close()

