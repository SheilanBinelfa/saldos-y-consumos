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
    - Añade los campos extra: **Unidad**, **Validados**, **Pendientes de validar**, **Pendientes de solicitar**

    **Export 3 — Informe Absentismos** *(Vacaciones y ausencias → Informes → Absentismos)*
    - Filtra por el mismo tipo de ausencia · Añade el campo **Código** del empleado
    - Campos necesarios: Código, Tipo, Estado, Fecha inicio, Duración, **Unidad**, **Duración total en minutos**

    **Resultado:** días/horas no disfrutados por empleado en el rango de fechas indicado,
    incluyendo los que tienen consumo 0 y no aparecen en los informes estándar.
    Los importes se calculan en minutos internamente (1 día = 480 min, 1 hora = 60 min)
    y se muestran en formato mixto (ej. "2d y 3h") para que días y horas sean siempre comparables.
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

# Normalizar Código de forma consistente entre ficheros (evita mismatches por ceros a la
# izquierda: un fichero puede traer "01661" como texto y otro "1661" como número)
def normalizar_codigo(x):
    s = str(x).strip()
    try:
        return str(int(float(s)))  # "01661" -> 1661.0 -> "1661" ; "1661" -> "1661"
    except (ValueError, TypeError):
        return s

for _df in (df_emp, df_sal, df_abs):
    if 'Código' in _df.columns:
        _df['Código'] = _df['Código'].apply(normalizar_codigo)

# Validate columns
missing_emp = {'Empleado','Código','Estado','Convenio'} - set(df_emp.columns)
missing_sal = {'Código','Tipo','Máximo','Unidad','Validados'} - set(df_sal.columns)
missing_abs = {'Código','Tipo','Estado','Fecha inicio','Duración','Unidad','Duración total en minutos'} - set(df_abs.columns)

if missing_emp:
    st.error(f"Al informe de Empleados le faltan columnas: {missing_emp}")
    st.stop()
if missing_sal:
    st.error(f"Al informe de Saldos y consumos le faltan columnas: {missing_sal}. Asegúrate de añadir Unidad, Validados, Pendientes de validar y Pendientes de solicitar antes de exportar.")
    st.stop()
if missing_abs:
    st.error(f"Al informe de Absentismos le faltan columnas: {missing_abs}. Asegúrate de añadir Código, Unidad y Duración total en minutos.")
    st.stop()

st.success("✓ Los tres ficheros se han cargado correctamente.")
st.divider()

# ── HELPERS: conversión de unidades ──────────────────────────────────────────
MINUTOS_POR_DIA = 480   # 1 jornada estándar = 8h
MINUTOS_POR_HORA = 60

def a_minutos(valor, unidad):
    """Convierte un valor (Máximo, Duración, etc.) a minutos según su Unidad."""
    if pd.isna(valor):
        return 0.0
    u = str(unidad).strip().lower()
    if u.startswith('d'):
        return valor * MINUTOS_POR_DIA
    elif u.startswith('h'):
        return valor * MINUTOS_POR_HORA
    return valor  # por si ya viniera en minutos u otra unidad no prevista

def format_duracion(minutos, jornada_min=MINUTOS_POR_DIA):
    """Formatea minutos a texto tipo '2d', '3h' o '2d y 3h'."""
    if pd.isna(minutos) or minutos <= 0:
        return "0h"
    minutos = round(minutos)
    dias, resto = divmod(minutos, jornada_min)
    horas = resto // MINUTOS_POR_HORA
    partes = []
    if dias > 0:
        partes.append(f"{int(dias)}d")
    if horas > 0:
        partes.append(f"{int(horas)}h")
    return " y ".join(partes) if partes else "0h"

def format_duracion_separado(dias_min, horas_min, jornada_min=MINUTOS_POR_DIA):
    """Suma por separado los minutos que vinieron registrados en Días y en Horas,
    SIN plegar un bucket en otro (ej. 1 día + 2 tramos de 4h se muestra como
    '1d y 8h', no como '2d'), para que se corresponda tal cual con lo que se ve
    en el informe de Absentismos."""
    if pd.isna(dias_min):
        dias_min = 0
    if pd.isna(horas_min):
        horas_min = 0
    dias = round(dias_min / jornada_min)
    horas = round(horas_min / MINUTOS_POR_HORA)
    partes = []
    if dias > 0:
        partes.append(f"{int(dias)}d")
    if horas > 0:
        partes.append(f"{int(horas)}h")
    return " y ".join(partes) if partes else "0h"

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

        # Filter saldos → máximo por empleado, convertido a minutos según su propia Unidad
        df_sal_f = df_sal[df_sal['Tipo'] == tipo_sel][
            ['Código','Máximo','Unidad']
        ].drop_duplicates(subset='Código').copy()
        df_sal_f['Maximo_min'] = df_sal_f.apply(
            lambda r: a_minutos(r['Máximo'], r['Unidad']), axis=1
        )
        df_sal_f = df_sal_f[['Código','Maximo_min']]

        # Filter absentismos → consumo en rango de fechas (ya viene en minutos totales)
        df_abs['Fecha inicio'] = pd.to_datetime(df_abs['Fecha inicio'], errors='coerce')
        df_abs_f = df_abs[
            (df_abs['Tipo'] == tipo_sel) &
            (df_abs['Estado'] == 'Validado') &
            (df_abs['Fecha inicio'] >= pd.Timestamp(date_from)) &
            (df_abs['Fecha inicio'] <= pd.Timestamp(date_to))
        ][['Código','Unidad','Duración total en minutos']].copy()

        # Sumamos por separado los registros en Días y en Horas (sin plegar unos en otros),
        # para que "Disfrutados" refleje tal cual lo que hay en el informe de Absentismos
        # (ej. 1 día + dos tramos de 4h se muestra como "1d y 8h", no como "2d")
        pivot = df_abs_f.pivot_table(
            index='Código', columns='Unidad', values='Duración total en minutos',
            aggfunc='sum', fill_value=0
        )
        for col in ['Días', 'Horas']:
            if col not in pivot.columns:
                pivot[col] = 0
        consumo = pivot[['Días', 'Horas']].reset_index()
        consumo.columns = ['Código', 'Disfrutados_dias_min', 'Disfrutados_horas_min']
        consumo['Disfrutados_min'] = consumo['Disfrutados_dias_min'] + consumo['Disfrutados_horas_min']

        # Merge
        df = df_emp_f.merge(df_sal_f, on='Código', how='left')
        df = df.merge(consumo, on='Código', how='left')

        df['Maximo_min']       = df['Maximo_min'].fillna(0)
        df['Disfrutados_min']  = df['Disfrutados_min'].fillna(0)
        df['Disfrutados_dias_min']  = df['Disfrutados_dias_min'].fillna(0)
        df['Disfrutados_horas_min'] = df['Disfrutados_horas_min'].fillna(0)
        df['No_disfrutados_min'] = (df['Maximo_min'] - df['Disfrutados_min']).clip(lower=0)
        df['sin_maximo']       = df['Maximo_min'] == 0

        # Columnas formateadas para mostrar/exportar
        df['Máximo']         = df['Maximo_min'].apply(format_duracion)
        df['Disfrutados']    = df.apply(
            lambda r: format_duracion_separado(r['Disfrutados_dias_min'], r['Disfrutados_horas_min']),
            axis=1
        )
        df['No disfrutados'] = df['No_disfrutados_min'].apply(format_duracion)

    # ── STATS ─────────────────────────────────────────────────────────────────
    total        = len(df)
    sin_disfrute = len(df[df['Disfrutados_min'] == 0])
    con_parcial  = len(df[(df['Disfrutados_min'] > 0) & (df['No_disfrutados_min'] > 0)])
    sin_maximo   = len(df[df['sin_maximo']])
    total_nd_min = df['No_disfrutados_min'].sum()

    st.markdown("<br>", unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.markdown(f'<div class="stat-card"><div class="stat-label">Total empleados</div><div class="stat-value">{total}</div></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="stat-card"><div class="stat-label">Sin disfrute</div><div class="stat-value">{sin_disfrute}</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="stat-card"><div class="stat-label">Disfrute parcial</div><div class="stat-value">{con_parcial}</div></div>', unsafe_allow_html=True)
    s4.markdown(f'<div class="stat-card"><div class="stat-label">Sin máximo definido</div><div class="stat-value">{sin_maximo}</div></div>', unsafe_allow_html=True)
    s5.markdown(f'<div class="stat-card highlight"><div class="stat-label">Total no disfrutados</div><div class="stat-value">{format_duracion(total_nd_min)}</div></div>', unsafe_allow_html=True)

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

    # Display table (se muestran las columnas formateadas, pero se ordena/colorea por el valor en minutos)
    display_df = df[['Código','Empleado','Centro de trabajo','Convenio',
                     'Máximo','Disfrutados','No disfrutados','No_disfrutados_min']].copy()
    display_df = display_df.sort_values('No_disfrutados_min', ascending=False).reset_index(drop=True)

    if search:
        mask = (
            display_df['Empleado'].str.contains(search, case=False, na=False) |
            display_df['Código'].str.contains(search, case=False, na=False) |
            display_df['Centro de trabajo'].str.contains(search, case=False, na=False)
        )
        display_df = display_df[mask]

    max_val = display_df['No_disfrutados_min'].max() if len(display_df) > 0 else 1

    display_cols = [c for c in display_df.columns if c != 'No_disfrutados_min']

    def color_nd(row):
        val = row['No_disfrutados_min']
        if val <= 0:
            style = "background-color:#d8f3e3;color:#2d6a4f;font-weight:500;"
        elif val < max_val:
            style = "background-color:#fff0e0;color:#e07a1f;font-weight:500;"
        else:
            style = "background-color:#fdecea;color:#c0392b;font-weight:500;"
        return [style if col == "No disfrutados" else "" for col in display_cols]

    st.dataframe(
        display_df.drop(columns=['No_disfrutados_min']).style.apply(
            lambda r: color_nd(display_df.loc[r.name]), axis=1
        ),
        use_container_width=True,
        height=min(600, 60 + len(display_df) * 38),
        column_config={
            "Código":            st.column_config.TextColumn("Código", width="small"),
            "Empleado":          st.column_config.TextColumn("Empleado", width="large"),
            "Centro de trabajo": st.column_config.TextColumn("Centro", width="medium"),
            "Convenio":          st.column_config.TextColumn("Convenio", width="medium"),
            "Máximo":            st.column_config.TextColumn("Máximo", width="small"),
            "Disfrutados":       st.column_config.TextColumn("Disfrutados", width="small"),
            "No disfrutados":    st.column_config.TextColumn("No disfrutados", width="small"),
        },
        hide_index=True,
    )
    st.caption(f"{len(display_df)} empleados · Solo validados · {date_from.strftime('%d/%m/%Y')} – {date_to.strftime('%d/%m/%Y')} · {tipo_sel}")
