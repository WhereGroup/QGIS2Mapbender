import json
import requests

from qgis.core import QgsMessageLog, Qgis
from sympy.codegen.ast import continue_
# from sympy.codegen.ast import continue_

from .helpers import waitCursor
from .settings import TAG

class ApiRequest:
    def __init__(self, server_config):
        self.server_config = server_config
        self.api_url = "http://" + self.server_config.url + "/mapbender/api"
        # credentials
        self.credentials = {
            "username": self.server_config.username,
            "password": self.server_config.password
        }

        self.status_code_login, self.token, self.response_json = self.get_token()
        self.header = {"Authorization": f"Bearer {self.token}"}


    def send_api_request(self, endpoint: str, method: str) -> tuple:
        with waitCursor():
            request_method = requests.get if method.lower() == 'get' else requests.post
            response = request_method(self.api_url + endpoint, json=self.credentials)
            status_code = response.status_code
            try:
                response_json = response.json()
            except ValueError:
                response_json = None
            return status_code, response_json

    def get_token(self) -> tuple:
        status_code_login, response_json = self.send_api_request("/login_check", "post")
        token = response_json.get("token") if response_json else None
        return status_code_login, token, response_json

    def upload_zip(self, file):
        return

