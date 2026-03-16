
import os
import logging
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

DEFAULTS: Dict[str, Any] = {
    'backup': True,
    'log_level': 'INFO',
    'date_format': 'dd/mm/yyyy',
    'log_max_bytes': 3 * 1024 * 1024,
    'log_backups': 3,
}


def load_config(config_path: str = 'config.yaml') -> Dict[str, Any]:
    cfg = dict(DEFAULTS)
    if os.path.isfile(config_path) and yaml is not None:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                settings = data.get('settings', {}) if isinstance(data.get('settings'), dict) else {}
                cfg.update(settings)
        except Exception:
            pass
    # Normalize log level
    level = str(cfg.get('log_level', 'INFO')).upper()
    if level not in ('DEBUG','INFO','WARNING','ERROR','CRITICAL'):
        level = 'INFO'
    cfg['log_level'] = level
    return cfg
