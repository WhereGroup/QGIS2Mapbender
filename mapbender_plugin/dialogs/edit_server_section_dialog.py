import configparser
import os
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/edit_server_section_dialog.ui'))

class EditServerSectionDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.saveEditedSectionButton.clicked.connect(self.saveEditedConfigSection)
        self.removeDialogButtonBox.rejected.connect(self.reject)

        # get config file path
        self.file = os.path.dirname(__file__)
        self.plugin_dir = os.path.dirname(self.file)
        self.config_path = self.plugin_dir + '/server_config.cfg'

        # parse config file
        try:
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)
        except configparser.Error as error:
            self.iface.messageBar().pushMessage("Error: Could not parse", error, level=Qgis.Critical)

        # read config sections
        config_sections = self.config.sections()
        self.editSectionComboBox.addItems(config_sections)
        self.setServiceParameters()
        self.editSectionComboBox.currentIndexChanged.connect(self.setServiceParameters)



    def setServiceParameters(self):
        selected_section = self.editSectionComboBox.currentText()
        server_url = self.config.get(selected_section, 'url')
        server_username = self.config.get(selected_section, 'username')
        server_password = self.config.get(selected_section, 'password')
        # fill fields with parameters from selected config section
        self.editServiceNameLineEdit.setText(selected_section)
        self.editServerAddressLineEdit.setText(server_url)
        self.editUserNameLineEdit.setText(server_username)
        self.editPasswordLineEdit.setText(server_password)

    def saveEditedConfigSection(self):
        edited_section_name = self.editServiceNameLineEdit.text()
        edited_server_address = self.editServerAddressLineEdit.text()
        edited_user_name = self.editUserNameLineEdit.text()
        edited_password = self.editPasswordLineEdit.text()

        if edited_section_name == self.editSectionComboBox.currentText():
            self.config.set(edited_section_name, 'url', edited_server_address)
            self.config.set(edited_section_name, 'username', edited_user_name)
            self.config.set(edited_section_name, 'password', edited_password)
        else:
            self.config.remove_section(self.editSectionComboBox.currentText())
            self.config.add_section(edited_section_name)
            self.config.set(edited_section_name, 'url', edited_server_address)
            self.config.set(edited_section_name, 'username', edited_user_name)
            self.config.set(edited_section_name, 'password', edited_password)

        try:
            with open(self.config_path, 'w') as config_file:
                self.config.write(config_file)
            config_file.close()
            successBox = QMessageBox()
            successBox.setIconPixmap(QPixmap(self.plugin_dir +  '/resources/icons/mIconSuccess.svg'))
            successBox.setWindowTitle("Success")
            successBox.setText("Section successfully updated")
            successBox.setStandardButtons(QMessageBox.Ok)
            result = successBox.exec_()
            if result == QMessageBox.Ok:
                self.close()
        except configparser.Error:
            failBox = QMessageBox()
            failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
            failBox.setWindowTitle("Failed")
            failBox.setText("Section could not be edited")
            failBox.setStandardButtons(QMessageBox.Ok)
            result = failBox.exec_()
            if result == QMessageBox.Ok:
                self.close()



