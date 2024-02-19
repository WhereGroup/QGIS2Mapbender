import configparser
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QMessageBox

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'resources/ui/remove_server_section_dialog.ui'))

class RemoveServerSectionDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.removeSelectedSectionButton.clicked.connect(self.saveRemoveConfigSection)
        self.removeDialogButtonBox.rejected.connect(self.reject)

        # get config file path
        self.plugin_dir = os.path.dirname(__file__)
        self.config_path = self.plugin_dir + '/server_config.cfg'

        # parse config file
        try:
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)
        except configparser.ParsingError as error:
            self.iface.messageBar().pushMessage("Error: Could not parse", error, level=Qgis.Critical)

        # read config sections
        config_sections = self.config.sections()
        self.removeSectionComboBox.addItems(config_sections)


    def saveRemoveConfigSection(self):
        selected_section = self.removeSectionComboBox.currentText()
        self.config.remove_section(selected_section)

        successBox = QMessageBox()
        successBox.setIcon(QMessageBox.Question)
        #successBox.setWindowTitle("..")
        successBox.setText("Are you sure you want to delete the section '" + selected_section + "' ?")
        successBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = successBox.exec_()
        if result == QMessageBox.Yes:
            try:
                with open(self.config_path, 'w') as config_file:
                    self.config.write(config_file)
                config_file.close()
                successBox = QMessageBox()
                successBox.setIcon(QMessageBox.Information)
                successBox.setWindowTitle("Success")
                successBox.setText("Section successfully removed")
                successBox.setStandardButtons(QMessageBox.Ok)
                result = successBox.exec_()
                if result == 1024:
                    self.close()
            except configparser.DuplicateSectionError as error:
                print(error)
                raise
                sys.exit(1)
        #else:
            #self.close()


