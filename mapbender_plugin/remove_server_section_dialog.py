import os
from PyQt5 import uic

# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'resources/ui/remove_server_section_dialog.ui'))

class RemoveServerSectionDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
