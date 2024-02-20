import configparser
import os
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from PyQt5.uic.properties import QtGui

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/add_server_section_dialog.ui'))

class AddServerSectionDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.saveNewSectionButton.clicked.connect(self.saveNewConfigSection)
        self.addSectionDialogButtonBox.rejected.connect(self.reject)

        # get config file path
        self.file = os.path.dirname(__file__)
        self.plugin_dir = os.path.dirname(self.file)
        self.config_path = self.plugin_dir + '/server_config.cfg'

    def saveNewConfigSection(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        new_section_name = self.newServiceNameLineEdit.text()
        new_server_address = self.newServerAddressLineEdit.text()
        new_user_name = self.newUserNameLineEdit.text()
        new_password = self.newPasswordLineEdit.text()

        try:
            self.config.add_section(new_section_name)
            self.config.set(new_section_name, 'url', new_server_address)
            self.config.set(new_section_name, 'username', new_user_name)
            self.config.set(new_section_name, 'password', new_password)
            with open(self.config_path,'w') as config_file:
                self.config.write(config_file)
            config_file.close()
            successBox = QMessageBox()
            #successBox.setIcon(QMessageBox.Information)
            successBox.setIconPixmap(QPixmap(self.plugin_dir +  '/resources/icons/mIconSuccess.svg'))
            successBox.setWindowTitle("Success")
            successBox.setText("New section successfully added")
            successBox.setStandardButtons(QMessageBox.Ok)
            result = successBox.exec_()
            if result == QMessageBox.Ok:
                self.close()
        except configparser.DuplicateSectionError:
            failBox = QMessageBox()
            #failBox.setIcon(QMessageBox.Warning)
            failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
            failBox.setWindowTitle("Failed")
            failBox.setText("Section could not be added: section name already exists!")
            failBox.setStandardButtons(QMessageBox.Ok)
            result = failBox.exec_()
            if result == QMessageBox.Ok:
                self.close()
        except configparser.Error:
            failBox = QMessageBox()
            #failBox.setIcon(QMessageBox.Warning)
            failBox.setIconPixmap(QPixmap(self.plugin_dir + '/resources/icons/mIconWarning.svg'))
            failBox.setWindowTitle("Failed")
            failBox.setText("Section could not be added")
            failBox.setStandardButtons(QMessageBox.Ok)
            result = failBox.exec_()
            if result == QMessageBox.Ok:
                self.close()

