import json
import os

from thexp.utils.paths import config_path, _default_config


def write_global_config(dumpsrc: dict):
    """
    write global config
    Notes:
    ------
    User should not call this method directly
    """
    path = config_path()
    with open(path, "w") as w:
        return json.dump(dumpsrc, w, indent=2)


def global_config() -> dict:
    """load global config"""
    path = config_path()
    if not os.path.exists(path):
        write_global_config(_default_config())
    with open(path, "r") as r:
        return json.load(r)


