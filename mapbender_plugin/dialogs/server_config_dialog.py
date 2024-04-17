import os
from typing import Optional

from PyQt5 import uic
from PyQt5.QtCore import QRegExp, QSettings
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from PyQt5.QtWidgets import QDialogButtonBox, QLineEdit, QRadioButton
from qgis._gui import QgsFileWidget

from mapbender_plugin.helpers import show_succes_box_ok, list_qgs_settings_child_groups, show_fail_box_ok, get_os
from mapbender_plugin.server_config import ServerConfig
from mapbender_plugin.settings import PLUGIN_SETTINGS_SERVER_CONFIG_KEY

# Dialog from .ui file
WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/server_config_dialog.ui'))


class ServerConfigDialog(BASE, WIDGET):
    dialogButtonBox: QDialogButtonBox
    serverConfigNameLineEdit: QLineEdit
    serverAddressLineEdit: QLineEdit
    qgisProjectPathLineEdit: QLineEdit
    qgisServerPathLineEdit: QLineEdit
    mbPathLineEdit: QLineEdit
    mbBasisUrlLineEdit: QLineEdit
    winPKFileWidget: QgsFileWidget
    credentialsPlainTextRadioButton: QRadioButton
    credentialsAuthDbRadioButton: QRadioButton


    def __init__(self, server_config_name: Optional[str] = None, mode: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.mandatoryFields = [
            self.serverConfigNameLineEdit,
            self.serverAddressLineEdit,
            self.qgisProjectPathLineEdit,
            self.qgisServerPathLineEdit,
            self.mbPathLineEdit,
            self.mbBasisUrlLineEdit
        ]
        if get_os() == "Linux":
            self.winPKFileWidget.setEnabled(False)
        self.setupConnections()
        self.authcfg = ''
        self.selected_server_config_name = server_config_name
        self.mode = mode
        self.dialogButtonBox.button(QDialogButtonBox.Save).setEnabled(False)
        if server_config_name:
            self.getSavedServerConfig(server_config_name, mode)
        if self.mode == 'edit':
            self.dialogButtonBox.button(QDialogButtonBox.Save).setEnabled(True)

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

    def setupConnections(self):
        self.dialogButtonBox.accepted.connect(self.saveServerConfig)
        self.dialogButtonBox.rejected.connect(self.reject)
        self.serverConfigNameLineEdit.textChanged.connect(self.validateFields)
        self.serverAddressLineEdit.textChanged.connect(self.validateFields)
        self.qgisProjectPathLineEdit.textChanged.connect(self.validateFields)
        self.qgisServerPathLineEdit.textChanged.connect(self.validateFields)
        self.mbPathLineEdit.textChanged.connect(self.validateFields)
        self.mbBasisUrlLineEdit.textChanged.connect(self.validateFields)

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
            self.credentialsAuthDbRadioButton.setChecked(True)
            self.userNameLineEdit.setText('')
            self.passwordLineEdit.setText('')
        else:
            self.credentialsPlainTextRadioButton.setChecked(True)
        self.qgisProjectPathLineEdit.setText(server_config.projects_path)
        self.qgisServerPathLineEdit.setText(server_config.qgis_server_path)
        self.mbPathLineEdit.setText(server_config.mb_app_path)
        self.mbBasisUrlLineEdit.setText(server_config.mb_basis_url)
        self.winPKFileWidget.lineEdit().setText(server_config.windows_pk_path)

    def getServerConfigFromFormular(self) -> ServerConfig:
        return ServerConfig(
            name=self.serverConfigNameLineEdit.text(),
            url=self.serverAddressLineEdit.text(),
            port=self.serverPortLineEdit.text(),
            username=self.userNameLineEdit.text(),
            password=self.passwordLineEdit.text(),
            projects_path=self.qgisProjectPathLineEdit.text(),
            qgis_server_path=self.qgisServerPathLineEdit.text(),
            mb_app_path=self.mbPathLineEdit.text(),
            mb_basis_url=self.mbBasisUrlLineEdit.text(),
            authcfg=self.authcfg,
            windows_pk_path=self.winPKFileWidget.lineEdit().text()
        )

    def validateFields(self) -> None:
        self.dialogButtonBox.button(QDialogButtonBox.Save).setEnabled(
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

