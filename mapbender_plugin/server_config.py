from dataclasses import dataclass

from qgis._core import QgsSettings, QgsApplication, QgsAuthMethodConfig


@dataclass
class ServerConfig:
    name: str
    url: str
    port: int
    username: str
    password: str
    projects_path: str
    mb_app_path: str
    mb_basis_url: str
    authcfg:str

    # @staticmethod
    # def saveToSettings(name, url, port, username, password, projects_path, mb_app_path, mb_basis_url):
    #     s = QgsSettings()
    #     s.setValue(f"mapbender-plugin/connection/{name}/url", url)
    #     s.setValue(f"mapbender-plugin/connection/{name}/port", port)
    #     s.setValue(f"mapbender-plugin/connection/{name}/username", username)
    #     s.setValue(f"mapbender-plugin/connection/{name}/password", password)
    #     s.setValue(f"mapbender-plugin/connection/{name}/projects_path", projects_path)
    #     s.setValue(f"mapbender-plugin/connection/{name}/mb_app_path", mb_app_path)
    #     s.setValue(f"mapbender-plugin/connection/{name}/mb_basis_url", mb_basis_url)

    def save(self):
        s = QgsSettings()
        s.setValue(f"mapbender-plugin/connection/{self.name}/url", self.url)
        s.setValue(f"mapbender-plugin/connection/{self.name}/port", self.port)
        # s.setValue(f"mapbender-plugin/connection/{self.name}/username", self.username)
        # s.setValue(f"mapbender-plugin/connection/{self.name}/password", self.password)
        s.setValue(f"mapbender-plugin/connection/{self.name}/username", '')
        s.setValue(f"mapbender-plugin/connection/{self.name}/password", '')
        s.setValue(f"mapbender-plugin/connection/{self.name}/projects_path", self.projects_path)
        s.setValue(f"mapbender-plugin/connection/{self.name}/mb_app_path", self.mb_app_path)
        s.setValue(f"mapbender-plugin/connection/{self.name}/mb_basis_url", self.mb_basis_url)

        authCfgId = ServerConfig.save_basic_to_auth_db(self.name, self.username, self.password)
        s.setValue(f"mapbender-plugin/connection/{self.name}/authcfg", authCfgId)

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
        # set Basic
        conf = QgsAuthMethodConfig()
        print(conf)
        conf.setName(server_name)
        conf.setMethod("Basic")
        conf.setConfig("username", username)
        conf.setConfig("password", password)
        # check if method parameters are correctly set
        assert conf.isValid()

        # register data in authdb returning the ``authcfg`` of the stored
        # configuration
        auth_manager.storeAuthenticationConfig(conf)
        newAuthCfgId = conf.id()
        assert newAuthCfgId
        print(newAuthCfgId)
        return newAuthCfgId

    @staticmethod
    def getParamsFromSettings(name: str):
        s = QgsSettings()
        url = s.value(f"mapbender-plugin/connection/{name}/url")
        port = s.value(f"mapbender-plugin/connection/{name}/port")
        #username = s.value(f"mapbender-plugin/connection/{name}/username")
        #password = s.value(f"mapbender-plugin/connection/{name}/password")
        projects_path = s.value(f"mapbender-plugin/connection/{name}/projects_path")
        mb_app_path = s.value(f"mapbender-plugin/connection/{name}/mb_app_path")
        mb_basis_url = s.value(f"mapbender-plugin/connection/{name}/mb_basis_url")
        authcfg = s.value(f"mapbender-plugin/connection/{name}/authcfg")

        username, password = ServerConfig.get_username_and_password_from_auth_db(authcfg)

        return ServerConfig(name, url, port, username, password, projects_path, mb_app_path, mb_basis_url, authcfg)

    @staticmethod
    def get_username_and_password_from_auth_db(authcfg):
        """ Read connection details from authManager
        """
        # password encrypted in AuthManager
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
            print('no config id')
            return username, password

    def isValid(self) -> bool:
        variables = [self.name, self.url, self.port, self.username, self.password, self.projects_path, self.mb_app_path,
                     self.mb_basis_url]
        for var in variables:
            if " " in var:
                return False
        return True
