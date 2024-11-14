
import os
from typing import Optional

from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDockWidget

from QGIS2Mapbender.main_dialog import MainDialog


class MapbenderPlugin:
    dlg: Optional[MainDialog] = None
    def __init__(self, iface):
        """Constructor of the QGIS2Mapbender."""
        self.dlg = None
        self.iface = iface

    def initGui(self):
        """Create action that will start plugin configuration"""
        icon_path = os.path.join(os.path.dirname(__file__), 'resources/icons/mapbender_logo.png')
        self.action = QAction(QIcon(icon_path), 'QGIS2Mapbender', self.iface.mainWindow())
        self.iface.addPluginToMenu("&QGIS2Mapbender", self.action)
        self.iface.addToolBarIcon(self.action)

        # Connect the action to the run method
        self.action.triggered.connect(self.run)

    def unload(self):
        self.iface.removePluginMenu("&QGIS2Mapbender", self.action)
        self.iface.removeToolBarIcon(self.action)
        if self.dlg:
            self.dlg.close()
            self.dlg = None

    def openPyConsole(self):
        """In Windows, check that the Python console is open. If not, it is open and will close soon.
        This is a workaround for a problem that only occurs on Windows: The factory2 library sometimes throws an error
        when it tries to library sometimes throws an error when it tries to write to standard output (console).
        This will definitely be fixed when the new Mapbender API is released."""
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

        self.dlg = MainDialog()
        self.dlg.show()
        # sys.exit(dlg.exec_())
