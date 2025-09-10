"""
Módulo para gerenciar arquivos usando Google Cloud Storage
Este módulo é opcional e pode ser usado para armazenar arquivos JSON no GCS
em vez do sistema de arquivos local.
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Tenta importar Google Cloud Storage
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("Google Cloud Storage não está disponível. Usando armazenamento local.")

class StorageManager:
    """Gerenciador de armazenamento que pode usar GCS ou sistema de arquivos local"""
    
    def __init__(self, bucket_name=None):
        self.use_gcs = GCS_AVAILABLE and bucket_name and os.environ.get('USE_GCS', 'false').lower() == 'true'
        self.bucket_name = bucket_name
        self.bucket = None
        
        if self.use_gcs:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(bucket_name)
                logger.info(f"Usando Google Cloud Storage: {bucket_name}")
            except Exception as e:
                logger.error(f"Erro ao conectar ao GCS: {e}")
                self.use_gcs = False
        
        if not self.use_gcs:
            logger.info("Usando sistema de arquivos local")
    
    def read_json(self, filepath):
        """Lê um arquivo JSON do GCS ou sistema local"""
        if self.use_gcs:
            try:
                blob = self.bucket.blob(filepath)
                content = blob.download_as_text()
                return json.loads(content)
            except Exception as e:
                logger.error(f"Erro ao ler {filepath} do GCS: {e}")
                # Fallback para arquivo local
                return self._read_local_json(filepath)
        else:
            return self._read_local_json(filepath)
    
    def write_json(self, filepath, data):
        """Escreve um arquivo JSON no GCS ou sistema local"""
        if self.use_gcs:
            try:
                blob = self.bucket.blob(filepath)
                content = json.dumps(data, ensure_ascii=False, indent=2)
                blob.upload_from_string(content, content_type='application/json')
                logger.info(f"Arquivo {filepath} salvo no GCS")
                # Também salva localmente como backup
                self._write_local_json(filepath, data)
                return True
            except Exception as e:
                logger.error(f"Erro ao escrever {filepath} no GCS: {e}")
                # Fallback para arquivo local
                return self._write_local_json(filepath, data)
        else:
            return self._write_local_json(filepath, data)
    
    def _read_local_json(self, filepath):
        """Lê um arquivo JSON do sistema local"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Arquivo {filepath} não encontrado")
            return None
        except Exception as e:
            logger.error(f"Erro ao ler arquivo local {filepath}: {e}")
            return None
    
    def _write_local_json(self, filepath, data):
        """Escreve um arquivo JSON no sistema local"""
        try:
            # Cria diretório se não existir
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Escreve de forma atômica
            tmp_path = f"{filepath}.tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, filepath)
            return True
        except Exception as e:
            logger.error(f"Erro ao escrever arquivo local {filepath}: {e}")
            return False
    
    def list_files(self, prefix=''):
        """Lista arquivos no GCS ou sistema local"""
        if self.use_gcs:
            try:
                blobs = self.bucket.list_blobs(prefix=prefix)
                return [blob.name for blob in blobs]
            except Exception as e:
                logger.error(f"Erro ao listar arquivos do GCS: {e}")
                return []
        else:
            # Lista arquivos locais
            files = []
            for root, dirs, filenames in os.walk(prefix or '.'):
                for filename in filenames:
                    if filename.endswith('.json'):
                        files.append(os.path.join(root, filename))
            return files
    
    def delete_file(self, filepath):
        """Deleta um arquivo do GCS ou sistema local"""
        if self.use_gcs:
            try:
                blob = self.bucket.blob(filepath)
                blob.delete()
                logger.info(f"Arquivo {filepath} deletado do GCS")
                # Também deleta localmente
                self._delete_local_file(filepath)
                return True
            except Exception as e:
                logger.error(f"Erro ao deletar {filepath} do GCS: {e}")
                return self._delete_local_file(filepath)
        else:
            return self._delete_local_file(filepath)
    
    def _delete_local_file(self, filepath):
        """Deleta um arquivo do sistema local"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo local {filepath}: {e}")
            return False
    
    def backup_file(self, filepath):
        """Cria backup de um arquivo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{filepath}.backup_{timestamp}"
        
        data = self.read_json(filepath)
        if data:
            return self.write_json(backup_name, data)
        return False

# Função para obter bucket name do Secret Manager
def get_bucket_name():
    """Obtém o nome do bucket do Secret Manager ou variável de ambiente"""
    try:
        from google.cloud import secretmanager
        if os.environ.get('FLASK_ENV') == 'production':
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('PROJECT_ID')
            if project_id:
                name = f"projects/{project_id}/secrets/quiz-gcs-bucket/versions/latest"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.warning(f"Erro ao obter bucket do Secret Manager: {e}")
    
    return os.environ.get('GCS_BUCKET_NAME')

# Instância global do gerenciador de armazenamento
storage_manager = StorageManager(bucket_name=get_bucket_name())

# Funções auxiliares para compatibilidade
def read_json(filepath):
    """Função auxiliar para ler JSON"""
    return storage_manager.read_json(filepath)

def write_json(filepath, data):
    """Função auxiliar para escrever JSON"""
    return storage_manager.write_json(filepath, data)
