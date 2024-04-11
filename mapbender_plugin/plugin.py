
import os
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

from mapbender_plugin.main_dialog import MainDialog


class MapbenderPlugin:
    def __init__(self, iface):
        """Constructor of the Mapbender plugin."""
        self.iface = iface

    def initGui(self):
        """Create action that will start plugin configuration"""
        icon_path = os.path.join(os.path.dirname(__file__), 'resources/icons/mapbender_logo.png')
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
        self.dlg = MainDialog()
        self.dlg.exec()








