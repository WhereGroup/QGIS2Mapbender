import configparser
import os
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from qgis._core import QgsSettings

from mapbender_plugin.helpers import list_qgs_settings_child_groups, list_qgs_settings_values, show_succes_box_ok, \
    show_fail_box_ok

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/edit_server_section_dialog.ui'))

class EditServerSectionDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.editDialogButtonBox.accepted.connect(self.saveEditedConfigSection)
        self.editDialogButtonBox.rejected.connect(self.reject)

        server_config_sections = list_qgs_settings_child_groups("mapbender-plugin/connection")

    def setServiceParameters(self, selected_section):
        self.selected_section = selected_section
        con_params = list_qgs_settings_values(selected_section)
        server_url = con_params['url']
        server_port = con_params['port']
        server_username = con_params['username']
        server_password = con_params['password']
        server_qgis_projects_path = con_params['projects_path']

        self.editServiceNameLineEdit.setText(selected_section)
        self.editPortLineEdit.setText(server_port)
        self.editServerAddressLineEdit.setText(server_url)
        self.editUserNameLineEdit.setText(server_username)
        self.editPasswordLineEdit.setText(server_password)
        self.editQgisProjectPathLineEdit.setText(server_qgis_projects_path)

    def saveEditedConfigSection(self):
        edited_section_name = self.editServiceNameLineEdit.text()
        edited_server_address = self.editServerAddressLineEdit.text()
        edited_port = self.editPortLineEdit.text()
        edited_user_name = self.editUserNameLineEdit.text()
        edited_password = self.editPasswordLineEdit.text()
        edited_server_qgis_projects_path = self.editQgisProjectPathLineEdit.text()

        s = QgsSettings()
        try:
            if edited_section_name != self.selected_section:
                s.remove(f"mapbender-plugin/connection/{self.selected_section}")

            s.setValue(f"mapbender-plugin/connection/{edited_section_name}/url", edited_server_address)
            s.setValue(f"mapbender-plugin/connection/{edited_section_name}/port", edited_port)
            s.setValue(f"mapbender-plugin/connection/{edited_section_name}/username", edited_user_name)
            s.setValue(f"mapbender-plugin/connection/{edited_section_name}/password", edited_password)
            s.setValue(f"mapbender-plugin/connection/{edited_section_name}/projects_path", edited_server_qgis_projects_path)

            if (show_succes_box_ok('Success', 'Section successfully updated')) == QMessageBox.Ok:
                self.close()
        except:
            if (show_fail_box_ok('Failed', 'Section could not be successfully updated')) == QMessageBox.Ok:
                self.close()




