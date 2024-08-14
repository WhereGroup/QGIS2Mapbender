
import os
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDockWidget

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

        # Connect the action to the run method
        self.action.triggered.connect(self.run)

    def unload(self):
        self.iface.removePluginMenu("&Mapbender plugin", self.action)
        self.iface.removeToolBarIcon(self.action)

    def openPyConsole(self):
        """In Windows, check if the Python console is open. If not, it is open and will be closed soon.
        This is a workaround for a problem that only occurs in Windows: In fact, the factory2 library sometimes throws
        an error when it tries to write to standard output (console)."""
        if os.name == 'nt':
            pythonConsole: QDockWidget = self.iface.mainWindow().findChild(QDockWidget, 'PythonConsole')
            isOpenAtStart = True if pythonConsole and pythonConsole.isVisible() else False

            # Open and close the console again
            if not isOpenAtStart:
                self.iface.actionShowPythonDialog().trigger()
                self.iface.actionShowPythonDialog().trigger()


    def run(self):
        """Plugin run method : launch the GUI."""
        self.openPyConsole()

        dlg = MainDialog()
        dlg.exec()
