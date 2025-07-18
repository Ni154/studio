import os
import shutil
from datetime import datetime

BACKUP_DIR = "backups/"

def criar_backup(diretorio_origem: str):
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino_backup = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    try:
        shutil.copytree(diretorio_origem, destino_backup)
        return True, destino_backup
    except Exception as e:
        return False, str(e)

