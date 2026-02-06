"""
main.py - 小铁皮入口
"""

import os
import sys
from pathlib import Path

# 日志文件用于调试
LOG_FILE = Path.home() / '.xiaotiepi' / 'debug.log'

def log(msg):
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(f"{msg}\n")
    except:
        pass

log("=== App starting ===")

# 修复 py2app 打包后的 SSL 证书路径问题
def setup_ssl_certificates():
    try:
        import certifi
        cert_path = certifi.where()
        os.environ['SSL_CERT_FILE'] = cert_path
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
        log(f"Cert exists: {os.path.exists(cert_path)}")
    except Exception as e:
        log(f"certifi error: {e}")

setup_ssl_certificates()

# 预先导入并初始化 anthropic SDK
log("Pre-importing anthropic SDK...")
_anthropic_client = None
try:
    import httpcore
    log("httpcore OK")
    import httpx
    log("httpx OK")
    import anthropic
    log(f"anthropic OK: {anthropic.__version__}")

    # 尝试获取 API key 并创建 client
    from paper_agent.api_key_manager import get_api_key
    _api_key = get_api_key()
    if _api_key:
        log("Creating test client...")
        _anthropic_client = anthropic.Anthropic(api_key=_api_key)
        log("Client created OK!")
    else:
        log("No API key found")
except BaseException as e:
    import traceback
    log(f"Pre-import FAILED: {type(e).__name__}: {e}")
    log(traceback.format_exc())

log("Starting Pet...")
from pet import Pet

if __name__ == '__main__':
    pet = Pet()
    pet.run()
