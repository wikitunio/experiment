import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import datetime
import requests
import io
import base64
import os

# -- PAGE CONFIGURATION --
st.set_page_config(page_title="AgriTech UREA Dashboard", layout="wide", initial_sidebar_state="expanded")

# -- IMAGE ENCODER --
@st.cache_data
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

img_b64 = get_base64_of_bin_file("IMG_9291.JPG")
bg_css = f'background-image: linear-gradient(rgba(0, 0, 50, 0.75), rgba(0, 0, 50, 0.75)), url("data:image/jpeg;base64,{img_b64}");' if img_b64 else 'background-color: #1E3A8A;'

# -- ULTRA-COMPACT CUSTOM CSS --
st.markdown(f"""
    <style>
    .hero-container {{
        {bg_css}
        background-size: cover;
        background-position: center;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }}
    .hero-container h1 {{ font-size: 26px; margin-bottom: 0px; margin-top: 0px; color: white !important; font-weight: bold; }}
    .hero-container p {{ font-size: 14px; opacity: 0.9; margin-bottom: 0px; margin-top: 2px; }}
    
    div[data-testid="metric-container"] {{
        background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 8px rgba(0,0,0,0.04);
    }}
    
    .section-header {{ color: #1E3A8A; margin-top: 15px; margin-bottom: 10px; font-weight: 700; font-size: 20px; border-bottom: 2px solid #1E3A8A; padding-bottom: 4px; }}
    
    /* Sleek Horizontal Vessel Cards */
    .v-card {{ border-radius: 8px; padding: 12px; box-shadow: 2px 4px 10px rgba(0,0,0,0.06); min-height: 200px; border-top: 4px solid; display: flex; flex-direction: column; }}
    .v-rx {{ background: linear-gradient(135deg, #ffffff, #f1f5f9); border-top-color: #1E3A8A; }}
    .v-st {{ background: linear-gradient(135deg, #ffffff, #fffbeb); border-top-color: #d97706; }}
    .v-hpd {{ background: linear-gradient(135deg, #ffffff, #ecfdf5); border-top-color: #059669; }}
    .v-hpa {{ background: linear-gradient(135deg, #ffffff, #f0f9ff); border-top-color: #0284c7; }}
    .v-lpa {{ background: linear-gradient(135deg, #ffffff, #f0fdfa); border-top-color: #0d9488; }}
    
    .v-title {{ font-size: 14px; font-weight: bold; margin-bottom: 10px; text-align: center; padding-bottom: 6px; border-bottom: 1px solid rgba(0,0,0,0.1); }}
    .v-title-rx {{ color: #1E3A8A; }} .v-title-st {{ color: #d97706; }} .v-title-hpd {{ color: #059669; }} .v-title-hpa {{ color: #0284c7; }} .v-title-lpa {{ color: #0d9488; }}
    
    .v-row {{ display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0; border-bottom: 1px dashed rgba(0,0,0,0.05); }}
    .v-row:last-child {{ border-bottom: none; }}
    .v-row span {{ color: #555; }}
    .v-row b {{ color: #111; }}
    
    .footer {{ text-align: center; padding: 20px 0px; color: #666666; font-size: 13px; border-top: 1px solid #e0e0e0; margin-top: 30px; }}
    .footer a {{ color: #1E3A8A; text-decoration: none; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="hero-container">
        <h1>🏭 UREA Plant Daily Operations</h1>
        <p>AgriTech Limited | Iskandarabad, Daudkhel</p>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=10)
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

    # 1. Load PQ Trends
    try:
        df_pq_raw = pd.read_excel(excel_data, sheet_name="PQ Trends", skiprows=1)
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

    # 2. Load Efficiencies (Added Col C for NH3 Conv and Col H for Stripper N/C)
    excel_data.seek(0)
    try:
        df_eff_raw = pd.read_excel(excel_data, sheet_name="Efficiencies", skiprows=2)
        df_eff = pd.DataFrame()
        df_eff['Date'] = pd.to_datetime(df_eff_raw.iloc[:, 0], errors='coerce')
        df_eff['CO2_Conv'] = pd.to_numeric(df_eff_raw.iloc[:, 1], errors='coerce').fillna(0)
        df_eff['NH3_Conv'] = pd.to_numeric(df_eff_raw.iloc[:, 2], errors='coerce').fillna(0)  # Column C
        df_eff['Rx_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 3], errors='coerce').fillna(0)
        df_eff['Rx_HC'] = pd.to_numeric(df_eff_raw.iloc[:, 4], errors='coerce').fillna(0)
        df_eff['Stripper_Eff'] = pd.to_numeric(df_eff_raw.iloc[:, 6], errors='coerce').fillna(0)
        df_eff['Stripper_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 7], errors='coerce').fillna(0) # Column H
        df_eff['HPD_Eff'] = pd.to_numeric(df_eff_raw.iloc[:, 9], errors='coerce').fillna(0)
        df_eff['HPA_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 12], errors='coerce').fillna(0)
        df_eff['HPA_HC'] = pd.to_numeric(df_eff_raw.iloc[:, 13], errors='coerce').fillna(0)
        df_eff['LPA_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 14], errors='coerce').fillna(0)
        df_eff['LPA_HC'] = pd.to_numeric(df_eff_raw.iloc[:, 15], errors='coerce').fillna(0)
        df_eff = df_eff.dropna(subset=['Date'])
    except: return pd.DataFrame(), "Check Efficiencies Sheet Format"

    # 3. Load Lab Analysis Sheet (Added for Urea Conc in Col E)
    excel_data.seek(0)
    try:
        # Assuming header starts on row 2 (skiprows=1). Adjust if needed.
        df_lab_raw = pd.read_excel(excel_data, sheet_name="Lab Analysis", skiprows=1)
        df_lab = pd.DataFrame()
        df_lab['Date'] = pd.to_datetime(df_lab_raw.iloc[:, 0], errors='coerce')
        df_lab['Urea_Conc'] = pd.to_numeric(df_lab_raw.iloc[:, 4], errors='coerce').fillna(0) # Column E
        df_lab = df_lab.dropna(subset=['Date'])
    except Exception as e:
        # If sheet is missing or named differently, don't crash the whole app
        df_lab = pd.DataFrame(columns=['Date', 'Urea_Conc'])

    # Merge all three dataframes
    df_master = pd.merge(df_pq, df_eff, on='Date', how='left')
    if not df_lab.empty:
        df_master = pd.merge(df_master, df_lab, on='Date', how='left')
    else:
        df_master['Urea_Conc'] = 0.0

    agg_funcs = {
        'Production': 'sum', 'Load': 'mean', 'Moisture': 'mean', 'Biuret': 'mean',
        'APS': 'mean', 'CO2_Conv': 'mean', 'NH3_Conv': 'mean', 'Rx_NC': 'mean', 'Rx_HC': 'mean',
        'Stripper_Eff': 'mean', 'Stripper_NC': 'mean', 'HPD_Eff': 'mean', 'HPA_NC': 'mean', 'HPA_HC': 'mean',
        'LPA_NC': 'mean', 'LPA_HC': 'mean', 'Urea_Conc': 'mean', 'Remarks': 'first'
    }
    df_daily = df_master.groupby('Date').agg(agg_funcs).reset_index()
    
    # Auto-convert decimals to percentages for specific columns
    for col in ['CO2_Conv', 'NH3_Conv', 'Stripper_Eff', 'HPD_Eff', 'Urea_Conc']:
        if col in df_daily.columns:
            df_daily[col] = df_daily[col].apply(lambda x: x * 100 if 0 < x <= 1.5 else x)
            
    return df_daily.sort_values('Date'), ""

df, err_msg = load_data()

if err_msg:
    st.error(f"⚠️ {err_msg}")
elif not df.empty:
    st.sidebar.header("📅 Dashboard Controls")
    
    yesterday = datetime.date.today() - timedelta(days=1)
    selected_date = st.sidebar.date_input("Select Shift Date", yesterday)
    selected_date_dt = pd.to_datetime(selected_date)
    
    daily_data = df[df['Date'] == selected_date_dt]
    yesterday_data = df[df['Date'] == (selected_date_dt - timedelta(days=1))]
    
    if not daily_data.empty:
        def get_val(data, col): return float(data[col].values[0]) if not data.empty and col in data.columns else 0.0
        def get_delta(col): return get_val(daily_data, col) - get_val(yesterday_data, col)

        remarks = daily_data['Remarks'].values[0]
        if str(remarks) != 'nan' and str(remarks).strip() and str(remarks).strip() != '0':
            st.info(f"📝 **Shift Log:** {remarks}")

        # --- SECTION 1: PRODUCTION & QUALITY ---
        st.markdown(f"<h3 class='section-header'>📊 Production & Quality ({selected_date.strftime('%d %b %Y')})</h3>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Production", f"{get_val(daily_data, 'Production'):,.0f} MT", f"{get_delta('Production'):.0f} MT")
        c2.metric("Plant Load", f"{get_val(daily_data, 'Load'):.1f} %", f"{get_delta('Load'):.1f} %")
        c3.metric("Moisture", f"{get_val(daily_data, 'Moisture'):.3f} %", f"{get_delta('Moisture'):.3f} %", delta_color="inverse")
        c4.metric("Biuret", f"{get_val(daily_data, 'Biuret'):.2f} %", f"{get_delta('Biuret'):.2f} %", delta_color="inverse")
        c5.metric("APS", f"{get_val(daily_data, 'APS'):.2f} mm", f"{get_delta('APS'):.2f} mm")

        # --- SECTION 2: SYNTHESIS LOOP & VESSELS ---
        st.markdown("<h3 class='section-header'>🧪 Synthesis Loop & Major Vessels</h3>", unsafe_allow_html=True)
        
        v1, v2, v3, v4, v5 = st.columns(5)
        
        with v1:
            st.markdown(f"""
            <div class="v-card v-rx">
                <div class="v-title v-title-rx">⚗️ Reactor</div>
                <div class="v-row"><span>N/C (3.11)</span><b>{get_val(daily_data, 'Rx_NC'):.2f}</b></div>
                <div class="v-row"><span>H/C (0.52)</span><b>{get_val(daily_data, 'Rx_HC'):.2f}</b></div>
                <div class="v-row"><span>CO2 Conv (58%)</span><b>{get_val(daily_data, 'CO2_Conv'):.1f}%</b></div>
                <div class="v-row"><span>NH3 Conv (37%)</span><b>{get_val(daily_data, 'NH3_Conv'):.1f}%</b></div>
                <div class="v-row"><span>Urea Conc(32.74%)</span><b>{get_val(daily_data, 'Urea_Conc'):.2f}%</b></div>
            </div>
            """, unsafe_allow_html=True)
            
        with v2:
            st.markdown(f"""
            <div class="v-card v-st">
                <div class="v-title v-title-st">🌪️ Stripper</div>
                <div class="v-row"><span>Eff (78%)</span><b>{get_val(daily_data, 'Stripper_Eff'):.1f}%</b></div>
                <div class="v-row"><span>Stripper N/C (2.01)</span><b>{get_val(daily_data, 'Stripper_NC'):.2f}</b></div>
            </div>
            """, unsafe_allow_html=True)

        with v3:
            st.markdown(f"""
            <div class="v-card v-hpd">
                <div class="v-title v-title-hpd">🌡️ HPD</div>
                <div class="v-row"><span>Eff (65.4%)</span><b>{get_val(daily_data, 'HPD_Eff'):.1f}%</b></div>
            </div>
            """, unsafe_allow_html=True)
            
        with v4:
            st.markdown(f"""
            <div class="v-card v-hpa">
                <div class="v-title v-title-hpa">💧 HPA</div>
                <div class="v-row"><span>N/C (2.38)</span><b>{get_val(daily_data, 'HPA_NC'):.2f}</b></div>
                <div class="v-row"><span>H/C (1.29)</span><b>{get_val(daily_data, 'HPA_HC'):.2f}</b></div>
            </div>
            """, unsafe_allow_html=True)
            
        with v5:
            st.markdown(f"""
            <div class="v-card v-lpa">
                <div class="v-title v-title-lpa">☁️ LPA</div>
                <div class="v-row"><span>N/C (2.29)</span><b>{get_val(daily_data, 'LPA_NC'):.2f}</b></div>
                <div class="v-row"><span>H/C (2.28)</span><b>{get_val(daily_data, 'LPA_HC'):.2f}</b></div>
            </div>
            """, unsafe_allow_html=True)

        # --- SECTION 3: TRENDS ---
        week_start = selected_date_dt - timedelta(days=6)
        st.markdown(f"<h3 class='section-header'>📈 One Week Trends ({week_start.strftime('%d %b')} to {selected_date.strftime('%d %b %Y')})</h3>", unsafe_allow_html=True)
        df_7d = df[(df['Date'] <= selected_date_dt) & (df['Date'] >= week_start)]
        
        def add_ref(fig, val=None):
            date_str = selected_date.strftime('%Y-%m-%d')
            fig.add_vline(x=date_str, line_width=2, line_dash="dash", line_color="gray")
            if val is not None: fig.add_hline(y=val, line_dash="dot", line_color="red")
            fig.update_layout(margin=dict(t=40, b=20, l=10, r=10), height=300)
            return fig

        t1, t2 = st.columns(2)
        
        with t1:
            f1 = px.line(df_7d, x='Date', y='Production', markers=True, title='1. Daily Production Trend (MT)', line_shape='spline')
            f1.update_traces(line_color='#2ca02c') 
            st.plotly_chart(add_ref(f1), use_container_width=True, key="t1")
        with t2:
            f2 = px.line(df_7d, x='Date', y='CO2_Conv', markers=True, title='2. Reactor CO2 Conversion Trend (%)', line_shape='spline')
            f2.update_traces(line_color='#9467bd') 
            f2.update_yaxes(range=[0, 100])
            st.plotly_chart(add_ref(f2, 58.0), use_container_width=True, key="t2")
            
        with t1:
            f3 = px.line(df_7d, x='Date', y='Rx_NC', markers=True, title='3. Reactor N/C Ratio Trend (Design: 3.11)', line_shape='spline')
            st.plotly_chart(add_ref(f3, 3.11), use_container_width=True, key="t3")
        with t2:
            f4 = px.line(df_7d, x='Date', y='Stripper_Eff', markers=True, title='4. Stripper Efficiency Trend (%)', line_shape='spline')
            f4.update_traces(line_color='#d97706') 
            f4.update_yaxes(range=[0, 100])
            st.plotly_chart(add_ref(f4, 78.0), use_container_width=True, key="t4")
            
        with t1:
            f5 = px.line(df_7d, x='Date', y='Moisture', markers=True, title='5. Avg Moisture (Design: 0.3%)', line_shape='spline')
            st.plotly_chart(add_ref(f5, 0.3), use_container_width=True, key="t5")
        with t2:
            f6 = px.line(df_7d, x='Date', y='Biuret', markers=True, title='6. Avg Biuret (Design: 0.9%)', line_shape='spline')
            st.plotly_chart(add_ref(f6, 0.9), use_container_width=True, key="t6")
            
        with t1:
            f7 = px.line(df_7d, x='Date', y='APS', markers=True, title='7. Avg APS Trend', line_shape='spline')
            st.plotly_chart(add_ref(f7), use_container_width=True, key="t7")
        with t2:
            f8 = px.line(df_7d, x='Date', y='HPD_Eff', markers=True, title='8. HPD Efficiency Trend (%)', line_shape='spline')
            f8.update_traces(line_color='#059669') 
            f8.update_yaxes(range=[0, 100])
            st.plotly_chart(add_ref(f8, 65.4), use_container_width=True, key="t8")

    else:
        st.info(f"No data found for {selected_date.strftime('%d %b %Y')}. Please select a date from the file history.")

# -- FOOTER SECTION --
st.markdown(f"""
    <div class="footer">
        Developed by <a href="https://www.linkedin.com/in/wikitunio" target="_blank">Waqar Ahmed Tunio</a> with Ai<br>
        Email: <a href="mailto:ahmed.waqar@pafl.com.pk">ahmed.waqar@pafl.com.pk</a>
    </div>
    """, unsafe_allow_html=True)
