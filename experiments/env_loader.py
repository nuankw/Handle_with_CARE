import os
import re
from dotenv import load_dotenv, dotenv_values

def mask_sensitive_keys(config: dict) -> dict:
    # Match anything ending in _KEY, _SECRET, _TOKEN (case-insensitive)
    sensitive_pattern = re.compile(r".*(key|secret|token)$", re.IGNORECASE)

    return {
        k: "***HIDDEN***" if sensitive_pattern.match(k) else v
        for k, v in config.items()
    }

def load_env(env: str = "dev", override: bool = True):
    """
    Load either `.env.dev` or `.env.prod`.

    Args:
        env (str): Either "dev" or "prod".
        override (bool): Whether to overwrite existing env vars.
    """
    env_file = f"envs/.env.{env}"
    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file, override=override)
        print(f"Loaded environment from: {env_file}")
        config = dotenv_values(dotenv_path=env_file)
        masked_config = mask_sensitive_keys(config)
        print(f"Configured environment variables: {masked_config}")
    else:
        raise FileNotFoundError(f"Could not find {env_file}.")
    

if __name__ == "__main__":
    # load_env("dev")
    # load_env("final")
    load_env("example")