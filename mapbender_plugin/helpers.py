import os
import shutil

from PyQt5.QtCore import Qt
from decorator import contextmanager
from fabric2 import Connection
import paramiko

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from qgis._core import QgsApplication, QgsProject, QgsSettings, QgsMessageLog, Qgis
from qgis.utils import iface

from mapbender_plugin.settings import TAG


def get_plugin_dir() -> str:
    plugin_dir = os.path.dirname(__file__)
    return plugin_dir


def get_project_layers() -> list:
    project = QgsProject.instance()
    project.read()
    layers_names = []
    for layer in project.mapLayers().values():
        layers_names.append(layer.name())
    return layers_names


def qgis_project_is_saved() -> bool:
    # Get and check .qgz project path
    source_project_dir_path = QgsProject.instance().readPath("./")
    source_project_file_path = QgsProject.instance().fileName()
    if source_project_dir_path == "./" or source_project_file_path == "":
        show_fail_box_ok('Failed',
                         "Please use the Mapbender Plugin from a saved QGIS-Project")
        return False
    return True


def create_fail_box(title, text):
    failBox = QMessageBox()
    failBox.setIconPixmap(QPixmap(":/images/themes/default/mIconWarning.svg"))
    failBox.setWindowTitle(title)
    failBox.setText(text)
    return failBox


def show_fail_box_ok(title, text):
    failBox = create_fail_box(title, text)
    failBox.setStandardButtons(QMessageBox.Ok)
    return failBox.exec_()


def show_fail_box_yes_no(title, text):
    failBox = create_fail_box(title, text)
    failBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    return failBox.exec_()


def show_succes_box_ok(title, text):
    plugin_dir = get_plugin_dir()
    successBox = QMessageBox()
    successBox.setIconPixmap(QPixmap(plugin_dir + '/resources/icons/mIconSuccess.svg'))
    successBox.setWindowTitle(title)
    successBox.setText(text)
    successBox.setStandardButtons(QMessageBox.Ok)
    return successBox.exec_()


def show_question_box(text):
    questionBox = QMessageBox()
    questionBox.setIcon(QMessageBox.Question)
    questionBox.setText(text)
    questionBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    return questionBox.exec_()


def get_plugin_dir():
    file = os.path.dirname(__file__)
    plugin_dir = os.path.dirname(file) + '/mapbender_plugin'
    return plugin_dir


def list_qgs_settings_child_groups(key):
    s = QgsSettings()
    s.beginGroup(key)
    subkeys = s.childGroups()
    s.endGroup
    return subkeys

@contextmanager
def waitCursor():
    try:
        QgsApplication.setOverrideCursor(Qt.WaitCursor)
        yield
    except Exception as ex:
        raise ex
    finally:
        QgsApplication.restoreOverrideCursor()


def validate_no_spaces(*variables):
    for var in variables:
        if " " in var:
            return False
    return True


def update_mb_slug_in_settings(mb_slug, is_mb_slug):
    s = QgsSettings()
    if s.contains("mapbender-plugin/mb_templates"):
        s.beginGroup('mapbender-plugin/')
        mb_slugs = s.value('mb_templates')
        s.endGroup()
        if isinstance(mb_slugs, str):
            mb_slugs_list = mb_slugs.split(", ")
        elif isinstance(mb_slugs, list):
            mb_slugs_list = mb_slugs
        else:
            raise TypeError("Konnte MB template nicht lesen")

        if is_mb_slug and mb_slug not in mb_slugs_list:
            mb_slugs_list.append(mb_slug)
            updated_mb_slugs = ", ".join(mb_slugs_list)
            s.setValue('mapbender-plugin/mb_templates', updated_mb_slugs)
        elif mb_slug in mb_slugs_list:
            mb_slugs_list.remove(mb_slug)
            updated_mb_slugs = ", ".join(mb_slugs_list)
            s.setValue('mapbender-plugin/mb_templates', updated_mb_slugs)

    elif is_mb_slug:
        s.setValue('mapbender-plugin/mb_templates', mb_slug)
