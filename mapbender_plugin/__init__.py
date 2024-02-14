from qgis.core import QgsMessageLog
def classFactory(iface):
    from .plugin import Mapbenderplugin
    QgsMessageLog.logMessage('iface', 'iface')
    return Mapbenderplugin(iface)

