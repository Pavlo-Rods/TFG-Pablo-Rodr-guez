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

# FUNCIÓN PARA EXTRAER Y GUARDAR CÓDIGO AUTOMÁTICAMENTE
def extract_and_save_code(message_content, agent_name):
    """Extrae código de los mensajes y lo guarda automáticamente en archivos"""
    
    # Patrones para detectar diferentes tipos de código
    patterns = {
        'snake_logic.py': r'```python\s*#.*?snake_logic\.py.*?\n(.*?)```',
        'snake_game.py': r'```python\s*#.*?snake_game\.py.*?\n(.*?)```',
        'test_snake.py': r'```python\s*#.*?test_snake\.py.*?\n(.*?)```',
        'README.md': r'```markdown\s*#.*?README\.md.*?\n(.*?)```',
        'requirements.txt': r'```(?:txt|text)\s*#.*?requirements\.txt.*?\n(.*?)```',
    }
    
    # También buscar patrones más generales
    general_patterns = {
        'snake_logic.py': r'class Snake.*?(?=class \w+|$|\n\n```)',
        'snake_game.py': r'import pygame.*?(?=\n\n```|$)',
        'test_snake.py': r'import unittest.*?(?=\n\n```|$)',
    }
    
    files_created = []
    
    for filename, pattern in patterns.items():
        matches = re.findall(pattern, message_content, re.DOTALL | re.IGNORECASE)
        if matches:
            # Tomar el match más largo (más completo)
            code_content = max(matches, key=len).strip()
            if len(code_content) > 50:  # Solo guardar si tiene contenido sustancial
                filepath = os.path.join(OUTPUT_DIR, filename)
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(code_content)
                    files_created.append(filename)
                    print(f"[OK] {agent_name} -> {filename} guardado ({len(code_content)} chars)")
                except Exception as e:
                    print(f"[ERROR] Error guardando {filename}: {e}")
    
    # Si no encontró archivos específicos, buscar por contenido
    if not files_created:
        if 'class Snake' in message_content and 'snake_logic' not in [f.lower() for f in files_created]:
            code_blocks = re.findall(r'```python\n(.*?)```', message_content, re.DOTALL)
            for block in code_blocks:
                if 'class Snake' in block:
                    filepath = os.path.join(OUTPUT_DIR, 'snake_logic.py')
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(block.strip())
                    files_created.append('snake_logic.py')
                    print(f"[OK] {agent_name} -> snake_logic.py extraido automaticamente")
                    break
        
        if 'pygame' in message_content and 'snake_game' not in [f.lower() for f in files_created]:
            code_blocks = re.findall(r'```python\n(.*?)```', message_content, re.DOTALL)
            for block in code_blocks:
                if 'pygame' in block:
                    filepath = os.path.join(OUTPUT_DIR, 'snake_game.py')
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(block.strip())
                    files_created.append('snake_game.py')
                    print(f"[OK] {agent_name} -> snake_game.py extraido automaticamente")
                    break
    
    return files_created

# AGENTE COORDINADOR PRINCIPAL CON ESCRITURA DE ARCHIVOS
coordinador_principal = AssistantAgent(
    name="CoordinadorPrincipal",
    system_message="""Eres el Coordinador Principal de un sistema multiagente jerárquico para desarrollar el juego Snake usando Llama3.

INSTRUCCIONES CRÍTICAS PARA GENERAR ARCHIVOS:
- Cada vez que coordines una tarea, asegúrate de que el agente genere código COMPLETO
- El código debe estar en bloques ```python con comentarios que especifiquen el nombre del archivo
- Ejemplo correcto:
```python
# output/snake_logic.py
class Snake:
    def __init__(self):
        # código completo aquí
        pass
```

TU ROL COMO LÍDER:
- Liderar y coordinar el desarrollo completo del juego Snake
- EXIGIR que cada agente genere archivos completos y funcionales
- Revisar e integrar las contribuciones de todos los agentes especializados  
- Asegurar que TODOS los archivos se generen correctamente

ARQUITECTURA DEL PROYECTO SNAKE:
1. Lógica del juego (Snake, Food, GameState) -> snake_logic.py
2. Interfaz gráfica (Pygame) -> snake_game.py
3. Testing y validación -> test_snake.py
4. Documentación -> README.md, requirements.txt

FLUJO DE TRABAJO:
1. Pedir a DesarrolladorLogica que genere snake_logic.py COMPLETO
2. Pedir a DesarrolladorInterfaz que genere snake_game.py COMPLETO
3. Pedir a TesterDebugger que genere test_snake.py COMPLETO
4. Pedir a Documentador que genere README.md y requirements.txt COMPLETOS

IMPORTANTE: 
- NO aceptes respuestas parciales o incompletas
- Cada archivo debe tener al menos 100 líneas de código funcional
- Verifica que cada agente genere su archivo antes de continuar

Cuando todos los archivos estén generados, di "DESARROLLO SNAKE COMPLETADO - TODOS LOS ARCHIVOS CREADOS".""",
    llm_config=ollama_config_llama3,
)

# AGENTE DESARROLLADOR DE LÓGICA MEJORADO
desarrollador_logica = AssistantAgent(
    name="DesarrolladorLogica",
    system_message="""Eres un agente especializado en el desarrollo de la lógica core del juego Snake.

TAREA CRÍTICA: Debes generar el archivo snake_logic.py COMPLETO y FUNCIONAL.

ESTRUCTURA OBLIGATORIA:
```python
# output/snake_logic.py
import random
from enum import Enum

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Snake:
    def __init__(self, x=10, y=10):
        self.body = [(x, y)]
        self.direction = Direction.RIGHT
        self.grow_pending = False
    
    def move(self):
        # Implementar movimiento completo
        pass
    
    def grow(self):
        # Implementar crecimiento
        pass
    
    def check_collision(self, width, height):
        # Implementar detección de colisiones
        pass

class Food:
    def __init__(self, width, height):
        self.position = self.generate_position(width, height)
    
    def generate_position(self, width, height):
        # Implementar generación de comida
        pass

class GameState:
    def __init__(self, width=40, height=30):
        self.width = width
        self.height = height
        self.snake = Snake()
        self.food = Food(width, height)
        self.score = 0
        self.game_over = False
    
    def update(self):
        # Implementar lógica de actualización
        pass
    
    def reset(self):
        # Implementar reset del juego
        pass
```

REQUISITOS:
- El archivo debe tener mínimo 150 líneas de código
- Todas las funciones deben estar implementadas completamente
- Incluir manejo de errores y validaciones
- Código limpio y bien comentado

GENERA EL ARCHIVO COMPLETO AHORA. No des explicaciones, solo el código completo entre ```python y ```.""",
    llm_config=ollama_config_codeqwen,
)

# AGENTE DESARROLLADOR DE INTERFAZ MEJORADO
desarrollador_interfaz = AssistantAgent(
    name="DesarrolladorInterfaz", 
    system_message="""Eres un agente especializado en el desarrollo de la interfaz gráfica del juego Snake usando Pygame.

TAREA CRÍTICA: Debes generar el archivo snake_game.py COMPLETO y EJECUTABLE.

ESTRUCTURA OBLIGATORIA:
```python
# output/snake_game.py
import pygame
import sys
from snake_logic import Snake, Food, GameState, Direction

# Configuración de colores
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# Configuración de la ventana
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
CELL_SIZE = 20

class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake Game - SMA")
        self.clock = pygame.time.Clock()
        self.game_state = GameState()
        self.running = True
    
    def handle_events(self):
        # Implementar manejo de eventos completo
        pass
    
    def update_game(self):
        # Implementar actualización del juego
        pass
    
    def render(self):
        # Implementar renderizado completo
        pass
    
    def run(self):
        # Bucle principal del juego
        while self.running:
            self.handle_events()
            self.update_game()
            self.render()
            self.clock.tick(10)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
```

REQUISITOS:
- El archivo debe tener mínimo 200 líneas de código
- Debe importar correctamente desde snake_logic.py
- Implementar todos los métodos completamente
- Incluir pantalla de game over y puntuación
- Debe ser ejecutable inmediatamente

GENERA EL ARCHIVO COMPLETO AHORA. Solo código entre ```python y ```.""",
    llm_config=ollama_config_codeqwen,
)

# AGENTE TESTER MEJORADO
tester_debugger = AssistantAgent(
    name="TesterDebugger",
    system_message="""Eres un agente especializado en testing y debugging del juego Snake.

TAREA CRÍTICA: Debes generar el archivo test_snake.py COMPLETO con todos los tests.

ESTRUCTURA OBLIGATORIA:
```python
# output/test_snake.py
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from snake_logic import Snake, Food, GameState, Direction

class TestSnakeLogic(unittest.TestCase):
    def setUp(self):
        self.snake = Snake()
        self.food = Food(40, 30)
        self.game_state = GameState()
    
    def test_snake_initialization(self):
        # Test inicialización de serpiente
        pass
    
    def test_snake_movement(self):
        # Test movimiento de serpiente
        pass
    
    def test_snake_growth(self):
        # Test crecimiento de serpiente
        pass
    
    def test_collision_detection(self):
        # Test detección de colisiones
        pass
    
    def test_food_generation(self):
        # Test generación de comida
        pass
    
    def test_game_state_update(self):
        # Test actualización del estado
        pass
    
    def test_score_system(self):
        # Test sistema de puntuación
        pass

class TestGameIntegration(unittest.TestCase):
    def setUp(self):
        self.game = GameState()
    
    def test_full_game_cycle(self):
        # Test ciclo completo del juego
        pass
    
    def test_game_reset(self):
        # Test reset del juego
        pass

if __name__ == '__main__':
    unittest.main()
```

REQUISITOS:
- Mínimo 15 tests diferentes
- Cada test debe estar completamente implementado
- Incluir tests de integración
- Tests de casos extremos
- Mínimo 100 líneas de código

GENERA EL ARCHIVO COMPLETO AHORA. Solo código entre ```python y ```.""",
    llm_config=ollama_config_codellama,
)

# AGENTE DOCUMENTADOR MEJORADO
documentador = AssistantAgent(
    name="Documentador",
    system_message="""Eres un agente especializado en crear documentación técnica completa para el juego Snake.

TAREA CRÍTICA: Debes generar README.md y requirements.txt COMPLETOS.

GENERA PRIMERO requirements.txt:
```txt
# output/requirements.txt
pygame>=2.5.0
psutil>=5.9.0
```

LUEGO GENERA README.md COMPLETO:
```markdown
# output/README.md
# 🐍 Snake Game - Sistema Multiagente

## Descripción
Juego Snake desarrollado usando un Sistema Multiagente (SMA) jerárquico con diferentes modelos de Ollama.

## Arquitectura del Sistema
- **CoordinadorPrincipal** (Llama3): Coordinación general
- **DesarrolladorLogica** (CodeQwen): Lógica del juego
- **DesarrolladorInterfaz** (CodeQwen): Interfaz Pygame
- **TesterDebugger** (CodeLlama): Testing y debugging
- **Documentador** (Mistral): Documentación

## Instalación

### Requisitos Previos
- Python 3.12+
- Ollama instalado y configurado

### Modelos Ollama Necesarios
```bash
ollama pull llama3
ollama pull codeqwen
ollama pull codellama
ollama pull mistral
```

### Instalación de Dependencias
```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar el Juego
```bash
python snake_game.py
```

### Ejecutar Tests
```bash
python test_snake.py
```

## Controles
- ↑: Arriba
- ↓: Abajo
- ←: Izquierda
- →: Derecha
- ESC: Salir

## Estructura de Archivos
```
output/
├── snake_logic.py      # Lógica del juego
├── snake_game.py       # Interfaz gráfica
├── test_snake.py       # Tests unitarios
├── README.md           # Este archivo
└── requirements.txt    # Dependencias
```

## Desarrollo
El proyecto fue desarrollado usando un SMA jerárquico con 5 agentes especializados.

## Licencia
MIT License
```

REQUISITOS:
- README debe tener mínimo 80 líneas
- Incluir toda la información necesaria
- Formateo markdown correcto
- Instrucciones claras y completas

GENERA AMBOS ARCHIVOS COMPLETOS AHORA.""",
    llm_config=ollama_config_mistral,
)

# AGENTE COORDINADOR LOCAL MEJORADO
coordinador_usuario = UserProxyAgent(
    name="CoordinadorUsuario",
    human_input_mode="NEVER",
    code_execution_config=False,
    max_consecutive_auto_reply=2,
    is_termination_msg=lambda msg: any(keyword in msg.get("content", "").lower() for keyword in [
        "desarrollo snake completado",
        "todos los archivos creados",
        "archivos generados correctamente"
    ]),
    system_message="""Eres el coordinador local que facilita la comunicación y EXTRAE AUTOMÁTICAMENTE LOS ARCHIVOS.

FUNCIÓN CRÍTICA: Después de cada mensaje de un agente especializado, debes:
1. Buscar código en el mensaje
2. Extraer y guardar automáticamente en archivos
3. Confirmar que el archivo se guardó correctamente

Termina cuando todos los archivos estén creados: snake_logic.py, snake_game.py, test_snake.py, README.md, requirements.txt""",
)

# FUNCIÓN PARA PROCESAR MENSAJES DESPUÉS DEL CHAT
def process_messages_after_chat(messages):
    """Procesa todos los mensajes después del chat para extraer código"""
    files_created = []
    
    for message in messages:
        if hasattr(message, 'get') and message.get('content'):
            content = message.get('content', '')
            sender_name = message.get('name', 'Unknown')
            
            # Solo procesar mensajes de agentes especializados
            if sender_name in ['DesarrolladorLogica', 'DesarrolladorInterfaz', 'TesterDebugger', 'Documentador']:
                extracted_files = extract_and_save_code(content, sender_name)
                files_created.extend(extracted_files)
                if extracted_files:
                    print(f"Archivos extraidos de {sender_name}: {', '.join(extracted_files)}")
    
    return files_created

# Framework de testing mejorado
class Caso2TestFramework:
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "performance": {},
            "validation": {},
            "architecture": {},
            "integration": {},
            "files_created": []
        }
    
    def monitor_performance(self):
        """Monitorea el rendimiento del sistema"""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        cpu_percent = self.process.cpu_percent()
        
        self.results["performance"] = {
            "memory_usage_mb": round(memory_mb, 2),
            "cpu_usage_percent": round(cpu_percent, 2),
            "execution_time_seconds": round(time.time() - self.start_time, 2)
        }
    
    def validate_files_created(self):
        """Valida que se hayan creado todos los archivos esperados"""
        expected_files = [
            'snake_logic.py',
            'snake_game.py', 
            'test_snake.py',
            'README.md',
            'requirements.txt'
        ]
        
        created_files = []
        if os.path.exists(OUTPUT_DIR):
            created_files = [f for f in os.listdir(OUTPUT_DIR) if f in expected_files]
        
        self.results["files_created"] = {
            "expected": expected_files,
            "created": created_files,
            "completion_percentage": round(len(created_files) / len(expected_files) * 100, 2),
            "missing": [f for f in expected_files if f not in created_files]
        }
    
    def validate_file_content(self):
        """Valida el contenido de los archivos creados"""
        file_validations = {}
        
        validations = {
            'snake_logic.py': ['class Snake', 'class Food', 'class GameState'],
            'snake_game.py': ['pygame', 'SnakeGame', 'if __name__'],
            'test_snake.py': ['unittest', 'TestSnake', 'def test_'],
            'README.md': ['# Snake Game', '## Installation', '## Usage'],
            'requirements.txt': ['pygame']
        }
        
        for filename, required_content in validations.items():
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    validations_passed = sum(1 for req in required_content if req in content)
                    file_validations[filename] = {
                        "exists": True,
                        "size_bytes": len(content),
                        "validations_passed": validations_passed,
                        "validations_total": len(required_content),
                        "is_valid": validations_passed >= len(required_content) * 0.8
                    }
                except Exception as e:
                    file_validations[filename] = {
                        "exists": True,
                        "error": str(e),
                        "is_valid": False
                    }
            else:
                file_validations[filename] = {
                    "exists": False,
                    "is_valid": False
                }
        
        self.results["file_validation"] = file_validations
    
    def generate_report(self, messages):
        """Genera el reporte final completo"""
        self.monitor_performance()
        self.validate_files_created()
        self.validate_file_content()
        
        # Calcular score general basado en archivos creados
        files_score = self.results["files_created"]["completion_percentage"]
        
        if "file_validation" in self.results:
            valid_files = sum(1 for f in self.results["file_validation"].values() if f.get("is_valid", False))
            total_files = len(self.results["file_validation"])
            validation_score = (valid_files / total_files * 100) if total_files > 0 else 0
        else:
            validation_score = 0
        
        self.results["overall_score"] = round((files_score + validation_score) / 2, 2)
        
        # Guardar reporte
        report_path = os.path.join(OUTPUT_DIR, "caso2_snake_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== REPORTE FINAL CASO 2 - DESARROLLO SNAKE ===")
        print(f"Score General: {self.results['overall_score']}%")
        print(f"Archivos Creados: {len(self.results['files_created']['created'])}/5")
        print(f"Archivos Validos: {sum(1 for f in self.results.get('file_validation', {}).values() if f.get('is_valid', False))}")
        
        if self.results['files_created']['missing']:
            print(f"Archivos Faltantes: {', '.join(self.results['files_created']['missing'])}")
        
        print(f"Tiempo Total: {self.results['performance']['execution_time_seconds']}s")
        print(f"Memoria Usada: {self.results['performance']['memory_usage_mb']} MB")
        print(f"Reporte guardado en: {report_path}")
        
        return self.results["overall_score"] >= 80

# Configurar el chat grupal
participantes = [coordinador_usuario, coordinador_principal, desarrollador_logica, 
                desarrollador_interfaz, tester_debugger, documentador]

chat_grupal = GroupChat(
    agents=participantes,
    messages=[],
    max_round=15,  # Aumentar rondas para dar tiempo a generar archivos
    speaker_selection_method="round_robin",
)

gestor = GroupChatManager(
    groupchat=chat_grupal, 
    llm_config=ollama_config_llama3
)

# Inicializar framework de testing
test_framework = Caso2TestFramework()

# Mensaje inicial mejorado
mensaje_inicial = """
PROYECTO CRITICO: Desarrollo del Juego Snake con SMA Jerarquico

INSTRUCCION CRITICA PARA TODOS LOS AGENTES:
Cada agente DEBE generar su archivo completo usando el formato exacto:

```python
# output/nombre_archivo.py
[CODIGO COMPLETO AQUI]
```

ARCHIVOS REQUERIDOS OBLIGATORIOS:
1. snake_logic.py - DesarrolladorLogica (clases Snake, Food, GameState)
2. snake_game.py - DesarrolladorInterfaz (interfaz Pygame completa) 
3. test_snake.py - TesterDebugger (tests unitarios completos)
4. README.md - Documentador (documentacion tecnica)
5. requirements.txt - Documentador (dependencias)

OBJETIVO: Crear TODOS los archivos funcionales del juego Snake
TIEMPO LIMITE: 10 minutos
DIRECTORIO: output/

CoordinadorPrincipal: Coordina a cada agente para que genere su archivo COMPLETO y FUNCIONAL. 
NO aceptes codigo parcial o incompleto. Cada archivo debe tener minimo 100 lineas de codigo real.

COMIENZA EL DESARROLLO AHORA!"""

# Ejecutar el sistema
try:
    print("=== INICIANDO DESARROLLO DEL JUEGO SNAKE ===")
    print("Extraccion automatica de codigo activada")
    print("Generacion de archivos al final del chat")
    print("=" * 50)
    
    # Función para ejecutar con timeout
    def ejecutar_chat():
        try:
            result = coordinador_usuario.initiate_chat(
                gestor, 
                message=mensaje_inicial
            )
            return result
        except Exception as e:
            print(f"Error en el chat: {e}")
            return None
    
    # Ejecutar con timeout
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Tiempo límite excedido")
    
    # Configurar timeout (solo en sistemas Unix)
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(600)  # 10 minutos
        result = ejecutar_chat()
        signal.alarm(0)  # Cancelar timeout
    except (AttributeError, OSError):
        # En Windows o sistemas sin señales, usar threading
        resultado_queue = Queue()
        
        def ejecutar_chat_thread():
            try:
                result = ejecutar_chat()
                resultado_queue.put(("success", result))
            except Exception as e:
                resultado_queue.put(("error", e))
        
        chat_thread = threading.Thread(target=ejecutar_chat_thread)
        chat_thread.daemon = True
        chat_thread.start()
        chat_thread.join(timeout=600)
        
        if chat_thread.is_alive():
            print("\nTiempo limite excedido (10 minutos)")
        elif not resultado_queue.empty():
            status, result = resultado_queue.get()
            if status == "error":
                raise result

except Exception as e:
    print(f"\nError durante la ejecucion: {e}")
finally:
    # Procesar mensajes y extraer archivos al final
    try:
        if 'chat_grupal' in locals():
            conversation = getattr(chat_grupal, 'messages', [])
            
            # Extraer archivos de la conversacion
            print("\n=== PROCESANDO MENSAJES PARA EXTRAER ARCHIVOS ===")
            files_created = process_messages_after_chat(conversation)
            
            # Generar reporte
            success = test_framework.generate_report(conversation)
            
            # Mostrar archivos creados
            if os.path.exists(OUTPUT_DIR):
                archivos = [f for f in os.listdir(OUTPUT_DIR) if not f.endswith('.json')]
                if archivos:
                    print(f"\nARCHIVOS GENERADOS EN {OUTPUT_DIR}/:")
                    for archivo in sorted(archivos):
                        filepath = os.path.join(OUTPUT_DIR, archivo)
                        size = os.path.getsize(filepath)
                        print(f"   [OK] {archivo} ({size} bytes)")
                else:
                    print(f"\nNo se generaron archivos en {OUTPUT_DIR}/")
                    print("POSIBLES SOLUCIONES:")
                    print("   1. Verificar que Ollama este ejecutandose: ollama serve")
                    print("   2. Verificar modelos: ollama list")
                    print("   3. Probar conexion: curl http://localhost:11434/api/tags")
            
            if success:
                print(f"\nDESARROLLO COMPLETADO EXITOSAMENTE!")
                print(f"Ejecutar juego: python {OUTPUT_DIR}/snake_game.py")
                print(f"Ejecutar tests: python {OUTPUT_DIR}/test_snake.py")
            else:
                print(f"\nDesarrollo incompleto. Revisar archivos generados.")
        
        print(f"\nRESUMEN FINAL:")
        print(f"   • Directorio: {OUTPUT_DIR}/")
        print(f"   • Reporte: caso2_snake_report.json")
        print(f"   • Logs: Ver consola para detalles")
        
    except Exception as report_error:
        print(f"\nError generando reporte: {report_error}")

print("\n" + "="*50)
print("SISTEMA MULTIAGENTE SNAKE - FINALIZADO")
print("="*50)