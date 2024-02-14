
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from qgis.core import (
    QgsProject,
)

#import ConfigParser

class Mapbenderplugin:
    def __init__(self, iface):
        self.iface = iface

    def __init__(self,iface):
        """Constructor of the Mapbender plugin."""
        self.iface = iface
        self.project = QgsProject.instance()

    def initGui(self):
        """Create action that will start plugin configuration"""
        icon_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        self.action = QAction(QIcon(icon_path), 'Mapbender plugin', self.iface.mainWindow())
        self.iface.addPluginToMenu("&Mapbender plugin", self.action)
        self.iface.addToolBarIcon(self.action)

        # connect the action to the run method
        self.action.triggered.connect(self.run)

    def unload(self):
        self.iface.removePluginMenu("&Mapbender plugin", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        """Plugin run method : launch the GUI."""
        self.dlg = MapbenderPluginDialog()
        self.dlg.exec()



# Dialog aus .ui-Datei
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'main_dialog.ui'))

class MapbenderPluginDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.buttonBox.rejected.connect(self.reject)



