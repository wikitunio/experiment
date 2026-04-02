import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import datetime
import requests
import io
import numpy as np

# -- PAGE CONFIGURATION & CSS --
st.set_page_config(page_title="AGL UREA Dashboard", layout="wide", initial_sidebar_state="collapsed")
github_img_url = "https://raw.githubusercontent.com/wikitunio/experiment/main/IMG_9291.JPG"
bg_css = f'background-image: linear-gradient(rgba(0, 0, 50, 0.75), rgba(0, 0, 50, 0.75)), url("{github_img_url}"); background-color: #1E3A8A;'

st.markdown(f"""
    <style>
    .hero-container {{ {bg_css} background-size: cover; background-position: center; padding: 15px 20px; border-radius: 8px; color: white; text-align: center; margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3); }}
    .hero-container h1 {{ font-size: 26px; margin-bottom: 0px; margin-top: 0px; color: white !important; font-weight: bold; }}
    .hero-container p {{ font-size: 14px; opacity: 0.9; margin-bottom: 0px; margin-top: 2px; }}
    div[data-testid="metric-container"] {{ background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 8px rgba(0,0,0,0.04); }}
    .section-header {{ color: #1E3A8A; margin-top: 15px; margin-bottom: 10px; font-weight: 700; font-size: 20px; border-bottom: 2px solid #1E3A8A; padding-bottom: 4px; }}
    .v-card {{ border-radius: 8px; padding: 12px; box-shadow: 2px 4px 10px rgba(0,0,0,0.06); min-height: 200px; border-top: 4px solid; display: flex; flex-direction: column; }}
    .v-rx {{ background: linear-gradient(135deg, #ffffff, #f1f5f9); border-top-color: #1E3A8A; }}
    .v-st {{ background: linear-gradient(135deg, #ffffff, #fffbeb); border-top-color: #d97706; }}
    .v-hpd {{ background: linear-gradient(135deg, #ffffff, #ecfdf5); border-top-color: #059669; }}
    .v-hpa {{ background: linear-gradient(135deg, #ffffff, #f0f9ff); border-top-color: #0284c7; }}
    .v-lpa {{ background: linear-gradient(135deg, #ffffff, #f0fdfa); border-top-color: #0d9488; }}
    .v-title {{ font-size: 14px; font-weight: bold; margin-bottom: 10px; text-align: center; padding-bottom: 6px; border-bottom: 1px solid rgba(0,0,0,0.1); }}
    .v-title-rx {{ color: #1E3A8A; }} .v-title-st {{ color: #d97706; }} .v-title-hpd {{ color: #059669; }} .v-title-hpa {{ color: #0284c7; }} .v-title-lpa {{ color: #0d9488; }}
    .v-row {{ display: flex; justify-content: space-between; align-items: center; font-size: 13px; padding: 4px 0; border-bottom: 1px dashed rgba(0,0,0,0.05); }}
    .v-row:last-child {{ border-bottom: none; }}
    .v-row span {{ color: #555; }} .v-row b {{ color: #111; display: flex; align-items: center; gap: 4px; }}
    .delta-badge {{ font-size: 10px; padding: 2px 4px; border-radius: 4px; font-weight: bold; }}
    .sim-panel {{ background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
    .footer {{ text-align: center; padding: 20px 0px; color: #666666; font-size: 13px; border-top: 1px solid #e0e0e0; margin-top: 30px; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown("""<div class="hero-container"><h1>🏭 UREA Plant Daily Operations</h1><p>AGL (AgriTech Limited) | Iskandarabad, Daudkhel</p></div>""", unsafe_allow_html=True)

# --- APIs & DATA LOADING ---
@st.cache_data(ttl=900)
def get_daudkhel_weather():
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast?latitude=32.88&longitude=71.54&current=temperature_2m,relative_humidity_2m", timeout=5).json()
        return r['current']['temperature_2m'], r['current']['relative_humidity_2m']
    except: return None, None

@st.cache_data(ttl=300)

def load_data():

    # THE FIX FOR 503 ERROR: Use a "User-Agent" header to look like a real browser

    url = "https://muet14-my.sharepoint.com/:x:/g/personal/18ch37_students_muet_edu_pk/IQAwrk9MhgHFTZl2r-JviPwVAfxUR7fGMtM8izdZFteTZoQ?download=1"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x86) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    

    try:

        response = requests.get(url, headers=headers)

        response.raise_for_status() # Check for HTTP errors

        excel_data = io.BytesIO(response.content)

    except Exception as e:

        return pd.DataFrame(), f"Cloud Connection Error: {e}. Please check if the OneDrive link is still active."


    # Load Sheets
    try:
        df_pq = pd.read_excel(xls, sheet_name="PQ Trends", skiprows=1).iloc[:, [0,1,2,3,4,6,11]]
        df_pq.columns = ['Date', 'Production', 'Load', 'Moisture', 'Biuret', 'APS', 'Remarks']
        df_pq['Date'] = pd.to_datetime(df_pq['Date'], errors='coerce')
        for c in ['Production','Load','Moisture','Biuret','APS']: df_pq[c] = pd.to_numeric(df_pq[c], errors='coerce').fillna(0)
    except: df_pq = pd.DataFrame(columns=['Date'])

    try:
        df_eff = pd.read_excel(xls, sheet_name="Efficiencies", skiprows=2).iloc[:, [0,1,2,3,4,6,7,9,12,13,14,15]]
        df_eff.columns = ['Date','CO2_Conv','NH3_Conv','Rx_NC','Rx_HC','Stripper_Eff','Stripper_NC','HPD_Eff','HPA_NC','HPA_HC','LPA_NC','LPA_HC']
        df_eff['Date'] = pd.to_datetime(df_eff['Date'], errors='coerce')
        for c in df_eff.columns[1:]: df_eff[c] = pd.to_numeric(df_eff[c], errors='coerce').fillna(0)
    except: df_eff = pd.DataFrame(columns=['Date'])

    try:
        s_name = "Lab Analysis" if "Lab Analysis" in xls.sheet_names else "Lab analysis"
        df_lab = pd.read_excel(xls, sheet_name=s_name, skiprows=1).iloc[:, [0,4,6,8,18,19,22,23]]
        df_lab.columns = ['Date','Urea_Conc','Stripper_NH3','Stripper_Urea','HPA_NH3','HPA_CO2','LPA_NH3','LPA_CO2']
        df_lab['Date'] = pd.to_datetime(df_lab['Date'], errors='coerce')
        for c in df_lab.columns[1:]: df_lab[c] = pd.to_numeric(df_lab[c], errors='coerce').fillna(0)
    except: df_lab = pd.DataFrame(columns=['Date'])

    try:
        s_name = "Product Analysis" if "Product Analysis" in xls.sheet_names else "Product analysis"
        df_pa = pd.read_excel(xls, sheet_name=s_name, skiprows=1).iloc[:, [0,6]]
        df_pa.columns = ['Date','Free_Ammonia']
        df_pa['Date'] = pd.to_datetime(df_pa['Date'], errors='coerce').dt.floor('d')
        df_pa['Free_Ammonia'] = pd.to_numeric(df_pa['Free_Ammonia'], errors='coerce')
        df_pa_daily = df_pa.groupby('Date').agg({'Free_Ammonia': 'mean'}).reset_index()
    except: df_pa_daily = pd.DataFrame(columns=['Date'])

    # Merge
    df_m = df_pq.dropna(subset=['Date'])
    for d in [df_eff, df_lab, df_pa_daily]: 
        if not d.empty: df_m = pd.merge(df_m, d.dropna(subset=['Date']), on='Date', how='left')
    
    df_m.fillna(0.0, inplace=True)
    df_daily = df_m.groupby('Date').mean(numeric_only=True).reset_index()
    if 'Remarks' in df_m.columns: df_daily['Remarks'] = df_m.groupby('Date')['Remarks'].first().values

    df_daily['Theo_CO2_Conv'] = df_daily.apply(lambda r: (62.5 + (r.get('Rx_NC',0)-3.11)*8.5 - (r.get('Rx_HC',0)-0.52)*6.0) if r.get('Rx_NC',0)>0 else 0, axis=1).clip(50, 75)
    
    pct_cols = ['CO2_Conv','NH3_Conv','Stripper_Eff','HPD_Eff','Urea_Conc','Stripper_NH3','Stripper_Urea']
    for c in pct_cols:
        if c in df_daily.columns: df_daily[c] = df_daily[c].apply(lambda x: x*100 if 0 < x <= 1.5 else x)
            
    df_daily['Eq_Gap'] = df_daily.apply(lambda r: r['Theo_CO2_Conv'] - r['CO2_Conv'] if r.get('CO2_Conv',0)>0 else 0, axis=1)
    return df_daily.sort_values('Date'), ""

# --- MAIN APP ---
df, err_msg = load_data()
if err_msg: st.error(f"⚠️ {err_msg}")
elif not df.empty:
    yesterday = datetime.date.today() - timedelta(days=1)
    
    c_title, c_date = st.columns([6, 1])
    with c_date:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        selected_date = st.date_input("Shift Date", yesterday, label_visibility="collapsed")
    with c_title:
        st.markdown(f"<h3 class='section-header' style='border-bottom: none; margin-bottom: 0px; padding-bottom: 0px;'>📊 Production & Quality ({selected_date.strftime('%d %b %Y')})</h3>", unsafe_allow_html=True)
    st.markdown("<div style='border-bottom: 2px solid #1E3A8A; padding-bottom: 5px; margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    
    dt_sel = pd.to_datetime(selected_date)
    d_today = df[df['Date'] == dt_sel]
    d_yest = df[df['Date'] == (dt_sel - timedelta(days=1))]
    
    if not d_today.empty:
        def get_val(data, col): return float(data[col].values[0]) if not data.empty and col in data.columns else 0.0
        def get_delta_val(col):
            y = get_val(d_yest, col)
            return None if d_yest.empty or y == 0 else get_val(d_today, col) - y

        remarks = d_today.get('Remarks', pd.Series([''])).values[0]
        if str(remarks) not in ['nan','','0','None']: st.info(f"📝 **Shift Log:** {remarks}")

        # KPIs
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        kpis = [
            (c1, "Production", 'Production', 'MT', False), (c2, "Plant Load", 'Load', '%', False),
            (c3, "Moisture", 'Moisture', '%', True), (c4, "Biuret", 'Biuret', '%', True),
            (c5, "APS", 'APS', 'mm', False), (c6, "Free NH3", 'Free_Ammonia', 'ppm', True)
        ]
        for col, title, key, unit, inv in kpis:
            val, delta = get_val(d_today, key), get_delta_val(key)
            dec = 0 if key == 'Production' else (3 if key == 'Moisture' else (1 if key in ['Load','Free_Ammonia'] else 2))
            col.metric(title, f"{val:,.{dec}f} {unit}", f"{delta:,.{dec}f} {unit}" if delta is not None else None, delta_color="inverse" if inv else "normal")

        # HTML Helper for Vessels
        def html_val(col, dec=2, is_pct=False):
            val, delta = get_val(d_today, col), get_delta_val(col)
            v_str = f"{val:.{dec}f}{'%' if is_pct else ''}"
            if delta is None or round(delta, dec) == 0: return f"<b>{v_str} <span class='delta-badge' style='background:#f3f4f6; color:#9ca3af;'>-</span></b>"
            d_str = f"{abs(round(delta, dec)):.{dec}f}{'%' if is_pct else ''}"
            if delta > 0: return f"<b>{v_str} <span class='delta-badge' style='background:#dcfce7; color:#16a34a;'>▲ {d_str}</span></b>"
            return f"<b>{v_str} <span class='delta-badge' style='background:#fee2e2; color:#dc2626;'>▼ {d_str}</span></b>"

        # Vessels Loop (Greatly compressed!)
        st.markdown("<h3 class='section-header'>🧪 Synthesis Loop & Major Vessels</h3>", unsafe_allow_html=True)
        v_cols = st.columns(5)
        vessels = [
            ("⚗️ Reactor", "rx", [("N/C (Ref: 3.11)", 'Rx_NC', 2, False), ("H/C (Ref: 0.52)", 'Rx_HC', 2, False), ("CO2 Conv (58%)", 'CO2_Conv', 1, True), ("Eq Gap (< 3.0%)", 'Eq_Gap', 1, True), ("Urea Conc", 'Urea_Conc', 2, True)]),
            ("🌪️ Stripper", "st", [("Eff (Ref: 78%)", 'Stripper_Eff', 1, True), ("N/C (Ref: 2.01)", 'Stripper_NC', 2, False), ("Ammonia", 'Stripper_NH3', 2, True), ("Urea Conc", 'Stripper_Urea', 2, True)]),
            ("🌡️ HPD", "hpd", [("Eff (Ref: 65.4%)", 'HPD_Eff', 1, True)]),
            ("💧 HPA", "hpa", [("N/C (Ref: 2.38)", 'HPA_NC', 2, False), ("H/C (Ref: 1.29)", 'HPA_HC', 2, False)]),
            ("☁️ LPA", "lpa", [("N/C (Ref: 2.29)", 'LPA_NC', 2, False), ("H/C (Ref: 2.28)", 'LPA_HC', 2, False)])
        ]
        
        for i, (title, css, rows) in enumerate(vessels):
            with v_cols[i]:
                html = f'<div class="v-card v-{css}"><div class="v-title v-title-{css}">{title}</div>'
                for label, k, d, pct in rows: html += f'<div class="v-row"><span>{label}</span>{html_val(k, d, pct)}</div>'
                st.markdown(html + '</div>', unsafe_allow_html=True)

        # Trends
        st.markdown("<h3 class='section-header' style='margin-top: 35px;'>📈 Plant Trends Analysis</h3>", unsafe_allow_html=True)
        t_days = st.slider("Quick Lookback Window (Days)", 3, 30, 7)
        df_t = df[(df['Date'] <= dt_sel) & (df['Date'] >= dt_sel - timedelta(days=t_days-1))]
        
        def add_ref(fig, val=None):
            fig.add_vline(x=dt_sel.strftime('%Y-%m-%d'), line_width=2, line_dash="dash", line_color="gray")
            if val is not None: fig.add_hline(y=val, line_dash="dot", line_color="red")
            fig.update_layout(margin=dict(t=40, b=20, l=10, r=10), height=300)
            return fig

        fig_c = make_subplots(specs=[[{"secondary_y": True}]])
        fig_c.add_trace(go.Scatter(x=df_t['Date'], y=df_t['Production'], name="Prod (MT)", line=dict(color='#2ca02c', width=3)), secondary_y=False)
        fig_c.add_trace(go.Scatter(x=df_t['Date'], y=df_t['Load'], name="Load (%)", line=dict(color='#1f77b4', width=3, dash='dot')), secondary_y=True)
        fig_c.update_layout(title="1. Production & Plant Load", margin=dict(t=40,b=20,l=10,r=10), height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig_c.add_vline(x=dt_sel.strftime('%Y-%m-%d'), line_width=2, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_c, use_container_width=True)

        t1, t2 = st.columns(2)
        charts = [
            (t1, 'CO2_Conv', '2. Reactor CO2 Conv (%)', '#9467bd', 58.0), (t2, 'Rx_NC', '3. Reactor N/C Ratio', '#1f77b4', 3.11),
            (t1, 'Stripper_Eff', '4. Stripper Eff (%)', '#d97706', 78.0), (t2, 'HPD_Eff', '5. HPD Eff (%)', '#059669', 65.4),
            (t1, 'Moisture', '6. Avg Moisture (%)', '#17becf', 0.3), (t2, 'Biuret', '7. Avg Biuret (%)', '#e377c2', 0.9),
            (t1, 'APS', '8. Avg APS (mm)', '#7f7f7f', None)
        ]
        for col, yv, title, color, ref in charts:
            with col:
                fig = px.line(df_t, x='Date', y=yv, markers=True, title=title, line_shape='spline')
                fig.update_traces(line_color=color)
                if 'Eff' in yv or 'Conv' in yv: fig.update_yaxes(range=[0, 100])
                st.plotly_chart(add_ref(fig, ref), use_container_width=True)

        # Custom Export
        st.markdown("<hr style='border:1px solid #1E3A8A; margin: 30px 0;'><h3 class='section-header'>🛠️ Custom Data Export</h3>", unsafe_allow_html=True)
        c_ctrl1, c_ctrl2 = st.columns([1, 2])
        with c_ctrl1: dates = st.date_input("Time Period:", value=(dt_sel.date()-timedelta(days=6), dt_sel.date()), min_value=df['Date'].min().date(), max_value=df['Date'].max().date())
        with c_ctrl2: vars = st.multiselect("Variables:", [c for c in df.columns if c not in ['Date', 'Remarks']], default=['Moisture', 'Biuret'])
        
        if len(dates) == 2 and vars:
            df_cust = df[(df['Date'].dt.date >= dates[0]) & (df['Date'].dt.date <= dates[1])]
            if not df_cust.empty:
                cg, cs = st.columns([3, 1])
                with cg:
                    f_c = px.line(df_cust, x='Date', y=vars, markers=True, title="Custom Trend", line_shape='spline')
                    f_c.update_layout(height=400, margin=dict(t=40,b=20,l=10,r=10))
                    st.plotly_chart(f_c, use_container_width=True)
                with cs:
                    sdf = df_cust[vars].agg(['mean', 'min', 'max']).T
                    sdf.columns = ['Avg', 'Min', 'Max']
                    st.dataframe(sdf.style.format("{:.2f}"), use_container_width=True)
                    csv = df_cust[['Date'] + vars].to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download CSV", data=csv, file_name=f"AGL_Data_{dates[0]}_{dates[1]}.csv", mime="text/csv", use_container_width=True)

        # AI Section
        st.markdown("<hr style='border:1px solid #1E3A8A; margin: 30px 0;'><h3 class='section-header'>🧠 Process Simulators</h3>", unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        with s1: w_op = st.slider("Vanes Open (%)", 0, 100, 20, 5)
        with s2: f_op = st.slider("Fan Open (%)", 0, 100, 70, 5)
        with s3: m_tmp = st.slider("Melt Temp (°C)", 132.0, 145.0, 138.0, 0.5)
        with s4: v_abs = st.slider("Vacuum (mmHg)", 10.0, 80.0, 30.0, 1.0)

        ca1, ca2 = st.columns(2)
        with ca1:
            st.markdown("#### 🎯 Biuret Predictor")
            df_c = df[(df['Load']>0) & (df['Biuret']>0)].dropna(subset=['Load','Biuret'])
            if len(df_c) > 2:
                p = np.poly1d(np.polyfit(df_c['Load'], df_c['Biuret'], 1))
                sim_b = p(get_val(d_today, 'Load')) + (m_tmp-138.0)*0.015 + (v_abs-30.0)*0.005
                st.info(f"Simulated Biuret: **{sim_b:.2f}%**")
        with ca2:
            st.markdown("#### 🌧️ Prilling Cooling")
            tmp, hum = get_daudkhel_weather()
            if tmp:
                est_m = 0.25 + max(0,(tmp-25)*0.002) + max(0,(hum-40)*0.0015) + max(0,(get_val(d_today,'Load')-100)*0.001) + max(0,(100-f_op)*0.0005) + max(0,(100-w_op)*0.0008) + max(0,(m_tmp-138)*0.003) + max(0,(v_abs-30)*0.0015)
                st.info(f"Daudkhel: **{tmp}°C / {hum}% RH** | Est Moisture: **{est_m:.3f}%**")

        # VMG Tab
        st.markdown("<hr style='border:1px dashed #e2e8f0; margin: 30px 0;'><h4>❄️ HP Carbamate Predictor</h4>", unsafe_allow_html=True)
        def vmg_ui(n, c, h, k):
            c1, c2 = st.columns([1, 2])
            with c1:
                n_i = st.number_input("NH3 (wt%)", value=float(n), step=0.5, key=k+"_n")
                c_i = st.number_input("CO2 (wt%)", value=float(c), step=0.5, key=k+"_c")
                h_i = st.number_input("Balance (wt%)", value=float(h), step=0.5, key=k+"_h")
            tot = n_i + c_i + h_i if (n_i + c_i + h_i) > 0 else 1
            nc = ((n_i/tot*100)/17.031) / ((c_i/tot*100)/44.01) if c_i > 0 else 0
            ct = 105.0 + (20.0 - (h_i/tot*100))*2.8 + abs(nc-2.3)**2 * 15.0
            with c2: st.success(f"**N/C Ratio:** {nc:.2f} | **Crystallization Temp:** {ct:.1f} °C")

        tb1, tb2, tb3 = st.tabs(["🧪 HPA", "🧪 LPA", "🎛️ Custom"])
        with tb1:
            if get_val(d_today, 'HPA_NH3') > 0: vmg_ui(get_val(d_today, 'HPA_NH3'), get_val(d_today, 'HPA_CO2'), max(0, 100-get_val(d_today, 'HPA_NH3')-get_val(d_today, 'HPA_CO2')), "h1")
            else: vmg_ui(42.0, 38.0, 20.0, "h2")
        with tb2:
            if get_val(d_today, 'LPA_NH3') > 0: vmg_ui(get_val(d_today, 'LPA_NH3'), get_val(d_today, 'LPA_CO2'), max(0, 100-get_val(d_today, 'LPA_NH3')-get_val(d_today, 'LPA_CO2')), "l1")
            else: vmg_ui(38.0, 36.0, 26.0, "l2")
        with tb3: vmg_ui(42.0, 38.0, 20.0, "c1")

    else: st.info("No data for selected date.")

st.markdown("<div class='footer'>Developed by Waqar Ahmed Tunio with Ai</div>", unsafe_allow_html=True)
