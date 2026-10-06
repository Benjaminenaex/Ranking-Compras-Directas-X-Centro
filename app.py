import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Compras Directas", layout="wide")

st.title("📊 Reporte de Compras Directas y Ranking por Centro")

# Carga de archivos en la barra lateral
st.sidebar.header("Cargar Archivos SAP")
file_me5a = st.sidebar.file_uploader("Subir ME5A con Ariba (.xlsx)", type=["xlsx"])
file_me2m = st.sidebar.file_uploader("Subir ME2M (.xlsx)", type=["xlsx"])

@st.cache_data
def load_data(file):
    if file is not None:
        df = pd.read_excel(file)
        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip()
        return df
    return None

df_me5a = load_data(file_me5a)
df_me2m = load_data(file_me2m)

if df_me2m is not None:
    # Identificación automática de columnas clave (ajustar según el encabezado exacto de SAP)
    col_centro = next((c for c in df_me2m.columns if 'Centro' in c), 'Centro')
    col_monto = next((c for c in df_me2m.columns if 'Valor' in c or 'Monto' in c or 'Neto' in c), None)
    col_grupo = next((c for c in df_me2m.columns if 'Grupo' in c), 'Grupo de compras')
    col_area = next((c for c in df_me2m.columns if 'Solicitante' in c or 'Centro de coste' in c), 'Solicitante')

    if col_monto:
        df_me2m[col_monto] = pd.to_numeric(df_me2m[col_monto], errors='coerce').fillna(0)

    # Filtros de usuario
    st.sidebar.subheader("Filtros")
    centros_sel = st.sidebar.multiselect("Filtrar por Centro", options=df_me2m[col_centro].dropna().unique())
    
    df_filtered = df_me2m.copy()
    if centros_sel:
        df_filtered = df_filtered[df_filtered[col_centro].isin(centros_sel)]

    # KPIs Principales
    monto_total = df_filtered[col_monto].sum() if col_monto else 0
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
                ranking_centro,
                x=col_centro,
                y='Monto Total ($)',
                text_auto='.2s',
                title="Monto Acumulado por Centro",
                color='Monto Total ($)',
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_centro, use_container_width=True)

        with col_table:
            st.dataframe(
                ranking_centro.style.format({'Monto Total ($)': "${:,.2f}"}),
                hide_index=True,
                use_container_width=True
            )

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

    with tab2:
        if col_area in df_filtered.columns and col_monto:
            area_df = (
                df_filtered.groupby(col_area)[col_monto]
                .sum()
                .reset_index()
                .sort_values(by=col_monto, ascending=False)
            )
            st.dataframe(
                area_df.style.format({col_monto: "${:,.2f}"}),
                use_container_width=True
            )
else:
    st.info("Por favor sube los archivos de Excel en el panel izquierdo para comenzar el análisis.")
