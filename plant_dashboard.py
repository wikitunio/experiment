import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="AgriTech UREA Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .section-header { color: #1E3A8A; margin-top: 30px; margin-bottom: 10px; font-weight: 600; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px;}
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 UREA Plant Daily Operations Dashboard")

@st.cache_data(ttl=600)
def load_data():
    file_name = "UREA Lab Analysis Dashboard.xlsx"
    
    # 1. Load PQ Trends
    try:
        df_pq_raw = pd.read_excel(file_name, sheet_name="PQ Trends", skiprows=1)
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
        return pd.DataFrame(), f"Error loading PQ Trends: {e}"

    # 2. Load Efficiencies
    try:
        df_eff_raw = pd.read_excel(file_name, sheet_name="Efficiencies", skiprows=2)
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
        return pd.DataFrame(), f"Error loading Efficiencies: {e}"

    # 3. Merge cleanly
    df_master = pd.merge(df_pq, df_eff, on='Date', how='left')
    
    # 4. Aggregate multiple shifts into daily averages
    agg_funcs = {
        'Production': 'sum',
        'Load': 'mean',
        'Moisture': 'mean',
        'Biuret': 'mean',
        'APS': 'mean',
        'CO2_Conv': 'mean',
        'Rx_NC': 'mean',
        'Rx_HC': 'mean',
        'Stripper_Eff': 'mean',
        'HPD_Eff': 'mean',
        'HPA_NC': 'mean',
        'HPA_HC': 'mean',
        'LPA_NC': 'mean',
        'LPA_HC': 'mean',
        'Remarks': 'first'
    }
    
    df_daily = df_master.groupby('Date').agg(agg_funcs).reset_index()
    df_daily = df_daily.sort_values('Date')
    
    return df_daily, ""

df, err_msg = load_data()

if err_msg:
    st.error(err_msg)
elif df.empty:
    st.error("No valid data found in the Excel file.")
else:
    # Sidebar
    st.sidebar.header("📅 Dashboard Controls")
    latest_date = df['Date'].max()
    selected_date = st.sidebar.date_input("Select Shift Date", latest_date)
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
        r1, r2, r3, r4, r5, r6 = st.columns(6)
        
        co2_conv = get_val(daily_data, 'CO2_Conv')
        if co2_conv > 0 and co2_conv <= 1.0: co2_conv *= 100 
        
        r1.metric("CO2 Conversion (Ref: 58.0%)", f"{co2_conv:.1f} %")
        r2.metric("Reactor N/C (Ref: 3.11)", f"{get_val(daily_data, 'Rx_NC'):.2f}")
        r3.metric("HPA N/C (Ref: 2.38)", f"{get_val(daily_data, 'HPA_NC'):.2f}")
        r4.metric("HPA H/C (Ref: 1.289)", f"{get_val(daily_data, 'HPA_HC'):.2f}")
        r5.metric("LPA N/C (Ref: 2.29)", f"{get_val(daily_data, 'LPA_NC'):.2f}")
        r6.metric("LPA H/C (Ref: 2.28)", f"{get_val(daily_data, 'LPA_HC'):.2f}")

        # --- SECTION 3: EFFICIENCIES ---
        st.markdown("<h3 class='section-header'>⚙️ Equipment Efficiencies</h3>", unsafe_allow_html=True)
        g1, g2, g3 = st.columns(3)
        
        def make_gauge(val, title, ref_val):
            if val > 0 and val <= 1.0: val *= 100
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = val,
                title = {'text': f"{title}<br><span style='font-size:14px;color:gray'>Ref/Design: {ref_val}%</span>", 'font': {'size': 18}},
                number = {'suffix': "%", 'font': {'size': 24}},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#2a9d8f"},
                    'steps': [{'range': [0, 60], 'color': "#e63946"}, {'range': [60, 85], 'color': "#ffb703"}],
                }
            ))
            fig.update_layout(height=230, margin=dict(l=20, r=20, t=50, b=10))
            return fig
            
        with g1: st.plotly_chart(make_gauge(get_val(daily_data, 'Stripper_Eff'), "Stripper", 78.0), use_container_width=True)
        with g2: st.plotly_chart(make_gauge(get_val(daily_data, 'HPD_Eff'), "HPD", 65.4), use_container_width=True)
        with g3: st.plotly_chart(make_gauge(0, "LPD", 65.0), use_container_width=True) # LPD placeholder

        st.markdown("---")

        # --- SECTION 4: 1-WEEK TREND ---
        week_start = selected_date - timedelta(days=6)
        st.markdown(f"<h3 class='section-header'>📈 One Week Trend ({week_start.strftime('%d %b')} to {selected_date.strftime('%d %b %Y')})</h3>", unsafe_allow_html=True)
        
        mask_7d = (df['Date'] <= selected_date) & (df['Date'] >= week_start)
        df_7d = df.loc[mask_7d]
        
        def add_ref_line(fig):
            # THE FIX: Convert datetime to string before passing to Plotly
            date_str = selected_date.strftime('%Y-%m-%d')
            fig.add_vline(x=date_str, line_width=2, line_dash="dash", line_color="gray", annotation_text="Selected", annotation_position="top left")
            return fig

        t1, t2 = st.columns(2)
        
        with t1:
            fig_moist = px.line(df_7d, x='Date', y='Moisture', markers=True, title='Average Moisture Trend', line_shape='spline')
            fig_moist.update_traces(line_color='#00b4d8', line_width=3, marker_size=8)
            st.plotly_chart(add_ref_line(fig_moist), use_container_width=True)
            
            fig_aps = px.line(df_7d, x='Date', y='APS', markers=True, title='Average APS Trend', line_shape='spline')
            fig_aps.update_traces(line_color='#ff9f1c', line_width=3, marker_size=8)
            st.plotly_chart(add_ref_line(fig_aps), use_container_width=True)
            
        with t2:
            fig_biuret = px.line(df_7d, x='Date', y='Biuret', markers=True, title='Average Biuret Trend', line_shape='spline')
            fig_biuret.update_traces(line_color='#e63946', line_width=3, marker_size=8)
            st.plotly_chart(add_ref_line(fig_biuret), use_container_width=True)
            
            fig_nc = px.line(df_7d, x='Date', y='Rx_NC', markers=True, title='Reactor N/C Ratio Trend', line_shape='spline')
            fig_nc.update_traces(line_color='#2a9d8f', line_width=3, marker_size=8)
            st.plotly_chart(add_ref_line(fig_nc), use_container_width=True)

    else:
        st.warning("No data found for the selected date. Please pick another date from the sidebar.")
