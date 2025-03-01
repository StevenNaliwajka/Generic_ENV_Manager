import re
from pathlib import Path
from typing import Optional


class ENVUtil:

    @staticmethod
    def create_env(file_path: str, data: dict, overwrite: bool = False) -> None:
        file_path = Path(file_path)

        # Ensure the directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # If the file exists and overwrite is False, raise an error
        if file_path.exists() and not overwrite:
            raise FileExistsError(f"File '{file_path}' already exists.")

        try:
            with file_path.open("w", encoding="utf-8") as file:
                for key, value in data.items():
                    # Convert non-string values to string
                    value = str(value)

                    # Handle values with special characters
                    if "\n" in value:
                        file.write(f"{key}=\"\"\"{value}\"\"\"\n")
                    elif " " in value or "#" in value or "=" in value:
                        file.write(f"{key}=\"{value}\"\n")
                    else:
                        file.write(f"{key}={value}\n")
        except Exception as e:
            raise IOError(f"Unable to write to file '{file_path}': {e}")

    @staticmethod
    def read_env(file_path: str) -> Optional[dict]:
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"Error: File '{file_path}' not found.")
            return None

        try:
            env_data = {}
            with file_path.open("r", encoding="utf-8") as file:
                multi_key, multi_value = None, []
                for line in file:
                    line = line.strip()

                    # Ignore empty lines or full-line comments
                    if not line or line.startswith("#"):
                        continue

                    # Handle multiline values
                    if multi_key:
                        if line.endswith('"""'):
                            multi_value.append(line[:-3])
                            env_data[multi_key] = "\n".join(multi_value).strip()
                            multi_key, multi_value = None, []
                        else:
                            multi_value.append(line)
                        continue

                    # Parse key-value pair
                    key, value = map(str.strip, line.split("=", 1))

                    # Handle multiline start
                    if value.startswith('"""'):
                        multi_key = key
                        multi_value.append(value[3:])
                        continue

                    # Remove inline comments
                    value = re.split(r"\s+#", value, 1)[0].strip()

                    # Handle quoted values
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Convert boolean-like values
                    if value.lower() in ("true", "false"):
                        value = value.lower() == "true"

                    # Convert numeric values
                    elif value.isdigit():
                        value = int(value)
                    elif re.fullmatch(r"[-+]?\d*\.\d+", value):
                        value = float(value)

                    env_data[key] = value

            return env_data

        except Exception as e:
            print(f"Error reading '{file_path}': {e}")
            return None

    @staticmethod
    def update_env(file_path: str, new_data: dict) -> None:
        existing_data = ENVUtil.read_env(file_path) or {}
        existing_data.update(new_data)
        ENVUtil.create_env(file_path, existing_data, overwrite=True)

    @staticmethod
    def delete_env(file_path: str) -> None:
        file_path = Path(file_path)
        if file_path.exists():
            file_path.unlink()
