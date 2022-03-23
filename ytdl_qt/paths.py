import os
import pathlib
from typing import Optional


class Paths:
    app_name = 'ytdl-qt'
    history_file = 'url-history.csv'
    config_name = 'config.ini'

    @staticmethod
    def get_history_path():
        if os.name == 'nt':
            return pathlib.Path(
                os.getenv('APPDATA'),
                Paths.app_name,
                Paths.history_file
            )
        elif os.name == 'posix':
            return pathlib.Path(
                os.getenv('XDG_DATA_HOME', default=f"{os.getenv('HOME')}/.local/share"),
                Paths.app_name,
                Paths.history_file
            )
        else:
            assert True is False, 'Unknown OS'

    @staticmethod
    def find_in_path(name: str) -> Optional[str]:
        if os.path.isfile(name):
            return os.path.abspath(name)
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                final = os.path.join(path, name)
                if os.path.isfile(final):
                    return final
        return None

    @staticmethod
    def get_config_path() -> pathlib.Path:
        if os.name == 'nt':
            return pathlib.Path(
                os.getenv('APPDATA'),
                Paths.app_name,
                Paths.config_name
            )
        elif os.name == 'posix':
            return pathlib.Path(
                os.getenv('XDG_CONFIG_HOME', default=f"{os.getenv('HOME')}/.config"),
                Paths.app_name,
                Paths.config_name
            )
        else:
            assert True is False, 'Unknown OS'

    @staticmethod
    def get_userdata_dir() -> pathlib.Path:
        if os.name == 'nt':
            return pathlib.Path(
                os.getenv('APPDATA'),
                Paths.app_name
            )
        elif os.name == 'posix':
            return pathlib.Path(
                os.getenv('XDG_DATA_HOME', default=f"{os.getenv('HOME')}/.local/share"),
                Paths.app_name
            )
        else:
            assert True is False, 'Unknown OS'

    @staticmethod
    def get_ffmpeg_path() -> Optional[str]:
        if os.name == 'nt':
            name = 'ffmpeg.exe'
        else:
            name = 'ffmpeg'
        return Paths.find_in_path(name)
