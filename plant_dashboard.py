import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import datetime
import requests
import io

# -- PAGE CONFIGURATION --
st.set_page_config(page_title="AgriTech UREA Dashboard", layout="wide", initial_sidebar_state="expanded")

# -- BEAUTIFUL CUSTOM CSS --
st.markdown("""
    <style>
    .hero-container {
        background-image: linear-gradient(rgba(0, 0, 50, 0.6), rgba(0, 0, 50, 0.6)), url("app/static/IMG_9291.JPG");
        background-size: cover;
        background-position: center;
        padding: 70px 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
    }
    .hero-container h1 { font-size: 40px; margin-bottom: 5px; color: white !important; }
    .hero-container p { font-size: 18px; opacity: 0.9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .section-header { color: #1E3A8A; margin-top: 35px; margin-bottom: 15px; font-weight: 700; border-bottom: 2px solid #1E3A8A; padding-bottom: 8px;}
    .footer { text-align: center; padding: 40px 0px; color: #666666; font-size: 14px; border-top: 1px solid #e0e0e0; margin-top: 50px; }
    .footer a { color: #1E3A8A; text-decoration: none; font-weight: bold; }
    
    /* CSS for Graphical Equipment Vessels */
    .vessel-reactor {
        background: #e0e5ec; border-radius: 30px 30px 10px 10px; border: 4px solid #1E3A8A;
        padding: 20px; box-shadow: inset 15px 0 20px rgba(0,0,0,0.08); height: 100%;
    }
    .vessel-stripper {
        background: #e0e5ec; border-radius: 10px 10px 30px 30px; border: 4px solid #d97706;
        padding: 20px; box-shadow: inset -15px 0 20px rgba(0,0,0,0.08); height: 100%;
    }
    .vessel-hpd {
        background: #e0e5ec; border-radius: 15px; border: 4px solid #059669;
        padding: 20px; box-shadow: inset 10px 0 15px rgba(0,0,0,0.08); height: 100%;
    }
    .vessel-hpa {
        background: #e0e5ec; border-radius: 20px 20px 5px 5px; border: 4px solid #0284c7;
        padding: 20px; box-shadow: inset 10px 0 15px rgba(0,0,0,0.08); height: 100%;
    }
    .vessel-lpa {
        background: #e0e5ec; border-radius: 20px 20px 5px 5px; border: 4px solid #0d9488;
        padding: 20px; box-shadow: inset 10px 0 15px rgba(0,0,0,0.08); height: 100%;
    }
    
    .vessel-header-rx { background: #1E3A8A; color: white; text-align: center; font-weight: bold; padding: 8px; border-radius: 5px; margin-bottom: 15px; }
    .vessel-header-st { background: #d97706; color: white; text-align: center; font-weight: bold; padding: 8px; border-radius: 5px; margin-bottom: 15px; }
    .vessel-header-hpd { background: #059669; color: white; text-align: center; font-weight: bold; padding: 8px; border-radius: 5px; margin-bottom: 15px; }
    .vessel-header-hpa { background: #0284c7; color: white; text-align: center; font-weight: bold; padding: 8px; border-radius: 5px; margin-bottom: 15px; }
    .vessel-header-lpa { background: #0d9488; color: white; text-align: center; font-weight: bold; padding: 8px; border-radius: 5px; margin-bottom: 15px; }
    .gauge-combo-title { text-align: center; font-size: 16px; font-weight: bold; color: #1E3A8A; margin-bottom: 0px; padding-top: 5px; }
    
    .vessel-row { display: flex; justify-content: space-between; border-bottom: 1px dashed #b0b0b0; padding: 6px 0; font-size: 15px; }
    .vessel-row:last-child { border-bottom: none; }
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

    excel_data.seek(0)
    try:
        df_eff_raw = pd.read_excel(excel_data, sheet_name="Efficiencies", skiprows=2)
        df_eff = pd.DataFrame()
        df_eff['Date'] = pd.to_datetime(df_eff_raw.iloc[:, 0], errors='coerce')
        df_eff['CO2_Conv'] = pd.to_numeric(df_eff_raw.iloc[:, 1], errors='coerce').fillna(0)
        df_eff['Rx_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 3], errors='coerce').fillna(0)
        df_eff['Rx_HC'] = pd.to_numeric(df_eff_raw.iloc[:, 4], errors='coerce').fillna(0)
        df_eff['Stripper_Eff'] = pd.to_numeric(df_eff_raw.iloc[:, 6], errors='coerce').fillna(0)
        df_eff['HPD_Eff'] = pd.to_numeric(df_eff_raw.iloc[:, 9], errors='coerce').fillna(0)
        df_eff['HPA_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 12], errors='coerce').fillna(0)
        df_eff['HPA_HC'] = pd.to_numeric(df_eff_raw.iloc[:, 13], errors='coerce').fillna(0)
        df_eff['LPA_NC'] = pd.to_numeric(df_eff_raw.iloc[:, 14], errors='coerce').fillna(0)
        df_eff['LPA_HC'] = pd.to_numeric(df_eff_raw.iloc[:, 15], errors='coerce').fillna(0)
        df_eff = df_eff.dropna(subset=['Date'])
    except: return pd.DataFrame(), "Check Efficiencies Sheet Format"

    df_master = pd.merge(df_pq, df_eff, on='Date', how='left')
    agg_funcs = {
        'Production': 'sum', 'Load': 'mean', 'Moisture': 'mean', 'Biuret': 'mean',
        'APS': 'mean', 'CO2_Conv': 'mean', 'Rx_NC': 'mean', 'Rx_HC': 'mean',
        'Stripper_Eff': 'mean', 'HPD_Eff': 'mean', 'HPA_NC': 'mean', 'HPA_HC': 'mean',
        'LPA_NC': 'mean', 'LPA_HC': 'mean', 'Remarks': 'first'
    }
    df_daily = df_master.groupby('Date').agg(agg_funcs).reset_index()
    
    # Convert Decimals to Percentages
    for col in ['CO2_Conv', 'Stripper_Eff', 'HPD_Eff']:
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
        def get_val(data, col): return float(data[col].values[0]) if not data.empty else 0.0
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

        # --- SECTION 2: GRAPHICAL VESSELS ---
        st.markdown("<h3 class='section-header'>🧪 Synthesis Loop & Major Vessels</h3>", unsafe_allow_html=True)
        
        # Row 1: Reactor, Stripper, HPD
        v1, v2, v3 = st.columns([1, 1, 1])
        
        with v1:
            st.markdown(f"""
            <div class="vessel-reactor">
                <div class="vessel-header-rx">Urea Reactor</div>
                <div class="vessel-row"><span>Reactor N/C (Ref: 3.11)</span><b>{get_val(daily_data, 'Rx_NC'):.2f}</b></div>
                <div class="vessel-row"><span>Reactor H/C</span><b>{get_val(daily_data, 'Rx_HC'):.2f}</b></div>
                <div class="vessel-row"><span>CO2 Conversion (Ref: 58%)</span><b>{get_val(daily_data, 'CO2_Conv'):.1f}%</b></div>
                <div class="vessel-row"><span>NH3 Conversion</span><b style="color:#d9534f;">N/A</b></div>
                <div class="vessel-row"><span>Urea Concentration</span><b style="color:#d9534f;">N/A</b></div>
            </div>
            """, unsafe_allow_html=True)
            
        with v2:
            st.markdown(f"""
            <div class="vessel-stripper">
                <div class="vessel-header-st">Urea Stripper</div>
                <div class="vessel-row"><span>Efficiency (Ref: 78%)</span><b>{get_val(daily_data, 'Stripper_Eff'):.1f}%</b></div>
                <div class="vessel-row"><span>Stripper N/C</span><b style="color:#d9534f;">N/A</b></div>
            </div>
            """, unsafe_allow_html=True)

        with v3:
            st.markdown(f"""
            <div class="vessel-hpd">
                <div class="vessel-header-hpd">High Pressure Decomposer (HPD)</div>
                <div class="vessel-row"><span>Efficiency (Ref: 65.4%)</span><b>{get_val(daily_data, 'HPD_Eff'):.1f}%</b></div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 2: HPA, LPA, and the New Combo Gauge!
        v4, v5, v6 = st.columns([1, 1, 1])
        with v4:
            st.markdown(f"""
            <div class="vessel-hpa">
                <div class="vessel-header-hpa">High Pressure Absorber (HPA)</div>
                <div class="vessel-row"><span>HPA N/C (Design: 2.38)</span><b>{get_val(daily_data, 'HPA_NC'):.2f}</b></div>
                <div class="vessel-row"><span>HPA H/C (Design: 1.289)</span><b>{get_val(daily_data, 'HPA_HC'):.2f}</b></div>
            </div>
            """, unsafe_allow_html=True)
        with v5:
            st.markdown(f"""
            <div class="vessel-lpa">
                <div class="vessel-header-lpa">Low Pressure Absorber (LPA)</div>
                <div class="vessel-row"><span>LPA N/C (Design: 2.29)</span><b>{get_val(daily_data, 'LPA_NC'):.2f}</b></div>
                <div class="vessel-row"><span>LPA H/C (Design: 2.28)</span><b>{get_val(daily_data, 'LPA_HC'):.2f}</b></div>
            </div>
            """, unsafe_allow_html=True)
            
        with v6:
            # THE FIX: Dual Gauge inside the synthesis loop section!
            st.markdown("<div class='gauge-combo-title'>Equipment Efficiencies</div>", unsafe_allow_html=True)
            fig_combo = go.Figure()
            # Stripper (Left side)
            fig_combo.add_trace(go.Indicator(
                mode="gauge+number", value=get_val(daily_data, 'Stripper_Eff'),
                title={'text': "Stripper", 'font': {'size': 14, 'color': '#666'}},
                number={'suffix': "%", 'font': {'size': 20, 'color': '#1E3A8A'}},
                domain={'x': [0, 0.45], 'y': [0, 1]},
                gauge={'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': "#d97706"}, 'bgcolor': "#e0e0e0", 'borderwidth': 0}
            ))
            # HPD (Right side)
            fig_combo.add_trace(go.Indicator(
                mode="gauge+number", value=get_val(daily_data, 'HPD_Eff'),
                title={'text': "HPD", 'font': {'size': 14, 'color': '#666'}},
                number={'suffix': "%", 'font': {'size': 20, 'color': '#1E3A8A'}},
                domain={'x': [0.55, 1], 'y': [0, 1]},
                gauge={'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': "#059669"}, 'bgcolor': "#e0e0e0", 'borderwidth': 0}
            ))
            fig_combo.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_combo, use_container_width=True, key="combo_gauge")

        # --- SECTION 3: TRENDS ---
        week_start = selected_date_dt - timedelta(days=6)
        st.markdown(f"<h3 class='section-header'>📈 One Week Trends ({week_start.strftime('%d %b')} to {selected_date.strftime('%d %b %Y')})</h3>", unsafe_allow_html=True)
        df_7d = df[(df['Date'] <= selected_date_dt) & (df['Date'] >= week_start)]
        
        def add_ref(fig, val=None):
            date_str = selected_date.strftime('%Y-%m-%d')
            fig.add_vline(x=date_str, line_width=2, line_dash="dash", line_color="gray")
            if val: fig.add_hline(y=val, line_dash="dot", line_color="red")
            return fig

        # THE FIX: Complete graph reordering to match your exact request
        t1, t2 = st.columns(2)
        
        # Row 1 of Graphs
        with t1:
            f1 = px.line(df_7d, x='Date', y='Production', markers=True, title='1. Daily Production Trend (MT)', line_shape='spline')
            f1.update_traces(line_color='#2ca02c') 
            st.plotly_chart(add_ref(f1), use_container_width=True, key="t1")
        with t2:
            f2 = px.line(df_7d, x='Date', y='CO2_Conv', markers=True, title='2. Reactor CO2 Conversion Trend (%)', line_shape='spline')
            f2.update_traces(line_color='#9467bd') 
            st.plotly_chart(add_ref(f2, 58.0), use_container_width=True, key="t2")
            
        # Row 2 of Graphs
        with t1:
            f3 = px.line(df_7d, x='Date', y='Rx_NC', markers=True, title='3. Reactor N/C Ratio Trend (Design: 3.11)', line_shape='spline')
            st.plotly_chart(add_ref(f3, 3.11), use_container_width=True, key="t3")
        with t2:
            f4 = px.line(df_7d, x='Date', y='Stripper_Eff', markers=True, title='4. Stripper Efficiency Trend (%)', line_shape='spline')
            f4.update_traces(line_color='#d97706') 
            st.plotly_chart(add_ref(f4, 78.0), use_container_width=True, key="t4")
            
        # Row 3 of Graphs
        with t1:
            f5 = px.line(df_7d, x='Date', y='Moisture', markers=True, title='5. Avg Moisture (Design: 0.3%)', line_shape='spline')
            st.plotly_chart(add_ref(f5, 0.3), use_container_width=True, key="t5")
        with t2:
            f6 = px.line(df_7d, x='Date', y='Biuret', markers=True, title='6. Avg Biuret (Design: 0.9%)', line_shape='spline')
            st.plotly_chart(add_ref(f6, 0.9), use_container_width=True, key="t6")
            
        # Row 4 of Graphs
        with t1:
            f7 = px.line(df_7d, x='Date', y='APS', markers=True, title='7. Avg APS Trend', line_shape='spline')
            st.plotly_chart(add_ref(f7), use_container_width=True, key="t7")
        with t2:
            f8 = px.line(df_7d, x='Date', y='HPD_Eff', markers=True, title='8. HPD Efficiency Trend (%)', line_shape='spline')
            f8.update_traces(line_color='#059669') 
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
