#!/usr/bin/env python3
"""
Launcher ultra-estável para a aplicação RPA Doc
Resolve problemas de threading, encoding e dependências
"""

import os
import sys
import time
import signal
import traceback
import logging
from pathlib import Path

# Configurar encoding para Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def setup_logging():
    """Configurar logging sem emojis para evitar problemas de encoding"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def check_dependencies():
    """Verificar dependências críticas"""
    logger = logging.getLogger(__name__)
    required_modules = [
        'flask', 'flask_sqlalchemy', 'PIL', 'openai', 
        'pytesseract', 'docx', 'markdown'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"OK - {module}")
        except ImportError:
            missing.append(module)
            logger.error(f"FALTANDO - {module}")
    
    if missing:
        logger.error(f"Módulos faltando: {missing}")
        logger.info("Execute: pip install -r requirements.txt")
        return False
    return True

def cleanup_handler(signum, frame):
    """Handler para cleanup limpo"""
    logger = logging.getLogger(__name__)
    logger.info("Recebido sinal de parada - fazendo cleanup...")
    sys.exit(0)

def create_stable_app():
    """Criar aplicação com configurações estáveis"""
    logger = logging.getLogger(__name__)
    
    try:
        # Importar aplicação principal (agora é a versão estável)
        import app
        
        # Substituir logs problemáticos
        original_info = app.app.logger.info
        original_error = app.app.logger.error
        
        def safe_info(msg):
            # Remover emojis e caracteres problemáticos
            clean_msg = str(msg).encode('ascii', 'ignore').decode('ascii')
            return original_info(clean_msg)
            
        def safe_error(msg):
            clean_msg = str(msg).encode('ascii', 'ignore').decode('ascii')
            return original_error(clean_msg)
        
        app.app.logger.info = safe_info
        app.app.logger.error = safe_error
        
        # Configurar app para estabilidade
        app.app.config['DEBUG'] = False
        app.app.config['TESTING'] = False
        app.app.config['THREADED'] = True
        
        # Desabilitar auto-reload que causa problemas
        app.app.config['USE_RELOADER'] = False
        
        logger.info("Aplicação carregada com configurações estáveis")
        return app.app
        
    except Exception as e:
        logger.error(f"Erro ao carregar aplicação: {e}")
        logger.error(traceback.format_exc())
        return None

def run_server(app, host='localhost', port=5000):
    """Executar servidor com configurações otimizadas"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 50)
        logger.info("SERVIDOR RPA DOC - MODO ESTÁVEL")
        logger.info(f"URL: http://{host}:{port}")
        logger.info("Para parar: Ctrl+C")
        logger.info("=" * 50)
        
        # Verificar se porta está livre
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, port)) == 0:
                logger.error(f"Porta {port} já está em uso!")
                return False
        
        # Executar servidor
        app.run(
            host=host,
            port=port,
            debug=False,           # Sem debug para estabilidade
            use_reloader=False,    # Sem auto-reload
            threaded=True,         # Threading habilitado
            processes=1,           # Single process
            passthrough_errors=False  # Capturar erros
        )
        
        return True
        
    except KeyboardInterrupt:
        logger.info("Servidor parado pelo usuário")
        return True
    except Exception as e:
        logger.error(f"Erro no servidor: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Função principal com tratamento robusto de erros"""
    
    # Setup inicial
    logger = setup_logging()
    
    # Registrar handlers de cleanup
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        logger.info("Iniciando launcher estável...")
        
        # Verificar ambiente
        logger.info(f"Python: {sys.version}")
        logger.info(f"Diretório: {os.getcwd()}")
        logger.info(f"Plataforma: {sys.platform}")
        
        # Verificar dependências
        if not check_dependencies():
            logger.error("Dependências faltando - abortando")
            input("\nPressione Enter para sair...")
            return 1
        
        # Criar aplicação
        app = create_stable_app()
        if not app:
            logger.error("Falha ao criar aplicação - abortando")
            input("\nPressione Enter para sair...")
            return 1
        
        # Executar servidor
        success = run_server(app)
        if not success:
            logger.error("Falha no servidor")
            input("\nPressione Enter para sair...")
            return 1
            
        return 0
        
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        logger.error(traceback.format_exc())
        
        print("\nSOLUÇÕES POSSÍVEIS:")
        print("1. Execute como Administrador")
        print("2. Verifique Windows Firewall") 
        print("3. Instale dependências: pip install -r requirements.txt")
        print("4. Verifique antivírus")
        
        input("\nPressione Enter para sair...")
        return 1

if __name__ == "__main__":
    sys.exit(main())