import os
import json
from pathlib import Path

KEY_FILE = Path.home() / '.xiaotiepi' / 'api_key.json'

def get_api_key() -> str:
    if os.environ.get('ANTHROPIC_API_KEY'):
        return os.environ['ANTHROPIC_API_KEY']

    if KEY_FILE.exists():
        try:
            with open(KEY_FILE, 'r') as f:
                data = json.load(f)
                return data.get('anthropic_api_key', '')
        except:
            pass
    return ''

def save_api_key(key: str) -> bool:
    try:
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(KEY_FILE, 'w') as f:
            json.dump({'anthropic_api_key': key}, f)
        return True
    except:
        return False

def has_api_key() -> bool:
    return bool(get_api_key())
