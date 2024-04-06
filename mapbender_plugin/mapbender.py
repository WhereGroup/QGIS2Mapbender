import json

from qgis._core import QgsMessageLog, Qgis

from mapbender_plugin.helpers import waitCursor
from mapbender_plugin.settings import TAG


class MapbenderUpload():
    def __init__(self, server_config, wms_url):
        self.server_config = server_config
        self.wms_url = wms_url

    def run_mapbender_command(self, connection, command: str) -> str:
        """
            Executes a Mapbender command using the provided connection.

            Args:
                connection: An instance of fabric.connection.Connection.

            Returns:
                exit_status (int): The exit status of the executed command.
                output (str): The standard output (stdout) from the command.
                error_output (str): The standard error output (stderr) from the command.
            """
        with waitCursor():
            result = connection.run(
                f"cd ..; cd {self.server_config.mb_app_path}; bin/console mapbender:{command}")
            exit_status = result.exited
            output = result.stdout
            error_output = result.stderr
            return exit_status, output, error_output

    def wms_show(self, connection):
        """
        Displays layer information of a persisted WMS source.
        Parses the url of the WMS Source to get the information.
        :param url: url of the WMS Source
        :return: exit_status (0 = success, 1 = fail),
        :return: sources_ids (list with sources ids if available)
        """
        exit_status, output, error_output = self.run_mapbender_command(connection, f"wms:show --json '{self.wms_url}'")
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

    def wms_add(self, connection):
        """
        Adds a new WMS Source to your Mapbender Service repository.
        :param url: url of the WMS Source
        :return: exit_status (0 = success, 1 = fail),
        :return: source_id (id of the new added source)
        """
        exit_status, output, error_output = self.run_mapbender_command(connection, f"wms:add '{self.wms_url}'")
        if exit_status == 0 and output:
            spl = 'Saved new source #'
            source_id = output.split(spl,1)[1]
            return exit_status, source_id
        else:
            source_id = ''
            return exit_status, source_id


    def wms_reload(self, connection, id):
        """
        Reloads (updates) a WMS source from given url.
        :param id: existing source id
        :param url: url of the WMS Source
        :return: exit_status (0 = success, 1 = fail)
        """
        exit_status, output, error_output = self.run_mapbender_command(connection, f"wms:reload:url {id} '{self.wms_url}'")
        return exit_status, output, error_output

    def app_clone(self, connection, template_slug):
        """
        Clones an existing application in the Application backend. This will create a new application with
        a _imp suffix as application name.
        :param template_slug: template slug to clone
        :return: exit_status (0 = success, 1 = fail),
        :return:slug of the new clone app
        :return:error_output
        """
        exit_status, output, error_output = self.run_mapbender_command(connection, f"application:clone '{template_slug}'")
        if output != '':
            spl = 'slug'
            slug = (output.split(spl,1)[1]).split(',')[0].strip()
            return exit_status, slug, error_output
        else:
            slug = ''
            return exit_status, slug, error_output

    def wms_assign(self, connection, slug, source_id, layer_set):
        """
        :param slug:
        :param source_id:
        :param layer_set:
        :return: exit_status (0 = success, 1 = fail), output, error_output
        """
        exit_status, output, error_output = (
            self.run_mapbender_command(connection, f"wms:assign '{slug}' '{source_id}' '{layer_set}'"))
        QgsMessageLog.logMessage(f"wms:assign '{slug}' '{source_id}' '{layer_set}'", TAG, level=Qgis.Info)
        return exit_status, output, error_output


