import configparser
import os
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from PyQt5.uic.properties import QtGui
from qgis._core import QgsApplication, QgsSettings
from qgis.utils import iface

from mapbender_plugin.helpers import show_succes_box_ok, show_fail_box_ok

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/add_server_section_dialog.ui'))

class AddServerSectionDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.saveNewSectionButton.clicked.connect(self.saveNewConfigSection)
        self.addSectionDialogButtonBox.rejected.connect(self.reject)

        # # get config file path
        # self.file = os.path.dirname(__file__)
        # self.plugin_dir = os.path.dirname(self.file)

    def saveNewConfigSection(self):
        new_section_name = self.newServiceNameLineEdit.text()
        new_server_address = self.newServerAddressLineEdit.text()
        new_server_port = self.newServerPortLineEdit.text()
        new_user_name = self.newUserNameLineEdit.text()
        new_password = self.newPasswordLineEdit.text()

        try:
            #test
            s = QgsSettings()
            # setValue: Sets the value of setting key to value. If the key already exists, the previous value is
            # overwritten. An optional Section argument can be used to set a value to a specific Section.
            s.setValue(f"mapbender-plugin/connection/{new_section_name}/url", self.newServerAddressLineEdit.text())
            s.setValue(f"mapbender-plugin/connection/{new_section_name}/port", self.newServerPortLineEdit.text())
            s.setValue(f"mapbender-plugin/connection/{new_section_name}/username", self.newUserNameLineEdit.text())
            s.setValue(f"mapbender-plugin/connection/{new_section_name}/password", self.newPasswordLineEdit.text())

            if (show_succes_box_ok('Success', 'New section successfully added')) == QMessageBox.Ok:
                self.close()
        except:
            if (show_fail_box_ok('Failed', 'Section could not be added')) == QMessageBox.Ok:
                self.close()

        # except configparser.DuplicateSectionError:
        #     failBox = QMessageBox()
        #     failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
        #     failBox.setWindowTitle("Failed")
        #     failBox.setText("Section could not be added: section name already exists!")
        #     failBox.setStandardButtons(QMessageBox.Ok)
        #     result = failBox.exec_()
        #     if result == QMessageBox.Ok:
        #         self.close()


