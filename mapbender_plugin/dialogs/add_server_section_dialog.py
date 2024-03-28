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
    os.path.dirname(__file__), 'ui/add_server_section_dialog.ui'))


class AddServerSectionDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.addSectionDialogButtonBox.accepted.connect(self.saveNewConfigSection)
        self.addSectionDialogButtonBox.rejected.connect(self.reject)

    def saveNewConfigSection(self):
        new_section_name = self.newServiceNameLineEdit.text()
        new_server_address = self.newServerAddressLineEdit.text()
        new_port = self.newServerPortLineEdit.text()
        new_user_name = self.newUserNameLineEdit.text()
        new_password = self.newPasswordLineEdit.text()
        new_server_qgis_projects_path = self.newQgisProjectPathLineEdit.text()
        new_server_mb_app_path = self.newMbPathLineEdit.text()
        new_mb_basis_url = self.newMbBasisUrlLineEdit.text()

        if (not new_section_name or not new_server_address or not new_server_qgis_projects_path
                or not new_server_mb_app_path or not new_mb_basis_url):
            if (show_fail_box_ok('Failed', 'Please fill in the mandatory fields')) == QMessageBox.Ok:
                return

        if not validate_no_spaces(new_section_name, new_server_address, new_port, new_user_name, new_password,
                                  new_server_qgis_projects_path, new_server_mb_app_path, new_mb_basis_url):
            if (show_fail_box_ok('Failed', 'Fields should not have blank spaces')) == QMessageBox.Ok:
                return

        else:
        # check if name already exists and create a yes/no box (if existing: setValue: Sets the value of setting key to value. If the key already exists, the previous value is
        #             # # overwritten. An optional Section argument can be used to set a value to a specific Section.)

        # else:
            ServerConfig.saveToSettings(new_section_name, new_server_address, new_port, new_user_name, new_password, new_server_qgis_projects_path, new_server_mb_app_path, new_mb_basis_url)
            if (show_succes_box_ok('Success', 'New section successfully added')) == QMessageBox.Ok:
                self.close()

