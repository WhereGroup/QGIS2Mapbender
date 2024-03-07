import json
from enum import Enum
from typing import Iterable, Optional
from fabric2 import Connection
import paramiko
from qgis._core import Qgis, QgsMessageLog

from qgis.utils import iface

TAG = 'Mapbender QGIS-Plugin'

class MapbenderUpload():
    def __init__(self, host, user):
        #self.connection = Connection(host=host,user=user)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.WarningPolicy())
        self.client.connect(hostname=host, username=user)

    def run_mapbender_command(self, command: str):
        stdin, stdout, stderr = self.client.exec_command(f"cd ..; cd /data/mapbender/application/; bin/console mapbender:{command}")
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode("utf-8")
        error_output = stderr.read().decode("utf-8")
        return exit_status, output, error_output

    def wms_parse_url_validate(self, url: str):
        exit_status, output, error_output = self.run_mapbender_command(f"wms:parse:url --validate '{url}'")
        return exit_status, output, error_output

    def wms_show(self, url: str): # output = source-id list
        exit_status, output, error_output = self.run_mapbender_command(f"wms:show --json '{url}'")
        #     if options:
        #         options_string = " ".join(("--{option}" for option in options))
        #     ... = run_app_console_mapbender_command(f"wms:parse:url {options_string if options_string else ''} {wms_id} {file_path}")
        #     ...
        parsed_json = json.loads(output)
        sources_ids = [obj["id"] for obj in parsed_json]  # list
        return exit_status, sources_ids

    def wms_add(self, url: str):
        exit_status, output, error_output = self.run_mapbender_command(f"wms:add '{url}'")
        # output -> source_id
        source_id = 23 # replace after command output is updated
        return exit_status, source_id
    def wms_reload(self, id, url: str): # MAPBENDER CONSOLE OUTPUT PENDING
        exit_status, output, error_output = self.run_mapbender_command(f"wms:reload:url {id} '{url}'")
        return exit_status

    def app_clone(self, slug): # MAPBENDER CONSOLE OUTPUT PENDING
        exit_status, output, error_output = self.run_mapbender_command(f"application:clone '{slug}'")
        # ouput -> slug
        slug = 'template_plugin_imp' # replace after command output is updated
        return exit_status, slug

    def wms_assign(self, slug, source_id):
        exit_status, output, error_output = self.run_mapbender_command(f"wms:assign '{slug}' '{source_id}'")
        return exit_status

    def close_connection(self):
        self.client.close()

