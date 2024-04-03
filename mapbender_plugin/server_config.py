from dataclasses import dataclass

from qgis._core import QgsSettings

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

    @staticmethod
    def saveToSettings(name, url, port, username, password, projects_path, mb_app_path, mb_basis_url):
        s = QgsSettings()
        s.setValue(f"mapbender-plugin/connection/{name}/url", url)
        s.setValue(f"mapbender-plugin/connection/{name}/port", port)
        s.setValue(f"mapbender-plugin/connection/{name}/username", username)
        s.setValue(f"mapbender-plugin/connection/{name}/password", password)
        s.setValue(f"mapbender-plugin/connection/{name}/projects_path", projects_path)
        s.setValue(f"mapbender-plugin/connection/{name}/mb_app_path", mb_app_path)
        s.setValue(f"mapbender-plugin/connection/{name}/mb_basis_url", mb_basis_url)

    def save(self):
        s = QgsSettings()
        s.setValue(f"mapbender-plugin/connection/{self.name}/url", self.url)
        s.setValue(f"mapbender-plugin/connection/{self.name}/port", self.port)
        s.setValue(f"mapbender-plugin/connection/{self.name}/username", self.username)
        s.setValue(f"mapbender-plugin/connection/{self.name}/password", self.password)
        s.setValue(f"mapbender-plugin/connection/{self.name}/projects_path", self.projects_path)
        s.setValue(f"mapbender-plugin/connection/{self.name}/mb_app_path", self.mb_app_path)
        s.setValue(f"mapbender-plugin/connection/{self.name}/mb_basis_url", self.mb_basis_url)

    @staticmethod
    def getParamsFromSettings(name: str):
        s = QgsSettings()
        url = s.value(f"mapbender-plugin/connection/{name}/url")
        port = s.value(f"mapbender-plugin/connection/{name}/port")
        username = s.value(f"mapbender-plugin/connection/{name}/username")
        password = s.value(f"mapbender-plugin/connection/{name}/password")
        projects_path = s.value(f"mapbender-plugin/connection/{name}/projects_path")
        mb_app_path = s.value(f"mapbender-plugin/connection/{name}/mb_app_path")
        mb_basis_url = s.value(f"mapbender-plugin/connection/{name}/mb_basis_url")

        return ServerConfig(name, url, port, username, password, projects_path, mb_app_path, mb_basis_url)

    def isValid(self) -> bool:
        variables = [self.name, self.url, self.port, self.username, self.password, self.projects_path, self.mb_app_path,
                     self.mb_basis_url]
        for var in variables:
            if " " in var:
                return False
        return True
