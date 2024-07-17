import os
import json


class Config:
    def __init__(self, default_path="default.json"):
        try:
            with open(default_path) as default_file:
                self.default = json.load(default_file)
        except:
            self.default = dict()

    def __getattr__(self, item):
        env_item = item.upper()
        if env_item in os.environ:
            return os.environ[env_item]
        elif item in self.default:
            return self.default[item]
        else:
            raise AttributeError(f"There is no {item}")

    def as_bool(self, item) -> bool:
        prop = self.__getattr__(item).upper()
        return prop == "TRUE"

    def as_float(self, item, default) -> float:
        try:
            return float(self.__getattr__(item))
        except AttributeError:
            return float(default)

    def as_int(self, item, default) -> int:
        try:
            return int(self.__getattr__(item))
        except AttributeError:
            return int(default)
