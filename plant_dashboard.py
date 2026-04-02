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

# -- PAGE CONFIGURATION --
st.set_page_config(page_title="AGL UREA Dashboard", layout="wide", initial_sidebar_state="collapsed")

# -- THE SPEED FIX: LOAD IMAGE VIA URL --
github_img_url = "https://raw.githubusercontent.com/wikitunio/experiment/main/IMG_9291.JPG"
bg_css = f'background-image: linear-gradient(rgba(0, 0, 50, 0.75), rgba(0, 0, 50, 0.75)), url("{github_img_url}"); background-color: #1E3A8A;'

# -- ULTRA-COMPACT CUSTOM CSS --
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
    .footer {{ text-align: center; padding: 20px 0px; color: #666666; font-size: 13px; border-top: 1px solid #e0e0e0; margin-top: 30px; }}
    .footer a {{ color: #1E3A8A; text-decoration: none; font-weight: bold; }}
    .sim-panel {{ background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="hero-container">
        <h1>🏭 UREA Plant Daily Operations</h1>
        <p>AGL (AgriTech Limited) | Iskandarabad, Daudkhel</p>
    </div>
    """, unsafe_allow_html=True)

# --- DAUDKHEL WEATHER API FETCH ---
@st.cache_data(ttl=900)
def get_daudkhel_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=32.88&longitude=71.54&current=temperature_2m,relative_humidity_2m"
    try:
        r = requests.get(url, timeout=5).json()
        return r['current']['temperature_2m'], r['current']['relative_humidity_2m']
    except:
        return None, None

@st.cache_data(ttl=3600)
def load_data():
    url = "https://muet14-my.sharepoint.com/:x:/g/personal/18ch37_students_muet_edu_pk/IQAwrk9MhgHFTZl2r-JviPwVAfxUR7fGMtM8izdZFteTZoQ?download=1"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x86) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36', 'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        excel_data = io.BytesIO(response.content)
    except Exception as e:
        return pd.DataFrame(), f"Connection Error: {e}"

    try:
        xls = pd.ExcelFile(excel_data)
    except Exception as e:
        return pd.DataFrame(), f"Error reading Excel structure: {e}"

    # 1. PQ Trends
    try:
        df_pq_raw = pd.read_excel(xls, sheet_name="PQ Trends", skiprows=1)
        df_pq = pd.DataFrame()
        df_pq['Date'] = pd.to_datetime(df_pq_raw.iloc[:, 0], errors='coerce')
        df_pq['Production'] = pd.to_numeric(df_pq_raw.iloc[:, 1], errors='coerce').fillna(0)
        df_pq['Load'] = pd.to_numeric(df_pq_raw.iloc[:, 2], errors='coerce').fillna(0)
        df_pq['Moisture'] = pd.to_numeric(df_pq_raw.iloc[:, 3], errors='coerce').fillna(0)
        df_pq['Biuret'] = pd.to_numeric(df_pq_raw.iloc[:, 4], errors='coerce').fillna(0)
        df_pq['APS'] = pd.to_numeric(df_pq_raw.iloc[:, 6], errors='coerce').fillna(0)
        df_pq['Remarks'] = df_pq_raw.iloc[:, 11].astype(str)
        df_pq = df_pq.dropna(subset=['Date'])
    except: return pd.DataFrame(), "Check PQ Trends Sheet Format"

    # 2. Efficiencies
    try:
        df_eff_raw = pd.read_excel(xls, sheet_name="Efficiencies", skiprows=2)
        df_eff = pd.DataFrame()
        df_eff['Date'] = pd.to_datetime(df_eff_raw.iloc[:, 0], errors='coerce')
        df_eff['CO2_Conv'] = pd.to_numeric(df_eff_raw.iloc[:, 1], errors='coerce').fillna(0)
        df_eff['NH3_Conv'] = pd.to_numeric(df_eff_raw.iloc[:, 2], errors='coerce').fillna(0)  
        df_eff['Rx_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 3], errors='coerce').fillna(0)
        df_eff['Rx_HC'] = pd.to_numeric(df_eff_raw.iloc[:, 4], errors='coerce').fillna(0)
        df_eff['Stripper_Eff'] = pd.to_numeric(df_eff_raw.iloc[:, 6], errors='coerce').fillna(0)
        df_eff['Stripper_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 7], errors='coerce').fillna(0) 
        df_eff['HPD_Eff'] = pd.to_numeric(df_eff_raw.iloc[:, 9], errors='coerce').fillna(0)
        df_eff['HPA_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 12], errors='coerce').fillna(0)
        df_eff['HPA_HC'] = pd.to_numeric(df_eff_raw.iloc[:, 13], errors='coerce').fillna(0)
        df_eff['LPA_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 14], errors='coerce').fillna(0)
        df_eff['LPA_HC'] = pd.to_numeric(df_eff_raw.iloc[:, 15], errors='coerce').fillna(0)
        df_eff = df_eff.dropna(subset=['Date'])
    except: return pd.DataFrame(), "Check Efficiencies Sheet Format"

    # 3. Lab Analysis 
    try:
        try: df_lab_raw = pd.read_excel(xls, sheet_name="Lab Analysis", skiprows=1)
        except: df_lab_raw = pd.read_excel(xls, sheet_name="Lab analysis", skiprows=1)
        
        df_lab = pd.DataFrame()
        df_lab['Date'] = pd.to_datetime(df_lab_raw.iloc[:, 0], errors='coerce')
        df_lab['Urea_Conc'] = pd.to_numeric(df_lab_raw.iloc[:, 4], errors='coerce').fillna(0) 
        df_lab['Stripper_NH3'] = pd.to_numeric(df_lab_raw.iloc[:, 6], errors='coerce').fillna(0) 
        df_lab['Stripper_Urea'] = pd.to_numeric(df_lab_raw.iloc[:, 8], errors='coerce').fillna(0) 
        df_lab['HPA_NH3'] = pd.to_numeric(df_lab_raw.iloc[:, 18], errors='coerce').fillna(0) 
        df_lab['HPA_CO2'] = pd.to_numeric(df_lab_raw.iloc[:, 19], errors='coerce').fillna(0) 
        df_lab['LPA_NH3'] = pd.to_numeric(df_lab_raw.iloc[:, 22], errors='coerce').fillna(0) 
        df_lab['LPA_CO2'] = pd.to_numeric(df_lab_raw.iloc[:, 23], errors='coerce').fillna(0) 
        
        df_lab = df_lab.dropna(subset=['Date'])
    except Exception as e:
        df_lab = pd.DataFrame(columns=['Date', 'Urea_Conc', 'Stripper_NH3', 'Stripper_Urea', 'HPA_NH3', 'HPA_CO2', 'LPA_NH3', 'LPA_CO2'])

    # 4. Product Analysis
    try:
        try: df_pa_raw = pd.read_excel(xls, sheet_name="Product Analysis", skiprows=1)
        except: df_pa_raw = pd.read_excel(xls, sheet_name="Product analysis", skiprows=1)
        
        df_pa = pd.DataFrame()
        df_pa['Date'] = pd.to_datetime(df_pa_raw.iloc[:, 0], errors='coerce').dt.floor('d')
        df_pa['Free_Ammonia'] = pd.to_numeric(df_pa_raw.iloc[:, 6], errors='coerce')
        df_pa = df_pa.dropna(subset=['Date'])
        df_pa_daily = df_pa.groupby('Date').agg({'Free_Ammonia': 'mean'}).reset_index()
    except Exception as e:
        df_pa_daily = pd.DataFrame(columns=['Date', 'Free_Ammonia'])

    # Merge Engine
    df_master = pd.merge(df_pq, df_eff, on='Date', how='left')
    if not df_lab.empty: df_master = pd.merge(df_master, df_lab, on='Date', how='left')
    else:
        for col in ['Urea_Conc', 'Stripper_NH3', 'Stripper_Urea', 'HPA_NH3', 'HPA_CO2', 'LPA_NH3', 'LPA_CO2']: df_master[col] = 0.0

    if not df_pa_daily.empty: df_master = pd.merge(df_master, df_pa_daily, on='Date', how='left')
    else: df_master['Free_Ammonia'] = 0.0

    agg_funcs = {
        'Production': 'sum', 'Load': 'mean', 'Moisture': 'mean', 'Biuret': 'mean',
        'APS': 'mean', 'CO2_Conv': 'mean', 'NH3_Conv': 'mean', 'Rx_NC': 'mean', 'Rx_HC': 'mean',
        'Stripper_Eff': 'mean', 'Stripper_NC': 'mean', 'HPD_Eff': 'mean', 'HPA_NC': 'mean', 'HPA_HC': 'mean',
        'LPA_NC': 'mean', 'LPA_HC': 'mean', 'Urea_Conc': 'mean', 'Stripper_NH3': 'mean', 'Stripper_Urea': 'mean',
        'HPA_NH3': 'mean', 'HPA_CO2': 'mean', 'LPA_NH3': 'mean', 'LPA_CO2': 'mean',
        'Free_Ammonia': 'mean', 'Remarks': 'first'
    }
    df_daily = df_master.groupby('Date').agg(agg_funcs).reset_index()
    
    # --- MATH FIX: Corrected H/C baseline to Reactor Design (0.52) ---
    def calc_theo_conv(row):
        if row['Rx_NC'] == 0 or row['Rx_HC'] == 0: return 0.0
        return 62.5 + (row['Rx_NC'] - 3.11) * 8.5 - (row['Rx_HC'] - 0.52) * 6.0
    
    df_daily['Theo_CO2_Conv'] = df_daily.apply(calc_theo_conv, axis=1).clip(50, 75)
    
    pct_cols = ['CO2_Conv', 'NH3_Conv', 'Stripper_Eff', 'HPD_Eff', 'Urea_Conc', 'Stripper_NH3', 'Stripper_Urea', 'HPA_NH3', 'HPA_CO2', 'LPA_NH3', 'LPA_CO2']
    for col in pct_cols:
        if col in df_daily.columns:
            df_daily[col] = df_daily[col].apply(lambda x: x * 100 if 0 < x <= 1.5 else x)
            
    df_daily['Eq_Gap'] = df_daily.apply(lambda r: r['Theo_CO2_Conv'] - r['CO2_Conv'] if r['CO2_Conv'] > 0 else 0, axis=1)
            
    return df_daily.sort_values('Date'), ""

df, err_msg = load_data()

if err_msg:
    st.error(f"⚠️ {err_msg}")
elif not df.empty:
    yesterday = datetime.date.today() - timedelta(days=1)
    
    c_title, c_date = st.columns([6, 1])
    with c_date:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        selected_date = st.date_input("Shift Date", yesterday, label_visibility="collapsed")
        
    with c_title:
        st.markdown(f"<h3 class='section-header' style='border-bottom: none; margin-bottom: 0px; padding-bottom: 0px;'>📊 Production & Quality ({selected_date.strftime('%d %b %Y')})</h3>", unsafe_allow_html=True)
    
    st.markdown("<div style='border-bottom: 2px solid #1E3A8A; padding-bottom: 5px; margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    
    selected_date_dt = pd.to_datetime(selected_date)
    daily_data = df[df['Date'] == selected_date_dt]
    yesterday_data = df[df['Date'] == (selected_date_dt - timedelta(days=1))]
    
    if not daily_data.empty:
        def get_val(data, col): return float(data[col].values[0]) if not data.empty and col in data.columns else 0.0
        
        def get_delta_val(col):
            y_val = get_val(yesterday_data, col)
            if yesterday_data.empty or y_val == 0: return None
            return get_val(daily_data, col) - y_val

        remarks = daily_data['Remarks'].values[0]
        if str(remarks) != 'nan' and str(remarks).strip() and str(remarks).strip() != '0':
            st.info(f"📝 **Shift Log:** {remarks}")

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        d_prod = get_delta_val('Production')
        c1.metric("Production", f"{get_val(daily_data, 'Production'):,.0f} MT", f"{d_prod:.0f} MT" if d_prod is not None else None)
        
        d_load = get_delta_val('Load')
        c2.metric("Plant Load", f"{get_val(daily_data, 'Load'):.1f} %", f"{d_load:.1f} %" if d_load is not None else None)
        
        d_moist = get_delta_val('Moisture')
        c3.metric("Moisture", f"{get_val(daily_data, 'Moisture'):.3f} %", f"{d_moist:.3f} %" if d_moist is not None else None, delta_color="inverse")
        
        d_biuret = get_delta_val('Biuret')
        c4.metric("Biuret", f"{get_val(daily_data, 'Biuret'):.2f} %", f"{d_biuret:.2f} %" if d_biuret is not None else None, delta_color="inverse")
        
        d_aps = get_delta_val('APS')
        c5.metric("APS", f"{get_val(daily_data, 'APS'):.2f} mm", f"{d_aps:.2f} mm" if d_aps is not None else None)
        
        d_fnh3 = get_delta_val('Free_Ammonia')
        c6.metric("Free NH3", f"{get_val(daily_data, 'Free_Ammonia'):.1f} ppm", f"{d_fnh3:.1f} ppm" if d_fnh3 is not None else None, delta_color="inverse")

        def html_val(col, decimals=2, is_pct=False):
            val = get_val(daily_data, col)
            delta = get_delta_val(col)
            val_str = f"{val:.{decimals}f}"
            if is_pct: val_str += "%"
            
            if delta is None or round(delta, decimals) == 0:
                return f"<b>{val_str} <span class='delta-badge' style='background:#f3f4f6; color:#9ca3af;'>-</span></b>"
                
            delta_val = round(delta, decimals)
            d_str = f"{abs(delta_val):.{decimals}f}"
            if is_pct: d_str += "%"
            
            if delta_val > 0: return f"<b>{val_str} <span class='delta-badge' style='background:#dcfce7; color:#16a34a;'>▲ {d_str}</span></b>"
            else: return f"<b>{val_str} <span class='delta-badge' style='background:#fee2e2; color:#dc2626;'>▼ {d_str}</span></b>"

        st.markdown("<h3 class='section-header'>🧪 Synthesis Loop & Major Vessels</h3>", unsafe_allow_html=True)
        v1, v2, v3, v4, v5 = st.columns(5)
        with v1:
            st.markdown(f"""
            <div class="v-card v-rx">
                <div class="v-title v-title-rx">⚗️ Reactor</div>
                <div class="v-row"><span>N/C (Ref: 3.11)</span>{html_val('Rx_NC', 2)}</div>
                <div class="v-row"><span>H/C (Ref: 0.52)</span>{html_val('Rx_HC', 2)}</div>
                <div class="v-row"><span>CO2 Conv (58%)</span>{html_val('CO2_Conv', 1, True)}</div>
                <div class="v-row"><span style="color:#059669; font-weight:bold;">Equilibrium Gap (Ref: &lt; 3.0%)</span>{html_val('Eq_Gap', 1, True)}</div>
                <div class="v-row"><span>Urea Conc(32.7%)</span>{html_val('Urea_Conc', 2, True)}</div>
            </div>
            """, unsafe_allow_html=True)
        with v2:
            st.markdown(f"""
            <div class="v-card v-st">
                <div class="v-title v-title-st">🌪️ Stripper</div>
                <div class="v-row"><span>Eff (Ref: 78%)</span>{html_val('Stripper_Eff', 1, True)}</div>
                <div class="v-row"><span>Stripper N/C (2.01)</span>{html_val('Stripper_NC', 2)}</div>
                <div class="v-row"><span>Ammonia</span>{html_val('Stripper_NH3', 2, True)}</div>
                <div class="v-row"><span>Urea Conc</span>{html_val('Stripper_Urea', 2, True)}</div>
            </div>
            """, unsafe_allow_html=True)
        with v3:
            st.markdown(f"""
            <div class="v-card v-hpd">
                <div class="v-title v-title-hpd">🌡️ HPD</div>
                <div class="v-row"><span>Eff (Ref: 65.4%)</span>{html_val('HPD_Eff', 1, True)}</div>
            </div>
            """, unsafe_allow_html=True)
        with v4:
            st.markdown(f"""
            <div class="v-card v-hpa">
                <div class="v-title v-title-hpa">💧 HPA</div>
                <div class="v-row"><span>N/C (Ref: 2.38)</span>{html_val('HPA_NC', 2)}</div>
                <div class="v-row"><span>H/C (Ref: 1.29)</span>{html_val('HPA_HC', 2)}</div>
            </div>
            """, unsafe_allow_html=True)
        with v5:
            st.markdown(f"""
            <div class="v-card v-lpa">
                <div class="v-title v-title-lpa">☁️ LPA</div>
                <div class="v-row"><span>N/C (Ref: 2.29)</span>{html_val('LPA_NC', 2)}</div>
                <div class="v-row"><span>H/C (Ref: 2.28)</span>{html_val('LPA_HC', 2)}</div>
            </div>
            """, unsafe_allow_html=True)

        # --- SECTION 3: TRENDS ---
        st.markdown("<h3 class='section-header' style='margin-top: 35px;'>📈 Plant Trends Analysis</h3>", unsafe_allow_html=True)
        
        trend_days = st.slider("Quick Lookback Window (Days)", min_value=3, max_value=30, value=7, step=1)
        trend_start = selected_date_dt - timedelta(days=trend_days - 1)
        st.caption(f"Showing standard operational trends from **{trend_start.strftime('%d %b %Y')}** to **{selected_date.strftime('%d %b %Y')}**")
        
        df_trend = df[(df['Date'] <= selected_date_dt) & (df['Date'] >= trend_start)]
        
        def add_ref(fig, val=None):
            date_str = selected_date.strftime('%Y-%m-%d')
            fig.add_vline(x=date_str, line_width=2, line_dash="dash", line_color="gray")
            if val is not None: fig.add_hline(y=val, line_dash="dot", line_color="red")
            fig.update_layout(margin=dict(t=40, b=20, l=10, r=10), height=300)
            return fig

        fig_combo = make_subplots(specs=[[{"secondary_y": True}]])
        fig_combo.add_trace(go.Scatter(x=df_trend['Date'], y=df_trend['Production'], name="Production (MT)", mode='lines+markers', line=dict(color='#2ca02c', width=3)), secondary_y=False)
        fig_combo.add_trace(go.Scatter(x=df_trend['Date'], y=df_trend['Load'], name="Plant Load (%)", mode='lines+markers', line=dict(color='#1f77b4', width=3, dash='dot')), secondary_y=True)
        fig_combo.update_layout(title_text="1. Production & Plant Load", margin=dict(t=40, b=20, l=10, r=10), height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig_combo.update_yaxes(title_text="Production (MT)", secondary_y=False)
        fig_combo.update_yaxes(title_text="Plant Load (%)", secondary_y=True)
        fig_combo.add_vline(x=selected_date.strftime('%Y-%m-%d'), line_width=2, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_combo, use_container_width=True, key="combo_prod_load")

        t1, t2 = st.columns(2)
        with t1:
            f2 = px.line(df_trend, x='Date', y='CO2_Conv', markers=True, title='2. Reactor CO2 Conversion Trend (%)', line_shape='spline')
            f2.update_traces(line_color='#9467bd') 
            f2.update_yaxes(range=[0, 100])
            st.plotly_chart(add_ref(f2, 58.0), use_container_width=True, key="t2")
            
            f4 = px.line(df_trend, x='Date', y='Stripper_Eff', markers=True, title='4. Stripper Efficiency Trend (%)', line_shape='spline')
            f4.update_traces(line_color='#d97706') 
            f4.update_yaxes(range=[0, 100])
            st.plotly_chart(add_ref(f4, 78.0), use_container_width=True, key="t4")
            
            f6 = px.line(df_trend, x='Date', y='Moisture', markers=True, title='6. Avg Moisture (Design: 0.3%)', line_shape='spline')
            st.plotly_chart(add_ref(f6, 0.3), use_container_width=True, key="t6")
            
            f8 = px.line(df_trend, x='Date', y='APS', markers=True, title='8. Avg APS Trend', line_shape='spline')
            st.plotly_chart(add_ref(f8), use_container_width=True, key="t8")

        with t2:
            f3 = px.line(df_trend, x='Date', y='Rx_NC', markers=True, title='3. Reactor N/C Ratio Trend (Design: 3.11)', line_shape='spline')
            st.plotly_chart(add_ref(f3, 3.11), use_container_width=True, key="t3")
            
            f5 = px.line(df_trend, x='Date', y='HPD_Eff', markers=True, title='5. HPD Efficiency Trend (%)', line_shape='spline')
            f5.update_traces(line_color='#059669') 
            f5.update_yaxes(range=[0, 100])
            st.plotly_chart(add_ref(f5, 65.4), use_container_width=True, key="t5")
            
            f7 = px.line(df_trend, x='Date', y='Biuret', markers=True, title='7. Avg Biuret (Design: 0.9%)', line_shape='spline')
            st.plotly_chart(add_ref(f7, 0.9), use_container_width=True, key="t7")

        # --- SECTION 4: CUSTOM TREND BUILDER & EXPORT ---
        st.markdown("<hr style='border:1px solid #1E3A8A; margin: 30px 0;'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section-header'>🛠️ Custom Trend & Data Export</h3>", unsafe_allow_html=True)
        st.caption("Select a custom time period and variables to plot them together and view their summary statistics.")
        
        c_ctrl1, c_ctrl2 = st.columns([1, 2])
        with c_ctrl1:
            min_date = df['Date'].min().date()
            max_date = df['Date'].max().date()
            
            default_end = selected_date_dt.date()
            if default_end > max_date: default_end = max_date
            
            default_start = default_end - timedelta(days=6)
            if default_start < min_date: default_start = min_date
            
            custom_dates = st.date_input(
                "Select Exact Time Period:",
                value=(default_start, default_end),
                min_value=min_date,
                max_value=max_date
            )
            
        with c_ctrl2:
            available_vars = [col for col in df.columns if col not in ['Date', 'Remarks']]
            selected_vars = st.multiselect("Select Variables:", available_vars, default=['Moisture', 'Biuret'])
        
        if len(custom_dates) == 2 and selected_vars:
            c_start, c_end = custom_dates
            mask_custom = (df['Date'].dt.date >= c_start) & (df['Date'].dt.date <= c_end)
            df_custom = df.loc[mask_custom]
            
            if not df_custom.empty:
                c_graph, c_stats = st.columns([3, 1])
                
                with c_graph:
                    fig_custom = px.line(df_custom, x='Date', y=selected_vars, markers=True, title="Custom Trend Analysis", line_shape='spline')
                    fig_custom.update_layout(height=400, margin=dict(t=40, b=20, l=10, r=10), legend_title_text='Variables')
                    st.plotly_chart(fig_custom, use_container_width=True, key="custom_chart")
                    
                with c_stats:
                    st.markdown("#### 📊 Period Summary")
                    summary_df = df_custom[selected_vars].agg(['mean', 'min', 'max']).T
                    summary_df.columns = ['Average', 'Minimum', 'Maximum']
                    
                    st.dataframe(summary_df.style.format("{:.2f}"), use_container_width=True)
                    
                    csv = df_custom[['Date'] + selected_vars].to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Custom CSV",
                        data=csv,
                        file_name=f"AGL_Custom_Data_{c_start}_to_{c_end}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.warning("No data found for this custom date range.")
        elif len(custom_dates) < 2:
            st.info("Please select an End Date for the custom time period.")

        # --- SECTION 5: AI & PREDICTIVE ANALYTICS ---
        st.markdown("<hr style='border:1px solid #1E3A8A; margin: 30px 0;'>", unsafe_allow_html=True)
        st.markdown("<h3 class='section-header'>🧠 AI Predictive Analytics & Automation</h3>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class="sim-panel">
            <h4 style="margin-top:0px; color:#334155;">🎛️ Real-Time Process Simulator</h4>
            <p style="font-size:13px; color:#64748b;">Adjust physical plant parameters below to simulate the immediate impact on product Quality (Biuret) and Cooling (Moisture).</p>
        </div>
        """, unsafe_allow_html=True)
        
        sim1, sim2, sim3, sim4 = st.columns(4)
        with sim1: win_open = st.slider("Vanes Opening (%)", min_value=0, max_value=100, value=20, step=5, help="16 sets, Max Area: 72m²")
        with sim2: fan_open = st.slider("ID Fan Louvers (%)", min_value=0, max_value=100, value=70, step=5, help="Induced Draft Fan Louver Control")
        with sim3: melt_temp = st.slider("Melt Temp (°C)", min_value=132.0, max_value=145.0, value=138.0, step=0.5, help="Temp of Urea melt going to Prilling Tower")
        with sim4: vac_abs = st.slider("Vacuum (mmHg Abs)", min_value=10.0, max_value=80.0, value=30.0, step=1.0, help="Absolute pressure of Final Concentrator")

        st.markdown("<br>", unsafe_allow_html=True)
        c_ai1, c_ai2 = st.columns([1, 1])
        
        with c_ai1:
            st.markdown("#### 🎯 Dynamic Biuret Predictor")
            st.caption("Predicts Biuret formation based on Historical Plant Load + Vacuum Distillation + Melt Temperature.")
            
            df_clean = df[(df['Load'] > 0) & (df['Biuret'] > 0)].dropna(subset=['Load', 'Biuret'])
            
            if len(df_clean) > 2:
                z = np.polyfit(df_clean['Load'], df_clean['Biuret'], 1)
                p = np.poly1d(z)
                current_load = get_val(daily_data, 'Load')
                base_pred_biuret = p(current_load)
                
                temp_biuret_penalty = (melt_temp - 138.0) * 0.015 
                vac_biuret_penalty = (vac_abs - 30.0) * 0.005
                simulated_biuret = base_pred_biuret + temp_biuret_penalty + vac_biuret_penalty
                
                fig_pred = go.Figure()
                fig_pred.add_trace(go.Scatter(x=df_clean['Load'], y=df_clean['Biuret'], mode='markers', name='Historical Data', marker=dict(size=8, color='#e2e8f0', opacity=0.6)))
                
                x_trend = np.linspace(df_clean['Load'].min(), df_clean['Load'].max(), 10)
                fig_pred.add_trace(go.Scatter(x=x_trend, y=p(x_trend), mode='lines', name='Baseline Trend', line=dict(color='#94a3b8', dash='dash')))
                fig_pred.add_trace(go.Scatter(x=[current_load], y=[simulated_biuret], mode='markers', name='Simulated State', marker=dict(size=14, color='red', symbol='star')))
                
                fig_pred.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250, xaxis_title="Plant Load (%)", yaxis_title="Biuret (%)", showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_pred, use_container_width=True, key="biuret_pred")
                
                if simulated_biuret > 0.9: st.error(f"⚠️ **Warning:** Predicted Biuret is **{simulated_biuret:.2f}%**. To reduce it, try improving concentrator vacuum below {vac_abs} mmHg Abs or dropping melt temp.")
                else: st.success(f"✅ **Safe Quality:** Predicted Biuret is **{simulated_biuret:.2f}%**.")
            else:
                st.warning("Not enough valid historical data to generate prediction.")
                
        with c_ai2:
            st.markdown("#### 🌧️ Prilling Cooling Predictor")
            st.caption("Estimates Moisture deviation based on real-time ambient weather, Aerodynamic Draft, and Melt Temp.")
            
            temp, hum = get_daudkhel_weather()
            
            if temp is not None and hum is not None:
                st.markdown(f"""
                <div style='background:#f0f9ff; padding:15px; border-radius:8px; border-left:4px solid #0284c7; margin-bottom:15px;'>
                    <b>Live Daudkhel Weather:</b><br>
                    🌡️ Temperature: <b>{temp}°C</b> &nbsp; | &nbsp; 💧 Humidity: <b>{hum}%</b>
                </div>
                """, unsafe_allow_html=True)
                
                base_moist = 0.25
                weather_penalty = max(0, (temp - 25) * 0.002) + max(0, (hum - 40) * 0.0015)
                load_penalty = max(0, (get_val(daily_data, 'Load') - 100) * 0.001)
                draft_penalty = max(0, (100 - fan_open) * 0.0005) + max(0, (100 - win_open) * 0.0008)
                thermal_penalty = max(0, (melt_temp - 138.0) * 0.003)
                vacuum_penalty = max(0, (vac_abs - 30.0) * 0.0015)
                
                est_moisture = base_moist + weather_penalty + load_penalty + draft_penalty + thermal_penalty + vacuum_penalty
                
                if est_moisture > 0.3: st.error(f"⚠️ **Warning:** Insufficient cooling for current thermodynamics. Estimated moisture: **{est_moisture:.3f}%** (Exceeds 0.3% Design). Increase Draft Fan or reduce Melt Temp.")
                elif est_moisture > 0.28: st.warning(f"⚡ **Alert:** Cooling margin is shrinking. Estimated moisture: **{est_moisture:.3f}%**. Monitor crystallization at EL+82500.")
                else: st.success(f"✅ **Optimal:** Excellent draft and thermal conditions. Estimated moisture: **{est_moisture:.3f}%**.")
            else:
                st.error("Failed to connect to weather API. Please check server outbound rules.")

        # --- FEATURE: VMG UREA INSPIRED CARBAMATE CRYSTALLIZATION PREDICTOR ---
        st.markdown("<hr style='border:1px dashed #e2e8f0; margin: 30px 0;'>", unsafe_allow_html=True)
        st.markdown("#### ❄️ HP Carbamate Crystallization Predictor (VMG-Inspired)")
        st.caption("Calculate the safe operating temperature for Carbamate pumps. Switch tabs to load today's actual Lab Analysis data or use the Custom Calculator.")
        
        def render_vmg_tab(default_nh3, default_co2, default_h2o, key_prefix):
            c_carb1, c_carb2 = st.columns([1, 2])
            with c_carb1:
                carb_nh3 = st.number_input("NH3 (wt%)", value=float(default_nh3), step=0.5, key=f"{key_prefix}_nh3")
                carb_co2 = st.number_input("CO2 (wt%)", value=float(default_co2), step=0.5, key=f"{key_prefix}_co2")
                carb_h2o = st.number_input("H2O + Urea (wt%)", value=float(default_h2o), step=0.5, key=f"{key_prefix}_h2o", help="Balance mostly consists of Water with trace solvent Urea.")
                
            total_wt = carb_nh3 + carb_co2 + carb_h2o
            if total_wt == 0: total_wt = 1 
            
            n_nh3 = (carb_nh3 / total_wt) * 100
            n_co2 = (carb_co2 / total_wt) * 100
            n_h2o = (carb_h2o / total_wt) * 100
            
            nc_ratio = (n_nh3 / 17.031) / (n_co2 / 44.01) if n_co2 > 0 else 0
            cryst_temp = 105.0 + (20.0 - n_h2o) * 2.8 + abs(nc_ratio - 2.3)**2 * 15.0
                
            with c_carb2:
                st.markdown(f"""
                <div style='background:linear-gradient(135deg, #f0f9ff, #e0f2fe); padding:20px; border-radius:8px; border-left:4px solid #0284c7; height: 100%; display: flex; flex-direction: column; justify-content: center;'>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 10px;'>
                        <span style='color: #475569; font-size: 14px;'>Normalized Composition:</span>
                        <b style='color: #0f172a;'>NH₃: {n_nh3:.1f}% | CO₂: {n_co2:.1f}% | Balance: {n_h2o:.1f}%</b>
                    </div>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 10px;'>
                        <span style='color: #475569; font-size: 14px;'>Molar N/C Ratio:</span>
                        <b style='color: #0f172a;'>{nc_ratio:.2f}</b>
                    </div>
                    <div style='display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #cbd5e1; padding-top: 10px;'>
                        <span style='color: #0369a1; font-size: 18px; font-weight: bold;'>Predicted Crystallization Temp:</span>
                        <span style='color: #be123c; font-size: 24px; font-weight: bold;'>{cryst_temp:.1f} °C</span>
                    </div>
                    <p style='font-size: 12px; color: #64748b; margin-top: 10px; margin-bottom: 0;'>
                        <i>*If the HP Carbamate Pump operating temperature drops below <b>{cryst_temp:.1f} °C</b>, rapid solidification will occur causing severe pump damage. Decreasing water improves conversion efficiency but raises this risk limit.</i>
                    </p>
                </div>
                """, unsafe_allow_html=True)

        tab_hpa, tab_lpa, tab_custom = st.tabs(["🧪 HPA Profile (Lab Data)", "🧪 LPA Profile (Lab Data)", "🎛️ Custom Calculator"])
        
        with tab_hpa:
            hpa_nh3 = get_val(daily_data, 'HPA_NH3')
            hpa_co2 = get_val(daily_data, 'HPA_CO2')
            if hpa_nh3 > 0 and hpa_co2 > 0:
                hpa_h2o = max(0.0, 100.0 - hpa_nh3 - hpa_co2)
                st.info(f"Loaded actual HPA lab analysis for {selected_date.strftime('%d %b %Y')}. You can adjust these values to see what happens.")
                render_vmg_tab(hpa_nh3, hpa_co2, hpa_h2o, "hpa")
            else:
                st.warning(f"No HPA Lab Data recorded for {selected_date.strftime('%d %b %Y')}. Showing default values.")
                render_vmg_tab(42.0, 38.0, 20.0, "hpa_default")

        with tab_lpa:
            lpa_nh3 = get_val(daily_data, 'LPA_NH3')
            lpa_co2 = get_val(daily_data, 'LPA_CO2')
            if lpa_nh3 > 0 and lpa_co2 > 0:
                lpa_h2o = max(0.0, 100.0 - lpa_nh3 - lpa_co2)
                st.info(f"Loaded actual LPA lab analysis for {selected_date.strftime('%d %b %Y')}. You can adjust these values to see what happens.")
                render_vmg_tab(lpa_nh3, lpa_co2, lpa_h2o, "lpa")
            else:
                st.warning(f"No LPA Lab Data recorded for {selected_date.strftime('%d %b %Y')}. Showing default values.")
                render_vmg_tab(38.0, 36.0, 26.0, "lpa_default")
                
        with tab_custom:
            st.info("Independent theoretical calculator.")
            render_vmg_tab(42.0, 38.0, 20.0, "custom")

    else:
        st.info(f"No data found for {selected_date.strftime('%d %b %Y')}. Please select a date from the file history.")

# -- FOOTER SECTION --
st.markdown(f"""
    <div class="footer">
        Developed by <a href="https://www.linkedin.com/in/wikitunio" target="_blank">Waqar Ahmed Tunio</a> with Ai<br>
        Email: <a href="mailto:ahmed.waqar@pafl.com.pk">ahmed.waqar@pafl.com.pk</a>
    </div>
    """, unsafe_allow_html=True)
