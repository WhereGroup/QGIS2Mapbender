from dataclasses import dataclass

from qgis.core import QgsSettings, QgsApplication, QgsAuthMethodConfig, QgsMessageLog, Qgis

from mapbender_plugin.settings import PLUGIN_SETTINGS_SERVER_CONFIG_KEY, TAG


@dataclass
class ServerConfig:
    name: str
    url: str
    port: int
    username: str
    password: str
    projects_path: str
    qgis_server_path: str
    mb_app_path: str
    mb_basis_url: str
    authcfg: str

    def save(self):
        s = QgsSettings()
        s.setValue(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{self.name}/url", self.url)
        s.setValue(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{self.name}/port", self.port)
        s.setValue(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{self.name}/username", '')
        s.setValue(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{self.name}/password", '')
        s.setValue(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{self.name}/projects_path", self.projects_path)
        s.setValue(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{self.name}/qgis_server_path", self.qgis_server_path)
        s.setValue(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{self.name}/mb_app_path", self.mb_app_path)
        s.setValue(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{self.name}/mb_basis_url", self.mb_basis_url)

        authCfgId = ServerConfig.save_basic_to_auth_db(self.name, self.username, self.password)
        s.setValue(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{self.name}/authcfg", authCfgId)

    @staticmethod
    def save_basic_to_auth_db(server_name, username, password):
        """
        Saves the password securely in the qgis-auth.db file.

        Args:
            server_name (str): Name of the server or connection.
            username (str): User's username.
            password (str): User's password.
        """
        auth_manager = QgsApplication.authManager()
        conf = QgsAuthMethodConfig()
        conf.setName(server_name)
        conf.setMethod("Basic")
        conf.setConfig("username", username)
        conf.setConfig("password", password)
        # Check if method parameters are correctly set
        assert conf.isValid()

        # Register data in authdb returning the ``authcfg`` of the stored configuration
        auth_manager.storeAuthenticationConfig(conf)
        newAuthCfgId = conf.id()
        assert newAuthCfgId
        return newAuthCfgId

    @staticmethod
    def getParamsFromSettings(name: str):
        s = QgsSettings()
        url = s.value(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{name}/url")
        port = s.value(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{name}/port")
        projects_path = s.value(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{name}/projects_path")
        qgis_server_path = s.value(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{name}/qgis_server_path")
        mb_app_path = s.value(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{name}/mb_app_path")
        mb_basis_url = s.value(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{name}/mb_basis_url")
        authcfg = s.value(f"{PLUGIN_SETTINGS_SERVER_CONFIG_KEY}/connection/{name}/authcfg")

        username, password = ServerConfig.get_username_and_password_from_auth_db(authcfg)

        return ServerConfig(name, url, port, username, password, projects_path, qgis_server_path, mb_app_path, mb_basis_url, authcfg)

    @staticmethod
    def get_username_and_password_from_auth_db(authcfg):
        auth_manager = QgsApplication.authManager()
        conf = QgsAuthMethodConfig()
        auth_manager.loadAuthenticationConfig(authcfg, conf, True)
        if conf.id():
            username = conf.config('username', '')
            password = conf.config('password', '')
            return username, password
        else:
            username = ''
            password = ''
            QgsMessageLog.logMessage("No config id...", TAG, level=Qgis.Warning)
            return username, password

    # def isValid(self) -> bool:
    #     variables = [self.name, self.url, self.port, self.username, self.password, self.projects_path, self.mb_app_path,
    #                  self.mb_basis_url]
    #     for var in variables:
    #         if " " in var:
    #             return False
    #     return True
