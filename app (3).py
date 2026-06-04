import streamlit as st
import pandas as pd
from datetime import date

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
  .topbar-brand { font-family: 'DM Mono', monospace; font-size: 13px;
    letter-spacing: 0.04em; display: flex; align-items: center; gap: 10px; }
  .topbar-dot { width: 8px; height: 8px; border-radius: 50%;
    background: #52b788; display: inline-block; }

  .stat-card { background: #fff; border: 1px solid #e2e0d8;
    border-radius: 10px; padding: 16px 20px; }
  .stat-label { font-size: 11px; color: #9b9890; text-transform: uppercase;
    letter-spacing: 0.05em; margin-bottom: 4px; }
  .stat-value { font-family: 'DM Mono', monospace; font-size: 24px;
    font-weight: 500; color: #1a1917; }
  .stat-card.highlight { border-color: #52b788; background: #d8f3e3; }
  .stat-card.highlight .stat-value { color: #2d6a4f; }

  .upload-box { background: #f9f8f5; border: 1px dashed #c8c5b8;
    border-radius: 10px; padding: 20px; margin-bottom: 8px; }
  .upload-title { font-weight: 600; font-size: 14px; margin-bottom: 4px; }
  .upload-sub { font-size: 12px; color: #6b6860; margin-bottom: 12px; }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 24px; padding-bottom: 24px; }
</style>
""", unsafe_allow_html=True)

# ─── TOPBAR ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
  <div class="topbar-brand">
    <span class="topbar-dot"></span>
    Saldos y Consumos por Absentismo · Endalia
  </div>
</div>
""", unsafe_allow_html=True)

# ─── INSTRUCCIONES ───────────────────────────────────────────────────────────
with st.expander("📋 ¿Cómo usar esta herramienta?", expanded=False):
    st.markdown("""
    **Export 1 — Informe Empleados** *(Personas y puestos → Informes → Empleados)*
    - Filtra por los convenios que tienen derecho al tipo de ausencia
    - Incluye empleados en estado **Activo**
    - Campos necesarios: Empleado, Código, Estado, Empresa, Centro de trabajo, Convenio

    **Export 2 — Informe Saldos y consumos** *(Vacaciones y ausencias → Informes → Saldos y consumos)*
    - Filtra por el tipo de ausencia (ej. "Asuntos propios")
    - Añade los campos: **Validados**, **Pendientes de validar**, **Pendientes de solicitar**
    - Campos necesarios: Código, Tipo, Máximo, Validados

    **Export 3 — Informe Absentismos** *(Vacaciones y ausencias → Informes → Absentismos)*
    - Filtra por el mismo tipo de ausencia
    - Añade el campo **Código** del empleado
    - Campos necesarios: Código, Tipo, Estado, Fecha inicio, Duración

    **Resultado:** la herramienta calcula los días a pagar por empleado en el rango de fechas indicado,
    incluyendo los que tienen consumo 0 y no aparecen en los informes estándar.
    """)

st.divider()

# ─── UPLOADS ─────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 1 · Empleados")
    st.caption("Personas y puestos → Informes → Empleados")
    f_empleados = st.file_uploader("Subir Excel", type=["xlsx"], key="emp")

with col2:
    st.markdown("#### 2 · Saldos y consumos")
    st.caption("Vacaciones y ausencias → Informes → Saldos y consumos")
    f_saldos = st.file_uploader("Subir Excel", type=["xlsx"], key="sal")

with col3:
    st.markdown("#### 3 · Absentismos")
    st.caption("Vacaciones y ausencias → Informes → Absentismos")
    f_abs = st.file_uploader("Subir Excel", type=["xlsx"], key="abs")

# ─── PROCESS ─────────────────────────────────────────────────────────────────
if f_empleados and f_saldos and f_abs:

    try:
        df_emp = pd.read_excel(f_empleados)
        df_sal = pd.read_excel(f_saldos)
        df_abs = pd.read_excel(f_abs)
    except Exception as e:
        st.error(f"Error leyendo los ficheros: {e}")
        st.stop()

    # Validate columns
    missing_emp = {'Empleado','Código','Estado','Convenio'} - set(df_emp.columns)
    missing_sal = {'Código','Tipo','Máximo','Validados'} - set(df_sal.columns)
    missing_abs = {'Código','Tipo','Estado','Fecha inicio','Duración'} - set(df_abs.columns)

    if missing_emp:
        st.error(f"Al informe de Empleados le faltan columnas: {missing_emp}")
        st.stop()
    if missing_sal:
        st.error(f"Al informe de Saldos y consumos le faltan columnas: {missing_sal}. Asegúrate de añadir Validados, Pendientes de validar y Pendientes de solicitar.")
        st.stop()
    if missing_abs:
        st.error(f"Al informe de Absentismos le faltan columnas: {missing_abs}. Asegúrate de añadir el campo Código.")
        st.stop()

    st.divider()

    # ─── FILTERS ─────────────────────────────────────────────────────────────
    st.markdown("#### ⚙️ Configuración")

    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 1.5, 1.5, 1])

    with fc1:
        tipos = sorted(df_sal['Tipo'].dropna().unique().tolist())
        tipo_default = next((t for t in tipos if 'asuntos' in t.lower()), tipos[0] if tipos else None)
        tipo_idx = tipos.index(tipo_default) if tipo_default and tipo_default in tipos else 0
        tipo_sel = st.selectbox("Tipo de ausencia", options=tipos, index=tipo_idx)

    with fc2:
        convenios = sorted(df_emp['Convenio'].dropna().unique().tolist())
        convenios_sel = st.multiselect("Convenios", options=convenios, default=convenios)

    with fc3:
        # Default: current quarter start
        today = date.today()
        q = (today.month - 1) // 3
        q_starts = [date(today.year,1,1), date(today.year,4,1),
                    date(today.year,7,1), date(today.year,10,1)]
        q_ends   = [date(today.year,3,31), date(today.year,6,30),
                    date(today.year,9,30), date(today.year,12,31)]
        date_from = st.date_input("Fecha inicio", value=q_starts[q], format="DD/MM/YYYY")

    with fc4:
        date_to = st.date_input("Fecha fin", value=q_ends[q], format="DD/MM/YYYY")

    with fc5:
        st.markdown("<br>", unsafe_allow_html=True)
        run = st.button("Calcular", type="primary", use_container_width=True)

    if run:
        if not convenios_sel:
            st.warning("Selecciona al menos un convenio.")
            st.stop()
        if date_from > date_to:
            st.error("La fecha de inicio debe ser anterior al fin.")
            st.stop()

        # ─── FILTER EMPLOYEES ────────────────────────────────────────────────
        df_emp_f = df_emp[
            (df_emp['Estado'] == 'Activo') &
            (df_emp['Convenio'].isin(convenios_sel))
        ][['Empleado','Código','Empresa','Centro de trabajo','Convenio']].copy()

        if df_emp_f.empty:
            st.warning("No hay empleados activos con los convenios seleccionados.")
            st.stop()

        # ─── FILTER SALDOS → máximo por empleado ─────────────────────────────
        df_sal_f = df_sal[df_sal['Tipo'] == tipo_sel][
            ['Código','Máximo']
        ].drop_duplicates(subset='Código').copy()

        # ─── FILTER ABSENTISMOS → consumo en el rango de fechas ──────────────
        df_abs['Fecha inicio'] = pd.to_datetime(df_abs['Fecha inicio'], errors='coerce')
        df_abs_f = df_abs[
            (df_abs['Tipo'] == tipo_sel) &
            (df_abs['Estado'] == 'Validado') &
            (df_abs['Fecha inicio'] >= pd.Timestamp(date_from)) &
            (df_abs['Fecha inicio'] <= pd.Timestamp(date_to))
        ][['Código','Duración']].copy()

        # Aggregate consumption per employee in the date range
        consumo = df_abs_f.groupby('Código')['Duración'].sum().reset_index()
        consumo.columns = ['Código','Consumido (d)']

        # ─── MERGE ───────────────────────────────────────────────────────────
        df = df_emp_f.merge(df_sal_f, on='Código', how='left')
        df = df.merge(consumo, on='Código', how='left')

        df['Máximo']       = df['Máximo'].fillna(0)
        df['Consumido (d)'] = df['Consumido (d)'].fillna(0)
        df['Días a pagar'] = (df['Máximo'] - df['Consumido (d)']).clip(lower=0)

        # ─── STATS ───────────────────────────────────────────────────────────
        total        = len(df)
        sin_consumo  = len(df[df['Consumido (d)'] == 0])
        con_parcial  = len(df[(df['Consumido (d)'] > 0) & (df['Días a pagar'] > 0)])
        sin_maximo   = len(df[df['Máximo'] == 0])
        total_dias   = df['Días a pagar'].sum()

        st.markdown("<br>", unsafe_allow_html=True)
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.markdown(f'<div class="stat-card"><div class="stat-label">Total empleados</div><div class="stat-value">{total}</div></div>', unsafe_allow_html=True)
        s2.markdown(f'<div class="stat-card"><div class="stat-label">Sin consumo</div><div class="stat-value">{sin_consumo}</div></div>', unsafe_allow_html=True)
        s3.markdown(f'<div class="stat-card"><div class="stat-label">Consumo parcial</div><div class="stat-value">{con_parcial}</div></div>', unsafe_allow_html=True)
        s4.markdown(f'<div class="stat-card"><div class="stat-label">Sin máximo definido</div><div class="stat-value">{sin_maximo}</div></div>', unsafe_allow_html=True)
        s5.markdown(f'<div class="stat-card highlight"><div class="stat-label">Total días a pagar</div><div class="stat-value">{total_dias:.2f} d</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if sin_maximo > 0:
            st.warning(f"⚠️ {sin_maximo} empleados no tienen máximo definido en Saldos y consumos. Revisa que el tipo de ausencia y periodo son correctos.")

        # ─── TABLE + EXPORT ──────────────────────────────────────────────────
        tc1, tc2 = st.columns([4, 1])
        with tc1:
            search = st.text_input("Buscar...", placeholder="Nombre, código o centro de trabajo", label_visibility="collapsed")
        with tc2:
            export_df = df[['Código','Empleado','Empresa','Centro de trabajo','Convenio',
                            'Máximo','Consumido (d)','Días a pagar']].copy()
            csv = export_df.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")
            st.download_button(
                label="↓ Exportar CSV",
                data=csv,
                file_name=f"DiasPagar_{tipo_sel.replace(' ','_')}_{date_from}_{date_to}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Display df
        display_df = df[['Código','Empleado','Centro de trabajo','Convenio',
                         'Máximo','Consumido (d)','Días a pagar']].copy()
        display_df = display_df.sort_values('Días a pagar', ascending=False).reset_index(drop=True)

        if search:
            mask = (
                display_df['Empleado'].str.contains(search, case=False, na=False) |
                display_df['Código'].str.contains(search, case=False, na=False) |
                display_df['Centro de trabajo'].str.contains(search, case=False, na=False)
            )
            display_df = display_df[mask]

        max_dias = display_df['Máximo'].max() if len(display_df) > 0 else 1

        def color_dias(val):
            if val <= 0:
                return "background-color:#d8f3e3;color:#2d6a4f;font-weight:500;"
            elif val < max_dias:
                return "background-color:#fff0e0;color:#e07a1f;font-weight:500;"
            else:
                return "background-color:#fdecea;color:#c0392b;font-weight:500;"

        st.dataframe(
            display_df.style
                .applymap(color_dias, subset=["Días a pagar"])
                .format({"Máximo":"{:.2f}","Consumido (d)":"{:.2f}","Días a pagar":"{:.2f}"}),
            use_container_width=True,
            height=min(600, 60 + len(display_df) * 38),
            column_config={
                "Código":            st.column_config.TextColumn("Código", width="small"),
                "Empleado":          st.column_config.TextColumn("Empleado", width="large"),
                "Centro de trabajo": st.column_config.TextColumn("Centro", width="medium"),
                "Convenio":          st.column_config.TextColumn("Convenio", width="medium"),
                "Máximo":            st.column_config.NumberColumn("Máximo (d)", format="%.2f", width="small"),
                "Consumido (d)":     st.column_config.NumberColumn("Consumido (d)", format="%.2f", width="small"),
                "Días a pagar":      st.column_config.NumberColumn("A pagar (d)", format="%.2f", width="small"),
            },
            hide_index=True,
        )
        st.caption(f"{len(display_df)} empleados · Validados · {date_from.strftime('%d/%m/%Y')} – {date_to.strftime('%d/%m/%Y')} · {tipo_sel}")

else:
    # Show which files are still missing
    missing = []
    if not f_empleados: missing.append("Empleados")
    if not f_saldos:    missing.append("Saldos y consumos")
    if not f_abs:       missing.append("Absentismos")

    if missing:
        st.markdown(f"""
        <div style="text-align:center;padding:48px 24px;color:#9b9890;">
            <div style="font-size:36px;margin-bottom:12px;">📂</div>
            <div style="font-size:14px;">Faltan por subir: <strong style="color:#6b6860;">{', '.join(missing)}</strong></div>
        </div>
        """, unsafe_allow_html=True)
