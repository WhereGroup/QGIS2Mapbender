import configparser
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QMessageBox
from PyQt5.uic.properties import QtGui

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'resources/ui/add_server_section_dialog.ui'))

class AddServerSectionDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.saveNewSectionButton.clicked.connect(self.saveNewConfigSection)
        self.addSectionDialogButtonBox.rejected.connect(self.reject)

        # get config file path
        self.plugin_dir = os.path.dirname(__file__)
        self.config_path = self.plugin_dir + '/server_config.cfg'

    def saveNewConfigSection(self):
        # get config file path
        self.plugin_dir = os.path.dirname(__file__)
        self.config_path = self.plugin_dir + '/server_config.cfg'

        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        new_section_name = self.newServiceNameLineEdit.text()
        new_server_address = self.newServerAddressLineEdit.text()
        new_user_name = self.newUserNameLineEdit.text()
        new_password = self.newPasswordLineEdit.text()

        self.config.add_section(new_section_name)
        self.config.set(new_section_name, 'url', new_server_address)
        self.config.set(new_section_name, 'username', new_user_name)
        self.config.set(new_section_name, 'password', new_password)
        try:
            with open(self.config_path,'w') as config_file:
                self.config.write(config_file)
            config_file.close()
            print('saved')

            successBox = QMessageBox()
            successBox.setIcon(QMessageBox.Information)
            successBox.setWindowTitle("Success")
            successBox.setText("New section successfully added")
            successBox.setStandardButtons(QMessageBox.Ok)
            result = successBox.exec_()
            if result == 1024:
                self.close()


        except configparser.DuplicateSectionError as error:
            print(error)
            raise
            sys.exit(1)

