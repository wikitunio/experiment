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

# -- THE SPEED FIX: LOAD IMAGE VIA URL INSTEAD OF BASE64 --
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
                <div class="v-row"><span style="color:#059669; font-weight:bold;">Eq Gap (Ref: &lt; 3.0%)</span>{html_val('Eq_Gap', 1, True)}</div>
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
                <div class="v-row"><span>N/C (Ref: 2.38)
