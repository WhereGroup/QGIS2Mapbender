import json

import paramiko
from qgis._core import QgsMessageLog, Qgis

from mapbender_plugin.settings import TAG


class MapbenderUpload():
    def __init__(self, host, user, mb_app_path):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.WarningPolicy())
        self.client.connect(hostname=host, username=user)
        self.mb_app_path = mb_app_path

    def run_mapbender_command(self, command: str):
        stdin, stdout, stderr = (
            self.client.exec_command(f"cd ..; cd {self.mb_app_path}; bin/console mapbender:{command}"))
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode("utf-8")
        error_output = stderr.read().decode("utf-8")
        return exit_status, output, error_output

    def wms_parse_url_validate(self, url: str):
        exit_status, output, error_output = self.run_mapbender_command(f"wms:parse:url --validate '{url}'")
        return exit_status, output, error_output

    def wms_show(self, url: str):
        """
        Displays layer information of a persisted WMS source.
        Parses the url of the WMS Source to get the information.
        :param url: url of the WMS Source
        :return: exit_status (0 = success, 1 = fail),
        :return: sources_ids (list with sources ids if available)
        """
        exit_status, output, error_output = self.run_mapbender_command(f"wms:show --json '{url}'")
        #     if options:
        #         options_string = " ".join(("--{option}" for option in options))
        #     ... = run_app_console_mapbender_command(f"wms:parse:url {options_string if options_string else ''} {wms_id} {file_path}")
        #     ...
        if exit_status == 0:
            parsed_json = json.loads(output)
            sources_ids = [obj["id"] for obj in parsed_json]
            return exit_status, sources_ids
        else:
            sources_ids = []
            return exit_status,  sources_ids

    def wms_add(self, url: str):
        """
        Adds a new WMS Source to your Mapbender Service repository.
        :param url: url of the WMS Source
        :return: exit_status (0 = success, 1 = fail),
        :return: source_id (id of the new added source)
        """
        exit_status, output, error_output = self.run_mapbender_command(f"wms:add '{url}'")
        if exit_status == 0 and output:
            spl = 'Saved new source #'
            source_id = output.split(spl,1)[1]
            return exit_status, source_id
        else:
            source_id = ''
            return exit_status, source_id


    def wms_reload(self, id, url: str):
        """
        Reloads (updates) a WMS source from given url.
        :param id: existing source id
        :param url: url of the WMS Source
        :return: exit_status (0 = success, 1 = fail)
        """
        exit_status, output, error_output = self.run_mapbender_command(f"wms:reload:url {id} '{url}'")
        return exit_status, output, error_output

    def app_clone(self, template_slug):
        """
        Clones an existing application in the Application backend. This will create a new application with
        a _imp suffix as application name.
        :param template_slug: template slug to clone
        :return: exit_status (0 = success, 1 = fail),
        :return:slug of the new clone app
        :return:error_output
        """
        exit_status, output, error_output = self.run_mapbender_command(f"application:clone '{template_slug}'")
        if output != '':
            spl = 'slug'
            slug = (output.split(spl,1)[1]).split(',')[0].strip()
            return exit_status, slug, error_output
        else:
            slug = ''
            return exit_status, slug, error_output

    def wms_assign(self, slug, source_id, layer_set):
        """
        :param slug:
        :param source_id:
        :param layer_set:
        :return: exit_status (0 = success, 1 = fail), output, error_output
        """
        exit_status, output, error_output = (
            self.run_mapbender_command(f"wms:assign '{slug}' '{source_id}' '{layer_set}'"))
        QgsMessageLog.logMessage(f"wms:assign '{slug}' '{source_id}' '{layer_set}'", TAG, level=Qgis.Info)
        return exit_status, output, error_output

    def close_connection(self):
        self.client.close()

