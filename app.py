import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Compras Directas", layout="wide")

st.title("📊 Reporte de Compras Directas y Ranking por Centro")

# Carga de archivos en la barra lateral
st.sidebar.header("1. Cargar Archivos SAP")
file_me5a = st.sidebar.file_uploader("Subir ME5A con Ariba (.xlsx)", type=["xlsx"])
file_me2m = st.sidebar.file_uploader("Subir ME2M (.xlsx)", type=["xlsx"])

@st.cache_data
def load_data(file):
    if file is not None:
        df = pd.read_excel(file)
        # Limpieza de nombres de columnas
        df.columns = df.columns.astype(str).str.strip()
        return df
    return None

def clean_numeric(series):
    """Limpia cadenas de números típicas de SAP (formato europeo, signos negativos al final, etc.)"""
    if series is None:
        return pd.Series(dtype=float)
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0)
    
    s = series.astype(str).str.strip()
    # Eliminar símbolos de moneda y espacios
    s = s.str.replace(r'[$€CLPUSD\s]', '', regex=True)
    # Formato negativo al final de SAP (ej: "100,00-")
    s = s.str.replace(r'^(.+)-$', r'-\1', regex=True)
    # Reemplazar puntos de miles y comas decimales
    s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce').fillna(0)

def auto_detect_col(df, keywords):
    """Busca coincidencias flexibles de nombres de columnas"""
    for kw in keywords:
        for col in df.columns:
            if kw.lower() in str(col).lower():
                return col
    return None

df_me5a = load_data(file_me5a)
df_me2m = load_data(file_me2m)

if df_me2m is not None:
    all_cols = list(df_me2m.columns)
    
    # Detección automática de columnas clave
    auto_centro = auto_detect_col(df_me2m, ['centro', 'cent'])
    auto_monto = auto_detect_col(df_me2m, ['valor', 'monto', 'neto', 'importe', 'precio', 'total', 'val.'])
    auto_grupo = auto_detect_col(df_me2m, ['grupo', 'grp', 'ekgrp'])
    auto_area = auto_detect_col(df_me2m, ['solicitante', 'área', 'area', 'coste', 'ceco'])

    # Selector manual de columnas en el Sidebar por si falla la auto-detección
    with st.sidebar.expander("⚙️ Configuración de Columnas", expanded=False):
        col_centro = st.selectbox("Columna Centro", options=all_cols, index=all_cols.index(auto_centro) if auto_centro in all_cols else 0)
        col_monto = st.selectbox("Columna Monto / Valor", options=["[Ninguna]"] + all_cols, index=all_cols.index(auto_monto)+1 if auto_monto in all_cols else 0)
        col_grupo = st.selectbox("Columna Grupo de Compra", options=["[Ninguna]"] + all_cols, index=all_cols.index(auto_grupo)+1 if auto_grupo in all_cols else 0)
        col_area = st.selectbox("Columna Área / Solicitante", options=["[Ninguna]"] + all_cols, index=all_cols.index(auto_area)+1 if auto_area in all_cols else 0)

    col_monto = None if col_monto == "[Ninguna]" else col_monto
    col_grupo = None if col_grupo == "[Ninguna]" else col_grupo
    col_area = None if col_area == "[Ninguna]" else col_area

    # Filtrado y procesamiento de montos
    df_filtered = df_me2m.copy()
    if col_monto:
        df_filtered[col_monto] = clean_numeric(df_filtered[col_monto])

    # Filtros
    st.sidebar.subheader("2. Filtros")
    centros_opt = sorted([str(x) for x in df_filtered[col_centro].dropna().unique()])
    centros_sel = st.sidebar.multiselect("Filtrar por Centro", options=centros_opt)
    
    if centros_sel:
        df_filtered = df_filtered[df_filtered[col_centro].astype(str).isin(centros_sel)]

    # KPIs Principales
    monto_total = df_filtered[col_monto].sum() if col_monto else 0.0
    total_registros = len(df_filtered)
    total_centros = df_filtered[col_centro].nunique()

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Monto Total Compras Directas", f"${monto_total:,.2f}")
    kpi2.metric("Total de Pedidos/Registros", f"{total_registros:,}")
    kpi3.metric("Centros Activos", f"{total_centros}")

    st.markdown("---")

    # 1. Ranking Compras Directas x Centro
    st.subheader("🏆 Ranking Compras Directas x Centro")
    
    if col_monto:
        ranking_centro = (
            df_filtered.groupby(col_centro)[col_monto]
            .agg(['sum', 'count'])
            .reset_index()
            .rename(columns={'sum': 'Monto Total ($)', 'count': 'Cant. Pedidos'})
            .sort_values(by='Monto Total ($)', ascending=False)
        )
        ranking_centro['Posición'] = range(1, len(ranking_centro) + 1)
        ranking_centro = ranking_centro[['Posición', col_centro, 'Monto Total ($)', 'Cant. Pedidos']]

        col_chart, col_table = st.columns([3, 2])

        with col_chart:
            fig_centro = px.bar(
                ranking_centro.head(20),
                x=col_centro,
                y='Monto Total ($)',
                text_auto='.2s',
                title="Monto Acumulado por Centro (Top 20)",
                color='Monto Total ($)',
                color_continuous_scale="Viridis"
            )
            fig_centro.update_layout(xaxis_type='category')
            st.plotly_chart(fig_centro, use_container_width=True)

        with col_table:
            st.dataframe(
                ranking_centro.style.format({'Monto Total ($)': "${:,.2f}"}),
                hide_index=True,
                use_container_width=True
            )
    else:
        st.warning("⚠️ No se ha seleccionado una columna de Monto/Valor. Selecciónala desplegando '⚙️ Configuración de Columnas' en la barra lateral.")

    # 2. Compras directas por Grupo de Compra y Áreas
    st.markdown("---")
    st.subheader("📌 Análisis por Grupo de Compra y Áreas")

    tab1, tab2 = st.tabs(["Por Grupo de Compra", "Por Área / Solicitante"])

    with tab1:
        if col_grupo and col_monto:
            grp_df = (
                df_filtered.groupby(col_grupo)[col_monto]
                .sum()
                .reset_index()
                .sort_values(by=col_monto, ascending=False)
            )
            fig_grp = px.pie(grp_df, values=col_monto, names=col_grupo, title="Distribución por Grupo de Compra")
            st.plotly_chart(fig_grp, use_container_width=True)
        else:
            st.info("Selecciona una columna de Grupo de Compra y Monto en '⚙️ Configuración de Columnas' para visualizar este gráfico.")

    with tab2:
        if col_area and col_monto:
            area_df = (
                df_filtered.groupby(col_area)[col_monto]
                .agg(['sum', 'count'])
                .reset_index()
                .rename(columns={'sum': 'Monto Total ($)', 'count': 'Cant. Registros'})
                .sort_values(by='Monto Total ($)', ascending=False)
            )
            st.dataframe(
                area_df.style.format({'Monto Total ($)': "${:,.2f}"}),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Selecciona una columna de Área/Solicitante y Monto en '⚙️ Configuración de Columnas' para visualizar esta tabla.")
else:
    st.info("Por favor sube los archivos de Excel en el panel izquierdo para comenzar el análisis.")
