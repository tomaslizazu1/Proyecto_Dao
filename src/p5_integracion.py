# -*- coding: utf-8 -*-
"""
integrador.py  —  P5: Integración 4 DataFrames -> CSV consolidado (LD-51)
=========================================================================
Proyecto 02 · Rentabilidad por Cliente · DAO SRL · Laboratorio 1 · UCA 2025
Autor: Bautista Verna

Toma los outputs de P1–P4 y genera output/rentabilidad_clientes_2025.csv,
con cv asignado por artículo (proporcional a m²) y validación contra los
KPIs de enero 2025.

Inputs (CSV intermedios, arquitectura desacoplada — ver LD-51):
    df_er.csv  (P3): una fila por artículo-mes. m², ingresos (x cliente),
                     cv_mod (total mensual). Fuente de cliente y cod_cliente.
    df_weg.csv (P2): una fila por mes. cv_pintura_mes, cv_quimicos_mes (compras).
    df_art.csv (P4): tabla maestra por artículo. Se usa SOLO para validar
                     cobertura artículo->cliente (no aporta columnas al CSV).
    df_compras.csv (P1): NO se usa en el margen (WEG ya cubre esos costos;
                     el resto de COMPRAS queda fuera del CMG por diseño).

Modelo de asignación (dos denominadores):
    ingresos     -> fracción DENTRO DEL CLIENTE  (m2_art / m2_cliente_mes)
    cv_pintura   -> fracción GLOBAL del mes       (m2_art / m2_total_mes)
    cv_quimicos  -> fracción GLOBAL del mes       (m2_art / m2_total_mes)
    cv_mod       -> fracción GLOBAL del mes       (m2_art / m2_total_mes)
    cmg          = ingresos - cv_pintura - cv_quimicos - cv_mod
    cmg_por_m2   = cmg / m2   (NaN si m2 == 0)

LIMITACIÓN CONOCIDA (LD-41 / LD-51):
    cv_pintura y cv_quimicos provienen de COMPRAS (WEG), no de CONSUMO. Luciano
    se abastece (compra desacoplada de la producción del mes), por lo que el CV
    y el cmg ABSOLUTOS no reconcilian con los KPIs contables y son un PROXY para
    RANKEAR clientes, no cifras contables. La reconciliación exacta (lógica Fx
    artículo por artículo) corresponde al Proyecto 01.
    Consecuencia: cmg_por_m2 es constante dentro de cada cliente (efecto del
    reparto proporcional por m²).

Validación enero 2025 (warning + export, nunca corta):
    DUROS:  Σ m² = 6.618,17 (tol 0,1%) · Σ ingresos = 18.444.872 (tol 5%)
    INFO :  Σ CV ≈ 6.640.741 · Σ cmg ≈ 11.804.132 · clientes ≈ 34
"""

# %% [BLOQUE 1] Imports y configuración -------------------------------------
import os
import pandas as pd
import numpy as np

# En Colab: subí los 3 CSV y poné INPUT_DIR = "/content".
# En el repo: carpeta de los CSV intermedios que dejan P2/P3/P4.
INPUT_DIR  = os.environ.get("DAO_INPUT_DIR", "output/intermedios")
OUTPUT_DIR = os.environ.get("DAO_OUTPUT_DIR", "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "rentabilidad_clientes_2025.csv")

MESES_ES = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12}

# KPIs validados por Luciano para enero 2025 (mes=1).
# (obtenido, esperado, tolerancia_relativa | None, tipo)
KPIS_ENERO = {
    "Sigma ingresos": (18_444_872, 0.05,  "DURO"),
    "Sigma m2":       (6_618.17,   0.001, "DURO"),
    "Sigma CV":       (6_640_741,  None,  "INFO"),
    "Sigma cmg":      (11_804_132, None,  "INFO"),
}
KPI_CLIENTES = 34  # total anual (incluye clientes sin m² pintado) -> INFO


def parse_mes(serie: pd.Series) -> pd.Series:
    """Normaliza mes a entero 1-12 desde 'ene-25' o '2025-01' (capa de
    saneamiento: cada compañero usó un formato distinto)."""
    s = serie.astype(str).str.strip().str.lower()
    m_texto = s.str.slice(0, 3).map(MESES_ES)                       # "ene-25"
    m_iso = pd.to_numeric(s.str.extract(r'^\d{4}-(\d{2})$')[0],     # "2025-01"
                          errors='coerce')
    return m_texto.fillna(m_iso).astype('Int64')


def norm_articulo(serie: pd.Series) -> pd.Series:
    """Llave de artículo homogénea: string de 6 dígitos con ceros a la
    izquierda (df_er trae int '371'; df_art trae '000001')."""
    return (serie.astype(str).str.strip()
            .str.replace(r'\.0$', '', regex=True)
            .str.zfill(6))


# %% [BLOQUE 2] Cargar y sanear df_er (P3) -----------------------------------
def cargar_df_er(input_dir: str) -> pd.DataFrame:
    df = pd.read_csv(os.path.join(input_dir, "df_er.csv"), sep=";", decimal=",")
    df = df[df["articulo"] != 0].copy()              # quitar fila resumen total
    df["mes"] = parse_mes(df["mes"])
    df["cod_cliente"] = df["cod_cliente"].astype("Int64")
    df["articulo"] = norm_articulo(df["articulo"])
    return df


# %% [BLOQUE 3] Cargar y sanear df_weg (P2) ----------------------------------
def cargar_df_weg(input_dir: str) -> pd.DataFrame:
    df = pd.read_csv(os.path.join(input_dir, "df_weg.csv"), sep=";", decimal=",")
    df = df.rename(columns={"TOTAL_PINTURA": "cv_pintura_mes",
                            "TOTAL_QUIMICOS": "cv_quimicos_mes"})
    df["mes"] = parse_mes(df["MES"])
    return df[["mes", "cv_pintura_mes", "cv_quimicos_mes"]]


# %% [BLOQUE 4] Cargar df_art (P4) — solo cobertura artículo->cliente ---------
def cargar_df_art(input_dir: str) -> pd.DataFrame:
    df = pd.read_csv(os.path.join(input_dir, "df_art.csv"))
    df["articulo"] = norm_articulo(df["articulo"])
    return df[["articulo"]].drop_duplicates().assign(_en_art=True)


# %% [BLOQUE 5] Integración y cálculo ----------------------------------------
def integrar(df_er: pd.DataFrame, df_weg: pd.DataFrame,
             df_art_lkp: pd.DataFrame) -> pd.DataFrame:
    # Totales mensuales (cv_mod viene replicado por fila -> tomar uno por mes)
    cv_mod_mes = df_er.groupby("mes")["cv_mod"].first().rename("cv_mod_mes")
    m2_total_mes = df_er.groupby("mes")["m2"].sum().rename("m2_total_mes")
    m2_cliente_mes = (df_er.groupby(["mes", "cod_cliente"])["m2"].sum()
                      .rename("m2_cliente_mes"))

    df = (df_er
          .merge(cv_mod_mes, on="mes")
          .merge(m2_total_mes, on="mes")
          .merge(m2_cliente_mes, on=["mes", "cod_cliente"])
          .merge(df_weg, on="mes", how="left")
          .merge(df_art_lkp, on="articulo", how="left"))

    # Validación de cobertura (no bloqueante): artículos sin maestro df_art.
    huerfanos = df.loc[df["_en_art"].isna(), "articulo"].nunique()
    if huerfanos:
        print(f"  [aviso] {huerfanos} artículo(s) sin match en df_art "
              f"(se conservan: igual tienen cliente/ingresos/m²).")

    # Fracciones por m² con guarda de división por cero -> NaN + aviso.
    g0 = (df["m2_total_mes"] == 0).sum()
    c0 = (df["m2_cliente_mes"] == 0).sum()
    if g0:
        print(f"  [aviso] {g0} fila(s) con m2_total_mes=0 -> CV en NaN.")
    if c0:
        print(f"  [aviso] {c0} fila(s) con m2_cliente_mes=0 -> ingresos en NaN.")
    df["fraccion_global"] = np.where(df["m2_total_mes"] > 0,
                                     df["m2"] / df["m2_total_mes"], np.nan)
    df["fraccion_cliente"] = np.where(df["m2_cliente_mes"] > 0,
                                      df["m2"] / df["m2_cliente_mes"], np.nan)

    # Reparto a nivel artículo.
    df["ingresos"]    = df["ingresos"]        * df["fraccion_cliente"]
    df["cv_pintura"]  = df["cv_pintura_mes"]  * df["fraccion_global"]
    df["cv_quimicos"] = df["cv_quimicos_mes"] * df["fraccion_global"]
    df["cv_mod"]      = df["cv_mod_mes"]      * df["fraccion_global"]

    df["cmg"] = (df["ingresos"] - df["cv_pintura"]
                 - df["cv_quimicos"] - df["cv_mod"])
    df["cmg_por_m2"] = np.where(df["m2"] > 0, df["cmg"] / df["m2"], np.nan)

    cols = ["cliente", "cod_cliente", "mes", "articulo", "descripcion", "m2",
            "ingresos", "cv_pintura", "cv_quimicos", "cv_mod", "cmg",
            "cmg_por_m2"]
    return (df[cols]
            .sort_values(["mes", "cliente", "articulo"])
            .reset_index(drop=True))


# %% [BLOQUE 6] Validación contra KPIs de enero ------------------------------
def validar_enero(csv: pd.DataFrame) -> None:
    e = csv[csv["mes"] == 1]
    obtenidos = {
        "Sigma ingresos": e["ingresos"].sum(),
        "Sigma m2":       e["m2"].sum(),
        "Sigma CV":       e[["cv_pintura", "cv_quimicos", "cv_mod"]].sum().sum(),
        "Sigma cmg":      e["cmg"].sum(),
    }
    print("\n=== VALIDACION ENERO 2025 ===")
    for k, (esp, tol, tipo) in KPIS_ENERO.items():
        obt = obtenidos[k]
        dv = (obt - esp) / esp * 100 if esp else 0.0
        if tipo == "DURO":
            flag = "OK" if abs(dv) <= tol * 100 else "FALLA"
        else:
            flag = "--"
        print(f"  [{tipo:4}] {k:14}: obtenido={obt:>16,.2f}  "
              f"esperado={esp:>16,.2f}  desvio={dv:+6.1f}%  {flag}")
    # Ingresos: mostrar los 3 números (gap estructural no atribuible).
    print(f"  [INFO] clientes únicos (CSV) = {csv['cod_cliente'].nunique()}  "
          f"(KPI anual ~{KPI_CLIENTES}; diferencia = clientes sin m² pintado).")
    print("  NOTA: CV y cmg son INFO. WEG=compras (no consumo) -> proxy para "
          "RANKING, no cifras contables. Reconciliación exacta = Proyecto 01.")


# %% [BLOQUE 7] main ---------------------------------------------------------
def main() -> pd.DataFrame:
    print(f"Leyendo CSV intermedios de: {INPUT_DIR}")
    df_er = cargar_df_er(INPUT_DIR)
    df_weg = cargar_df_weg(INPUT_DIR)
    df_art_lkp = cargar_df_art(INPUT_DIR)
    print(f"  df_er={df_er.shape}  df_weg={df_weg.shape}  "
          f"df_art(lookup)={df_art_lkp.shape}")

    csv = integrar(df_er, df_weg, df_art_lkp)
    validar_enero(csv)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    csv.to_csv(OUTPUT_FILE, index=False, decimal=".", encoding="utf-8-sig")
    print(f"\nCSV exportado: {OUTPUT_FILE}  ({len(csv)} filas, "
          f"{csv['mes'].nunique()} meses)")
    return csv


if __name__ == "__main__":
    main()
