#!/usr/bin/env python3
"""
Launcher com configurações de rede forçadas para resolver problemas de conectividade
"""

import os
import sys
import time
import socket
import webbrowser
import threading
from datetime import datetime

def check_port_available(port):
    """Verificar se a porta está disponível"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result != 0  # True se porta estiver livre
    except:
        return False

def kill_port_processes(port):
    """Matar processos na porta específica"""
    try:
        import subprocess
        # No Windows, usar netstat e taskkill
        result = subprocess.run(f'netstat -ano | findstr :{port}', 
                              shell=True, capture_output=True, text=True)
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        print(f"Matando processo PID {pid} na porta {port}")
                        subprocess.run(f'taskkill /PID {pid} /F', shell=True, capture_output=True)
    except Exception as e:
        print(f"Erro ao limpar porta: {e}")

def open_browser_delayed():
    """Abrir navegador após delay"""
    time.sleep(3)
    try:
        webbrowser.open('http://127.0.0.1:5000')
        print("Navegador aberto automaticamente")
    except:
        print("Não foi possível abrir o navegador automaticamente")

def test_connection():
    """Testar conectividade"""
    print("Testando conectividade...")
    
    import requests
    max_attempts = 10
    for i in range(max_attempts):
        try:
            response = requests.get('http://127.0.0.1:5000/health', timeout=2)
            if response.status_code == 200:
                print("OK: Conectividade funcionando!")
                return True
        except:
            pass
        
        print(f"Tentativa {i+1}/{max_attempts} falhou, tentando novamente...")
        time.sleep(1)
    
    print("FALHA na conectividade")
    return False

def main():
    port = 5000
    
    print("=" * 60)
    print("    GERADOR RPA DOC - VERSÃO ULTRA ESTÁVEL")
    print("=" * 60)
    print()
    
    print("Verificando ambiente...")
    print(f"Python: {sys.version}")
    print(f"Diretorio: {os.getcwd()}")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Limpar porta se necessário
    if not check_port_available(port):
        print(f"AVISO: Porta {port} em uso, limpando...")
        kill_port_processes(port)
        time.sleep(2)
    
    if check_port_available(port):
        print(f"OK: Porta {port} disponivel")
    else:
        print(f"ERRO: Porta {port} ainda ocupada")
        print("\nSOLUCOES:")
        print("1. Reinicie o computador")
        print("2. Execute como Administrador")
        print("3. Use porta diferente")
        input("\nPressione Enter para tentar mesmo assim...")
    
    print()
    print("INICIANDO SERVIDOR...")
    
    try:
        # Importar aplicação
        from app import app
        print("OK: Aplicacao carregada")
        
        # Configurar para máxima compatibilidade
        app.config.update({
            'DEBUG': False,
            'TESTING': False,
            'THREADED': True,
            'USE_RELOADER': False
        })
        
        print()
        print("CONFIGURACOES DE REDE:")
        print("   - Host: 0.0.0.0 (aceita de qualquer IP)")
        print("   - Porta: 5000")
        print("   - URLs de acesso:")
        print("     - http://localhost:5000")
        print("     - http://127.0.0.1:5000")
        print("     - http://0.0.0.0:5000")
        
        # Obter IP local
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"     - http://{local_ip}:5000")
        except:
            pass
        
        print()
        print("IMPORTANTE:")
        print("   - Se aparecer alerta do Firewall: CLIQUE EM 'PERMITIR'")
        print("   - Para parar: Pressione Ctrl+C")
        print("   - Navegador abrira automaticamente em 3 segundos")
        print()
        print("=" * 60)
        
        # Thread para abrir navegador
        browser_thread = threading.Thread(target=open_browser_delayed)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Thread para testar conectividade
        def test_later():
            time.sleep(5)
            test_connection()
        
        test_thread = threading.Thread(target=test_later)
        test_thread.daemon = True
        test_thread.start()
        
        # Iniciar servidor com configurações forçadas
        print("Iniciando servidor Flask...")
        app.run(
            host='0.0.0.0',    # CRUCIAL: Aceitar de qualquer IP
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True,
            use_debugger=False,
            passthrough_errors=False
        )
        
    except KeyboardInterrupt:
        print("\nServidor parado pelo usuario")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\nERRO: Porta {port} ja esta em uso!")
            print("\nSOLUCOES:")
            print("1. Feche outros servidores na porta 5000")
            print("2. Execute: netstat -ano | findstr :5000")
            print("3. Mate o processo com: taskkill /PID [PID] /F")
            print("4. Ou reinicie o computador")
        else:
            print(f"\nERRO DE REDE: {e}")
            print("\nSOLUCOES:")
            print("1. Execute como Administrador")
            print("2. Verifique Windows Firewall")
            print("3. Desative temporariamente antivirus")
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        print(traceback.format_exc())
        print("\nSOLUCOES:")
        print("1. Instale dependencias: pip install -r requirements.txt")
        print("2. Verifique se todos os modulos estao presentes")
        print("3. Execute como Administrador")
    
    print("\n" + "=" * 60)
    print("Pressione Enter para sair...")
    try:
        input()
    except:
        pass

if __name__ == "__main__":
    main()