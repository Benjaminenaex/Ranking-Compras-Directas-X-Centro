import io
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Dashboard Compras Directas & Cruce SAP",
    page_icon="📊",
    layout="wide",
)

# =====================================================================
# CONFIGURACIÓN DE PLATAFORMAS (Ariba vs SAP HANA)
# Regla: se mira el primer dígito del ID del pedido (Documento de compras)
#   - Ariba    -> ID comienza con 3
#   - SAP HANA -> ID comienza con 4 (incluye 45... y 47...)
# =====================================================================
PREFIJOS_ARIBA = ("3",)
PREFIJOS_SAP_HANA = ("4", "45", "47")

PLAT_TODAS = "Todas"
ESTADO_CRUZADO = "✅ Cruzado con ME2M"
ESTADO_SOLO_ME5A = "⚠️ Pedido no está en ME2M"
PLAT_ARIBA = "Ariba"
PLAT_HANA = "SAP HANA"
PLAT_OTRO = "Sin clasificar"

COLORES_PLATAFORMA = {
    PLAT_TODAS: "#E11D48",
    PLAT_ARIBA: "#F59E0B",
    PLAT_HANA: "#2563EB",
    PLAT_OTRO: "#94A3B8",
}

# =====================================================================
# ESTILOS
# =====================================================================
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.2 !important;
    }
    [data-testid="stMetric"] {
        border: 1px solid rgba(148,163,184,0.30);
        border-radius: 12px;
        padding: 12px 16px;
        background: rgba(148,163,184,0.06);
    }
    .custom-title {
        display: flex;
        align-items: center;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        color: inherit;
    }
    .custom-subtitle {
        opacity: 0.7;
        margin-bottom: 1.2rem;
        font-size: 0.95rem;
    }
    .custom-header {
        display: flex;
        align-items: center;
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.75rem;
        color: inherit;
    }
    .svg-icon {
        display: inline-block;
        vertical-align: middle;
        margin-right: 12px;
        flex-shrink: 0;
    }
    .section-label {
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        margin: 0.4rem 0 0.6rem 0;
    }
    /* Tarjetas del selector de plataforma */
    .plat-card {
        border: 2px solid rgba(148,163,184,0.35);
        border-radius: 14px;
        padding: 16px 18px;
        min-height: 150px;
        margin-bottom: 8px;
        transition: all 0.15s ease;
    }
    .plat-head {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.35rem;
        font-weight: 800;
    }
    .plat-dot {
        width: 14px; height: 14px; border-radius: 50%;
        display: inline-block;
    }
    .plat-rule { font-size: 0.85rem; opacity: 0.7; margin-top: 2px; }
    .plat-amount { font-size: 1.7rem; font-weight: 800; margin-top: 10px; }
    .plat-meta { font-size: 0.9rem; opacity: 0.8; }
    .plat-check { font-size: 0.85rem; font-weight: 700; margin-top: 6px; }
    /* Botones grandes en el área principal */
    [data-testid="stMain"] .stButton > button,
    section.main .stButton > button {
        min-height: 3rem;
        font-size: 1.05rem;
        font-weight: 700;
        border-radius: 10px;
    }
    /* Tarjetas de bienvenida */
    .step-card {
        border: 1px solid rgba(148,163,184,0.35);
        border-radius: 14px;
        padding: 18px;
        min-height: 150px;
        background: rgba(148,163,184,0.06);
    }
    .step-num {
        display: inline-flex; align-items: center; justify-content: center;
        width: 32px; height: 32px; border-radius: 50%;
        background: #E11D48; color: #FFFFFF; font-weight: 800;
        margin-bottom: 8px;
    }
    .step-title { font-weight: 700; font-size: 1.05rem; margin-bottom: 4px; }
    .step-text { opacity: 0.8; font-size: 0.92rem; }
    /* Tarjetas del diagnóstico Ariba: el texto se ajusta en varias líneas, nunca se corta */
    .diag-card {
        border: 1px solid rgba(148,163,184,0.30);
        border-radius: 12px;
        padding: 14px 16px;
        height: 100%;
        min-height: 150px;
        background: rgba(148,163,184,0.06);
    }
    .diag-title { font-weight: 700; font-size: 0.98rem; line-height: 1.25; white-space: normal; }
    .diag-value { font-size: 1.9rem; font-weight: 800; margin: 6px 0 4px 0; }
    .diag-text { font-size: 0.85rem; opacity: 0.75; line-height: 1.3; white-space: normal; }
    .diag-summary {
        border-left: 4px solid #F59E0B;
        padding: 10px 14px;
        margin: 4px 0 14px 0;
        border-radius: 6px;
        background: rgba(245,158,11,0.08);
        font-size: 0.95rem;
        line-height: 1.4;
    }
    </style>
""", unsafe_allow_html=True)

# Dibujos vectoriales minimalistas SVG
SVG_ICONS = {
    "report": '<svg class="svg-icon" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/><path d="M3 11l6-5 4 4 7-7"/><path d="M16 3h4v4"/></svg>',
    "trophy": '<svg class="svg-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/></svg>',
    "pie": '<svg class="svg-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>',
    "link": '<svg class="svg-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "alert": '<svg class="svg-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    "split": '<svg class="svg-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 3h5v5"/><path d="M8 3H3v5"/><path d="M12 22v-8.3a4 4 0 0 0-1.172-2.872L3 3"/><path d="m15 9 6-6"/></svg>',
}

st.markdown(
    f'<div class="custom-title">{SVG_ICONS["report"]} Reporte de Compras Directas, PNNA & Cruce SAP</div>'
    '<div class="custom-subtitle">Analiza compras directas (AD) por plataforma (Ariba / SAP HANA), centro, grupo de compra y PNNA.</div>',
    unsafe_allow_html=True,
)

# =====================================================================
# FUNCIONES AUXILIARES
# =====================================================================
@st.cache_data
def load_excel(file):
    if file is not None:
        df = pd.read_excel(file)
        df.columns = df.columns.astype(str).str.strip()
        return df
    return None


def clean_numeric(series):
    """Limpia cadenas de números típicas de SAP (formato europeo, signos negativos finales, etc.)"""
    if series is None:
        return pd.Series(dtype=float)
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0)

    s = series.astype(str).str.strip()
    s = s.str.replace(r'[$€CLPUSD\s]', '', regex=True)
    s = s.str.replace(r'^(.+)-$', r'-\1', regex=True)
    s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce').fillna(0)


def clasificar_plataforma(series):
    """Clasifica cada ID de pedido como Ariba (inicia con 3) o SAP HANA (inicia con 4 / 45 / 47)."""
    ids = (
        series.astype(str)
        .str.strip()
        .str.replace(r'\.0$', '', regex=True)   # 4500012345.0 -> 4500012345
        .str.lstrip('0')                          # elimina ceros a la izquierda
    )
    ids = ids.where(series.notna(), '')

    plataforma = pd.Series(PLAT_OTRO, index=series.index, dtype=object)
    plataforma[ids.str.startswith(PREFIJOS_SAP_HANA)] = PLAT_HANA
    plataforma[ids.str.startswith(PREFIJOS_ARIBA)] = PLAT_ARIBA
    return plataforma


def a_texto(series):
    """Convierte una columna a texto limpio (sin '.0' de Excel), dejando vacíos como NaN."""
    s = series.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    return s.where(series.notna() & (s != '') & (s.str.lower() != 'nan'))


@st.cache_data(show_spinner=False)
def columnas_con_ids_ariba(df):
    """Busca en todas las columnas valores con forma de ID Ariba (empiezan con 3 y tienen 6+ dígitos)."""
    resultado = []
    for c in df.columns:
        s = df[c].dropna().astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.lstrip('0')
        if s.empty:
            continue
        n3 = int(s.str.match(r'^3\d{5,}$').sum())
        n4 = int(s.str.match(r'^4\d{5,}$').sum())
        if n3 > 0:
            resultado.append({'Columna': c, 'Valores que empiezan con 3': n3, 'Valores que empiezan con 4': n4})
    return pd.DataFrame(resultado).sort_values('Valores que empiezan con 3', ascending=False) if resultado else pd.DataFrame()


# Streamlit no permite aplicar estilos (Pandas Styler) a tablas muy grandes:
# por sobre este número de celdas se muestra una versión con montos como texto.
MAX_CELDAS_ESTILO = 150_000


def estilo_montos(df, cols_monto=(), cols_enteros=()):
    """Formatea montos con $ y separador de miles.
    - Tablas chicas: usa Styler (mantiene el orden numérico al ordenar columnas).
    - Tablas grandes: convierte los montos a texto para evitar el error de Streamlit por exceso de celdas."""
    cols_monto = [c for c in cols_monto if c in df.columns]
    cols_enteros = [c for c in cols_enteros if c in df.columns]

    if df.size <= MAX_CELDAS_ESTILO:
        fmt = {c: "${:,.0f}" for c in cols_monto}
        fmt.update({c: "{:,.0f}" for c in cols_enteros})
        return df.style.format(fmt, na_rep="-")

    df_txt = df.copy()
    for c in cols_monto:
        df_txt[c] = pd.to_numeric(df_txt[c], errors='coerce').map(lambda x: f"${x:,.0f}" if pd.notna(x) else "-")
    for c in cols_enteros:
        df_txt[c] = pd.to_numeric(df_txt[c], errors='coerce').map(lambda x: f"{x:,.0f}" if pd.notna(x) else "-")
    return df_txt


def buscar_en_df(df, texto):
    """Filtra filas que contengan el texto en cualquier columna."""
    if not texto:
        return df
    mask = df.astype(str).apply(lambda col: col.str.contains(texto, case=False, na=False, regex=False)).any(axis=1)
    return df[mask]


def tarjeta_plataforma(nombre, regla, monto, cant, pct, color, activa):
    borde = color if activa else "rgba(148,163,184,0.35)"
    fondo = f"{color}1F" if activa else "rgba(148,163,184,0.06)"
    check = "✔ SELECCIONADO" if activa else "&nbsp;"
    return f"""
    <div class="plat-card" style="border-color:{borde}; background:{fondo};">
        <div class="plat-head"><span class="plat-dot" style="background:{color};"></span>{nombre}</div>
        <div class="plat-rule">{regla}</div>
        <div class="plat-amount">${monto:,.0f}</div>
        <div class="plat-meta">{cant:,} pedidos · {pct:.1f}% del monto</div>
        <div class="plat-check" style="color:{color};">{check}</div>
    </div>
    """


def set_plataforma(nombre):
    st.session_state.plataforma = nombre


def limpiar_filtros():
    st.session_state.plataforma = PLAT_TODAS
    st.session_state.centros_sel = []


def write_sheet_autofit(writer, df, sheet_name, workbook):
    """Escribe hojas en Excel autoajustando anchos para prevenir '####' y formato de texto estricto para evitar '4,5E+09'"""
    if df is None or df.empty:
        return

    df_clean = df.copy()

    # Pre-formatear documentos SAP a texto limpio sin notación científica
    for c in df_clean.columns:
        c_str = str(c).lower()
        if any(k in c_str for k in ['documento', 'pedido', 'solicitud', 'proveedor', 'posicion', 'posición', 'material', 'licitación', 'licitacion']):
            df_clean[c] = df_clean[c].astype(str).str.replace(r'\.0$', '', regex=True).str.replace('nan', '', case=False).str.replace('None', '', case=False)

    df_clean.to_excel(writer, sheet_name=sheet_name, index=False)
    ws = writer.sheets[sheet_name]

    # Formatos
    fmt_header = workbook.add_format({'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#1E293B', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
    fmt_currency = workbook.add_format({'num_format': '$ #,##0', 'border': 1})
    fmt_integer = workbook.add_format({'num_format': '#,##0', 'border': 1, 'align': 'center'})
    fmt_date = workbook.add_format({'num_format': 'yyyy-mm-dd', 'border': 1, 'align': 'center'})
    fmt_doc = workbook.add_format({'num_format': '@', 'border': 1, 'align': 'center'})
    fmt_text = workbook.add_format({'border': 1})

    for col_idx, col_name in enumerate(df_clean.columns):
        col_series = df_clean[col_name].astype(str)
        max_val = col_series.str.len().max()
        max_val_len = int(max_val) if pd.notna(max_val) else 0
        max_hdr_len = len(str(col_name))
        col_width = max(max(max_val_len, max_hdr_len) + 6, 14)

        col_lower = str(col_name).lower()
        if 'valor' in col_lower or 'monto' in col_lower or 'precio' in col_lower or '$' in col_name:
            cell_fmt = fmt_currency
        elif 'fecha' in col_lower:
            cell_fmt = fmt_date
        elif any(k in col_lower for k in ['documento', 'pedido', 'solicitud', 'proveedor', 'material']):
            cell_fmt = fmt_doc
        elif col_lower in ['posición', 'posicion', 'cant. pedidos', 'cant. registros', 'cant. solpeds', 'posisión']:
            cell_fmt = fmt_integer
        else:
            cell_fmt = fmt_text

        ws.set_column(col_idx, col_idx, col_width, cell_fmt)
        ws.write(0, col_idx, str(col_name), fmt_header)


def export_to_excel_styled(df_ranking, df_grupo, df_pnna, df_cruce, df_me2m_full, df_me5a_full, df_plataforma=None):
    output = io.BytesIO()

    has_xlsxwriter = False
    try:
        import xlsxwriter  # noqa: F401
        engine = 'xlsxwriter'
        has_xlsxwriter = True
    except (ImportError, ModuleNotFoundError):
        engine = None

    writer_kwargs = {'engine': engine} if engine else {}

    with pd.ExcelWriter(output, **writer_kwargs) as writer:
        if has_xlsxwriter:
            workbook = writer.book

            # 0. Resumen Ariba vs SAP HANA
            if df_plataforma is not None and not df_plataforma.empty:
                write_sheet_autofit(writer, df_plataforma, 'Ariba vs SAP HANA', workbook)
                ws0 = writer.sheets['Ariba vs SAP HANA']
                n = len(df_plataforma) + 1
                chart0 = workbook.add_chart({'type': 'doughnut'})
                chart0.add_series({
                    'name': 'Monto por Plataforma',
                    'categories': f"='Ariba vs SAP HANA'!$A$2:$A${n}",
                    'values': f"='Ariba vs SAP HANA'!$B$2:$B${n}",
                    'points': [{'fill': {'color': COLORES_PLATAFORMA.get(p, '#94A3B8')}} for p in df_plataforma['Plataforma']],
                    'data_labels': {'percentage': True},
                })
                chart0.set_title({'name': 'Compras Directas: Ariba vs SAP HANA'})
                chart0.set_size({'width': 520, 'height': 380})
                ws0.insert_chart('F2', chart0)

            # 1. Ranking Centros
            if df_ranking is not None and not df_ranking.empty:
                write_sheet_autofit(writer, df_ranking, 'Ranking Centros', workbook)
                ws1 = writer.sheets['Ranking Centros']

                chart1 = workbook.add_chart({'type': 'column'})
                chart1.add_series({
                    'name': 'Monto Total ($)',
                    'categories': f"='Ranking Centros'!$B$2:$B${min(21, len(df_ranking)+1)}",
                    'values': f"='Ranking Centros'!$C$2:$C${min(21, len(df_ranking)+1)}",
                    'fill': {'color': '#E11D48'}
                })
                chart1.set_title({'name': 'Top Compras Directas por Centro'})
                chart1.set_x_axis({'name': 'Centro'})
                chart1.set_y_axis({'name': 'Monto ($)'})
                chart1.set_legend({'position': 'none'})
                chart1.set_size({'width': 750, 'height': 420})
                ws1.insert_chart('F2', chart1)

            # 2. Grupos de Compra
            if df_grupo is not None and not df_grupo.empty:
                write_sheet_autofit(writer, df_grupo, 'Grupos de Compra', workbook)
                ws2 = writer.sheets['Grupos de Compra']

                chart2 = workbook.add_chart({'type': 'column'})
                chart2.add_series({
                    'name': 'Monto Total ($)',
                    'categories': f"='Grupos de Compra'!$A$2:$A${min(12, len(df_grupo)+1)}",
                    'values': f"='Grupos de Compra'!$B$2:$B${min(12, len(df_grupo)+1)}",
                    'fill': {'color': '#2563EB'}
                })
                chart2.set_title({'name': 'Monto por Grupo de Compra'})
                chart2.set_legend({'position': 'none'})
                chart2.set_size({'width': 650, 'height': 380})
                ws2.insert_chart('D2', chart2)

            # 3. PNNA por Área
            if df_pnna is not None and not df_pnna.empty:
                write_sheet_autofit(writer, df_pnna, 'PNNA por Área', workbook)
                ws3 = writer.sheets['PNNA por Área']

                chart3 = workbook.add_chart({'type': 'column'})
                chart3.add_series({
                    'name': 'Monto PNNA ($)',
                    'categories': f"='PNNA por Área'!$A$2:$A${min(16, len(df_pnna)+1)}",
                    'values': f"='PNNA por Área'!$C$2:$C${min(16, len(df_pnna)+1)}",
                    'fill': {'color': '#D97706'}
                })
                chart3.set_title({'name': 'Top PNNA por Área / Autor'})
                chart3.set_legend({'position': 'none'})
                chart3.set_size({'width': 750, 'height': 420})
                ws3.insert_chart('F2', chart3)

            # 4. Cruce SOLPED vs Pedido
            if df_cruce is not None and not df_cruce.empty:
                write_sheet_autofit(writer, df_cruce, 'Cruce ME5A vs ME2M', workbook)

            # 5. Detalle ME2M Completo
            if df_me2m_full is not None and not df_me2m_full.empty:
                write_sheet_autofit(writer, df_me2m_full.head(5000), 'Detalle Pedidos', workbook)

        else:
            # Fallback seguro openpyxl si xlsxwriter no está disponible
            if df_plataforma is not None and not df_plataforma.empty:
                df_plataforma.to_excel(writer, sheet_name='Ariba vs SAP HANA', index=False)
            if df_ranking is not None and not df_ranking.empty:
                df_ranking.to_excel(writer, sheet_name='Ranking Centros', index=False)
            if df_grupo is not None and not df_grupo.empty:
                df_grupo.to_excel(writer, sheet_name='Grupos de Compra', index=False)
            if df_pnna is not None and not df_pnna.empty:
                df_pnna.to_excel(writer, sheet_name='PNNA por Área', index=False)
            if df_cruce is not None and not df_cruce.empty:
                df_cruce.to_excel(writer, sheet_name='Cruce ME5A vs ME2M', index=False)
            if df_me2m_full is not None and not df_me2m_full.empty:
                df_me2m_full.head(5000).to_excel(writer, sheet_name='Detalle Pedidos', index=False)

    return output.getvalue()


# =====================================================================
# ESTADO INICIAL
# =====================================================================
if "plataforma" not in st.session_state:
    st.session_state.plataforma = PLAT_TODAS
if "centros_sel" not in st.session_state:
    st.session_state.centros_sel = []

# =====================================================================
# BARRA LATERAL: CARGA DE ARCHIVOS
# =====================================================================
st.sidebar.markdown("## 📂 1. Cargar archivos SAP")
file_me2m = st.sidebar.file_uploader(
    "ME2M – Pedidos de compra (.xlsx)",
    type=["xlsx"],
    help="Se usa para Compras Directas, el filtro Ariba / SAP HANA, Grupos de Compra y el Cruce.",
)
file_me5a = st.sidebar.file_uploader(
    "ME5A con Ariba – SOLPEDs (.xlsx)",
    type=["xlsx"],
    help="Se usa para PNNA (posiciones sin pedido) y el Cruce con ME2M.",
)

df_me5a = load_excel(file_me5a)
df_me2m = load_excel(file_me2m)

# Estado de carga visible
estado_me2m = f"✅ ME2M cargado ({len(df_me2m):,} filas)" if df_me2m is not None else "⬜ ME2M pendiente"
estado_me5a = f"✅ ME5A cargado ({len(df_me5a):,} filas)" if df_me5a is not None else "⬜ ME5A pendiente"
st.sidebar.caption(f"{estado_me2m}  \n{estado_me5a}")

# =====================================================================
# PANTALLA DE BIENVENIDA (sin archivos)
# =====================================================================
if df_me2m is None and df_me5a is None:
    st.info("👈 Para comenzar, sube tus archivos de Excel en el panel de la izquierda.")
    s1, s2, s3 = st.columns(3)
    pasos = [
        ("1", "Sube los archivos", "Carga el ME2M (pedidos) y, si quieres analizar PNNA y el cruce, también el ME5A."),
        ("2", "Elige la plataforma", "Usa el selector grande para ver Ariba (ID inicia con 3), SAP HANA (ID inicia con 4 / 45 / 47) o todas."),
        ("3", "Explora y exporta", "Revisa las pestañas de análisis y descarga el reporte consolidado en Excel."),
    ]
    for col, (n, titulo, texto) in zip([s1, s2, s3], pasos):
        col.markdown(
            f'<div class="step-card"><div class="step-num">{n}</div>'
            f'<div class="step-title">{titulo}</div><div class="step-text">{texto}</div></div>',
            unsafe_allow_html=True,
        )
    st.stop()

# =====================================================================
# PROCESAMIENTO ME2M
# =====================================================================
if df_me2m is not None:
    col_monto_me2m = next((c for c in df_me2m.columns if 'valor' in c.lower() or 'monto' in c.lower()), 'Por entregar (valor)')
    col_licita_me2m = next((c for c in df_me2m.columns if 'licita' in c.lower()), 'Licitación')
    col_centro_me2m = next((c for c in df_me2m.columns if 'centro' in c.lower() and 'suministrador' not in c.lower()), 'Centro')
    col_grp_me2m = next((c for c in df_me2m.columns if 'grupo' in c.lower()), 'Grupo de compras')
    col_doc_me2m = next((c for c in df_me2m.columns if 'documento' in c.lower() and 'fecha' not in c.lower()), 'Documento compras')
    col_pos_me2m = next((c for c in df_me2m.columns if 'posición' in c.lower() or 'posicion' in c.lower()), 'Posición')

    # Configuración de la clasificación Ariba / SAP HANA (editable por el usuario)
    with st.sidebar.expander("⚙️ Configuración Ariba / SAP HANA"):
        opciones_id = list(df_me2m.columns)
        idx_default = opciones_id.index(col_doc_me2m) if col_doc_me2m in opciones_id else 0
        col_id_plataforma = st.selectbox(
            "Columna ID del pedido",
            options=opciones_id,
            index=idx_default,
            help="Se evalúa el primer dígito: 3 = Ariba · 4 / 45 / 47 = SAP HANA.",
        )
        incluir_ariba_sin_ad = st.checkbox(
            "Contar pedidos Ariba (ID 3…) aunque su Licitación no empiece con AD",
            value=True,
            help="Los pedidos que nacen en Ariba normalmente no traen 'AD' en Licitación, por eso quedaban fuera.",
        )
        incluir_ariba_me5a = st.checkbox(
            "Agregar pedidos Ariba que están en ME5A pero no en ME2M",
            value=True,
            help="Toma el N° de pedido de la ME5A con Ariba. El monto usado es el valor de la SOLPED.",
        )

    df_me2m['Monto_Limpio'] = clean_numeric(df_me2m[col_monto_me2m]) if col_monto_me2m in df_me2m.columns else 0.0
    if col_licita_me2m in df_me2m.columns:
        df_me2m['Es_AD'] = df_me2m[col_licita_me2m].astype(str).str.strip().str.upper().str.startswith('AD')
    else:
        df_me2m['Es_AD'] = False
    df_me2m['Plataforma'] = clasificar_plataforma(df_me2m[col_id_plataforma])
    df_me2m['Es_Compra_Directa'] = df_me2m['Es_AD'] | ((df_me2m['Plataforma'] == PLAT_ARIBA) & incluir_ariba_sin_ad)
    df_me2m['Fuente'] = 'ME2M'
    for _c in [col_centro_me2m, col_grp_me2m]:
        if _c in df_me2m.columns:
            df_me2m[_c] = a_texto(df_me2m[_c])

# =====================================================================
# PROCESAMIENTO ME5A
# =====================================================================
if df_me5a is not None:
    col_monto_me5a = next((c for c in df_me5a.columns if 'valor' in c.lower() or 'monto' in c.lower()), 'Valor total')
    col_ped_me5a = next((c for c in df_me5a.columns if 'pedido' in c.lower() and 'posición' not in c.lower() and 'solicitud' not in c.lower()), 'Pedido')
    col_posped_me5a = next((c for c in df_me5a.columns if ('posició' in c.lower() or 'posicion' in c.lower()) and 'tipo' not in c.lower()), 'Posición de pedido')
    col_autor_me5a = next((c for c in df_me5a.columns if 'autor' in c.lower() or 'solicitante' in c.lower()), 'Autor')
    col_centro_me5a = next((c for c in df_me5a.columns if 'centro' in c.lower()), 'Centro')

    df_me5a['Monto_Limpio'] = clean_numeric(df_me5a[col_monto_me5a]) if col_monto_me5a in df_me5a.columns else 0.0
    df_me5a['Es_PNNA'] = df_me5a[col_ped_me5a].isna() | (df_me5a[col_ped_me5a] == 0) | (df_me5a[col_ped_me5a].astype(str).str.strip() == '')
    if col_centro_me5a in df_me5a.columns:
        df_me5a[col_centro_me5a] = a_texto(df_me5a[col_centro_me5a])
    df_me5a['Plataforma_Pedido'] = clasificar_plataforma(df_me5a[col_ped_me5a]) if col_ped_me5a in df_me5a.columns else PLAT_OTRO

# =====================================================================
# PEDIDOS ARIBA: diagnóstico y rescate desde ME5A
# =====================================================================
diag_ariba = {'me2m_total': 0, 'me2m_ad': 0, 'me5a_total': 0, 'me5a_extra': 0, 'me5a_agregados': 0}

if df_me2m is not None:
    es_ariba_me2m = df_me2m['Plataforma'] == PLAT_ARIBA
    diag_ariba['me2m_total'] = int(es_ariba_me2m.sum())
    diag_ariba['me2m_ad'] = int((es_ariba_me2m & df_me2m['Es_AD']).sum())

if df_me2m is not None and df_me5a is not None and col_ped_me5a in df_me5a.columns:
    ariba_me5a = df_me5a[(~df_me5a['Es_PNNA']) & (df_me5a['Plataforma_Pedido'] == PLAT_ARIBA)].copy()
    diag_ariba['me5a_total'] = len(ariba_me5a)

    if not ariba_me5a.empty:
        ids_me2m = set(pd.to_numeric(df_me2m[col_id_plataforma], errors='coerce').dropna().astype('int64'))
        ariba_me5a['_ped'] = pd.to_numeric(ariba_me5a[col_ped_me5a], errors='coerce')
        ariba_me5a = ariba_me5a[ariba_me5a['_ped'].notna() & ~ariba_me5a['_ped'].isin(ids_me2m)]
        diag_ariba['me5a_extra'] = len(ariba_me5a)

        if incluir_ariba_me5a and not ariba_me5a.empty:
            col_grp_me5a = next((c for c in df_me5a.columns if 'grupo' in c.lower()), None)
            filas = pd.DataFrame(index=ariba_me5a.index)
            filas[col_id_plataforma] = ariba_me5a['_ped'].astype('int64')
            filas[col_doc_me2m] = ariba_me5a['_ped'].astype('int64')
            filas[col_pos_me2m] = (pd.to_numeric(ariba_me5a[col_posped_me5a], errors='coerce')
                                   if col_posped_me5a in ariba_me5a.columns else None)
            filas[col_centro_me2m] = ariba_me5a[col_centro_me5a] if col_centro_me5a in ariba_me5a.columns else None
            filas[col_grp_me2m] = (a_texto(ariba_me5a[col_grp_me5a]) if col_grp_me5a else 'Sin grupo (ME5A)')
            filas[col_licita_me2m] = 'Ariba (desde ME5A)'
            filas['Monto_Limpio'] = ariba_me5a['Monto_Limpio']
            filas['Es_AD'] = False
            filas['Plataforma'] = PLAT_ARIBA
            filas['Es_Compra_Directa'] = True
            filas['Fuente'] = 'ME5A'
            df_me2m = pd.concat([df_me2m, filas.reset_index(drop=True)], ignore_index=True)
            diag_ariba['me5a_agregados'] = len(filas)

# =====================================================================
# BARRA LATERAL: FILTROS
# =====================================================================
st.sidebar.markdown("## 🔎 2. Filtros")
centros_me2m = df_me2m[col_centro_me2m].dropna().astype(str).unique() if df_me2m is not None and col_centro_me2m in df_me2m.columns else []
centros_me5a = df_me5a[col_centro_me5a].dropna().astype(str).unique() if df_me5a is not None and col_centro_me5a in df_me5a.columns else []
todos_centros = sorted(list(set(centros_me2m).union(set(centros_me5a))))

# Evita errores si un centro guardado ya no existe tras cambiar de archivo
st.session_state.centros_sel = [c for c in st.session_state.centros_sel if c in todos_centros]

centros_sel = st.sidebar.multiselect(
    "Centro",
    options=todos_centros,
    key="centros_sel",
    placeholder="Todos los centros",
    help="Deja vacío para incluir todos los centros.",
)

st.sidebar.markdown(
    "**Plataforma:** "
    f"<span style='color:{COLORES_PLATAFORMA.get(st.session_state.plataforma, '#E11D48')}; font-weight:700;'>"
    f"{st.session_state.plataforma}</span>  \n"
    "<small>Se cambia con el selector grande del panel principal.</small>",
    unsafe_allow_html=True,
)
st.sidebar.button("↺ Limpiar filtros", on_click=limpiar_filtros, use_container_width=True)

# Filtro por centro
df_me2m_filt = df_me2m.copy() if df_me2m is not None else None
df_me5a_filt = df_me5a.copy() if df_me5a is not None else None

if centros_sel:
    if df_me2m_filt is not None:
        df_me2m_filt = df_me2m_filt[df_me2m_filt[col_centro_me2m].astype(str).isin(centros_sel)]
    if df_me5a_filt is not None:
        df_me5a_filt = df_me5a_filt[df_me5a_filt[col_centro_me5a].astype(str).isin(centros_sel)]

# =====================================================================
# SELECTOR GRANDE DE PLATAFORMA (Ariba / SAP HANA)
# =====================================================================
plataforma_sel = st.session_state.plataforma
resumen_plat = None
df_cd_base = None  # compras directas con filtro de centro, antes del filtro de plataforma

if df_me2m_filt is not None:
    df_cd_base = df_me2m_filt[df_me2m_filt['Es_Compra_Directa']]

    resumen_plat = (
        df_cd_base.groupby('Plataforma')['Monto_Limpio']
        .agg(['sum', 'count'])
        .reindex([PLAT_ARIBA, PLAT_HANA, PLAT_OTRO])
        .fillna(0)
        .reset_index()
        .rename(columns={'sum': 'Monto Total ($)', 'count': 'Cant. Pedidos'})
    )
    resumen_plat['Cant. Pedidos'] = resumen_plat['Cant. Pedidos'].astype(int)
    total_monto = resumen_plat['Monto Total ($)'].sum()
    total_cant = int(resumen_plat['Cant. Pedidos'].sum())
    resumen_plat['Participación (%)'] = (
        (resumen_plat['Monto Total ($)'] / total_monto * 100).round(1) if total_monto else 0.0
    )
    resumen_plat = resumen_plat[(resumen_plat['Plataforma'] != PLAT_OTRO) | (resumen_plat['Cant. Pedidos'] > 0)]

    def _dato(plat, campo):
        fila = resumen_plat[resumen_plat['Plataforma'] == plat]
        return float(fila[campo].iloc[0]) if not fila.empty else 0.0

    st.markdown('<div class="section-label">🎯 ¿Qué compras directas quieres analizar?</div>', unsafe_allow_html=True)

    opciones = [
        (PLAT_TODAS, "Todas las compras directas (AD)", total_monto, total_cant, 100.0 if total_monto else 0.0),
        (PLAT_ARIBA, "ID del pedido comienza con 3", _dato(PLAT_ARIBA, 'Monto Total ($)'), int(_dato(PLAT_ARIBA, 'Cant. Pedidos')), _dato(PLAT_ARIBA, 'Participación (%)')),
        (PLAT_HANA, "ID del pedido comienza con 4 · 45 · 47", _dato(PLAT_HANA, 'Monto Total ($)'), int(_dato(PLAT_HANA, 'Cant. Pedidos')), _dato(PLAT_HANA, 'Participación (%)')),
    ]

    cols_sel = st.columns(3)
    for col, (nombre, regla, monto, cant, pct) in zip(cols_sel, opciones):
        activa = plataforma_sel == nombre
        with col:
            st.markdown(
                tarjeta_plataforma(nombre, regla, monto, cant, pct, COLORES_PLATAFORMA[nombre], activa),
                unsafe_allow_html=True,
            )
            st.button(
                f"{'✔ ' if activa else ''}Ver {nombre}",
                key=f"btn_plat_{nombre}",
                type="primary" if activa else "secondary",
                use_container_width=True,
                on_click=set_plataforma,
                args=(nombre,),
            )

    # Diagnóstico de dónde vienen (o por qué faltan) los pedidos Ariba
    sin_ariba = int(_dato(PLAT_ARIBA, 'Cant. Pedidos')) == 0
    with st.expander("🔍 ¿De dónde salen los pedidos Ariba?", expanded=sin_ariba):
        # Resumen en una frase, en lenguaje simple
        n_me2m = diag_ariba['me2m_total']
        n_me5a = diag_ariba['me5a_agregados']
        if n_me2m == 0 and n_me5a > 0:
            resumen = (f"Los <b>{n_me5a:,}</b> pedidos Ariba vienen de la <b>ME5A</b>, "
                       "porque el archivo ME2M no trae pedidos que empiecen con 3.")
        elif n_me2m > 0 and n_me5a > 0:
            resumen = (f"Hay <b>{n_me2m:,}</b> pedidos Ariba en la <b>ME2M</b> y se sumaron "
                       f"<b>{n_me5a:,}</b> más que solo aparecen en la <b>ME5A</b>.")
        elif n_me2m > 0:
            resumen = f"Los <b>{n_me2m:,}</b> pedidos Ariba vienen de la <b>ME2M</b>."
        else:
            resumen = "No se encontraron pedidos Ariba (ID que empiece con 3) en ninguno de los archivos."
        st.markdown(f'<div class="diag-summary">{resumen}</div>', unsafe_allow_html=True)

        tarjetas_diag = [
            ("Pedidos Ariba en ME2M", n_me2m,
             "Pedidos del archivo ME2M cuyo número empieza con 3."),
            ("De esos, con licitación AD", diag_ariba['me2m_ad'],
             "Pedidos Ariba de ME2M marcados como compra directa (Licitación empieza con «AD»)."),
            ("Pedidos Ariba en ME5A", diag_ariba['me5a_total'],
             "Solicitudes (SOLPED) de la ME5A que ya tienen un pedido que empieza con 3."),
            ("Sumados desde ME5A", n_me5a,
             "Pedidos Ariba que no están en ME2M y se agregaron al análisis tomándolos de la ME5A."),
        ]
        for col, (titulo, valor, texto) in zip(st.columns(4), tarjetas_diag):
            col.markdown(
                f'<div class="diag-card"><div class="diag-title">{titulo}</div>'
                f'<div class="diag-value">{valor:,}</div>'
                f'<div class="diag-text">{texto}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("")

        if diag_ariba['me2m_total'] > diag_ariba['me2m_ad'] and not incluir_ariba_sin_ad:
            st.warning("Hay pedidos Ariba en ME2M sin 'AD' en Licitación. Activa la opción correspondiente en "
                       "**⚙️ Configuración Ariba / SAP HANA** para incluirlos.")
        if diag_ariba['me5a_extra'] > 0 and not incluir_ariba_me5a:
            st.warning(f"Hay {diag_ariba['me5a_extra']:,} registros Ariba en ME5A que no están en ME2M. "
                       "Activa la opción correspondiente en **⚙️ Configuración Ariba / SAP HANA** para incluirlos.")
        if sin_ariba:
            st.error(f"No se encontraron IDs que empiecen con 3 en la columna «{col_id_plataforma}» (ME2M) "
                     "ni en la columna de pedido de la ME5A. Abajo están las columnas donde sí aparecen "
                     "valores que empiezan con 3: elige la correcta en **⚙️ Configuración Ariba / SAP HANA**.")
            cols_busqueda = [c for c in df_me2m.columns if c not in ('Monto_Limpio', 'Es_AD', 'Es_Compra_Directa', 'Plataforma', 'Fuente')]
            cand = columnas_con_ids_ariba(df_me2m[df_me2m['Fuente'] == 'ME2M'][cols_busqueda])
            if not cand.empty:
                st.markdown("**ME2M – columnas con valores que empiezan con 3:**")
                st.dataframe(cand, hide_index=True, use_container_width=True)
            if df_me5a is not None:
                cand5 = columnas_con_ids_ariba(df_me5a.drop(columns=['Monto_Limpio', 'Es_PNNA', 'Plataforma_Pedido'], errors='ignore'))
                if not cand5.empty:
                    st.markdown("**ME5A – columnas con valores que empiezan con 3:**")
                    st.dataframe(cand5, hide_index=True, use_container_width=True)
            if cand.empty and (df_me5a is None or cand5.empty):
                st.info("Ningún archivo contiene valores que empiecen con 3. Revisa que la exportación de ME2M "
                        "incluya los pedidos creados desde Ariba (variante / clase de documento).")
        else:
            st.caption("ℹ️ Regla: un pedido es **Ariba** si su número empieza con **3**, y **SAP HANA** si empieza "
                       "con **4** (45 o 47). Para los pedidos que vienen de la ME5A, el monto usado es el de la SOLPED.")

    cant_otro = int(_dato(PLAT_OTRO, 'Cant. Pedidos'))
    if cant_otro > 0:
        st.caption(
            f"⚠️ {cant_otro:,} compras directas tienen un ID que no comienza con 3 ni con 4 "
            f"(columna «{col_id_plataforma}»). Sólo aparecen al elegir «Todas»."
        )

    # Aplicar filtro de plataforma
    if plataforma_sel != PLAT_TODAS:
        df_me2m_filt = df_me2m_filt[df_me2m_filt['Plataforma'] == plataforma_sel]
else:
    st.info("Para usar el filtro **Ariba / SAP HANA** debes cargar el archivo **ME2M**.")

st.markdown("---")

# =====================================================================
# PRE-CÁLCULO DE TABLAS
# =====================================================================
ranking_centro = None
ranking_plat = None
grp_df = None
pnna_area = None
merged_df = None
df_cd = None

if df_me2m_filt is not None:
    df_cd = df_me2m_filt[df_me2m_filt['Es_Compra_Directa']]
    ranking_centro = (
        df_cd.groupby(col_centro_me2m)['Monto_Limpio']
        .agg(['sum', 'count'])
        .reset_index()
        .rename(columns={'sum': 'Monto Total ($)', 'count': 'Cant. Pedidos'})
        .sort_values(by='Monto Total ($)', ascending=False)
    )
    ranking_centro['Posición'] = range(1, len(ranking_centro) + 1)
    ranking_centro = ranking_centro[['Posición', col_centro_me2m, 'Monto Total ($)', 'Cant. Pedidos']]

    ranking_plat = df_cd.groupby([col_centro_me2m, 'Plataforma'])['Monto_Limpio'].sum().reset_index()

    grp_df = df_cd.groupby(col_grp_me2m)['Monto_Limpio'].sum().reset_index().sort_values(by='Monto_Limpio', ascending=False)

if df_me5a_filt is not None:
    df_pnna = df_me5a_filt[df_me5a_filt['Es_PNNA']]
    pnna_area = (
        df_pnna.groupby([col_autor_me5a, col_centro_me5a])['Monto_Limpio']
        .agg(['sum', 'count'])
        .reset_index()
        .rename(columns={'sum': 'Monto PNNA ($)', 'count': 'Cant. SOLPEDs'})
        .sort_values(by='Monto PNNA ($)', ascending=False)
    )

if df_me5a_filt is not None and df_me2m_filt is not None:
    df_me5a_proc = df_me5a_filt[~df_me5a_filt['Es_PNNA']].copy()
    df_me5a_proc['Pedido_Key'] = pd.to_numeric(df_me5a_proc[col_ped_me5a], errors='coerce').fillna(0).astype(int)
    df_me5a_proc['Pos_Key'] = pd.to_numeric(df_me5a_proc[col_posped_me5a], errors='coerce').fillna(0).astype(int)

    df_me2m_proc = df_me2m_filt[df_me2m_filt['Fuente'] == 'ME2M'].copy()
    df_me2m_proc['Pedido_Key'] = pd.to_numeric(df_me2m_proc[col_doc_me2m], errors='coerce').fillna(0).astype(int)
    df_me2m_proc['Pos_Key'] = pd.to_numeric(df_me2m_proc[col_pos_me2m], errors='coerce').fillna(0).astype(int)

    # Cruce desde la SOLPED (ME5A) hacia el pedido (ME2M).
    # Se usa LEFT JOIN para no perder las SOLPED cuyo pedido (p. ej. pedidos Ariba) no viene en la ME2M.
    merged_df = pd.merge(
        df_me5a_proc, df_me2m_proc,
        on=['Pedido_Key', 'Pos_Key'],
        how='left', suffixes=('_SOLPED', '_PEDIDO'),
        indicator=True,
    )
    merged_df['Estado cruce'] = merged_df['_merge'].map(
        {'both': ESTADO_CRUZADO, 'left_only': ESTADO_SOLO_ME5A}
    ).astype(object)
    merged_df = merged_df.drop(columns=['_merge'])

    # Plataforma: la del pedido en ME2M; si no cruzó, se toma del N° de pedido en la ME5A
    if 'Plataforma' in merged_df.columns:
        merged_df['Plataforma'] = merged_df['Plataforma'].fillna(merged_df['Plataforma_Pedido'])
    else:
        merged_df['Plataforma'] = merged_df['Plataforma_Pedido']

    # Filtro de plataforma (Ariba / SAP HANA) aplicado también al cruce
    if plataforma_sel != PLAT_TODAS:
        merged_df = merged_df[merged_df['Plataforma'] == plataforma_sel]

# =====================================================================
# BARRA LATERAL: EXPORTAR
# =====================================================================
st.sidebar.markdown("## 📥 3. Exportar reporte")
st.sidebar.caption(f"Incluye los filtros activos (plataforma: **{plataforma_sel}**).")
excel_data = export_to_excel_styled(ranking_centro, grp_df, pnna_area, merged_df, df_me2m_filt, df_me5a_filt, resumen_plat)
st.sidebar.download_button(
    label="⬇️ Descargar Reporte Completo (Excel)",
    data=excel_data,
    file_name=f"Reporte_Compras_Directas_{plataforma_sel.replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)

# =====================================================================
# KPIs
# =====================================================================
etiqueta_plat = "" if plataforma_sel == PLAT_TODAS else f" · {plataforma_sel}"
st.markdown(
    f"**Mostrando:** <span style='color:{COLORES_PLATAFORMA.get(plataforma_sel)}; font-weight:800;'>{plataforma_sel}</span>",
    unsafe_allow_html=True,
)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

monto_cd = df_cd['Monto_Limpio'].sum() if df_cd is not None else 0.0
cant_cd = df_cd.shape[0] if df_cd is not None else 0
monto_pnna = df_me5a_filt[df_me5a_filt['Es_PNNA']]['Monto_Limpio'].sum() if df_me5a_filt is not None else 0.0
cant_pnna = df_me5a_filt[df_me5a_filt['Es_PNNA']].shape[0] if df_me5a_filt is not None else 0

kpi1.metric("💰 Monto Directas", f"${monto_cd:,.0f}", help=f"Plataforma: {plataforma_sel}")
kpi2.metric("🧾 Órdenes Directas", f"{cant_cd:,}", help=f"Plataforma: {plataforma_sel}")
kpi3.metric("⏳ Monto PNNA", f"${monto_pnna:,.0f}")
kpi4.metric("📋 SOLPEDs PNNA", f"{cant_pnna:,}")

st.markdown("")

# =====================================================================
# PESTAÑAS
# =====================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Ranking por Centro",
    "🔀 Ariba vs SAP HANA",
    "🧩 Grupo de Compra",
    "⚠️ PNNA por Área",
    "🔗 Cruce SOLPED vs Pedido",
])

# ---------------- Tab 1: Ranking Compras Directas x Centro ----------------
with tab1:
    st.markdown(f'<div class="custom-header">{SVG_ICONS["trophy"]} Ranking Compras Directas por Centro{etiqueta_plat}</div>', unsafe_allow_html=True)
    if ranking_centro is not None and not ranking_centro.empty:
        c1, c2 = st.columns([3, 2])
        with c1:
            top_centros = ranking_centro.head(20)[col_centro_me2m].astype(str).tolist()
            plot_df = ranking_plat.copy()
            plot_df[col_centro_me2m] = plot_df[col_centro_me2m].astype(str)
            plot_df = plot_df[plot_df[col_centro_me2m].isin(top_centros)]

            fig_centro = px.bar(
                plot_df,
                x=col_centro_me2m,
                y='Monto_Limpio',
                color='Plataforma',
                color_discrete_map=COLORES_PLATAFORMA,
                category_orders={col_centro_me2m: top_centros},
                title="Monto acumulado por Centro (Top 20)",
                labels={'Monto_Limpio': 'Monto ($)', col_centro_me2m: 'Centro'},
            )
            fig_centro.update_layout(
                barmode='stack', xaxis_type='category',
                margin=dict(l=10, r=10, t=40, b=10),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title=None),
            )
            fig_centro.update_traces(hovertemplate='%{x}<br>$%{y:,.0f}<extra>%{fullData.name}</extra>')
            st.plotly_chart(fig_centro, use_container_width=True)

        with c2:
            st.dataframe(
                estilo_montos(ranking_centro, cols_monto=['Monto Total ($)'], cols_enteros=['Cant. Pedidos']),
                hide_index=True,
                use_container_width=True,
                height=440,
            )
    elif df_me2m is None:
        st.warning("Para ver el Ranking de Compras Directas debes cargar el archivo ME2M.")
    else:
        st.info("No hay compras directas para los filtros seleccionados.")

# ---------------- Tab 2: Ariba vs SAP HANA ----------------
with tab2:
    st.markdown(f'<div class="custom-header">{SVG_ICONS["split"]} Compras Directas: Ariba vs SAP HANA</div>', unsafe_allow_html=True)
    if df_cd_base is not None and not df_cd_base.empty:
        st.caption("La comparación muestra ambas plataformas (respeta el filtro de centro). El detalle de abajo respeta la plataforma seleccionada.")
        c1, c2 = st.columns([2, 3])
        with c1:
            pie_df = resumen_plat[resumen_plat['Monto Total ($)'] > 0]
            fig_plat = px.pie(
                pie_df, values='Monto Total ($)', names='Plataforma', hole=0.55,
                color='Plataforma', color_discrete_map=COLORES_PLATAFORMA,
                title="Participación del monto",
            )
            fig_plat.update_traces(textposition='inside', textinfo='percent+label')
            fig_plat.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_plat, use_container_width=True)

            st.dataframe(
                estilo_montos(resumen_plat, cols_monto=['Monto Total ($)'], cols_enteros=['Cant. Pedidos']),
                hide_index=True, use_container_width=True,
            )
        with c2:
            comp_centro = df_cd_base.groupby([col_centro_me2m, 'Plataforma'])['Monto_Limpio'].sum().reset_index()
            comp_centro[col_centro_me2m] = comp_centro[col_centro_me2m].astype(str)
            orden = (
                comp_centro.groupby(col_centro_me2m)['Monto_Limpio'].sum()
                .sort_values(ascending=False).head(15).index.tolist()
            )
            comp_centro = comp_centro[comp_centro[col_centro_me2m].isin(orden)]
            fig_comp = px.bar(
                comp_centro, x='Monto_Limpio', y=col_centro_me2m, color='Plataforma',
                orientation='h', barmode='group',
                color_discrete_map=COLORES_PLATAFORMA,
                category_orders={col_centro_me2m: orden},
                title="Ariba vs SAP HANA por Centro (Top 15)",
                labels={'Monto_Limpio': 'Monto ($)', col_centro_me2m: 'Centro'},
            )
            fig_comp.update_layout(
                yaxis_type='category', margin=dict(l=10, r=10, t=40, b=10), height=480,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title=None),
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown(f"#### 🧾 Detalle de compras directas · {plataforma_sel}")
        cols_det = [c for c in [col_id_plataforma, col_doc_me2m, col_pos_me2m, 'Plataforma', col_centro_me2m,
                                col_grp_me2m, col_licita_me2m, 'Fuente', 'Monto_Limpio'] if c in df_cd.columns]
        cols_det = list(dict.fromkeys(cols_det))  # quita duplicados manteniendo orden
        texto_busq = st.text_input("Buscar en el detalle", placeholder="Ej: N° de pedido, centro, grupo…", key="busq_detalle")
        df_det = buscar_en_df(df_cd[cols_det], texto_busq).rename(columns={'Monto_Limpio': 'Monto ($)'})
        st.caption(f"{len(df_det):,} registros")
        st.dataframe(
            estilo_montos(df_det, cols_monto=['Monto ($)']),
            hide_index=True, use_container_width=True,
        )
    elif df_me2m is None:
        st.warning("Carga el archivo ME2M para comparar Ariba y SAP HANA.")
    else:
        st.info("No hay compras directas para los filtros seleccionados.")

# ---------------- Tab 3: Grupo de Compra ----------------
with tab3:
    st.markdown(f'<div class="custom-header">{SVG_ICONS["pie"]} Distribución por Grupo de Compra{etiqueta_plat}</div>', unsafe_allow_html=True)
    if grp_df is not None and not grp_df.empty:
        if len(grp_df) > 8:
            top_grp = grp_df.iloc[:8].copy()
            otros_monto = grp_df.iloc[8:]['Monto_Limpio'].sum()
            otros_df = pd.DataFrame([{col_grp_me2m: 'Otros', 'Monto_Limpio': otros_monto}])
            grp_df_plot = pd.concat([top_grp, otros_df], ignore_index=True)
        else:
            grp_df_plot = grp_df

        c1, c2 = st.columns([3, 2])
        with c1:
            fig_grp = px.pie(grp_df_plot, values='Monto_Limpio', names=col_grp_me2m, title="Top 8 Grupos de Compra + Otros", hole=0.4)
            fig_grp.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_grp, use_container_width=True)
        with c2:
            st.dataframe(
                estilo_montos(grp_df.rename(columns={'Monto_Limpio': 'Monto ($)'}), cols_monto=['Monto ($)']),
                hide_index=True, use_container_width=True, height=440,
            )
    elif df_me2m is None:
        st.warning("Carga el archivo ME2M para ver el desglose por Grupo de Compra.")
    else:
        st.info("No hay compras directas para los filtros seleccionados.")

# ---------------- Tab 4: PNNA ----------------
with tab4:
    st.markdown(f'<div class="custom-header">{SVG_ICONS["alert"]} Ranking de PNNA (Posiciones No Asignadas) por Área / Autor</div>', unsafe_allow_html=True)
    st.caption("ℹ️ El filtro Ariba / SAP HANA no aplica aquí: las PNNA todavía no tienen pedido asignado.")
    if pnna_area is not None and not pnna_area.empty:
        fig_pnna = px.bar(
            pnna_area.head(15),
            x=col_autor_me5a,
            y='Monto PNNA ($)',
            color=col_centro_me5a,
            title="Top 15 Áreas/Solicitantes con Mayor Monto en PNNA Retenido",
            text_auto='.2s'
        )
        st.plotly_chart(fig_pnna, use_container_width=True)

        st.dataframe(
            estilo_montos(pnna_area, cols_monto=['Monto PNNA ($)'], cols_enteros=['Cant. SOLPEDs']),
            use_container_width=True, hide_index=True,
        )
    elif df_me5a is None:
        st.warning("Carga el archivo ME5A con Ariba para visualizar el análisis de PNNA.")
    else:
        st.info("No hay PNNA para los filtros seleccionados.")

# ---------------- Tab 5: Cruce ME5A vs ME2M ----------------
with tab5:
    st.markdown(f'<div class="custom-header">{SVG_ICONS["link"]} Cruce Trazable: SOLPEDs (ME5A) vs Pedidos (ME2M){etiqueta_plat}</div>', unsafe_allow_html=True)

    if merged_df is not None and not merged_df.empty:
        n_cruzados = int((merged_df['Estado cruce'] == ESTADO_CRUZADO).sum())
        n_solo_me5a = int((merged_df['Estado cruce'] == ESTADO_SOLO_ME5A).sum())

        m1, m2, m3 = st.columns(3)
        m1.metric("📋 SOLPEDs con pedido", f"{len(merged_df):,}")
        m2.metric("✅ Cruzadas con ME2M", f"{n_cruzados:,}")
        m3.metric("⚠️ Pedido no está en ME2M", f"{n_solo_me5a:,}")

        if n_solo_me5a > 0:
            st.caption("«Pedido no está en ME2M»: la SOLPED tiene N° de pedido en la ME5A, pero ese pedido no viene "
                       "en el archivo ME2M (habitual en pedidos Ariba). Se muestran igual para que puedas trazarlos.")

        f1, f2 = st.columns([1, 2])
        with f1:
            estado_sel = st.selectbox(
                "Estado del cruce",
                ["Todos", ESTADO_CRUZADO, ESTADO_SOLO_ME5A],
                key="estado_cruce",
            )
        with f2:
            texto_cruce = st.text_input("Buscar en el cruce", placeholder="Ej: N° SOLPED, pedido, autor…", key="busq_cruce")

        cols_show = [
            'Estado cruce', 'Solicitud de pedido', 'Pedido_Key', 'Pos_Key', 'Plataforma',
            col_autor_me5a, 'Proveedor/Centro suministrador',
            col_licita_me2m, 'Centro_SOLPED', 'Centro_PEDIDO', 'Monto_Limpio_SOLPED', 'Monto_Limpio_PEDIDO'
        ]
        cols_avail = list(dict.fromkeys([c for c in cols_show if c in merged_df.columns]))

        df_cruce_disp = merged_df[cols_avail].rename(columns={
            'Pedido_Key': 'Pedido',
            'Pos_Key': 'Posición',
            'Centro_SOLPED': 'Centro SOLPED',
            'Centro_PEDIDO': 'Centro Pedido',
            'Monto_Limpio_SOLPED': 'Monto SOLPED ($)',
            'Monto_Limpio_PEDIDO': 'Monto Pedido ($)',
        })

        if estado_sel != "Todos":
            df_cruce_disp = df_cruce_disp[df_cruce_disp['Estado cruce'] == estado_sel]
        df_cruce_disp = buscar_en_df(df_cruce_disp, texto_cruce)
        st.caption(f"{len(df_cruce_disp):,} registros")

        st.dataframe(
            estilo_montos(df_cruce_disp, cols_monto=['Monto SOLPED ($)', 'Monto Pedido ($)']),
            use_container_width=True,
            hide_index=True,
        )
    elif df_me5a is None or df_me2m is None:
        st.info("Para realizar el cruce unificado, debes subir **ambos archivos (ME5A y ME2M)** en la barra lateral.")
    else:
        st.info(f"No hay SOLPEDs con pedido {plataforma_sel if plataforma_sel != PLAT_TODAS else ''} "
                "para los filtros seleccionados.")
