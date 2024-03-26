import configparser
import os
from PyQt5 import uic
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from qgis._core import QgsSettings

from mapbender_plugin.helpers import show_succes_box_ok, show_question_box, list_qgs_settings_child_groups, show_fail_box_ok

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/remove_server_section_dialog.ui'))

class RemoveServerSectionDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.removeSelectedSectionButton.clicked.connect(self.saveRemoveConfigSection)
        self.removeDialogButtonBox.rejected.connect(self.reject)

        # # read config sections
        server_config_sections = list_qgs_settings_child_groups("mapbender-plugin/connection")
        self.removeSectionComboBox.addItems(server_config_sections)


    def saveRemoveConfigSection(self):
        selected_section = self.removeSectionComboBox.currentText()

        if (show_question_box(f"""Are you sure you want to remove the section '{selected_section}'?""")) == QMessageBox.Yes:
            try:
                s = QSettings()
                s.remove(f"mapbender-plugin/connection/{selected_section}")
                if (show_succes_box_ok('Success', 'Section successfully removed')) == QMessageBox.Ok:
                    #self.update_combo_box()
                    self.close()
            except:
                if (show_fail_box_ok('Failed',"Section could not be deleted")) == QMessageBox.Ok:
                    self.close()
        else:
            self.close()

    def update_combo_box(self):
        self.removeSectionComboBox.clear()
        config_sections = list_qgs_settings_child_groups("mapbender-plugin/connection")
        self.removeSectionComboBox.addItems(config_sections)





