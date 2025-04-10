import os
from typing import Optional

import requests
from PyQt5 import uic
from PyQt5.QtCore import QRegExp, QSettings
from PyQt5.QtGui import QIntValidator, QRegExpValidator, QIcon
from PyQt5.QtWidgets import QDialogButtonBox, QLineEdit, QRadioButton, QLabel, QComboBox, QPushButton
from fabric2 import Connection
from qgis.gui import QgsFileWidget

from ..helpers import show_succes_box_ok, list_qgs_settings_child_groups, show_fail_box_ok, get_os, \
    uri_validator, starts_with_single_slash_or_colon, waitCursor, check_if_project_folder_exists_on_server, \
    ends_with_single_slash
from ..server_config import ServerConfig
from ..settings import PLUGIN_SETTINGS_SERVER_CONFIG_KEY

# Dialog from .ui file
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/server_config_dialog.ui'))


class ServerConfigDialog(BASE, WIDGET):
    serverConfigNameLineEdit: QLineEdit
    serverAddressLineEdit: QLineEdit
    serverPortLineEdit: QLineEdit

    credentialsPlainTextRadioButton: QRadioButton
    credentialsAuthDbRadioButton: QRadioButton
    userNameLineEdit: QLineEdit
    passwordLineEdit: QLineEdit
    authLabel: QLabel

    protocolQgisServerCmbBox: QComboBox
    # serverConfigNameLabel1: QLabel
    qgisServerPathLineEdit: QLineEdit     # TODO: better to rename qgisServerUrlLineEdit
    qgisProjectPathLineEdit: QLineEdit

    protocolMapbenderCmbBox: QComboBox
    # serverConfigNameLabel2: QLabel
    mbBasisUrlLineEdit: QLineEdit
    mbPathLineEdit: QLineEdit

    winPKFileWidget: QgsFileWidget

    # buttons
    testButton: QPushButton
    dialogButtonBox: QDialogButtonBox

    def __init__(self, server_config_name: Optional[str] = None, mode: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.mandatoryFields = [
            self.serverConfigNameLineEdit,
            self.serverAddressLineEdit,
            self.qgisProjectPathLineEdit,
            self.qgisServerPathLineEdit,
            self.mbPathLineEdit,
            self.mbBasisUrlLineEdit,
            self.binConsoleCommandLineEdit
        ]
        if get_os() == "Linux":
            self.winPKFileWidget.setEnabled(False)
        self.setupConnections()
        self.authcfg = ''
        self.selected_server_config_name = server_config_name
        self.mode = mode
        self.dialogButtonBox.button(QDialogButtonBox.Save).setEnabled(False)
        self.testButton.setEnabled(False)
        if server_config_name:
            self.getSavedServerConfig(server_config_name, mode)
        if self.mode == 'edit':
            self.dialogButtonBox.button(QDialogButtonBox.Save).setEnabled(True)
            self.testButton.setEnabled(True)

        self.serverConfigNameLineEdit.setToolTip('Custom server configuration name without blank spaces')
        self.qgisProjectPathLineEdit.setToolTip('Example: /data/qgis-projects/')
        self.qgisProjectPathLineEdit.setPlaceholderText('/data/qgis-projects/')
        self.qgisServerPathLineEdit.setToolTip('Example: [SERVER_NAME]/cgi-bin/qgis_mapserv.fcgi')
        self.mbPathLineEdit.setToolTip('Example: /data/mapbender/application/')
        self.mbPathLineEdit.setPlaceholderText('/mapbender/index_dev.php/')
        self.mbBasisUrlLineEdit.setToolTip('Example: [SERVER_NAME]/mapbender/index_dev.php/')
        self.winPKFileWidget.setToolTip('Example: C:/Users/user/Documents/ED25519-Key_private_key.ppk')
        self.binConsoleCommandLineEdit.setToolTip('Example: bin/console')
        self.binConsoleCommandLineEdit.setPlaceholderText('bin/console')

        # QLineEdit validators
        regex = QRegExp("[^\\s;]*")  # regex for blank spaces and semicolon
        regex_validator = QRegExpValidator(regex)
        int_validator = QIntValidator()
        self.serverConfigNameLineEdit.setValidator(regex_validator)
        self.serverPortLineEdit.setValidator(int_validator)
        self.serverAddressLineEdit.setValidator(regex_validator)
        self.userNameLineEdit.setValidator(regex_validator)
        self.passwordLineEdit.setValidator(regex_validator)
        self.qgisProjectPathLineEdit.setValidator(regex_validator)
        self.qgisServerPathLineEdit.setValidator(regex_validator)
        self.mbPathLineEdit.setValidator(regex_validator)
        self.mbBasisUrlLineEdit.setValidator(regex_validator)

        self.checkedIcon = QIcon(":images/themes/default/mIconSuccess.svg")

    def setupConnections(self):
        self.dialogButtonBox.accepted.connect(self.saveServerConfig)
        self.dialogButtonBox.rejected.connect(self.reject)
        self.serverConfigNameLineEdit.textChanged.connect(self.validateFields)
        self.serverAddressLineEdit.textChanged.connect(self.onChangeServerName)
        self.credentialsPlainTextRadioButton.toggled.connect(self.onToggleCredential)
        self.qgisProjectPathLineEdit.textChanged.connect(self.validateFields)
        self.qgisServerPathLineEdit.textChanged.connect(self.validateFields)
        self.mbPathLineEdit.textChanged.connect(self.validateFields)
        self.mbBasisUrlLineEdit.textChanged.connect(self.validateFields)
        self.testButton.clicked.connect(self.execTests)

    def execTests(self) -> None:
        """Run a few tests (described in the method <testConnection> method). It displays a message if errors are found"""
        errorMsg = None
        self.testButton.setIcon(QIcon())
        with waitCursor():
            errorMsg = self.execTestsImpl()

        if errorMsg:
            show_fail_box_ok("Failed", errorMsg)
        else:
            self.testButton.setIcon(self.checkedIcon)
            show_succes_box_ok("Success", """Following tests are carried out:
            1. SSH connection is successfully established
            2. Successfully accessed the QGIS project path
            3. Successfully accessed the Mapbender path
            4. Mapbender's is validated and its response is 200
            5. QGIS's URL is valid and its response is 200""")

    def execTestsImpl(self) -> Optional[str]:
        """
        Tests the SSH connection and verifies access to IRLs of Mapbender and QGIS Server.

        This method performs the following steps:
            1. Establishes an SSH connection using the provided SSH client.
            2. Attempts to access a specified QGIS Project path.
            3. Attempts to access a specified Mapbender's path.
            4. Check the validity of the Mapbender URL and verify that the response is 200.
            5. Check the validity of the QGIS URL and verify that the response is 200.

        Return:
            If found, error message
        """
        configFromForm = self.getServerConfigFromFormular()
        # print(configFromForm)
        connect_kwargs = {"password": configFromForm.password}

        if not ends_with_single_slash(configFromForm.projects_path):
            return f"QGIS project path '{configFromForm.projects_path}' should end with one '/'"

        if not ends_with_single_slash(configFromForm.mb_app_path):
            return f"Mapbender application path '{configFromForm.mb_app_path}' should end with one '/'"

        with Connection(host=configFromForm.url, user=configFromForm.username,
                        port=configFromForm.port, connect_kwargs=connect_kwargs) as connection:
            try:  # test SSH connection
                connection.open()
                # connection.run('cd /')
                #  Tests 2 and 3:
                if not check_if_project_folder_exists_on_server(connection, configFromForm.projects_path):
                    return f"Unable to find folder {configFromForm.projects_path} on the server {configFromForm.url}."
                if not check_if_project_folder_exists_on_server(connection, configFromForm.mb_app_path):
                    return f"Unable to find folder {configFromForm.mb_app_path} on the server {configFromForm.url}."

            except Exception as e:
                return ("Unable to connect to the server via SSH, please check your details. "
                        f"Login, password are correct? Server address is correct?\n {str(e)}")

        # Test n. 4
        wmsServiceRequest = "?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"
        qgiServerUrl = (f'{self.protocolQgisServerCmbBox.currentText()}'
                        f'{configFromForm.qgis_server_path}'
                        f'{wmsServiceRequest}')
        errorStr = self.testHttpConn(qgiServerUrl, 'Qgis Server', configFromForm.qgis_server_path)
        if errorStr:
            return errorStr

        # Test n. 5
        mapbenderUrl = (f'{configFromForm.mb_protocol}'
                        f'{configFromForm.mb_basis_url}')
        errorStr = self.testHttpConn(mapbenderUrl, 'Mapbender', configFromForm.mb_basis_url)
        if errorStr:
            return errorStr

        return None

    def testHttpConn(self, url: str, serverName: str, lastPart: str) -> Optional[str]:
        # if not starts_with_single_slash_or_colon(lastPart):
        #     return f"Is the address {url} correct?"

        errorStr = f"Unable to connect to the {serverName} {url}. Is the address correct?"
        if not uri_validator(url):
            return f"The URL {url} seems not valid. Is the address correct?"

        try:
            resp = requests.get(url)
            if resp.status_code != 200:
                return errorStr
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError) as error:
            return f"{errorStr}\n {str(error)}"

        return None

    def getSavedServerConfig(self, server_config_name: str, mode: str):
        server_config = ServerConfig.getParamsFromSettings(server_config_name)
        self.authcfg = server_config.authcfg
        if mode == 'edit':
            self.serverConfigNameLineEdit.setText(server_config_name)
        self.serverPortLineEdit.setText(server_config.port)
        self.serverAddressLineEdit.setText(server_config.url)
        self.userNameLineEdit.setText(server_config.username)
        self.passwordLineEdit.setText(server_config.password)
        if server_config.authcfg:
            self.authLabel.setText(f'Authentication saved in database. Configuration: {server_config.authcfg}')
            self.credentialsAuthDbRadioButton.setChecked(True)
        else:
            self.authLabel.setText('')
            self.credentialsPlainTextRadioButton.setChecked(True)
        self.qgisProjectPathLineEdit.setText(server_config.projects_path)
        self.protocolQgisServerCmbBox.setCurrentText(server_config.qgis_server_protocol)
        self.qgisServerPathLineEdit.setText(server_config.qgis_server_path)
        self.mbPathLineEdit.setText(server_config.mb_app_path)
        self.protocolMapbenderCmbBox.setCurrentText(server_config.mb_protocol)
        self.mbBasisUrlLineEdit.setText(server_config.mb_basis_url)
        self.winPKFileWidget.lineEdit().setText(server_config.windows_pk_path)
        self.binConsoleCommandLineEdit.setText(server_config.bin_console_command)

    def getServerConfigFromFormular(self) -> ServerConfig:
        return ServerConfig(
            name=self.serverConfigNameLineEdit.text(),
            url=self.serverAddressLineEdit.text(),
            port=self.serverPortLineEdit.text(),
            username=self.userNameLineEdit.text(),
            password=self.passwordLineEdit.text(),
            projects_path=self.qgisProjectPathLineEdit.text(),
            qgis_server_protocol=self.protocolQgisServerCmbBox.currentText(),
            qgis_server_path=self.qgisServerPathLineEdit.text(),
            mb_app_path=self.mbPathLineEdit.text(),
            mb_protocol=self.protocolMapbenderCmbBox.currentText(),
            mb_basis_url=self.mbBasisUrlLineEdit.text(),
            authcfg=self.authcfg,
            windows_pk_path=self.winPKFileWidget.lineEdit().text(),
            bin_console_command=self.binConsoleCommandLineEdit.text()
        )

    def onChangeServerName(self, newValue) -> None:
        # print('newValue', newValue)
        self.qgisServerPathLineEdit.setPlaceholderText(newValue + '/cgi-bin/qgis_mapserv.fcgi')
        self.mbBasisUrlLineEdit.setPlaceholderText(newValue + '/mapbender/index.php/')
        self.validateFields()

    def validateFields(self) -> None:
        self.dialogButtonBox.button(QDialogButtonBox.Save).setEnabled(
            all(field.text() for field in self.mandatoryFields))

        self.testButton.setEnabled(
            all(field.text() for field in self.mandatoryFields))

    def checkConfigName(self, config_name_from_formular) -> bool:
        saved_config_names = list_qgs_settings_child_groups(f'{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection')
        if self.mode == 'edit' and config_name_from_formular not in saved_config_names:
            s = QSettings()
            s.remove(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{self.selected_server_config_name}")
            return True
        if config_name_from_formular in saved_config_names and self.mode != 'edit':
            show_fail_box_ok('Failed', 'Server configuration name already exists')
            return False
        return True

    def saveServerConfig(self):
        serverConfigFromFormular = self.getServerConfigFromFormular()
        if not self.checkConfigName(serverConfigFromFormular.name):
            return
        if self.credentialsPlainTextRadioButton.isChecked():
            serverConfigFromFormular.save(encrypted=False)
        else:
            serverConfigFromFormular.save(encrypted=True)
        show_succes_box_ok('Success', 'Server configuration successfully saved')
        self.close()
        return

    def onToggleCredential(self, isChecked: bool):
        """QLabel <authLabel> is visible only if credentials are NOT saved as plain text"""
        self.authLabel.setVisible(not isChecked)