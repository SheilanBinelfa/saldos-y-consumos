import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="Saldos y Consumos por Absentismo · Endalia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

  .file-ok { font-size: 12px; color: #2d6a4f; margin-top: 4px; }
  .file-pending { font-size: 12px; color: #9b9890; margin-top: 4px; }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 24px; padding-bottom: 24px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="topbar">
  <div class="topbar-brand">
    <span class="topbar-dot"></span>
    Saldos y Consumos por Absentismo · Endalia
  </div>
</div>
""", unsafe_allow_html=True)

with st.expander("📋 ¿Cómo usar esta herramienta?", expanded=False):
    st.markdown("""
    **Export 1 — Informe Empleados** *(Personas y puestos → Informes → Empleados)*
    - Filtra por los convenios que tienen derecho al tipo de ausencia · Estado: **Activo**
    - Campos necesarios: Empleado, Código, Estado, Empresa, Centro de trabajo, Convenio

    **Export 2 — Informe Saldos y consumos** *(Vacaciones y ausencias → Informes → Saldos y consumos)*
    - Filtra por el tipo de ausencia (ej. "Asuntos propios") y periodo
    - Añade los campos extra: **Validados**, **Pendientes de validar**, **Pendientes de solicitar**

    **Export 3 — Informe Absentismos** *(Vacaciones y ausencias → Informes → Absentismos)*
    - Filtra por el mismo tipo de ausencia · Añade el campo **Código** del empleado
    - Campos necesarios: Código, Tipo, Estado, Fecha inicio, Duración

    **Resultado:** días no disfrutados por empleado en el rango de fechas indicado,
    incluyendo los que tienen consumo 0 y no aparecen en los informes estándar.
    """)

st.divider()

# ── UPLOADS ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 1 · Empleados")
    st.caption("Personas y puestos → Informes → Empleados")
    f_empleados = st.file_uploader("Subir Excel", type=["xlsx"], key="emp")
    if f_empleados:
        st.markdown('<div class="file-ok">✓ Fichero cargado</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="file-pending">Pendiente de subir</div>', unsafe_allow_html=True)

with col2:
    st.markdown("#### 2 · Saldos y consumos")
    st.caption("Vacaciones y ausencias → Informes → Saldos y consumos")
    f_saldos = st.file_uploader("Subir Excel", type=["xlsx"], key="sal")
    if f_saldos:
        st.markdown('<div class="file-ok">✓ Fichero cargado</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="file-pending">Pendiente de subir</div>', unsafe_allow_html=True)

with col3:
    st.markdown("#### 3 · Absentismos")
    st.caption("Vacaciones y ausencias → Informes → Absentismos")
    f_abs = st.file_uploader("Subir Excel", type=["xlsx"], key="abs")
    if f_abs:
        st.markdown('<div class="file-ok">✓ Fichero cargado</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="file-pending">Pendiente de subir</div>', unsafe_allow_html=True)

# ── VALIDATE FILES ────────────────────────────────────────────────────────────
if not (f_empleados and f_saldos and f_abs):
    missing = []
    if not f_empleados: missing.append("Empleados")
    if not f_saldos:    missing.append("Saldos y consumos")
    if not f_abs:       missing.append("Absentismos")
    st.markdown(f"""
    <div style="text-align:center;padding:48px 24px;color:#9b9890;">
        <div style="font-size:36px;margin-bottom:12px;">📂</div>
        <div style="font-size:14px;">Faltan por subir: <strong style="color:#6b6860;">{', '.join(missing)}</strong></div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── READ FILES (cached) ───────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def read_excel(file_bytes, name):
    import io
    return pd.read_excel(io.BytesIO(file_bytes))

try:
    with st.spinner("Leyendo ficheros..."):
        df_emp = read_excel(f_empleados.getvalue(), f_empleados.name)
        df_sal = read_excel(f_saldos.getvalue(), f_saldos.name)
        df_abs = read_excel(f_abs.getvalue(), f_abs.name)
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
    st.error(f"Al informe de Saldos y consumos le faltan columnas: {missing_sal}. Asegúrate de añadir Validados, Pendientes de validar y Pendientes de solicitar antes de exportar.")
    st.stop()
if missing_abs:
    st.error(f"Al informe de Absentismos le faltan columnas: {missing_abs}. Asegúrate de añadir el campo Código.")
    st.stop()

st.success("✓ Los tres ficheros se han cargado correctamente.")
st.divider()

# ── FILTERS ───────────────────────────────────────────────────────────────────
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

# ── CALCULATE (only on button click) ─────────────────────────────────────────
if run:
    if not convenios_sel:
        st.warning("Selecciona al menos un convenio.")
        st.stop()
    if date_from > date_to:
        st.error("La fecha de inicio debe ser anterior al fin.")
        st.stop()

    with st.spinner("Calculando..."):

        # Filter employees
        df_emp_f = df_emp[
            (df_emp['Estado'] == 'Activo') &
            (df_emp['Convenio'].isin(convenios_sel))
        ][['Empleado','Código','Empresa','Centro de trabajo','Convenio']].copy()

        if df_emp_f.empty:
            st.warning("No hay empleados activos con los convenios seleccionados.")
            st.stop()

        # Filter saldos → máximo por empleado
        df_sal_f = df_sal[df_sal['Tipo'] == tipo_sel][
            ['Código','Máximo']
        ].drop_duplicates(subset='Código').copy()

        # Filter absentismos → consumo en rango de fechas
        df_abs['Fecha inicio'] = pd.to_datetime(df_abs['Fecha inicio'], errors='coerce')
        df_abs_f = df_abs[
            (df_abs['Tipo'] == tipo_sel) &
            (df_abs['Estado'] == 'Validado') &
            (df_abs['Fecha inicio'] >= pd.Timestamp(date_from)) &
            (df_abs['Fecha inicio'] <= pd.Timestamp(date_to))
        ][['Código','Duración']].copy()

        consumo = df_abs_f.groupby('Código')['Duración'].sum().reset_index()
        consumo.columns = ['Código','Disfrutados']

        # Merge
        df = df_emp_f.merge(df_sal_f, on='Código', how='left')
        df = df.merge(consumo, on='Código', how='left')

        df['Máximo']          = df['Máximo'].fillna(0)
        df['Disfrutados']     = df['Disfrutados'].fillna(0)
        df['No disfrutados']  = (df['Máximo'] - df['Disfrutados']).clip(lower=0)
        df['sin_maximo']      = df['Máximo'] == 0

    # ── STATS ─────────────────────────────────────────────────────────────────
    total        = len(df)
    sin_disfrute = len(df[df['Disfrutados'] == 0])
    con_parcial  = len(df[(df['Disfrutados'] > 0) & (df['No disfrutados'] > 0)])
    sin_maximo   = len(df[df['sin_maximo']])
    total_nd     = df['No disfrutados'].sum()

    st.markdown("<br>", unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.markdown(f'<div class="stat-card"><div class="stat-label">Total empleados</div><div class="stat-value">{total}</div></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="stat-card"><div class="stat-label">Sin disfrute</div><div class="stat-value">{sin_disfrute}</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="stat-card"><div class="stat-label">Disfrute parcial</div><div class="stat-value">{con_parcial}</div></div>', unsafe_allow_html=True)
    s4.markdown(f'<div class="stat-card"><div class="stat-label">Sin máximo definido</div><div class="stat-value">{sin_maximo}</div></div>', unsafe_allow_html=True)
    s5.markdown(f'<div class="stat-card highlight"><div class="stat-label">Total no disfrutados</div><div class="stat-value">{total_nd:.2f} d</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if sin_maximo > 0:
        st.warning(f"⚠️ {sin_maximo} empleados no tienen máximo definido en Saldos y consumos. Revisa que el tipo de ausencia y periodo son correctos.")

    # ── TABLE + EXPORT ─────────────────────────────────────────────────────────
    tc1, tc2 = st.columns([4, 1])
    with tc1:
        search = st.text_input("Buscar...", placeholder="Nombre, código o centro de trabajo", label_visibility="collapsed")
    with tc2:
        export_df = df[['Código','Empleado','Empresa','Centro de trabajo','Convenio',
                        'Máximo','Disfrutados','No disfrutados']].copy()
        export_df.columns = ['Código','Empleado','Empresa','Centro de trabajo','Convenio',
                             'Máximo','Disfrutados','No disfrutados']
        import io as _io
        buf = _io.BytesIO()
        export_df.to_excel(buf, index=False, engine='openpyxl')
        buf.seek(0)
        st.download_button(
            label="↓ Exportar Excel",
            data=buf.getvalue(),
            file_name=f"NoDisfrutados_{tipo_sel.replace(' ','_')}_{date_from}_{date_to}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    # Display table
    display_df = df[['Código','Empleado','Centro de trabajo','Convenio',
                     'Máximo','Disfrutados','No disfrutados']].copy()
    display_df = display_df.sort_values('No disfrutados', ascending=False).reset_index(drop=True)

    if search:
        mask = (
            display_df['Empleado'].str.contains(search, case=False, na=False) |
            display_df['Código'].str.contains(search, case=False, na=False) |
            display_df['Centro de trabajo'].str.contains(search, case=False, na=False)
        )
        display_df = display_df[mask]

    max_val = display_df['Máximo'].max() if len(display_df) > 0 else 1

    def color_nd(val):
        if val <= 0:
            return "background-color:#d8f3e3;color:#2d6a4f;font-weight:500;"
        elif val < max_val:
            return "background-color:#fff0e0;color:#e07a1f;font-weight:500;"
        else:
            return "background-color:#fdecea;color:#c0392b;font-weight:500;"

    st.dataframe(
        display_df.style
            .map(color_nd, subset=["No disfrutados"])
            .format({"Máximo":"{:.2f}","Disfrutados":"{:.2f}","No disfrutados":"{:.2f}"}),
        use_container_width=True,
        height=min(600, 60 + len(display_df) * 38),
        column_config={
            "Código":            st.column_config.TextColumn("Código", width="small"),
            "Empleado":          st.column_config.TextColumn("Empleado", width="large"),
            "Centro de trabajo": st.column_config.TextColumn("Centro", width="medium"),
            "Convenio":          st.column_config.TextColumn("Convenio", width="medium"),
            "Máximo":            st.column_config.NumberColumn("Máximo", format="%.2f", width="small"),
            "Disfrutados":       st.column_config.NumberColumn("Disfrutados", format="%.2f", width="small"),
            "No disfrutados":    st.column_config.NumberColumn("No disfrutados", format="%.2f", width="small"),
        },
        hide_index=True,
    )
    st.caption(f"{len(display_df)} empleados · Solo validados · {date_from.strftime('%d/%m/%Y')} – {date_to.strftime('%d/%m/%Y')} · {tipo_sel}")
