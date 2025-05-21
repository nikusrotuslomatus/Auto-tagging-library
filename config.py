import os

CONFIG_FILE_PATH = "config.txt"

def load_config():
    """
    Load key-value pairs from a plain text config file.
    """
    config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

def save_config(config):
    """
    Save key-value pairs to a plain text config file.
    """
    with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")
