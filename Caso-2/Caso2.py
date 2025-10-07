import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import json
import time
import psutil
import os
import threading
from queue import Queue
from datetime import datetime
import re

# Configurar directorio de salida
OUTPUT_DIR = "Caso-2/output"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Directorio '{OUTPUT_DIR}' creado para almacenar archivos generados.")

# Configuraciones de los diferentes LLMs - Solo Ollama
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# Configuración para Coordinador Principal (Llama3)
ollama_config_llama3 = {
    "config_list": [
        {
            "base_url": OLLAMA_BASE_URL,
            "api_key": "fake-key",
            "model": "llama3",
        }
    ],
}

# Configuración para modelos Ollama
ollama_config_codeqwen = {
    "config_list": [
        {
            "base_url": OLLAMA_BASE_URL,
            "api_key": "fake-key",
            "model": "codeqwen",
        }
    ],
}

ollama_config_codellama = {
    "config_list": [
        {
            "base_url": OLLAMA_BASE_URL,
            "api_key": "fake-key", 
            "model": "codellama",
        }
    ],
}

ollama_config_mistral = {
    "config_list": [
        {
            "base_url": OLLAMA_BASE_URL,
            "api_key": "fake-key",
            "model": "mistral",
        }
    ],
}

# FUNCIÓN MEJORADA PARA EXTRAER Y GUARDAR CÓDIGO AUTOMÁTICAMENTE
def extract_and_save_code(message_content, agent_name):
    """Extrae código de los mensajes y lo guarda automáticamente en archivos"""
    
    if not message_content or not isinstance(message_content, str):
        return []
    
    files_created = []
    
    # PRIMERO: Buscar comentarios que especifiquen nombre de archivo
    # Patrones como: # snake_logic.py, # output/snake_logic.py, etc.
    file_comment_pattern = r'#\s*(?:output/)?([a-zA-Z0-9_]+\.(?:py|txt|md))'
    file_comments = re.findall(file_comment_pattern, message_content)
    
    # Patrón para capturar bloques de código con o sin especificador de lenguaje
    code_patterns = [
        r'```python\s*\n(.*?)```',
        r'```(?:txt|text|markdown|md|)\s*\n(.*?)```',
        r'```\s*\n(.*?)```',
    ]
    
    all_code_blocks = []
    for pattern in code_patterns:
        matches = re.findall(pattern, message_content, re.DOTALL | re.IGNORECASE)
        all_code_blocks.extend(matches)
    
    # Si no hay bloques de código explícitos, buscar código suelto
    if not all_code_blocks:
        lines = message_content.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(kw) for kw in ['import ', 'from ', 'class ', 'def ', '@']):
                in_code = True
            
            if in_code:
                code_lines.append(line)
                if not stripped or (stripped and not any(c in stripped for c in ['(', ')', ':', '=', '[', ']', '{', '}']) and len(stripped.split()) > 5):
                    if len(code_lines) > 10:
                        all_code_blocks.append('\n'.join(code_lines))
                    code_lines = []
                    in_code = False
    
    # Procesar cada bloque de código encontrado
    for idx, code_block in enumerate(all_code_blocks):
        code_block = code_block.strip()
        
        if len(code_block) < 30:  # Ignorar bloques muy pequeños
            continue
        
        filename = None
        
        # ESTRATEGIA 1: Buscar comentario con nombre de archivo en el bloque
        first_lines = '\n'.join(code_block.split('\n')[:5])
        file_match = re.search(r'#\s*(?:output/)?([a-zA-Z0-9_]+\.(?:py|txt|md))', first_lines)
        if file_match:
            filename = file_match.group(1)
            # Limpiar el comentario del código
            code_block = re.sub(r'^#\s*(?:output/)?[a-zA-Z0-9_]+\.(?:py|txt|md).*?\n', '', code_block, count=1, flags=re.MULTILINE)
        
        # ESTRATEGIA 2: Detectar por contenido del código
        if not filename:
            # Python files
            if any(keyword in code_block for keyword in ['import ', 'class ', 'def ']):
                # Detectar snake_logic.py
                if ('class Snake' in code_block or 'class Food' in code_block or 'class GameState' in code_block) and 'pygame' not in code_block.lower():
                    filename = 'snake_logic.py'
                
                # Detectar snake_game.py
                elif 'pygame' in code_block.lower() and any(x in code_block for x in ['class ', 'def ']):
                    filename = 'snake_game.py'
                
                # Detectar test files
                elif 'unittest' in code_block and ('class Test' in code_block or 'def test_' in code_block):
                    filename = 'test_snake.py'
                
                # Detectar config files
                elif 'config' in code_block.lower() and 'class' in code_block:
                    filename = 'config.py'
                
                # Detectar utils/helpers
                elif any(word in code_block.lower() for word in ['helper', 'util', 'tool']):
                    filename = 'utils.py'
                
                # Archivo genérico basado en la primera clase o función
                elif not filename:
                    class_match = re.search(r'class\s+([A-Za-z0-9_]+)', code_block)
                    if class_match:
                        filename = f"{class_match.group(1).lower()}.py"
                    else:
                        def_match = re.search(r'def\s+([a-z_][a-z0-9_]*)', code_block)
                        if def_match:
                            filename = f"{def_match.group(1)}.py"
            
            # README files
            elif code_block.startswith('#') and any(word in code_block.lower() for word in ['snake', 'game', 'project', 'installation', 'usage']):
                filename = 'README.md'
            
            # Requirements files
            elif any(pkg in code_block.lower() for pkg in ['pygame', 'numpy', 'pytest', '==', '>=']):
                filename = 'requirements.txt'
            
            # Config files (JSON, YAML, etc)
            elif code_block.strip().startswith('{') or 'version:' in code_block:
                filename = 'config.json' if '{' in code_block else 'config.yaml'
        
        # ESTRATEGIA 3: Usar nombre genérico si no se puede detectar
        if not filename:
            if 'import' in code_block or 'class' in code_block or 'def' in code_block:
                filename = f'generated_code_{idx}.py'
            elif code_block.startswith('#'):
                filename = f'document_{idx}.md'
            else:
                filename = f'file_{idx}.txt'
        
        # Guardar archivo si no existe ya
        if filename and filename not in files_created:
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            # Si el archivo ya existe, no sobrescribirlo a menos que el nuevo código sea más largo
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                if len(existing_content) >= len(code_block):
                    print(f"⏭️  [{agent_name}] -> {filename} ya existe con más contenido, saltando...")
                    continue
            
            try:
                # Auto-completar imports si es necesario
                if filename.endswith('.py'):
                    if 'snake_logic' in filename:
                        if 'import random' not in code_block:
                            code_block = 'import random\n' + code_block
                        if 'from enum import Enum' not in code_block and 'Enum' in code_block:
                            code_block = 'from enum import Enum\n' + code_block
                    elif 'snake_game' in filename or 'game' in filename.lower():
                        if 'import pygame' not in code_block and 'pygame' in code_block.lower():
                            code_block = 'import pygame\nimport sys\n' + code_block
                    elif 'test' in filename:
                        if 'import unittest' not in code_block:
                            code_block = 'import unittest\n' + code_block
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(code_block)
                files_created.append(filename)
                print(f"✅ [{agent_name}] -> {filename} guardado ({len(code_block)} caracteres)")
            except Exception as e:
                print(f"❌ Error guardando {filename}: {e}")
    
    return files_created

# CLASE CUSTOM PARA INTERCEPTAR MENSAJES
class CustomGroupChatManager(GroupChatManager):
    """Manager personalizado que intercepta y procesa mensajes"""
    
    def _process_received_message(self, message, sender, silent):
        """Sobrescribimos este método para interceptar mensajes"""
        # Procesar el mensaje primero
        result = super()._process_received_message(message, sender, silent)
        
        # Extraer código si el mensaje lo contiene
        if isinstance(message, dict) and "content" in message:
            content = message["content"]
            sender_name = sender.name if hasattr(sender, 'name') else "Unknown"
            
            if sender_name in ['DesarrolladorLogica', 'DesarrolladorInterfaz', 'TesterDebugger', 'Documentador']:
                if '```' in content:
                    print(f"\n🔍 Interceptado mensaje de {sender_name}, extrayendo código...")
                    extract_and_save_code(content, sender_name)
        
        return result

# AGENTE COORDINADOR PRINCIPAL
coordinador_principal = AssistantAgent(
    name="CoordinadorPrincipal",
    system_message="""Eres el Coordinador Principal. Tu trabajo es pedir a cada agente que genere su archivo.

PROCESO SIMPLE:
1. Pide a DesarrolladorLogica que genere snake_logic.py
2. Pide a DesarrolladorInterfaz que genere snake_game.py
3. Pide a TesterDebugger que genere test_snake.py
4. Pide a Documentador que genere README.md y requirements.txt

Coordina paso a paso. Cuando todos los archivos estén listos, di: "COMPLETADO".""",
    llm_config=ollama_config_llama3,
)

# AGENTE DESARROLLADOR DE LÓGICA
desarrollador_logica = AssistantAgent(
    name="DesarrolladorLogica",
    system_message="""Genera el archivo snake_logic.py con las clases Snake, Food y GameState.

IMPORTANTE: Genera código completo y funcional en un bloque ```python

Ejemplo mínimo:
```python
import random
from enum import Enum

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Snake:
    def __init__(self):
        self.body = [(10, 10)]
        self.direction = Direction.RIGHT
    
    def move(self):
        head_x, head_y = self.body[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)
        self.body.insert(0, new_head)
        self.body.pop()
    
    def grow(self):
        self.body.append(self.body[-1])

class Food:
    def __init__(self, width, height):
        self.position = (random.randint(0, width-1), random.randint(0, height-1))

class GameState:
    def __init__(self):
        self.snake = Snake()
        self.food = Food(40, 30)
        self.score = 0
        self.game_over = False
```

Genera AHORA el código completo.""",
    llm_config=ollama_config_codeqwen,
)

desarrollador_interfaz = AssistantAgent(
    name="DesarrolladorInterfaz", 
    system_message="""Genera snake_game.py con la interfaz Pygame.

Genera código completo en un bloque ```python que importe de snake_logic.

Debe incluir:
- Importar pygame y clases de snake_logic
- Clase SnakeGame con init, handle_events, update, render, run
- Bucle principal del juego
- if __name__ == "__main__"

Genera AHORA el código completo.""",
    llm_config=ollama_config_codeqwen,
)

tester_debugger = AssistantAgent(
    name="TesterDebugger",
    system_message="""Genera test_snake.py con tests unitarios.

Genera código completo en un bloque ```python con:
- import unittest
- from snake_logic import Snake, Food, GameState
- Clases TestSnake con varios test_
- if __name__ == '__main__': unittest.main()

Genera AHORA el código completo.""",
    llm_config=ollama_config_codellama,
)

documentador = AssistantAgent(
    name="Documentador",
    system_message="""Genera README.md y requirements.txt.

Primero requirements.txt en un bloque ```txt:
```txt
pygame>=2.5.0
```

Luego README.md en un bloque ```markdown con:
- Título
- Descripción
- Instalación
- Uso
- Controles

Genera AHORA ambos archivos.""",
    llm_config=ollama_config_mistral,
)

# AGENTE COORDINADOR LOCAL
coordinador_usuario = UserProxyAgent(
    name="CoordinadorUsuario",
    human_input_mode="NEVER",
    code_execution_config=False,
    max_consecutive_auto_reply=1,
    is_termination_msg=lambda msg: "completado" in msg.get("content", "").lower(),
)

# Framework de testing
class Caso2TestFramework:
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
        self.results = {}
    
    def validate_files_created(self):
        """Valida archivos creados"""
        expected_files = ['snake_logic.py', 'snake_game.py', 'test_snake.py', 'README.md', 'requirements.txt']
        created_files = []
        
        if os.path.exists(OUTPUT_DIR):
            created_files = [f for f in os.listdir(OUTPUT_DIR) if f in expected_files]
        
        return {
            "expected": expected_files,
            "created": created_files,
            "completion": len(created_files) / len(expected_files) * 100
        }
    
    def generate_report(self):
        """Genera reporte final"""
        files_info = self.validate_files_created()
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "files": files_info,
            "execution_time": round(time.time() - self.start_time, 2)
        }
        
        report_path = os.path.join(OUTPUT_DIR, "caso2_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n{'='*50}")
        print(f"REPORTE FINAL")
        print(f"{'='*50}")
        print(f"Archivos creados: {len(files_info['created'])}/5")
        print(f"Completitud: {files_info['completion']:.1f}%")
        print(f"Tiempo: {self.results['execution_time']}s")
        
        for file in files_info['created']:
            filepath = os.path.join(OUTPUT_DIR, file)
            size = os.path.getsize(filepath)
            print(f"  ✅ {file} ({size} bytes)")
        
        for file in files_info['expected']:
            if file not in files_info['created']:
                print(f"  ❌ {file} (no generado)")

# Configurar chat grupal
participantes = [coordinador_usuario, coordinador_principal, desarrollador_logica, 
                desarrollador_interfaz, tester_debugger, documentador]

chat_grupal = GroupChat(
    agents=participantes,
    messages=[],
    max_round=12,
    speaker_selection_method="round_robin",
)

gestor = CustomGroupChatManager(groupchat=chat_grupal, llm_config=ollama_config_llama3)

# Inicializar framework
test_framework = Caso2TestFramework()

# Mensaje inicial
mensaje_inicial = """Inicia el desarrollo del juego Snake.

Cada agente debe generar su archivo:
- DesarrolladorLogica: snake_logic.py
- DesarrolladorInterfaz: snake_game.py
- TesterDebugger: test_snake.py
- Documentador: README.md y requirements.txt

Genera código completo en bloques ```python

CoordinadorPrincipal: Coordina a cada agente paso a paso."""

# Ejecutar
try:
    print("="*50)
    print("INICIANDO DESARROLLO SNAKE")
    print("="*50)
    
    coordinador_usuario.initiate_chat(gestor, message=mensaje_inicial)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Procesar mensajes al final como fallback
    print("\n" + "="*50)
    print("POST-PROCESAMIENTO DE MENSAJES")
    print("="*50)
    
    if hasattr(chat_grupal, 'messages'):
        for msg in chat_grupal.messages:
            if isinstance(msg, dict) and 'content' in msg and 'name' in msg:
                sender_name = msg['name']
                content = msg['content']
                if sender_name in ['DesarrolladorLogica', 'DesarrolladorInterfaz', 'TesterDebugger', 'Documentador']:
                    if '```' in content:
                        print(f"\n📝 Procesando mensaje almacenado de {sender_name}...")
                        extract_and_save_code(content, sender_name)
    
    test_framework.generate_report()
    
    print(f"\n{'='*50}")
    print("DESARROLLO FINALIZADO")
    print(f"Archivos en: {OUTPUT_DIR}/")
    print(f"{'='*50}")