import io
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Compras Directas & Cruce SAP", layout="wide")

# Estilos CSS para adaptar tarjetas de métricas e iconos SVG sin desbordamiento de texto
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.2 !important;
    }
    .custom-title {
        display: flex;
        align-items: center;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 1.2rem;
        color: #FFFFFF;
    }
    .custom-header {
        display: flex;
        align-items: center;
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.75rem;
        color: #FFFFFF;
    }
    .svg-icon {
        display: inline-block;
        vertical-align: middle;
        margin-right: 12px;
        flex-shrink: 0;
    }
    </style>
""", unsafe_allow_html=True)

# Dibujos vectoriales minimalistas SVG (sin emojis)
SVG_ICONS = {
    "report": '<svg class="svg-icon" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/><path d="M3 11l6-5 4 4 7-7"/><path d="M16 3h4v4"/></svg>',
    "trophy": '<svg class="svg-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/></svg>',
    "pie": '<svg class="svg-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>',
    "link": '<svg class="svg-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "alert": '<svg class="svg-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    "download": '<svg class="svg-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'
}

st.markdown(f'<div class="custom-title">{SVG_ICONS["report"]} Reporte de Compras Directas, PNNA & Cruce SAP</div>', unsafe_allow_html=True)

# Carga de archivos
st.sidebar.header("1. Cargar Archivos SAP")
file_me5a = st.sidebar.file_uploader("Subir ME5A con Ariba (.xlsx)", type=["xlsx"])
file_me2m = st.sidebar.file_uploader("Subir ME2M (.xlsx)", type=["xlsx"])

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

# Función para generar el archivo Excel formateado con gráficos integrados
def export_to_excel_styled(df_ranking, df_grupo, df_pnna, df_cruce, df_me2m_full, df_me5a_full):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formatos de celdas
        fmt_header = workbook.add_format({
            'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#1E293B',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        fmt_currency = workbook.add_format({'num_format': '$ #,##0', 'border': 1})
        fmt_integer = workbook.add_format({'num_format': '#,##0', 'border': 1, 'align': 'center'})
        fmt_text = workbook.add_format({'border': 1})

        # 1. Hoja Ranking Compras Directas
        if df_ranking is not None and not df_ranking.empty:
            df_ranking.to_excel(writer, sheet_name='Ranking Centros', index=False)
            ws = writer.sheets['Ranking Centros']
            
            # Ancho de columnas y formato
            ws.set_column('A:A', 12, fmt_integer)
            ws.set_column('B:B', 16, fmt_text)
            ws.set_column('C:C', 22, fmt_currency)
            ws.set_column('D:D', 16, fmt_integer)
            
            for col_num, col_name in enumerate(df_ranking.columns):
                ws.write(0, col_num, col_name, fmt_header)

            # Insertar Gráfico de Barras Carmesí en Excel
            chart1 = workbook.add_chart({'type': 'column'})
            chart1.add_series({
                'name': 'Monto Total ($)',
                'categories': f'=Ranking Centros!$B$2:$B${min(21, len(df_ranking)+1)}',
                'values': f'=Ranking Centros!$C$2:$C${min(21, len(df_ranking)+1)}',
                'fill': {'color': '#E11D48'}
            })
            chart1.set_title({'name': 'Top Compras Directas por Centro'})
            chart1.set_x_axis({'name': 'Centro'})
            chart1.set_y_axis({'name': 'Monto ($)'})
            chart1.set_style(10)
            ws.insert_chart('F2', chart1)

        # 2. Hoja Grupos de Compra
        if df_grupo is not None and not df_grupo.empty:
            df_grupo.to_excel(writer, sheet_name='Grupos de Compra', index=False)
            ws = writer.sheets['Grupos de Compra']
            ws.set_column('A:A', 22, fmt_text)
            ws.set_column('B:B', 22, fmt_currency)
            
            for col_num, col_name in enumerate(df_grupo.columns):
                ws.write(0, col_num, col_name, fmt_header)

            chart2 = workbook.add_chart({'type': 'column'})
            chart2.add_series({
                'name': 'Monto Total ($)',
                'categories': f'=Grupos de Compra!$A$2:$A${min(12, len(df_grupo)+1)}',
                'values': f'=Grupos de Compra!$B$2:$B${min(12, len(df_grupo)+1)}',
                'fill': {'color': '#2563EB'}
            })
            chart2.set_title({'name': 'Monto por Grupo de Compra'})
            ws.insert_chart('D2', chart2)

        # 3. Hoja PNNA por Área
        if df_pnna is not None and not df_pnna.empty:
            df_pnna.to_excel(writer, sheet_name='PNNA por Área', index=False)
            ws = writer.sheets['PNNA por Área']
            ws.set_column('A:A', 22, fmt_text)
            ws.set_column('B:B', 16, fmt_text)
            ws.set_column('C:C', 22, fmt_currency)
            ws.set_column('D:D', 16, fmt_integer)

            for col_num, col_name in enumerate(df_pnna.columns):
                ws.write(0, col_num, col_name, fmt_header)

            chart3 = workbook.add_chart({'type': 'column'})
            chart3.add_series({
                'name': 'Monto PNNA ($)',
                'categories': f'=PNNA por Área!$A$2:$A${min(16, len(df_pnna)+1)}',
                'values': f'=PNNA por Área!$C$2:$C${min(16, len(df_pnna)+1)}',
                'fill': {'color': '#D97706'}
            })
            chart3.set_title({'name': 'Top PNNA por Área / Autor'})
            ws.insert_chart('F2', chart3)

        # 4. Hoja Cruce SOLPED vs Pedido
        if df_cruce is not None and not df_cruce.empty:
            df_cruce.to_excel(writer, sheet_name='Cruce ME5A vs ME2M', index=False)
            ws = writer.sheets['Cruce ME5A vs ME2M']
            ws.set_column('A:Z', 18, fmt_text)
            for col_num, col_name in enumerate(df_cruce.columns):
                ws.write(0, col_num, col_name, fmt_header)

        # 5. Detalle ME2M Completo
        if df_me2m_full is not None and not df_me2m_full.empty:
            df_me2m_full.head(5000).to_excel(writer, sheet_name='Detalle ME2M', index=False)

    return output.getvalue()

df_me5a = load_excel(file_me5a)
df_me2m = load_excel(file_me2m)

if df_me2m is not None or df_me5a is not None:
    
    # Procesamiento ME2M
    if df_me2m is not None:
        col_monto_me2m = next((c for c in df_me2m.columns if 'valor' in c.lower() or 'monto' in c.lower()), 'Por entregar (valor)')
        col_licita_me2m = next((c for c in df_me2m.columns if 'licita' in c.lower()), 'Licitación')
        col_centro_me2m = next((c for c in df_me2m.columns if 'centro' in c.lower() and 'suministrador' not in c.lower()), 'Centro')
        col_grp_me2m = next((c for c in df_me2m.columns if 'grupo' in c.lower()), 'Grupo de compras')
        col_doc_me2m = next((c for c in df_me2m.columns if 'documento' in c.lower() or 'pedido' in c.lower()), 'Documento compras')
        col_pos_me2m = next((c for c in df_me2m.columns if 'posición' in c.lower() or 'posicion' in c.lower()), 'Posición')

        df_me2m['Monto_Limpio'] = clean_numeric(df_me2m[col_monto_me2m]) if col_monto_me2m in df_me2m.columns else 0.0
        df_me2m['Es_Compra_Directa'] = df_me2m[col_licita_me2m].astype(str).str.upper().str.startswith('AD') if col_licita_me2m in df_me2m.columns else False
    
    # Procesamiento ME5A
    if df_me5a is not None:
        col_monto_me5a = next((c for c in df_me5a.columns if 'valor' in c.lower() or 'monto' in c.lower()), 'Valor total')
        col_ped_me5a = next((c for c in df_me5a.columns if 'pedido' in c.lower() and 'posición' not in c.lower() and 'solicitud' not in c.lower()), 'Pedido')
        col_posped_me5a = next((c for c in df_me5a.columns if 'posició' in c.lower() or 'posicion' in c.lower()), 'Posición de pedido')
        col_autor_me5a = next((c for c in df_me5a.columns if 'autor' in c.lower() or 'solicitante' in c.lower()), 'Autor')
        col_centro_me5a = next((c for c in df_me5a.columns if 'centro' in c.lower()), 'Centro')

        df_me5a['Monto_Limpio'] = clean_numeric(df_me5a[col_monto_me5a]) if col_monto_me5a in df_me5a.columns else 0.0
        df_me5a['Es_PNNA'] = df_me5a[col_ped_me5a].isna() | (df_me5a[col_ped_me5a] == 0) | (df_me5a[col_ped_me5a].astype(str).str.strip() == '')

    # Filtro por Centro en Barra Lateral
    st.sidebar.subheader("2. Filtros Globales")
    centros_me2m = df_me2m[col_centro_me2m].dropna().astype(str).unique() if df_me2m is not None else []
    centros_me5a = df_me5a[col_centro_me5a].dropna().astype(str).unique() if df_me5a is not None else []
    todos_centros = sorted(list(set(centros_me2m).union(set(centros_me5a))))

    centros_sel = st.sidebar.multiselect("Filtrar por Centro", options=todos_centros)

    # Filtrar DataFrames
    df_me2m_filt = df_me2m.copy() if df_me2m is not None else None
    df_me5a_filt = df_me5a.copy() if df_me5a is not None else None

    if centros_sel:
        if df_me2m_filt is not None:
            df_me2m_filt = df_me2m_filt[df_me2m_filt[col_centro_me2m].astype(str).isin(centros_sel)]
        if df_me5a_filt is not None:
            df_me5a_filt = df_me5a_filt[df_me5a_filt[col_centro_me5a].astype(str).isin(centros_sel)]

    # Pre-calculo de tablas para exportación
    ranking_centro = None
    grp_df = None
    pnna_area = None
    merged_df = None

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

        df_me2m_proc = df_me2m_filt.copy()
        df_me2m_proc['Pedido_Key'] = pd.to_numeric(df_me2m_proc[col_doc_me2m], errors='coerce').fillna(0).astype(int)
        df_me2m_proc['Pos_Key'] = pd.to_numeric(df_me2m_proc[col_pos_me2m], errors='coerce').fillna(0).astype(int)

        merged_df = pd.merge(
            df_me5a_proc, df_me2m_proc,
            on=['Pedido_Key', 'Pos_Key'],
            how='inner', suffixes=('_SOLPED', '_PEDIDO')
        )

    # Botón de Descarga Consolidada en la Barra Lateral
    st.sidebar.markdown("---")
    st.sidebar.subheader("3. Exportar Reporte")
    
    excel_data = export_to_excel_styled(ranking_centro, grp_df, pnna_area, merged_df, df_me2m_filt, df_me5a_filt)
    st.sidebar.download_button(
        label="Descargar Reporte Completo (Excel)",
        data=excel_data,
        file_name="Reporte_Compras_Directas_Consolidado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    # Tarjetas de Métricas Generales (KPIs)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    monto_cd = df_me2m_filt[df_me2m_filt['Es_Compra_Directa']]['Monto_Limpio'].sum() if df_me2m_filt is not None else 0.0
    cant_cd = df_me2m_filt[df_me2m_filt['Es_Compra_Directa']].shape[0] if df_me2m_filt is not None else 0
    monto_pnna = df_me5a_filt[df_me5a_filt['Es_PNNA']]['Monto_Limpio'].sum() if df_me5a_filt is not None else 0.0
    cant_pnna = df_me5a_filt[df_me5a_filt['Es_PNNA']].shape[0] if df_me5a_filt is not None else 0

    kpi1.metric("Monto Compras Directas (AD)", f"${monto_cd:,.0f}")
    kpi2.metric("Cant. Órdenes Directas", f"{cant_cd:,}")
    kpi3.metric("Monto PNNA Pendiente", f"${monto_pnna:,.0f}")
    kpi4.metric("SOLPEDs en PNNA", f"{cant_pnna:,}")

    st.markdown("---")

    # Pestañas de Navegación
    tab1, tab2, tab3, tab4 = st.tabs([
        "Ranking Compras Directas", 
        "Grupo de Compra", 
        "PNNA x Monto y Área", 
        "Cruce SOLPEDs vs Pedidos"
    ])

    # Tab 1: Ranking Compras Directas x Centro (ME2M)
    with tab1:
        st.markdown(f'<div class="custom-header">{SVG_ICONS["trophy"]} Ranking Compras Directas por Centro (Propiedad del Pago)</div>', unsafe_allow_html=True)
        if ranking_centro is not None and not ranking_centro.empty:
            c1, c2 = st.columns([3, 2])
            with c1:
                fig_centro = px.bar(
                    ranking_centro.head(20),
                    x=col_centro_me2m,
                    y='Monto Total ($)',
                    text_auto='.2s',
                    title="Monto Acumulado por Centro (Top 20)",
                    color='Monto Total ($)',
                    color_continuous_scale="Viridis"
                )
                fig_centro.update_layout(coloraxis_showscale=False, xaxis_type='category', margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_centro, use_container_width=True)

            with c2:
                st.dataframe(
                    ranking_centro.style.format({'Monto Total ($)': "${:,.0f}"}),
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.warning("Para ver el Ranking de Compras Directas debes cargar el archivo ME2M.")

    # Tab 2: Compras Directas por Grupo de Compra
    with tab2:
        st.markdown(f'<div class="custom-header">{SVG_ICONS["pie"]} Distribución por Grupo de Compra</div>', unsafe_allow_html=True)
        if grp_df is not None and not grp_df.empty:
            if len(grp_df) > 8:
                top_grp = grp_df.iloc[:8].copy()
                otros_monto = grp_df.iloc[8:]['Monto_Limpio'].sum()
                otros_df = pd.DataFrame([{col_grp_me2m: 'Otros', 'Monto_Limpio': otros_monto}])
                grp_df_plot = pd.concat([top_grp, otros_df], ignore_index=True)
            else:
                grp_df_plot = grp_df

            fig_grp = px.pie(grp_df_plot, values='Monto_Limpio', names=col_grp_me2m, title="Top 8 Grupos de Compra + Otros", hole=0.4)
            fig_grp.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_grp, use_container_width=True)
        else:
            st.warning("Carga el archivo ME2M para ver el desglose por Grupo de Compra.")

    # Tab 3: PNNA por Monto y Área / Autor (ME5A)
    with tab3:
        st.markdown(f'<div class="custom-header">{SVG_ICONS["alert"]} Ranking de PNNA (Posiciones No Asignadas) por Área / Autor</div>', unsafe_allow_html=True)
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

            st.dataframe(pnna_area.style.format({'Monto PNNA ($)': "${:,.0f}"}), use_container_width=True, hide_index=True)
        else:
            st.warning("Carga el archivo ME5A con Ariba para visualizar el análisis de PNNA.")

    # Tab 4: Cruce SOLPEDs ME5A vs Pedidos ME2M (Merge Completo)
    with tab4:
        st.markdown(f'<div class="custom-header">{SVG_ICONS["link"]} Cruce Trazable: SOLPEDs (ME5A) vs Pedidos (ME2M)</div>', unsafe_allow_html=True)
        
        if merged_df is not None and not merged_df.empty:
            st.success(f"Se han cruzado exitosamente **{len(merged_df):,}** registros entre ME5A y ME2M.")

            cols_show = [
                'Solicitud de pedido', 'Pedido_Key', 'Pos_Key', 
                col_autor_me5a, 'Proveedor/Centro suministrador', 
                col_licita_me2m, 'Centro_PEDIDO', 'Monto_Limpio_SOLPED', 'Monto_Limpio_PEDIDO'
            ]
            cols_avail = [c for c in cols_show if c in merged_df.columns]

            st.dataframe(
                merged_df[cols_avail].style.format({
                    'Monto_Limpio_SOLPED': "${:,.0f}", 
                    'Monto_Limpio_PEDIDO': "${:,.0f}"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Para realizar el cruce unificado, debes subir **ambos archivos (ME5A y ME2M)** en la barra lateral.")

else:
    st.info("Por favor, sube los archivos de Excel en el panel izquierdo para comenzar el análisis.")
