import os
from PyQt5 import uic
from PyQt5.QtCore import QSettings
from configparser import ConfigParser

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'main_dialog.ui'))

class MainDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.sectionComboBoxLabel.hide()
        self.sectionComboBox.hide()
        self.uploadButton.hide()
        #self.addServerConfigButton().connect(self.addNewConfigSection)
        self.buttonBox.rejected.connect(self.reject)

        # get config file
        self.plugin_dir = os.path.dirname(__file__)
        config_path = self.plugin_dir + '/config_datei.cfg'

        # parse config file
        self.config = ConfigParser()
        self.config.read(config_path)

        # read sections and validate config params
        config_sections = self.config.sections()
        if len(config_sections) == 0:
            self.warningAddServiceText.show()
            self.editSelectedServerConfigButton.hide()
            self.editSelectedServiceConfigFileLabel.hide()
            self.deleteSelectedServerConfigButton.hide()
            self.deleteSelectedServiceConfigFileLabel.hide()
            self.exportServiceConfigFileButton.hide()
            self.exportServiceConfigFileLabel.hide()
        else:
            # sections-combobox
            self.sectionComboBox.addItems(config_sections)
            self.sectionComboBoxLabel.show()
            self.sectionComboBox.show()
            self.validateConfigParams()
            self.sectionComboBox.currentIndexChanged.connect(self.validateConfigParams)
            # config management
            #self.serverConfigManagementGroupBox.

    def validateConfigParams(self):
        selected_section = self.sectionComboBox.currentText()
        server_url = self.config.get(selected_section, 'url')
        server_username = self.config.get(selected_section, 'username')
        server_password = self.config.get(selected_section, 'password')
        if server_url == '' or len(server_url)<5:
            print('Please provide a value for URL')
        print(server_url, server_username, server_password)

    def addNewConfigSection(self):
        print('addNewConfigSection')



