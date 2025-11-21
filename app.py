import streamlit as st
import pandas as pd
import numpy as np
import altair as alt


# --------------------------------------------------
# Configuración de la página
# --------------------------------------------------
st.set_page_config(page_title="📊 Modelo Energético Solar", layout="wide")

st.title("📊 Modelo de Energía Solar")
st.markdown(
    """
Esta aplicación hace lo siguiente de forma automática usando los archivos:

- `consumo_diario.xlsx` → consumo diario de todos los equipos (ENERGIA (Wh)).  
- `energia_generada.xlsx` → energía generada diaria por un panel (kWh/día).

Cálculos que realiza:

1. Suma el consumo diario de todos los equipos (kWh/día).  
2. Lee la energía generada diaria por un panel de 1 kW (kWh/día) y la escala por la potencia del panel.  
3. Calcula la eficiencia global η_global = η_fv · η_cableado · η_MPPT · η_bat.  
4. Demanda diaria = consumo / η_global.  
5. Balance diario = generación − demanda.  
6. Evolución del SoC de la batería: SoC_día = SoC_(día−1) + B_día.  
7. Cuenta los días con SoC por debajo de la capacidad mínima (días sin batería).
"""
)

st.divider()

# --------------------------------------------------
# 1. Lectura directa de tus archivos Excel
# --------------------------------------------------
st.header("1️⃣ Lectura de datos desde los archivos fijos")

try:
    # consumo_diario.xlsx: tiene encabezados reales en la fila 2 (índice 1)
    df_consumo = pd.read_excel("consumo_diario.xlsx", header=1)
    
    # energia_generada.xlsx: cabecera normal en la primera fila
    df_generacion = pd.read_excel("energia_generada.xlsx")

except FileNotFoundError as e:
    st.error(
        f"No se han encontrado los archivos necesarios.\n\n"
        f"Asegúrate de que `consumo_diario.xlsx` y `energia_generada.xlsx` "
        f"están en la misma carpeta que este `app.py`.\n\n"
        f"Error: {e}"
    )
    st.stop()

# Vista rápida
with st.expander("Ver tablas originales"):
    st.subheader("consumo_diario.xlsx")
    st.dataframe(df_consumo)
    st.subheader("energia_generada.xlsx")
    st.dataframe(df_generacion)

# --------------------------------------------------
# 2. Cálculo del consumo diario total [kWh]
# --------------------------------------------------
st.header("2️⃣ Consumo diario total de los equipos")

# Columna de energía diaria por equipo en Wh
if "ENERGIA (Wh)" not in df_consumo.columns:
    st.error("En `consumo_diario.xlsx` no se ha encontrado la columna 'ENERGIA (Wh)'.")
    st.stop()

consumo_total_Wh = df_consumo["ENERGIA (Wh)"].sum()
consumo_total_kWh = consumo_total_Wh / 1000.0

st.markdown(
    f"""
- **Suma de ENERGIA (Wh) de todos los equipos**: `{consumo_total_Wh:.2f} Wh/día`  
- **Consumo diario total**: **{consumo_total_kWh:.3f} kWh/día**
"""
)

st.divider()

# --------------------------------------------------
# 3. Procesado de energía generada por el panel
# --------------------------------------------------
st.header("3️⃣ Energía generada diaria por panel")

# Comprobamos columnas esperadas
col_fecha = "fecha"
col_gen = "ENERGIA GENERADA POR UN PANEL DE 1kWh"

if col_fecha not in df_generacion.columns or col_gen not in df_generacion.columns:
    st.error(
        "En `energia_generada.xlsx` deben existir las columnas:\n"
        f"- '{col_fecha}'\n"
        f"- '{col_gen}'"
    )
    st.stop()

# Renombramos para trabajar más cómodo
df_gen = df_generacion[[col_fecha, col_gen]].copy()
df_gen.columns = ["fecha", "energia_1kw_kwh"]
df_gen["fecha"] = pd.to_datetime(df_gen["fecha"], errors="coerce")
df_gen = df_gen.dropna(subset=["fecha"]).sort_values("fecha")

st.markdown(
    """
Los datos de generación están expresados como **kWh/día para un panel de 1 kW**.
Puedes introducir ahora la potencia real del panel para escalar la energía generada.
"""
)

panel_kw = st.number_input(
    "Potencia del panel fotovoltaico [kW]",
    min_value=0.1,
    max_value=50.0,
    value=1.0,
    step=0.1,
)
df_gen["energia_kwh"] = df_gen["energia_1kw_kwh"] * panel_kw

st.markdown(
    f"Energía generada diaria = `energia_1kw_kwh × {panel_kw} kW` → columna **energia_kwh**"
)

with st.expander("Ver datos de generación procesados"):
    st.dataframe(df_gen.head())

st.divider()

# --------------------------------------------------
# 4. Eficiencia global y demanda diaria
# --------------------------------------------------
st.header("4️⃣ Eficiencia global y demanda diaria")

col_e1, col_e2, col_e3, col_e4 = st.columns(4)

with col_e1:
    eta_fv = st.number_input(
        "η_fv (rendimiento FV)",
        min_value=0.0, max_value=1.0, value=0.90, step=0.01
    )
with col_e2:
    eta_cableado = st.number_input(
        "η_cableado",
        min_value=0.0, max_value=1.0, value=0.98, step=0.01
    )
with col_e3:
    eta_mppt = st.number_input(
        "η_MPPT / regulador",
        min_value=0.0, max_value=1.0, value=0.96, step=0.01
    )
with col_e4:
    eta_bat = st.number_input(
        "η_batería (carga/descarga)",
        min_value=0.0, max_value=1.0, value=0.90, step=0.01
    )

eta_global = eta_fv * eta_cableado * eta_mppt * eta_bat

st.markdown(
    f"""
**Eficiencia global**

\\[
η_{{global}} = η_{{fv}} · η_{{cableado}} · η_{{MPPT}} · η_{{bat}} = {eta_global:.4f}
\\]

≈ **{eta_global*100:.2f} %**
"""
)

if eta_global <= 0:
    st.error("La eficiencia global es 0. Ajusta los parámetros de rendimiento.")
    st.stop()

# Demanda diaria equivalente (constante todos los días)
demanda_kwh = consumo_total_kWh / eta_global

# Demanda diaria equivalente (constante todos los días)
demanda_kwh = consumo_total_kWh / eta_global

st.markdown("**Demanda diaria equivalente** (incluyendo pérdidas del sistema):")

st.latex(
    rf"\text{{demanda}} = \frac{{{consumo_total_kWh:.3f}\,\text{{kWh}}}}{{\eta_{{global}}}} = {demanda_kwh:.3f}\,\text{{kWh/día}}"
)

# Creamos dataframe de simulación
df = df_gen.copy()
df["consumo_kwh"] = consumo_total_kWh
df["demanda_kwh"] = demanda_kwh
df["balance_kwh"] = df["energia_kwh"] - df["demanda_kwh"]
df["balance_Wh"] = df["balance_kwh"] * 1000.0

st.divider()

# --------------------------------------------------
# 5. Parámetros de la batería y cálculo del SoC
# --------------------------------------------------
st.header("5️⃣ Parámetros de la batería y simulación del SoC")

col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    V_bat = st.number_input(
        "Voltaje nominal batería [V]",
        min_value=1.0, max_value=1000.0, value=12.0, step=1.0
    )
with col_b2:
    C_bat_Ah = st.number_input(
        "Capacidad nominal batería [Ah]",
        min_value=1.0, max_value=10000.0, value=250.0, step=1.0
    )
with col_b3:
    DoD_pct = st.number_input(
        "Profundidad máxima de descarga DoD [%]",
        min_value=0.0, max_value=100.0, value=80.0, step=1.0
    )

E_max_Wh = V_bat * C_bat_Ah
E_min_Wh = E_max_Wh * (1 - DoD_pct / 100.0)

st.markdown(
    f"""
- Energía máxima batería (100% SoC): **{E_max_Wh:.1f} Wh**  
- Capacidad mínima permitida (según DoD): **{E_min_Wh:.1f} Wh**
"""
)

soc_init_pct = st.slider(
    "SoC inicial de la batería [% de la capacidad máxima]",
    min_value=0, max_value=100, value=100, step=1
)
SoC0_Wh = E_max_Wh * soc_init_pct / 100.0

st.markdown(
    f"SoC inicial = **{SoC0_Wh:.1f} Wh**  ({soc_init_pct} % de {E_max_Wh:.1f} Wh)"
)

# Cálculo de SoC día a día
soc_list = []
soc = SoC0_Wh

for b in df["balance_Wh"].values:
    soc = soc + b
    # Limitamos físicamente entre 0 y E_max
    if soc > E_max_Wh:
        soc = E_max_Wh
    if soc < 0:
        soc = 0
    soc_list.append(soc)

df["SoC_Wh"] = soc_list
df["SoC_%"] = df["SoC_Wh"] / E_max_Wh * 100.0
df["bateria_por_debajo_min"] = df["SoC_Wh"] < E_min_Wh

dias_sin_bateria = int(df["bateria_por_debajo_min"].sum())

st.divider()

# --------------------------------------------------
# 6. Resultados y visualización
# --------------------------------------------------
st.header("6️⃣ Resultados globales")

col_k1, col_k2, col_k3 = st.columns(3)

with col_k1:
    st.metric("Eficiencia global η_global", f"{eta_global*100:.2f} %")
with col_k2:
    st.metric("Días simulados", len(df))
with col_k3:
    st.metric("Días sin batería", dias_sin_bateria)

st.subheader("Tabla de resultados por día")
st.dataframe(
    df[[
        "fecha",
        "consumo_kwh",
        "energia_kwh",
        "demanda_kwh",
        "balance_kwh",
        "SoC_Wh",
        "SoC_%",
        "bateria_por_debajo_min"
    ]].set_index("fecha")
)

st.subheader("📈 Generación y demanda energética anual [kWh]")
st.line_chart(
    df.set_index("fecha")[[ 
        "demanda_kwh",
        "energia_kwh",
    ]]
)

st.subheader("📉 Estado de carga de la batería (SoC) [%]")
st.line_chart(
    df.set_index("fecha")[[
        "SoC_%"
    ]]
)

st.subheader("📉 Balance energético anual [kWh]")

# Color condicional para excedente / déficit
df["color"] = df["balance_kwh"].apply(
    lambda x: "EXCEDENTE" if x >= 0 else "DEFICIT"
)

chart_balance = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("fecha:T", title="Fecha"),
        y=alt.Y("balance_kwh:Q", title="Balance energético (kWh)"),
        color=alt.condition(
            alt.datum.balance_kwh >= 0,
            alt.value("#13A10E"),   # verde
            alt.value("#CC0000"),   # rojo
        ),
        tooltip=[
            alt.Tooltip("fecha:T", title="Fecha"),
            alt.Tooltip("balance_kwh:Q", title="Balance (kWh)"),
            alt.Tooltip("color:N", title="Tipo"),
        ]
    )
    .properties(
        width="container",
        height=350,
    )
)

st.altair_chart(chart_balance, use_container_width=True)


# --------------------------------------------------
# 7. Gráfico tipo Excel: Días sin suministro vs batería y potencia FV
# --------------------------------------------------

st.header("📉 Evaluación de la autonomía del sistema en funcion de la capacidad de la batería y potencia FV")

st.markdown(
    """
Este gráfico muestra el número de **días sin suministro** para diferentes potencias
fotovoltaicas y capacidades de batería, reproduciendo exactamente el estilo del gráfico Excel.
"""
)

# Valores iguales al Excel
lista_bat_Wh = [600, 1200, 1800, 2400, 3000]    # Capacidad de la bateria Wh
lista_pv_kw = [0.4, 0.5, 0.6, 0.8, 1.0]         # Potencia FV 

etiquetas_pv = {
    0.4: "2 × 200W",
    0.5: "2 × 250W",
    0.6: "2 × 300W",
    0.8: "2 × 400W",
    1.0: "2 × 500W",
}

# Colores fijos igual que Excel
colores_pv = {
    "2 × 200W": "#E41A1C",  # rojo
    "2 × 250W": "#FFB000",  # amarillo
    "2 × 300W": "#984EA3",  # morado
    "2 × 400W": "#377EB8",  # azul
    "2 × 500W": "#4DAF4A",  # verde
}

# Función para calcular días sin suministro
def sim_dias_sin(panel_kw: float, bat_Wh: float) -> int:
    E_max_Wh = bat_Wh
    E_min_Wh = E_max_Wh * (1 - DoD_pct / 100.0)
    soc = E_max_Wh
    dias_sin = 0

    for energia_1kw in df_gen["energia_1kw_kwh"]:
        energia_kwh = energia_1kw * panel_kw
        balance_kwh = energia_kwh - demanda_kwh
        soc += balance_kwh * 1000.0

        # límites físicos
        soc = min(soc, E_max_Wh)
        soc = max(soc, 0)

        if soc < E_min_Wh:
            dias_sin += 1

    return dias_sin

# Construir tabla
rows = []
for bat_Wh in lista_bat_Wh:
    for pv_kw in lista_pv_kw:
        dias_sin = sim_dias_sin(pv_kw, bat_Wh)
        etiqueta = etiquetas_pv[pv_kw]
        rows.append(
            {
                "E_bateria_Wh": bat_Wh,
                "Potencia_label": etiqueta,
                "Dias_sin": dias_sin,
            }
        )

df_excel = pd.DataFrame(rows)

# Gráfico tipo Excel
chart = (
    alt.Chart(df_excel)
    .mark_line(point=True, strokeWidth=2)
    .encode(
        x=alt.X("E_bateria_Wh:Q", title="Energía batería (Wh)"),
        y=alt.Y("Dias_sin:Q", title="Días sin suministro"),
        color=alt.Color(
            "Potencia_label:N",
            title="Potencia FV",
            scale=alt.Scale(domain=list(colores_pv.keys()),
                            range=list(colores_pv.values())),
        ),
        tooltip=[
            alt.Tooltip("E_bateria_Wh:Q", title="Energía batería (Wh)"),
            alt.Tooltip("Potencia_label:N", title="Potencia FV"),
            alt.Tooltip("Dias_sin:Q", title="Días sin suministro"),
        ],
    )
    .properties(width="container", height=400)
)

# Añadir etiquetas como números sobre cada punto
text = (
    alt.Chart(df_excel)
    .mark_text(
        align='left',
        baseline='middle',
        dx=6,       # separación horizontal
        dy=-6,      # separación vertical
        fontSize=12
    )
    .encode(
        x="E_bateria_Wh:Q",
        y="Dias_sin:Q",
        text="Dias_sin:Q",
        color=alt.Color(
            "Potencia_label:N",
            scale=alt.Scale(domain=list(colores_pv.keys()),
                            range=list(colores_pv.values())),
        )
    )
)

# Mostrar gráfico final
st.altair_chart(chart + text, use_container_width=True)

