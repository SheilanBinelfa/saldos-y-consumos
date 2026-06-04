import streamlit as st
import pandas as pd
import io

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Saldos y Consumos por Absentismo · Endalia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── STYLES ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

  .topbar {
    background: #1a1917; color: #fff; padding: 12px 24px;
    border-radius: 10px; display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 28px;
  }
  .topbar-brand { font-family: 'DM Mono', monospace; font-size: 13px; letter-spacing: 0.04em; display: flex; align-items: center; gap: 10px; }
  .topbar-dot { width: 8px; height: 8px; border-radius: 50%; background: #52b788; display: inline-block; }

  .stat-card { background: #fff; border: 1px solid #e2e0d8; border-radius: 10px; padding: 16px 20px; }
  .stat-label { font-size: 11px; color: #9b9890; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
  .stat-value { font-family: 'DM Mono', monospace; font-size: 24px; font-weight: 500; color: #1a1917; }
  .stat-card.highlight { border-color: #52b788; background: #d8f3e3; }
  .stat-card.highlight .stat-value { color: #2d6a4f; }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 24px; padding-bottom: 24px; }
</style>
""", unsafe_allow_html=True)

# ─── TOPBAR ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
  <div class="topbar-brand"><span class="topbar-dot"></span> Saldos y Consumos por Absentismo · Endalia</div>
</div>
""", unsafe_allow_html=True)

# ─── INSTRUCCIONES ───────────────────────────────────────────────────────────
with st.expander("📋 ¿Cómo usar esta herramienta?", expanded=False):
    st.markdown("""
    **Paso 1 — Informe de Empleados** (Módulo: Personas y puestos)
    - Filtra por los **convenios** que tienen derecho al tipo de ausencia a calcular
    - Incluye solo empleados en estado **Activo**
    - Descarga el Excel y súbelo aquí

    **Paso 2 — Informe de Saldos y consumos** (Módulo: Vacaciones y ausencias)
    - Filtra por el **tipo de ausencia** que quieres calcular (ej. "Asuntos propios")
    - Asegúrate de añadir los campos: **Validados**, **Pendientes de validar**, **Pendientes de solicitar**
    - Filtra por el **periodo** correspondiente
    - Descarga el Excel y súbelo aquí

    **Resultado:** la herramienta cruza ambos ficheros y calcula los días a pagar a cada empleado,
    incluyendo los que tienen consumo 0 y no aparecen en el informe de Saldos y consumos.
    """)

st.divider()

# ─── UPLOADS ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 1 · Informe Empleados")
    st.caption("Exportado desde Personas y puestos → Informes → Empleados")
    f_empleados = st.file_uploader("Subir Excel de Empleados", type=["xlsx"], key="emp")

with col2:
    st.markdown("#### 2 · Informe Saldos y consumos")
    st.caption("Exportado desde Vacaciones y ausencias → Informes → Saldos y consumos")
    f_saldos = st.file_uploader("Subir Excel de Saldos y consumos", type=["xlsx"], key="sal")

# ─── PROCESS ─────────────────────────────────────────────────────────────────
if f_empleados and f_saldos:

    try:
        df_emp = pd.read_excel(f_empleados)
        df_sal = pd.read_excel(f_saldos)
    except Exception as e:
        st.error(f"Error leyendo los ficheros: {e}")
        st.stop()

    # Validate columns
    emp_required = {'Empleado', 'Código', 'Estado', 'Empresa', 'Centro de trabajo', 'Convenio'}
    sal_required = {'Código', 'Tipo', 'Máximo', 'Validados'}

    missing_emp = emp_required - set(df_emp.columns)
    missing_sal = sal_required - set(df_sal.columns)

    if missing_emp:
        st.error(f"Al informe de Empleados le faltan columnas: {missing_emp}")
        st.stop()
    if missing_sal:
        st.error(f"Al informe de Saldos y consumos le faltan columnas: {missing_sal}. Asegúrate de añadir los campos Validados, Pendientes de validar y Pendientes de solicitar antes de exportar.")
        st.stop()

    st.divider()

    # ─── FILTERS ─────────────────────────────────────────────────────────────
    st.markdown("#### ⚙️ Configuración del cruce")

    fc1, fc2, fc3 = st.columns(3)

    with fc1:
        # Tipo de ausencia
        tipos = sorted(df_sal['Tipo'].dropna().unique().tolist())
        tipo_default = next((t for t in tipos if 'asuntos' in t.lower()), tipos[0] if tipos else None)
        tipo_idx = tipos.index(tipo_default) if tipo_default in tipos else 0
        tipo_sel = st.selectbox("Tipo de ausencia", options=tipos, index=tipo_idx)

    with fc2:
        # Convenios
        convenios = sorted(df_emp['Convenio'].dropna().unique().tolist())
        convenios_sel = st.multiselect("Convenios a incluir", options=convenios, default=convenios,
                                        help="Selecciona los convenios que tienen derecho a este tipo de ausencia")

    with fc3:
        # Estado empleados
        estados = sorted(df_emp['Estado'].dropna().unique().tolist())
        estado_default = ['Activo'] if 'Activo' in estados else estados
        estados_sel = st.multiselect("Estado empleados", options=estados, default=estado_default)

    run = st.button("Calcular días a pagar", type="primary", use_container_width=False)

    if run:
        if not convenios_sel:
            st.warning("Selecciona al menos un convenio.")
            st.stop()
        if not estados_sel:
            st.warning("Selecciona al menos un estado de empleado.")
            st.stop()

        # ─── FILTER EMPLOYEES ────────────────────────────────────────────────
        df_emp_f = df_emp[
            (df_emp['Estado'].isin(estados_sel)) &
            (df_emp['Convenio'].isin(convenios_sel))
        ][['Empleado', 'Código', 'Empresa', 'Centro de trabajo', 'Convenio']].copy()

        # ─── FILTER SALDOS ───────────────────────────────────────────────────
        df_sal_f = df_sal[df_sal['Tipo'] == tipo_sel][
            ['Código', 'Tipo', 'Máximo', 'Validados', 'Pendientes de validar', 'Pendientes de solicitar']
        ].copy()

        if df_emp_f.empty:
            st.warning("No hay empleados con los filtros seleccionados.")
            st.stop()

        # ─── MERGE ───────────────────────────────────────────────────────────
        df = df_emp_f.merge(df_sal_f, on='Código', how='left')

        df['Máximo']      = df['Máximo'].fillna(0)
        df['Validados']   = df['Validados'].fillna(0)
        df['Pendientes de validar']   = df['Pendientes de validar'].fillna(0)
        df['Pendientes de solicitar'] = df['Pendientes de solicitar'].fillna(0)
        df['Tipo']        = df['Tipo'].fillna(tipo_sel)

        df['Consumido (d)']   = df['Validados']
        df['Días a pagar']    = (df['Máximo'] - df['Consumido (d)']).clip(lower=0)
        df['Sin registro']    = df['Máximo'] == 0  # empleados que no aparecían en saldos

        # ─── STATS ───────────────────────────────────────────────────────────
        total       = len(df)
        sin_consumo = len(df[df['Consumido (d)'] == 0])
        con_consumo = len(df[(df['Consumido (d)'] > 0) & (df['Días a pagar'] > 0)])
        sin_registro = len(df[df['Sin registro']])
        total_dias  = df['Días a pagar'].sum()

        st.markdown("<br>", unsafe_allow_html=True)
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.markdown(f'<div class="stat-card"><div class="stat-label">Total empleados</div><div class="stat-value">{total}</div></div>', unsafe_allow_html=True)
        s2.markdown(f'<div class="stat-card"><div class="stat-label">Sin consumo (pago total)</div><div class="stat-value">{sin_consumo}</div></div>', unsafe_allow_html=True)
        s3.markdown(f'<div class="stat-card"><div class="stat-label">Consumo parcial</div><div class="stat-value">{con_consumo}</div></div>', unsafe_allow_html=True)
        s4.markdown(f'<div class="stat-card"><div class="stat-label">Sin máximo definido</div><div class="stat-value">{sin_registro}</div></div>', unsafe_allow_html=True)
        s5.markdown(f'<div class="stat-card highlight"><div class="stat-label">Total días a pagar</div><div class="stat-value">{total_dias:.2f} d</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ─── WARNING sin máximo ───────────────────────────────────────────────
        if sin_registro > 0:
            st.warning(f"⚠️ {sin_registro} empleados del convenio seleccionado no tienen máximo definido en el informe de Saldos y consumos. Revisa que el periodo y tipo de ausencia son correctos.")

        # ─── TABLE ───────────────────────────────────────────────────────────
        tc1, tc2 = st.columns([4, 1])
        with tc1:
            search = st.text_input("Buscar empleado o centro...", placeholder="Nombre, código o centro de trabajo", label_visibility="collapsed")
        with tc2:
            export_df = df[[
                'Código', 'Empleado', 'Empresa', 'Centro de trabajo', 'Convenio',
                'Máximo', 'Consumido (d)', 'Pendientes de validar', 'Pendientes de solicitar', 'Días a pagar'
            ]].copy()
            csv = export_df.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")
            st.download_button(
                label="↓ Exportar CSV",
                data=csv,
                file_name=f"DiasPagar_{tipo_sel.replace(' ','_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Filter by search
        display_df = df[[
            'Código', 'Empleado', 'Centro de trabajo', 'Convenio',
            'Máximo', 'Consumido (d)', 'Días a pagar'
        ]].copy().sort_values('Días a pagar', ascending=False).reset_index(drop=True)

        if search:
            mask = (
                display_df['Empleado'].str.contains(search, case=False, na=False) |
                display_df['Código'].str.contains(search, case=False, na=False) |
                display_df['Centro de trabajo'].str.contains(search, case=False, na=False)
            )
            display_df = display_df[mask]

        def color_dias(val):
            if val <= 0:
                return "background-color:#d8f3e3;color:#2d6a4f;font-weight:500;"
            elif val < display_df['Máximo'].max():
                return "background-color:#fff0e0;color:#e07a1f;font-weight:500;"
            else:
                return "background-color:#fdecea;color:#c0392b;font-weight:500;"

        st.dataframe(
            display_df.style
                .applymap(color_dias, subset=["Días a pagar"])
                .format({"Máximo": "{:.2f}", "Consumido (d)": "{:.2f}", "Días a pagar": "{:.2f}"}),
            use_container_width=True,
            height=min(600, 60 + len(display_df) * 38),
            column_config={
                "Código":           st.column_config.TextColumn("Código", width="small"),
                "Empleado":         st.column_config.TextColumn("Empleado", width="large"),
                "Centro de trabajo":st.column_config.TextColumn("Centro", width="medium"),
                "Convenio":         st.column_config.TextColumn("Convenio", width="medium"),
                "Máximo":           st.column_config.NumberColumn("Máximo (d)", format="%.2f", width="small"),
                "Consumido (d)":    st.column_config.NumberColumn("Consumido (d)", format="%.2f", width="small"),
                "Días a pagar":     st.column_config.NumberColumn("A pagar (d)", format="%.2f", width="small"),
            },
            hide_index=True,
        )

        st.caption(f"{len(display_df)} empleados · Solo solicitudes validadas · Tipo: {tipo_sel}")

elif f_empleados and not f_saldos:
    st.info("Sube también el informe de Saldos y consumos para continuar.")
elif f_saldos and not f_empleados:
    st.info("Sube también el informe de Empleados para continuar.")
else:
    st.markdown("""
    <div style="text-align:center;padding:48px 24px;color:#9b9890;">
        <div style="font-size:36px;margin-bottom:12px;">📂</div>
        <div style="font-size:14px;">Sube los dos informes para calcular los días a pagar</div>
    </div>
    """, unsafe_allow_html=True)
