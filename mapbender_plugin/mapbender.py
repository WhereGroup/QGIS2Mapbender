import json
from enum import Enum
from typing import Iterable, Optional
from fabric2 import Connection
import paramiko
from qgis._core import Qgis

from qgis.utils import iface

TAG = 'Mapbender QGIS-Plugin'

class mapbenderUpload():
    def run_app_console_mapbender_command(command: str):
        with Connection(host='mapbender-qgis.wheregroup.lan', user='root') as c:
            result = c.run(f"cd ..; cd /data/mapbender/application/; bin/console mapbender:{command}")
            if result.ok:
                # Command's output (stdout)
                stdout_output = result.stdout
                # Command's error (stderr)
                stderr_output = result.stderr
                # if stdout_output is JSON:
                try:
                    parsed_json = json.loads(stdout_output)
                    #source_id = parsed_json[0]["id"]
                    ids = [obj["id"] for obj in parsed_json] #list
                    print(ids)
                except json.JSONDecodeError:
                    print(stderr_output)
            else:
                print(f"Error by executing: {result.stderr}")

    def wms_parse_url_validate(url: str):
        mapbenderUpload.run_app_console_mapbender_command(f"wms:parse:url --validate '{url}'")

    def wms_show(url: str):
        mapbenderUpload.run_app_console_mapbender_command(f"wms:show --json '{url}'")


    # def application_clone(application: str):
    #     ... = run_app_console_mapbender_command(f"application:clone {application}")
    #     ...
    #
    # def add_wms(url: str):
    #     ... = run_app_console_mapbender_command(f"wms:add {url}")
    #     ...

    # def wms_reload_file(wms_id: int, file_path: str, options: Optional[Iterable[str]]):
    #     if options:
    #         options_string = " ".join(("--{option}" for option in options))
    #     ... = run_app_console_mapbender_command(f"wms:parse:url {options_string if options_string else ''} {wms_id} {file_path}")
    #     ...

