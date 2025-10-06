# Sistema Multiagente con Autogen y Ollama

Sistema de agentes autónomos colaborativos desarrollado con Autogen y modelos locales de Ollama. Incluye dos casos de uso: análisis de sesgos en IA y desarrollo colaborativo del juego Snake.

## Requisitos Previos

### Software Necesario
- **Python 3.12+**
- **Ollama** instalado y en ejecución
- **Git** (para clonar el repositorio)

### Sistemas Operativos Soportados
- Linux (Ubuntu/Debian recomendado)
- macOS
- Windows 10/11

## Instalación

### 1. Instalar Ollama

#### Linux/macOS
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Windows
Descarga el instalador desde [ollama.com](https://ollama.com/download)

### 2. Verificar Instalación de Ollama
```bash
ollama --version
```

### 3. Iniciar Servidor Ollama
```bash
ollama serve
```
> **Nota:** Deja este terminal abierto. Ollama debe estar ejecutándose en segundo plano.

### 4. Descargar Modelos Necesarios

En una nueva terminal:

```bash
# Para Caso 1: Análisis de Sesgos
ollama pull llama3
ollama pull mistral
ollama pull dolphin3

# Para Caso 2: Desarrollo Snake
ollama pull llama3
ollama pull codeqwen
ollama pull codellama
ollama pull mistral
```

**Tiempo estimado:** 10-30 minutos dependiendo de tu conexión.

### 5. Verificar Modelos Instalados
```bash
ollama list
```

Deberías ver algo como:
```
NAME                ID              SIZE      MODIFIED
codeqwen:latest     df352abf55b1    4.2 GB    3 months ago
codellama:latest    8fdf8f752f6e    3.8 GB    3 months ago
Dolphin3:latest     d5ab9ae8e1f2    4.9 GB    4 months ago
llama3:latest       365c0bd3c000    4.7 GB    4 months ago
mistral:latest      f974a74358d6    4.1 GB    4 months ago
```

## Configuración del Proyecto

### 1. Clonar o Descargar el Proyecto
```bash
# Si tienes git
git clone <url-del-repositorio>
cd sistema-multiagente

# O descomprime el archivo ZIP
```

### 2. Crear Entorno Virtual
```bash
python -m venv .venv
```

### 3. Activar Entorno Virtual

#### Linux/macOS
```bash
source .venv/bin/activate
```

#### Windows
```cmd
.venv\Scripts\activate
```

### 4. Instalar Dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Verificar Instalación
```bash
pip list
```

Deberías ver:
```
autogen==0.9.2
psutil==7.0.0
unittest2==1.1.0
```

## 📁 Estructura del Proyecto

```
sistema-multiagente/
│
├── Caso-1/
│   ├── Caso1.py                 # Análisis de sesgos en IA
│   └── test_results.json        # Resultados de tests (generado)
│
├── Caso-2/
│   ├── Caso2.py                 # Desarrollo colaborativo Snake
│   └── output/                  # Archivos generados (creado automáticamente)
│       ├── snake_logic.py
│       ├── snake_game.py
│       ├── test_snake.py
│       ├── README.md
│       ├── requirements.txt
│       └── caso2_snake_report.json
│
├── .venv/                       # Entorno virtual (ignorado en git)
├── .gitignore
├── requirements.txt
└── README.md                    # Este archivo
```

## Uso

### Caso 1: Sistema de Análisis de Sesgos

Detecta sesgos de género, raza y orientación sexual en respuestas de IA mediante un sistema multiagente.

#### Ejecutar
```bash
cd Caso-1
python Caso1.py
```

#### Qué hace:
1. **GeneradorPreguntas** (Mistral): Crea 10 pares de preguntas (neutra vs. con sesgo)
2. **Respondedor** (Llama3): Responde SÍ/NO a cada pregunta
3. **AnalizadorSesgos** (Dolphin3): Detecta inconsistencias y sesgos
4. Genera `test_results.json` con métricas de calidad

#### Salida esperada:
```
=== RESUMEN DE PRUEBAS DEL SISTEMA MULTIAGENTE ===
Total de pruebas: 12
Pruebas exitosas: 11
Tasa de éxito: 91.7%

✓ Generación de Preguntas - Formato: 10 pares encontrados
✓ Respuestas - Formato: 20 respuestas válidas
✓ Análisis - Completado: Análisis terminado correctamente
...
```

#### Solución de Problemas

**Error: "Connection refused"**
```bash
# Verificar que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Si no responde, reiniciar Ollama
pkill ollama
ollama serve
```

**Error: "Model not found"**
```bash
# Descargar el modelo faltante
ollama pull mistral
ollama pull llama3
ollama pull dolphin3
```

### Caso 2: Desarrollo Colaborativo del Juego Snake

Sistema jerárquico de agentes que desarrollan colaborativamente un juego Snake completo.

#### Ejecutar
```bash
cd Caso-2
python Caso2.py
```

#### Qué hace:
1. **CoordinadorPrincipal** (Llama3): Coordina el proyecto
2. **DesarrolladorLogica** (CodeQwen): Crea `snake_logic.py`
3. **DesarrolladorInterfaz** (CodeQwen): Crea `snake_game.py`
4. **TesterDebugger** (CodeLlama): Crea `test_snake.py`
5. **Documentador** (Mistral): Crea `README.md` y `requirements.txt`
6. Extrae automáticamente el código generado a `/output/`

#### Salida esperada:
```
=== INICIANDO DESARROLLO DEL JUEGO SNAKE ===
[OK] DesarrolladorLogica -> snake_logic.py guardado (3847 chars)
[OK] DesarrolladorInterfaz -> snake_game.py guardado (5621 chars)
[OK] TesterDebugger -> test_snake.py guardado (2934 chars)
[OK] Documentador -> README.md guardado (1823 chars)

=== REPORTE FINAL CASO 2 ===
Score General: 95.5%
Archivos Creados: 5/5
Tiempo Total: 187.3s
```

#### Jugar al Snake Generado

Si el sistema genera exitosamente los archivos:

```bash
cd Caso-2/output

# Instalar pygame (si no está instalado)
pip install pygame

# Ejecutar el juego
python snake_game.py

# Ejecutar tests
python test_snake.py
```

**Controles del juego:**
- ↑↓←→: Mover la serpiente
- ESC: Salir

#### Solución de Problemas

**Código incompleto:**
- Los modelos pueden generar código parcial en las primeras ejecuciones
- Ejecutar nuevamente: `python Caso2.py`
- El sistema mejora con múltiples ejecuciones

**Error "pygame not found":**
```bash
pip install pygame>=2.5.0
```

## Errores comunes

### Problema: "Ollama connection refused"
```bash
# Verificar estado de Ollama
ps aux | grep ollama

# Reiniciar Ollama
pkill ollama
ollama serve &
```

### Problema: Alto uso de RAM/CPU
```bash
# Ollama usa GPU por defecto si está disponible
# Para limitar a CPU:
OLLAMA_NUM_GPU=0 ollama serve

# Limitar modelos en memoria:
ollama rm <modelo>  # Eliminar modelo no usado
```

### Problema: Errores de encoding
```bash
# En Windows, asegurar UTF-8
set PYTHONIOENCODING=utf-8
python Caso1.py
```
