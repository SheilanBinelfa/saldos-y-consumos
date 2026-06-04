import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
import math

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Saldos y Consumos por Absentismo · Endalia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── STYLES ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

  /* Topbar */
  .topbar {
    background: #1a1917;
    color: #fff;
    padding: 12px 24px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
  }
  .topbar-brand { font-family: 'DM Mono', monospace; font-size: 13px; letter-spacing: 0.04em; display: flex; align-items: center; gap: 10px; }
  .topbar-dot { width: 8px; height: 8px; border-radius: 50%; background: #52b788; display: inline-block; }
  .topbar-right { font-family: 'DM Mono', monospace; font-size: 11px; color: #9b9890; }

  /* Login card */
  .login-card {
    background: #fff;
    border: 1px solid #e2e0d8;
    border-radius: 10px;
    padding: 32px;
    max-width: 440px;
    margin: 48px auto 0;
  }
  .login-title { font-size: 20px; font-weight: 600; margin-bottom: 6px; }
  .login-sub { color: #6b6860; font-size: 13px; margin-bottom: 24px; line-height: 1.6; }

  /* Stats */
  .stat-card {
    background: #fff;
    border: 1px solid #e2e0d8;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: left;
  }
  .stat-label { font-size: 11px; color: #9b9890; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
  .stat-value { font-family: 'DM Mono', monospace; font-size: 24px; font-weight: 500; color: #1a1917; }
  .stat-card.highlight { border-color: #52b788; background: #d8f3e3; }
  .stat-card.highlight .stat-value { color: #2d6a4f; }

  /* Badges */
  .badge-full { background: #fdecea; color: #c0392b; padding: 2px 10px; border-radius: 20px; font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500; }
  .badge-partial { background: #fff0e0; color: #e07a1f; padding: 2px 10px; border-radius: 20px; font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500; }
  .badge-zero { background: #d8f3e3; color: #2d6a4f; padding: 2px 10px; border-radius: 20px; font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500; }

  /* Hide streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 24px; padding-bottom: 24px; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ──────────────────────────────────────────────────────────────
AUTH_URL = "https://dev-api.endaliahr.com/auth/connect/token"
BASE_URL = "https://devapi.endaliahr.com/outbound/holidays/api/outbound"

# ─── SESSION STATE ───────────────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "client_label" not in st.session_state:
    st.session_state.client_label = ""
if "absence_types" not in st.session_state:
    st.session_state.absence_types = []

# ─── HELPERS ────────────────────────────────────────────────────────────────
def get_token(client_id: str, client_secret: str) -> str:
    """Obtiene Bearer token via OAuth2 client_credentials."""
    resp = requests.post(
        AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if resp.status_code != 200:
        raise ValueError(f"Credenciales incorrectas o sin acceso (HTTP {resp.status_code})")
    return resp.json()["access_token"]


def api_get_all(token: str, url: str, params: dict = {}) -> list:
    """Fetch paginado — recoge todas las páginas."""
    results = []
    offset = 0
    limit = 500
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        p = {**params, "limit": limit, "offset": offset}
        resp = requests.get(url, headers=headers, params=p, timeout=30)
        if resp.status_code != 200:
            raise ValueError(f"Error API {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", data.get("results", [])))
        results.extend(items)
        if len(items) < limit:
            break
        offset += limit
    return results


def load_absence_types(token: str) -> list:
    """Carga los tipos de ausencia activos."""
    try:
        items = api_get_all(token, f"{BASE_URL}/v1/absenteism/types/names")
        types = []
        for t in items:
            name = t.get("Name") or t.get("name") or t.get("TypeName") or str(t)
            code = t.get("Code") or t.get("code") or t.get("TypeCode") or name
            types.append({"name": name, "code": code})
        return types
    except Exception:
        return [{"name": "Asuntos Propios Ca...", "code": "asuntos_propios"}]


def fmt_days(val) -> str:
    if val is None:
        return "—"
    return f"{float(val):.2f} d".replace(".", ",")


def default_quarter_range():
    today = date.today()
    q = (today.month - 1) // 3
    starts = [date(today.year, 1, 1), date(today.year, 4, 1),
              date(today.year, 7, 1), date(today.year, 10, 1)]
    ends   = [date(today.year, 3, 31), date(today.year, 6, 30),
              date(today.year, 9, 30), date(today.year, 12, 31)]
    return starts[q], ends[q]


# ─── TOPBAR ─────────────────────────────────────────────────────────────────
badge = f'<span style="background:rgba(82,183,136,0.15);border:1px solid rgba(82,183,136,0.3);padding:4px 12px;border-radius:20px;color:#52b788;font-size:11px;">● {st.session_state.client_label}</span>' if st.session_state.token else ""
st.markdown(f"""
<div class="topbar">
  <div class="topbar-brand"><span class="topbar-dot"></span> Saldos y Consumos por Absentismo</div>
  <div class="topbar-right">{badge}</div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# SCREEN 1: LOGIN
# ════════════════════════════════════════════════════════════════════════════
if not st.session_state.token:

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="login-title">Acceso a la herramienta</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Introduce las credenciales de API proporcionadas por Endalia para tu organización.</div>', unsafe_allow_html=True)

        client_id     = st.text_input("Client ID", placeholder="Tu Client ID de Endalia", label_visibility="visible")
        client_secret = st.text_input("Client Secret", type="password", placeholder="cs_••••••••••••", label_visibility="visible")

        if st.button("Conectar", use_container_width=True, type="primary"):
            if not client_id or not client_secret:
                st.error("Introduce Client ID y Client Secret.")
            else:
                with st.spinner("Autenticando..."):
                    try:
                        token = get_token(client_id, client_secret)
                        st.session_state.token = token
                        st.session_state.client_label = client_id
                        with st.spinner("Cargando tipos de ausencia..."):
                            st.session_state.absence_types = load_absence_types(token)
                        st.success("Conectado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

        st.caption("¿No tienes credenciales? Contacta con tu gestor de cuenta en Endalia.")

    st.stop()


# ════════════════════════════════════════════════════════════════════════════
# SCREEN 2: MAIN
# ════════════════════════════════════════════════════════════════════════════

# Header row
hcol1, hcol2 = st.columns([5, 1])
with hcol1:
    st.markdown("### Saldos y Consumos por Absentismo")
    st.caption("Saldo disponible, consumido y días a pagar · Por tipo de ausencia y rango de fechas")
with hcol2:
    if st.button("← Cambiar cuenta", use_container_width=True):
        st.session_state.token = None
        st.session_state.client_label = ""
        st.session_state.absence_types = []
        st.rerun()

st.divider()

# ─── FILTER BAR ─────────────────────────────────────────────────────────────
fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 1.5])

with fc1:
    # Build type selector
    type_options = {t["name"]: t["code"] for t in st.session_state.absence_types}
    type_names   = list(type_options.keys())
    # Pre-select "Asuntos propios" if found
    default_idx  = next((i for i, n in enumerate(type_names) if "asuntos propios" in n.lower()), 0)
    selected_type_name = st.selectbox("Tipo de ausencia", options=type_names, index=default_idx)
    selected_type_code = type_options.get(selected_type_name, "")

q_start, q_end = default_quarter_range()

with fc2:
    date_from = st.date_input("Fecha inicio", value=q_start, format="DD/MM/YYYY")
with fc3:
    date_to = st.date_input("Fecha fin", value=q_end, format="DD/MM/YYYY")
with fc4:
    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("Calcular", use_container_width=True, type="primary")

# ─── RUN REPORT ─────────────────────────────────────────────────────────────
if run:
    if date_from > date_to:
        st.error("La fecha de inicio debe ser anterior al fin.")
        st.stop()

    with st.spinner("Cargando límites de empleados..."):
        try:
            limits_params = {}
            if selected_type_code:
                limits_params["typeCodes"] = selected_type_code
            limits = api_get_all(
                st.session_state.token,
                f"{BASE_URL}/v2/absenteism/period/employee-limits",
                limits_params,
            )
        except Exception as e:
            st.error(f"Error cargando límites: {e}")
            st.stop()

    if not limits:
        st.warning("No se encontraron empleados para este tipo de ausencia.")
        st.stop()

    with st.spinner("Cargando consumos del periodo..."):
        try:
            req_params = {"status": "4"}  # Solo validados
            requests_data = api_get_all(
                st.session_state.token,
                f"{BASE_URL}/v1/absenteism/requests-detailed/{date_from.strftime('%Y-%m-%d')}/{date_to.strftime('%Y-%m-%d')}",
                req_params,
            )
        except Exception as e:
            st.error(f"Error cargando consumos: {e}")
            st.stop()

    # Filter requests by type name
    filtered_reqs = [
        r for r in requests_data
        if selected_type_name.lower()[:8] in (r.get("RequestType") or "").lower()
    ] if selected_type_code else requests_data

    # Aggregate consumption per employee
    consumo_map = {}
    for r in filtered_reqs:
        emp_id = r.get("EmpID")
        consumo_map[emp_id] = consumo_map.get(emp_id, 0.0) + float(r.get("Duration") or 0)

    # Build result dataframe
    rows = []
    for emp in limits:
        emp_id   = emp.get("EmpID") or emp.get("empID") or emp.get("EmployeeID")
        maximo   = float(emp.get("MaxDays") or emp.get("maxDays") or emp.get("Maximum") or 0)
        consumido = consumo_map.get(emp_id, 0.0)
        dias_pagar = max(0.0, maximo - consumido)
        rows.append({
            "EmpID":      emp_id,
            "Código":     emp.get("EmpCode") or emp.get("empCode") or emp.get("EmployeeCode") or "—",
            "Empleado":   emp.get("EmpFullName") or emp.get("empFullName") or emp.get("EmployeeName") or "—",
            "Centro":     emp.get("WorkCenter") or emp.get("workCenter") or emp.get("CostCenter") or "—",
            "Máximo (d)": maximo,
            "Consumido (d)": consumido,
            "A pagar (d)": dias_pagar,
        })

    df = pd.DataFrame(rows).sort_values("A pagar (d)", ascending=False).reset_index(drop=True)

    # ─── STATS ──────────────────────────────────────────────────────────────
    total      = len(df)
    sin_consumo = len(df[df["Consumido (d)"] == 0])
    parciales  = len(df[(df["Consumido (d)"] > 0) & (df["A pagar (d)"] > 0)])
    total_dias = df["A pagar (d)"].sum()

    s1, s2, s3, s4 = st.columns(4)
    s1.markdown(f'<div class="stat-card"><div class="stat-label">Total empleados</div><div class="stat-value">{total}</div></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="stat-card"><div class="stat-label">Con consumo parcial</div><div class="stat-value">{parciales}</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="stat-card"><div class="stat-label">Sin consumo (máximo)</div><div class="stat-value">{sin_consumo}</div></div>', unsafe_allow_html=True)
    s4.markdown(f'<div class="stat-card highlight"><div class="stat-label">Total días a pagar</div><div class="stat-value">{total_dias:.2f} d</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── SEARCH + EXPORT ────────────────────────────────────────────────────
    tc1, tc2 = st.columns([4, 1])
    with tc1:
        search = st.text_input("Buscar empleado o centro...", placeholder="Nombre, código o centro de trabajo", label_visibility="collapsed")
    with tc2:
        # CSV export
        export_df = df.drop(columns=["EmpID"])
        csv = export_df.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")
        st.download_button(
            label="↓ Exportar CSV",
            data=csv,
            file_name=f"SaldosConsumos_{date_from}_{date_to}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ─── FILTER BY SEARCH ───────────────────────────────────────────────────
    display_df = df.drop(columns=["EmpID"])
    if search:
        mask = (
            display_df["Empleado"].str.contains(search, case=False, na=False) |
            display_df["Código"].str.contains(search, case=False, na=False) |
            display_df["Centro"].str.contains(search, case=False, na=False)
        )
        display_df = display_df[mask]

    # ─── TABLE ──────────────────────────────────────────────────────────────
    def color_pagar(val):
        if val <= 0:
            return "background-color:#d8f3e3;color:#2d6a4f;font-weight:500;"
        elif val < display_df["Máximo (d)"].max():
            return "background-color:#fff0e0;color:#e07a1f;font-weight:500;"
        else:
            return "background-color:#fdecea;color:#c0392b;font-weight:500;"

    st.dataframe(
        display_df.style.applymap(color_pagar, subset=["A pagar (d)"]).format({
            "Máximo (d)":    "{:.2f}",
            "Consumido (d)": "{:.2f}",
            "A pagar (d)":   "{:.2f}",
        }),
        use_container_width=True,
        height=min(600, 60 + len(display_df) * 38),
        column_config={
            "Código":        st.column_config.TextColumn("Código", width="small"),
            "Empleado":      st.column_config.TextColumn("Empleado", width="large"),
            "Centro":        st.column_config.TextColumn("Centro", width="medium"),
            "Máximo (d)":    st.column_config.NumberColumn("Máximo (d)", format="%.2f", width="small"),
            "Consumido (d)": st.column_config.NumberColumn("Consumido (d)", format="%.2f", width="small"),
            "A pagar (d)":   st.column_config.NumberColumn("A pagar (d)", format="%.2f", width="small"),
        },
        hide_index=True,
    )

    st.caption(f"{len(display_df)} empleado{'s' if len(display_df) != 1 else ''} · Solo solicitudes validadas · Periodo: {date_from.strftime('%d/%m/%Y')} – {date_to.strftime('%d/%m/%Y')}")
