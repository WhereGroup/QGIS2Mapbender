import os
import sys

from PyQt5 import uic
#from configparser import ConfigParser
import configparser

from qgis._core import Qgis

from mapbender_plugin.remove_server_section_dialog import RemoveServerSectionDialog

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'resources/ui/main_dialog.ui'))

class MainDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.addServerConfigButton.clicked.connect(self.addNewConfigSection)
        self.removeSelectedServerConfigButton.clicked.connect(self.removeConfigSection)
        self.buttonBoxTab1.rejected.connect(self.reject)
        self.buttonBoxTab2.rejected.connect(self.reject)

        # get config file path
        self.plugin_dir = os.path.dirname(__file__)
        self.config_path = self.plugin_dir + '/server_config.cfg'

        # check if config file exists
        if not os.path.isfile(self.config_path):
            try:
                # create the config file if not existing
                open(self.config_path, 'a').close()
            except OSError:
                self.iface.messageBar().pushMessage("Failed creating the file", "Please contact", level=Qgis.Critical)

        # parse config file
        try:
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)
        except configparser.ParsingError as error:
            self.iface.messageBar().pushMessage("Error: Could not parse", error, level=Qgis.Critical)

        # read sections and validate config params
        config_sections = self.config.sections()
        if len(config_sections) == 0:
            self.warningAddServiceText.show()
            self.sectionComboBoxLabel.hide()
            self.sectionComboBox.hide()
            self.uploadButton.hide()
            self.editSelectedServerConfigButton.hide()
            self.editSelectedServiceConfigFileLabel.hide()
            self.removeSelectedServerConfigButton.hide()
            self.removeSelectedServiceConfigFileLabel.hide()
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
            self.warningAddServiceText.hide()

    def validateConfigParams(self):
        selected_section = self.sectionComboBox.currentText()
        server_url = self.config.get(selected_section, 'url')
        server_username = self.config.get(selected_section, 'username')
        server_password = self.config.get(selected_section, 'password')
        if server_url == '' or len(server_url)<5:
            print('Please provide a value for URL')
        print(server_url, server_username, server_password)

    def addNewConfigSection(self):
        new_section_name = 'new'
        self.config.add_section(new_section_name)
        self.config.set(new_section_name, 'url', 'http://localhost:8080/bugs')
        self.config.set(new_section_name, 'username', 'dhellmann')
        self.config.set(new_section_name, 'password', 'secret')
        try:
            with open(self.config_path,'w') as config_file:
                self.config.write(config_file)
            config_file.close()
            print('saved')
        except configparser.DuplicateSectionError as error:
            print(error)
            raise
            sys.exit(1)

    def removeConfigSection(self):
        remove_server_dialog = RemoveServerSectionDialog()
        remove_server_dialog.exec()
        remove_section_name = 'new'
        self.config.remove_section(remove_section_name)
        with open(self.config_path,'w') as config_file:
            self.config.write(config_file)
        config_file.close()






