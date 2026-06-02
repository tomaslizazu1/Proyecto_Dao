# Proyecto 02 — Rentabilidad por Cliente

> **Laboratorio 1 · UCA Rosario · 2025**

Pipeline ETL en Python que procesa 12 meses de datos operativos de **DAO SRL** para calcular la rentabilidad de sus 34 clientes activos, con salida directa a un dashboard interactivo en Power BI.

---

## El problema de negocio

DAO SRL trabaja con múltiples clientes que presentan distintos volúmenes de producción, tipos de piezas y precios. Sin un análisis estructurado, es imposible determinar si todos los clientes son igualmente rentables: algunos pueden generar mucho trabajo pero poco margen. Este proyecto le da a Luciano (responsable del negocio) un ranking claro de sus 34 clientes activos por **Contribución Marginal por metro cuadrado (CMg/m²)**, permitiéndole decidir a quién cobrarle más, a quién priorizar y con quién renegociar condiciones.

---

## Arquitectura y tecnologías

```
Archivos fuente (.xls / .xlsx)
        │
        ▼
┌─────────────────────────────────────┐
│   Pipeline ETL — Python + pandas    │
│  (5 módulos en ramas Git separadas) │
└────────────────┬────────────────────┘
                 │
                 ▼
   rentabilidad_clientes_2025.csv
   (granularidad: cliente × mes)
                 │
                 ▼
      Dashboard Power BI (.pbix)
      (3 vistas para Luciano)
```

| Capa | Herramienta | Rol |
|---|---|---|
| ETL y cálculo | Python 3.x + pandas | Procesamiento de los 12 meses de archivos fuente |
| Lectura de archivos | xlrd / openpyxl | Compatibilidad con formatos `.xls` y `.xlsx` |
| Control de versiones | GitHub | Ramas separadas por módulo ETL |
| Output del pipeline | CSV consolidado | Interfaz entre Python y Power BI |
| Visualización | Power BI Desktop | Dashboard interactivo para el usuario final |

---

## Requisitos y dependencias

### Python

Se requiere **Python 3.10 o superior**. Se puede verificar la versión instalada con:

```bash
python --version
```

### Librerías (`requirements.txt`)

```
pandas>=2.2.0
xlrd>=2.0.1
openpyxl>=3.1.2
```

> **Nota sobre compatibilidad de formatos:**
> - `xlrd` es necesario para leer archivos `.xls` (formato heredado del ERP, ej.: `WEG_MM_YYYY.xls`, `Resumen_2025.xls`).
> - `openpyxl` es necesario para leer archivos `.xlsx` (ej.: `ART_POR_CLIENTE.XLSX`).
> - Ambas librerías deben instalarse aunque se use una sola por módulo.

---

## Estructura del proyecto

El repositorio organiza el trabajo en **5 módulos ETL independientes**, cada uno desarrollado en su propia rama Git. Los módulos P1 a P4 pueden ejecutarse en paralelo; P5 integra los resultados una vez que los cuatro anteriores están completos.

```
rentabilidad-por-cliente/
│
├── data/
│   ├── raw/                    # Archivos fuente originales (no versionados)
│   │   ├── COMPRAS_MM_YYYY.xls
│   │   ├── WEG_MM_YYYY.xls
│   │   ├── ER_SUPERFICIE_MM_YYYY.xls
│   │   └── ART_POR_CLIENTE.XLSX
│   └── output/
│       └── rentabilidad_clientes_2025.csv   # Output final del pipeline
│
├── src/
│   ├── p1_etl_compras.py       # Módulo P1: ETL de archivos COMPRAS (12 meses)
│   ├── p2_etl_weg.py           # Módulo P2: ETL de archivos WEG (12 meses)
│   ├── p3_etl_er_superficie.py # Módulo P3: ETL de ER_SUPERFICIE (12 meses, 3 hojas)
│   ├── p4_etl_art_cliente.py   # Módulo P4: ETL de ART_POR_CLIENTE + tabla maestra
│   └── p5_integracion.py       # Módulo P5: Integración, cálculo de KPIs y validación
│
├── requirements.txt
└── README.md
```

### Descripción de cada módulo

| Módulo | Archivo | Fuente de datos | Responsabilidad |
|---|---|---|---|
| **P1** | `p1_etl_compras.py` | `COMPRAS_MM_YYYY.xls` × 12 | Extrae, limpia y normaliza los costos de químicos por mes |
| **P2** | `p2_etl_weg.py` | `WEG_MM_YYYY.xls` × 12 | Extrae, limpia y normaliza los costos de pintura por mes |
| **P3** | `p3_etl_er_superficie.py` | `ER_SUPERFICIE_MM_YYYY.xls` × 12 | Lee las 3 hojas por archivo: superficie, ingresos y costo de mano de obra |
| **P4** | `p4_etl_art_cliente.py` | `ART_POR_CLIENTE.XLSX` | Construye la tabla maestra de 667 artículos con su mapeo a cliente, m² y velocidad de línea |
| **P5** | `p5_integracion.py` | Outputs de P1–P4 | Une los 4 DataFrames, calcula CMg y CMg/m² por cliente × mes, y valida contra `Resumen_2025.xls` |

---

## Instrucciones de ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/<org>/rentabilidad-por-cliente.git
cd rentabilidad-por-cliente
```

### 2. Crear y activar el entorno virtual

```bash
# Crear el entorno virtual
python -m venv venv

# Activar en macOS / Linux
source venv/bin/activate

# Activar en Windows
venv\Scripts\activate
```

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 4. Colocar los archivos fuente

Copiar todos los archivos de datos originales dentro de `data/raw/`. La carpeta **no está versionada** (figura en `.gitignore`) para proteger la información de DAO SRL.

```
data/raw/
├── COMPRAS_01_2025.xls
├── COMPRAS_02_2025.xls
│   ...
├── WEG_01_2025.xls
│   ...
├── ER_SUPERFICIE_01_2025.xls
│   ...
└── ART_POR_CLIENTE.XLSX
```

### 5. Ejecutar los módulos ETL en orden

Los módulos P1 a P4 procesan las fuentes de forma independiente. Ejecutarlos primero (pueden correr en cualquier orden entre sí):

```bash
python src/p1_etl_compras.py
python src/p2_etl_weg.py
python src/p3_etl_er_superficie.py
python src/p4_etl_art_cliente.py
```

Una vez que los cuatro módulos anteriores hayan finalizado sin errores, ejecutar el módulo de integración:

```bash
python src/p5_integracion.py
```

> **Importante:** P5 requiere que los outputs de P1–P4 estén disponibles. Si alguno de los módulos anteriores falla, corregirlo antes de continuar.

### 6. Verificar el output

Al finalizar la ejecución, el archivo consolidado estará disponible en:

```
data/output/rentabilidad_clientes_2025.csv
```

El script P5 imprime por consola un resumen de validación numérica comparando los totales calculados contra `Resumen_2025.xls`.

---

## Output: `rentabilidad_clientes_2025.csv`

El pipeline genera un único archivo consolidado con granularidad **cliente × mes**. Este CSV es la interfaz directa entre el bloque Python y Power BI, sin transformaciones adicionales.

| Columna | Tipo | Fuente |
|---|---|---|
| `cliente` | TEXT | ART_POR_CLIENTE.XLSX |
| `mes` | INT (1–12) | ER_SUPERFICIE |
| `articulo` | TEXT | ART_POR_CLIENTE.XLSX |
| `m2` | DECIMAL | ER_SUPERFICIE + ART_POR_CLIENTE |
| `ingresos` | DECIMAL | ER_SUPERFICIE (hoja ESTADO_DE_RESULTADO) |
| `cv_pintura` | DECIMAL | WEG_MM_YYYY.xls |
| `cv_quimicos` | DECIMAL | COMPRAS_MM_YYYY.xls |
| `cv_mod` | DECIMAL | ER_SUPERFICIE (hoja ESTADO_DE_RESULTADO) |
| `cmg` | DECIMAL | `ingresos − (cv_pintura + cv_quimicos + cv_mod)` |
| `cmg_por_m2` | DECIMAL | `cmg / m2` |

### Conexión con Power BI

1. Abrir **Power BI Desktop**.
2. Ir a `Inicio → Obtener datos → Texto/CSV`.
3. Seleccionar `data/output/rentabilidad_clientes_2025.csv`.
4. Cargar y refrescar el dashboard `.pbix`.

El dashboard incluye tres vistas:

- **Vista 1 — Ranking anual:** Gráfico de barras horizontales con los 34 clientes ordenados por CMg/m², con CMg total en pesos como segunda dimensión.
- **Vista 2 — Evolución mensual:** Gráfico de líneas con la evolución del CMg/m² por cliente a lo largo de 2025, con filtro por cliente.
- **Vista 3 — Detalle por artículo:** Tabla con m², CMg y CMg/m² por artículo dentro del cliente seleccionado.

---

## Sprints del proyecto

| Sprint | Tareas principales |
|---|---|
| Sprint 2 | Análisis de ART_POR_CLIENTE, definición del esquema CSV, configuración del repositorio |
| Sprint 3 | Desarrollo de módulos ETL P1–P4 |
| Sprint 4 | Integración P5, cálculo de KPIs, análisis de estacionalidad |
| Sprint 5 | Dashboard Power BI, reporte ejecutivo PDF, presentación final con Luciano |

---

*Propuesta elaborada por el equipo de Laboratorio 1 — UCA Rosario — 2026*
