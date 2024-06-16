# QGIS2Mapbender

## Description
QGIS plugin to populate Mapbender with QGIS-Server WMS from within QGIS.

## Installation and Requirements
### Installing the plugin
- To install the plugin, simply copy the folder with the plugin code into your QGIS profile folder:
  - Windows directory: C:\Users{USER}\AppData\Roaming\QGIS\QGIS3\profiles\{PROFILE}\python\plugins\
  - Linux directory: /home/{USER}/.local/share/QGIS/QGIS3/profiles/{PROFILE}/python/plugins

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
- Create at least one template application in Mapbender (that will be cloned and used to publish a new WMS) or an application that will be used to publish a new WMS.
    - These applications should have at least one layer set: 
      - layer set named "main" (default layer set for adding a new WMS to the application) OR 
      - layer set named with any other name (in this case, the name of the layer set should be specified when using the plugin)

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
