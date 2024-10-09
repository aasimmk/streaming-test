import os
import json
from dotenv import load_dotenv
from typing import Any, Optional


class ConfigLoader:
    def __init__(self, dotenv_filename: Optional[str] = ".env") -> None:
        """
        Load the .env file and initialize config variables.

        :param dotenv_filename: Name of the .env file. `Default: .env`
        """
        dotenv_path = os.path.join(os.path.dirname(__file__), dotenv_filename)
        load_dotenv(dotenv_path)

    @staticmethod
    def _str_to_bool(value: str) -> bool:
        true_values = {'true', '1', 't', 'yes', 'y'}
        false_values = {'false', '0', 'f', 'no', 'n'}
        value_lower = value.strip().lower()
        if value_lower in true_values:
            return True
        elif value_lower in false_values:
            return False
        else:
            raise ValueError(f"Cannot convert '{value}' to bool.")

    @staticmethod
    def _to_int(value: str, key: str) -> int:
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Error converting {key} to int: invalid literal for int() with value '{value}'.")

    @staticmethod
    def _to_float(value: str, key: str) -> float:
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Error converting {key} to float: invalid literal for float() with value '{value}'.")

    @staticmethod
    def _to_list(value: str, key: str) -> list:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise ValueError(f"Error converting {key} to list: invalid JSON format.")

    @staticmethod
    def _to_dict(value: str, key: str) -> dict:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise ValueError(f"Error converting {key} to dict: invalid JSON format.")

    # noinspection PyTypeChecker
    def get(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        Retrieve the environment variable and convert it to the type of the default value.

        :param key: The environment variable key.
        :param default: The default value to return if key is not found.
        :param required: If True, raise an error if the variable is not found and no default is provided.
        :return: The value of the environment variable in the type of the default value.
        """
        value = os.getenv(key, default)

        if value is None:
            if required:
                raise ValueError(f"Required environment variable '{key}' is missing.")
            else:
                return value

        if isinstance(value, bool):
            return self._str_to_bool(value)
        elif isinstance(value, int):
            return self._to_int(value, key)
        elif isinstance(value, float):
            return self._to_float(value, key)
        elif isinstance(value, list):
            return self._to_list(value, key)
        elif isinstance(value, dict):
            return self._to_dict(value, key)
        elif isinstance(value, str):
            return value
        else:
            raise ValueError(f"Unsupported default type: {type(default)} for key: {key}")


env = ConfigLoader()

SECRET_KEY = env.get("SECRET_KEY", required=True)
ALGORITHM = env.get("ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(env.get("ACCESS_TOKEN_EXPIRE_MINUTES", default=60))
