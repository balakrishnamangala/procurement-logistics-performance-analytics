"""YAML configuration loader with environment variable substitution."""
import os
import re
import yaml
from pathlib import Path
from typing import Any


def load_config(config_path: str) -> dict[str, Any]:
    """Load YAML config with ${ENV_VAR} substitution."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(path) as f:
        content = f.read()

    # Substitute ${VAR} patterns with environment variables
    def replace_env(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    content = re.sub(r'\$\{(\w+)\}', replace_env, content)
    config = yaml.safe_load(content)

    if config is None:
        raise ValueError(f"Empty config: {config_path}")
    return config
