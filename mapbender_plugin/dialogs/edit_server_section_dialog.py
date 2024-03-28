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

class EditServerConfigDialog(BASE, WIDGET):
    def __init__(self, selected_section, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.editDialogButtonBox.accepted.connect(self.saveEditedServerConfig)
        self.editDialogButtonBox.rejected.connect(self.reject)

        self.setServerConfig(selected_section)

        server_config_sections = list_qgs_settings_child_groups("mapbender-plugin/connection")

    #def get...
    def setServerConfig(self, selected_section):
        self.selected_section = selected_section
        server_params = list_qgs_settings_values(selected_section)
        server_url = server_params['url']
        #server_url = connection.url
        server_port = server_params['port']
        server_username = server_params['username']
        server_password = server_params['password']
        server_qgis_projects_path = server_params['projects_path']
        server_mapbender_app_path = server_params['mapbender_app_path']
        mapbender_basis_url = server_params['mapbender_basis_url']

    #def set...

        self.editServiceNameLineEdit.setText(selected_section)
        self.editPortLineEdit.setText(server_port)
        self.editServerAddressLineEdit.setText(server_url)
        self.editUserNameLineEdit.setText(server_username)
        self.editPasswordLineEdit.setText(server_password)
        self.editQgisProjectPathLineEdit.setText(server_qgis_projects_path)
        self.editMbPathLineEdit.setText(server_mapbender_app_path)
        self.editMbBasisUrlLineEdit.setText(mapbender_basis_url)

    def saveEditedServerConfig(self):
        # get edited values
        edited_section_name = self.editServiceNameLineEdit.text()
        edited_server_address = self.editServerAddressLineEdit.text()
        edited_port = self.editPortLineEdit.text()
        edited_user_name = self.editUserNameLineEdit.text()
        edited_password = self.editPasswordLineEdit.text()
        edited_server_qgis_projects_path = self.editQgisProjectPathLineEdit.text()
        edited_server_mapbender_app_path = self.editMbPathLineEdit.text()
        edited_mapbender_basis_url = self.editMbBasisUrlLineEdit.text()

        # check mandatory values
        if (not edited_section_name or not edited_server_address or not edited_server_qgis_projects_path
                or not edited_server_mapbender_app_path or not edited_mapbender_basis_url):
            show_fail_box_ok('Failed', 'Please fill in the mandatory fields')
        else:
            s = QgsSettings()
            try:
                if edited_section_name != self.selected_section:
                    s.remove(f"mapbender-plugin/connection/{self.selected_section}")

                s.setValue(f"mapbender-plugin/connection/{edited_section_name}/url", edited_server_address)
                s.setValue(f"mapbender-plugin/connection/{edited_section_name}/port", edited_port)
                s.setValue(f"mapbender-plugin/connection/{edited_section_name}/username", edited_user_name)
                s.setValue(f"mapbender-plugin/connection/{edited_section_name}/password", edited_password)
                s.setValue(f"mapbender-plugin/connection/{edited_section_name}/projects_path",
                           edited_server_qgis_projects_path)
                s.setValue(f"mapbender-plugin/connection/{edited_section_name}/mapbender_app_path",
                           edited_server_mapbender_app_path)
                s.setValue(f"mapbender-plugin/connection/{edited_section_name}/mapbender_basis_url",
                           edited_mapbender_basis_url)


                if (show_succes_box_ok('Success', 'Section successfully updated')) == QMessageBox.Ok:
                    self.close()
            except:
                if (show_fail_box_ok('Failed', 'Section could not be successfully updated')) == QMessageBox.Ok:
                    self.close()




