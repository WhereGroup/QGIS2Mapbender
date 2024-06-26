# QGIS2Mapbender

## Description
QGIS plugin to populate Mapbender with QGIS-Server WMS.

## Installation and Requirements
### Installing the plugin
- To install the plugin, simply copy the folder with the plugin code into your QGIS profile folder:
  - Windows: C:\Users{USER}\AppData\Roaming\QGIS\QGIS3\profiles\{PROFILE}\python\plugins\
  - Linux: /home/{USER}/.local/share/QGIS/QGIS3/profiles/{PROFILE}/python/plugins

### Requirements on your local system
- The QGIS project must be saved in the same folder as the data.
- Install fabric2 e.g. using the QGIS console if the library is not already installed:
  ```
  import pip
  pip.main(['install', 'fabric2'])
  ```
### Requirements on your server
- QGIS Server is installed on your server.
- Mapbender is installed on your server.
- Create at least one template application in Mapbender (that will be cloned and used to publish a new WMS) or an application that will be used to publish a new WMS. These applications should have at least one layer set: 
  - layer set named "main" (default layer set for adding a new WMS to the application) OR 
  - layer set named with any other name (in this case, the name of the layer set should be specified when using the plugin)

## Support
info@wheregroup.com

## License
The plugin is licensed under the attached GNU General Public License.
