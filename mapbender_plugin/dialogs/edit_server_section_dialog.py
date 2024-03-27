import configparser
import os
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from qgis._core import QgsSettings

from mapbender_plugin.helpers import list_qgs_settings_child_groups, list_qgs_settings_values

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/edit_server_section_dialog.ui'))

class EditServerSectionDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.saveEditedSectionButton.clicked.connect(self.saveEditedConfigSection)
        self.removeDialogButtonBox.rejected.connect(self.reject)

        server_config_sections = list_qgs_settings_child_groups("mapbender-plugin/connection")
        self.editSectionComboBox.addItems(server_config_sections)

        #self.setServiceParameters()
        #self.editSectionComboBox.currentIndexChanged.connect(self.setServiceParameters)

    def setServiceParameters(self, selected_section):
        #self.selected_section = self.editSectionComboBox.currentText()
        self.selected_section = selected_section
        con_params = list_qgs_settings_values(selected_section)
        server_url = con_params['url']
        server_port = con_params['port']
        server_username = con_params['username']
        server_password = con_params['password']

        self.editServiceNameLineEdit.setText(selected_section)
        self.editPortLineEdit.setText(server_port)
        self.editServerAddressLineEdit.setText(server_url)
        self.editUserNameLineEdit.setText(server_username)
        self.editPasswordLineEdit.setText(server_password)

    def saveEditedConfigSection(self):
        edited_section_name = self.editServiceNameLineEdit.text()
        edited_server_address = self.editServerAddressLineEdit.text()
        edited_port = self.editPortLineEdit.text()
        edited_user_name = self.editUserNameLineEdit.text()
        edited_password = self.editPasswordLineEdit.text()

        s = QgsSettings()

        if edited_section_name != self.selected_section:
            s.remove(f"mapbender-plugin/connection/{self.selected_section}")

        s.setValue(f"mapbender-plugin/connection/{edited_section_name}/url", edited_server_address)
        s.setValue(f"mapbender-plugin/connection/{edited_section_name}/port", edited_port)
        s.setValue(f"mapbender-plugin/connection/{edited_section_name}/username", edited_user_name)
        s.setValue(f"mapbender-plugin/connection/{edited_section_name}/password", edited_password)
            #
            # self.config.set(edited_section_name, 'url', edited_server_address)
            # self.config.set(edited_section_name, 'port', edited_port)
            # self.config.set(edited_section_name, 'username', edited_user_name)
            # self.config.set(edited_section_name, 'password', edited_password)
        # else:
        #     self.config.remove_section(self.editSectionComboBox.currentText())
        #     self.config.add_section(edited_section_name)
        #     self.config.set(edited_section_name, 'url', edited_server_address)
        #     self.config.set(edited_section_name, 'port', edited_port)
        #     self.config.set(edited_section_name, 'username', edited_user_name)
        #     self.config.set(edited_section_name, 'password', edited_password)

        # try:
        #     with open(self.config_path, 'w') as config_file:
        #         self.config.write(config_file)
        #     config_file.close()
        #     successBox = QMessageBox()
        #     successBox.setIconPixmap(QPixmap(self.plugin_dir +  '/resources/icons/mIconSuccess.svg'))
        #     successBox.setWindowTitle("Success")
        #     successBox.setText("Section successfully updated")
        #     successBox.setStandardButtons(QMessageBox.Ok)
        #     result = successBox.exec_()
        #     if result == QMessageBox.Ok:
        #         self.close()
        # except configparser.Error:
        #     failBox = QMessageBox()
        #     failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
        #     failBox.setWindowTitle("Failed")
        #     failBox.setText("Section could not be edited")
        #     failBox.setStandardButtons(QMessageBox.Ok)
        #     result = failBox.exec_()
        #     if result == QMessageBox.Ok:
        #         self.close()



