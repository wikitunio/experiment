import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import datetime
import requests
import io

st.set_page_config(page_title="AgriTech UREA Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .section-header { color: #1E3A8A; margin-top: 30px; margin-bottom: 15px; font-weight: 600; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px;}
    .gauge-title { text-align: center; font-size: 18px; font-weight: bold; color: #333333; margin-bottom: 2px; padding-top: 10px; }
    .gauge-sub { text-align: center; font-size: 13px; color: #888888; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 UREA Plant Daily Operations Dashboard")

@st.cache_data(ttl=600)
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
    except Exception as e:
        return pd.DataFrame(), f"Error processing PQ Trends sheet: {e}"

    # 2. Load Efficiencies (Restart from beginning of data stream)
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
    except Exception as e:
        return pd.DataFrame(), f"Error processing Efficiencies sheet: {e}"

    # 3. Merge
    df_master = pd.merge(df_pq, df_eff, on='Date', how='left')
    
    agg_funcs = {
        'Production': 'sum', 'Load': 'mean', 'Moisture': 'mean', 'Biuret': 'mean',
        'APS': 'mean', 'CO2_Conv': 'mean', 'Rx_NC': 'mean', 'Rx_HC': 'mean',
        'Stripper_Eff': 'mean', 'HPD_Eff': 'mean', 'HPA_NC': 'mean', 'HPA_HC': 'mean',
        'LPA_NC': 'mean', 'LPA_HC': 'mean', 'Remarks': 'first'
    }
    
    df_daily = df_master.groupby('Date').agg(agg_funcs).reset_index()
    df_daily = df_daily.sort_values('Date')
    
    return df_daily, ""

df, err_msg = load_data()

if err_msg:
    st.error(err_msg)
elif df.empty:
    st.info("Searching for plant data...")
else:
    st.sidebar.header("📅 Dashboard Controls")
    today = datetime.date.today()
    selected_date = st.sidebar.date_input("Select Shift Date", today)
    selected_date = pd.to_datetime(selected_date)
    
    daily_data = df[df['Date'] == selected_date]
    yesterday_data = df[df['Date'] == (selected_date - timedelta(days=1))]
    
    if not daily_data.empty:
        def get_val(data, col): return float(data[col].values[0]) if not data.empty else 0.0
        def get_delta(col): return get_val(daily_data, col) - get_val(yesterday_data, col)

        remarks = daily_data['Remarks'].values[0]
        if str(remarks) != 'nan' and str(remarks).strip() and str(remarks).strip() != '0':
            st.info(f"📝 **Shift Log/Remarks:** {remarks}")

        # --- SECTION 1: PRODUCTION & QUALITY ---
        st.markdown(f"<h3 class='section-header'>📊 Production & Quality Averages ({selected_date.strftime('%d %b %Y')})</h3>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Production", f"{get_val(daily_data, 'Production'):,.0f} MT", f"{get_delta('Production'):.0f} MT")
        c2.metric("Avg Plant Load", f"{get_val(daily_data, 'Load'):.1f} %", f"{get_delta('Load'):.1f} %")
        c3.metric("Avg Moisture", f"{get_val(daily_data, 'Moisture'):.3f} %", f"{get_delta('Moisture'):.3f} %", delta_color="inverse")
        c4.metric("Avg Biuret", f"{get_val(daily_data, 'Biuret'):.2f} %", f"{get_delta('Biuret'):.2f} %", delta_color="inverse")
        c5.metric("Avg APS", f"{get_val(daily_data, 'APS'):.2f} mm", f"{get_delta('APS'):.2f} mm")

        # --- SECTION 2: SYNTHESIS LOOP ---
        st.markdown("<h3 class='section-header'>🧪 Synthesis Loop & Absorbers</h3>", unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        co2_conv = get_val(daily_data, 'CO2_Conv')
        if co2_conv > 0 and co2_conv <= 1.0: co2_conv *= 100 
        r1.metric("CO2 Conversion (Ref: 58.0%)", f"{co2_conv:.1f} %")
        r2.metric("Reactor N/C (Ref: 3.11)", f"{get_val(daily_data, 'Rx_NC'):.2f}")
        r3.metric("HPA N/C (Ref: 2.38)", f"{get_val(daily_data, 'HPA_NC'):.2f}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        r4, r5, r6 = st.columns(3)
        r4.metric("HPA H/C (Ref: 1.289)", f"{get_val(daily_data, 'HPA_HC'):.2f}")
        r5.metric("LPA N/C (Ref: 2.29)", f"{get_val(daily_data, 'LPA_NC'):.2f}")
        r6.metric("LPA H/C (Ref: 2.28)", f"{get_val(daily_data, 'LPA_HC'):.2f}")

        # --- SECTION 3: EFFICIENCIES ---
        st.markdown("<h3 class='section-header'>⚙️ Equipment Efficiencies</h3>", unsafe_allow_html=True)
        g1, g2, g3 = st.columns(3)
        
        def make_gauge(val):
            if val > 0 and val <= 1.0: val *= 100
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", value = val,
                number = {'suffix': "%", 'font': {'size': 26, 'color': '#1E3A8A'}},
                gauge = {'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': "#1E3A8A"}, 'bgcolor': "#e0e0e0", 'borderwidth': 0}
            ))
            fig.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10))
            return fig
            
        with g1: 
            st.markdown("<div class='gauge-title'>Stripper</div><div class='gauge-sub'>Ref/Design: 78.0%</div>", unsafe_allow_html=True)
            st.plotly_chart(make_gauge(get_val(daily_data, 'Stripper_Eff')), use_container_width=True, key="stripper_gauge")
        with g2: 
            st.markdown("<div class='gauge-title'>HPD</div><div class='gauge-sub'>Ref/Design: 65.4%</div>", unsafe_allow_html=True)
            st.plotly_chart(make_gauge(get_val(daily_data, 'HPD_Eff')), use_container_width=True, key="hpd_gauge")
        with g3: 
            st.markdown("<div class='gauge-title'>LPD</div><div class='gauge-sub'>Ref/Design: 65.0%</div>", unsafe_allow_html=True)
            st.plotly_chart(make_gauge(0), use_container_width=True, key="lpd_gauge") 

        st.markdown("---")

        # --- SECTION 4: 1-WEEK TREND ---
        week_start = selected_date - timedelta(days=6)
        st.markdown(f"<h3 class='section-header'>📈 One Week Trend ({week_start.strftime('%d %b')} to {selected_date.strftime('%d %b %Y')})</h3>", unsafe_allow_html=True)
        mask_7d = (df['Date'] <= selected_date) & (df['Date'] >= week_start)
        df_7d = df.loc[mask_7d]
        
        def add_ref_line(fig):
            fig.add_vline(x=selected_date, line_width=2, line_dash="dash", line_color="gray")
            return fig

        t1, t2 = st.columns(2)
        with t1:
            f1 = px.line(df_7d, x='Date', y='Moisture', markers=True, title='Avg Moisture Trend (Design: 0.3%)', line_shape='spline')
            f1.add_hline(y=0.3, line_dash="dot", line_color="red")
            st.plotly_chart(add_ref_line(f1), use_container_width=True, key="moist_chart")
            f2 = px.line(df_7d, x='Date', y='APS', markers=True, title='Avg APS Trend', line_shape='spline')
            st.plotly_chart(add_ref_line(f2), use_container_width=True, key="aps_chart")
        with t2:
            f3 = px.line(df_7d, x='Date', y='Biuret', markers=True, title='Avg Biuret Trend (Design: 0.9%)', line_shape='spline')
            f3.add_hline(y=0.9, line_dash="dot", line_color="red")
            st.plotly_chart(add_ref_line(f3), use_container_width=True, key="biuret_chart")
            f4 = px.line(df_7d, x='Date', y='Rx_NC', markers=True, title='Reactor N/C Ratio Trend (Design: 3.11)', line_shape='spline')
            f4.add_hline(y=3.11, line_dash="dot", line_color="red")
            st.plotly_chart(add_ref_line(f4), use_container_width=True, key="nc_chart")
    else:
        st.info(f"No data found for {selected_date.strftime('%d %b %Y')}. Please select a date from the file history.")
