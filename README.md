# 📂 KIT Automatización de Archivos
<img width="1408" height="768" alt="Gemini_Generated_Image_eydhjdeydhjdeydh" src="https://github.com/user-attachments/assets/bde79283-7ef4-44ed-911a-111865fdd87b" />

¡Bienvenido al **Kit de Automatización de Archivos**! Este proyecto es una suite de herramientas desarrollada en Python diseñada para organizar, analizar, auditar y reportar de manera eficiente el estado y movimiento de tus archivos.

---

## ✨ Características Principales

*   **🗂️ Organización Inteligente:** Clasifica y mueve archivos automáticamente según reglas predefinidas.
*   **📊 Análisis de Datos:** Extrae información relevante de diversos tipos de archivos (CSV, logs, texto).
*   **📋 Generación de Reportes:** Crea resúmenes detallados de las operaciones y análisis realizados.
*   **👀 Auditoría Continua:** Mantiene un registro detallado de los cambios en el sistema para mayor seguridad y trazabilidad.
*   **⏪ Sistema de Reversión (Undo):** Permite deshacer cambios recientes utilizando un sistema de snapshots.

---

## 🏗️ Estructura del Proyecto

El proyecto está organizado de la siguiente manera:

| Directorio / Archivo | Descripción |
| :--- | :--- |
| `main.py` | Punto de entrada principal de la aplicación. |
| `organizer.py` | Módulo encargado de la lógica de organización de archivos. |
| `analyzer.py` | Módulo para el análisis del contenido de los archivos. |
| `auditor.py` | Gestiona la trazabilidad y registra eventos en `audit.log`. |
| `reports.py` | Genera los informes finales en el directorio `reportes/`. |
| `undo.py` | Maneja la reversión de acciones usando el directorio `snapshots/`. |
| `utils.py` | Funciones de utilidad y herramientas compartidas. |
| `requirements.txt` | Lista de dependencias de Python necesarias. |
| `tests/` | Pruebas unitarias para garantizar el funcionamiento de cada módulo. |
| `tests_sample/` | Archivos de prueba variados (PDF, TXT, LOG, JPG, CSV). |

---

## 🚀 Instalación y Uso

**1. Clonar el repositorio:**
\`\`\`bash
git clone <tu-repositorio>
cd KIT_Automatizacion_Archivos
\`\`\`

**2. Instalar las dependencias:**
Es recomendable usar un entorno virtual.
\`\`\`bash
pip install -r requirements.txt
\`\`\`

**3. Ejecutar la aplicación:**
\`\`\`bash
python main.py
\`\`\`

---

## 🧪 Pruebas (Testing)

Este proyecto incluye un entorno completo de pruebas para garantizar su fiabilidad. 

Para ejecutar los tests (como `test_organizer.py`, `test_analyzer.py`, `test_auditor.py` y `test_undo.py`), utiliza tu framework de pruebas preferido en la carpeta correspondiente:

\`\`\`bash
pytest tests/
\`\`\`

> **Nota:** El directorio `tests_sample/` contiene archivos de prueba seguros (como `datos_ventas.csv` o `imagen_evento.jpg`) para no afectar tus archivos reales durante el desarrollo.

---

## 📄 Licencia

Este proyecto es de uso privado/código abierto (Actualiza esta sección según la licencia que desees otorgar).
