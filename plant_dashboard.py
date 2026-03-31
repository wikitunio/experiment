import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# -- PAGE CONFIGURATION --
st.set_page_config(page_title="AgriTech UREA Plant", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for better attractiveness
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 UREA Plant Control Dashboard")
st.markdown("Monitor daily production, shift-wise quality averages, and loop efficiencies.")

# -- DATA LOADING & CLEANING --
@st.cache_data(ttl=600)
def load_data():
    file_name = "UREA Lab Analysis Dashboard.xlsx"
    
    # Read sheets
    df_pq = pd.read_excel(file_name, sheet_name="PQ Trends", skiprows=1)
    df_rx = pd.read_excel(file_name, sheet_name="Reactor", skiprows=3)
    
    # Clean column names (removes weird enters/newlines from excel headers)
    df_pq.columns = df_pq.columns.str.replace('\n', ' ').str.strip()
    df_rx.columns = df_rx.columns.str.replace('\n', ' ').str.strip()
    
    # Ensure Dates are datetime objects
    df_pq['Date'] = pd.to_datetime(df_pq['Date'])
    df_rx['Date'] = pd.to_datetime(df_rx['Date'])
    
    # Merge sheets
    df_master = pd.merge(df_pq, df_rx, on='Date', how='inner')
    df_master = df_master.dropna(subset=['Prod.'])
    df_master = df_master[df_master['Prod.'] > 0]
    
    # --- CRASH-PROOFING NEW COLUMNS ---
    # If you haven't added these to Excel yet, this stops the app from crashing
    new_cols = ['Stripper Eff', 'HPD Eff', 'LPD Eff', 'HPA N/C', 'HPA H/C', 'LPA N/C', 'LPA H/C']
    for col in new_cols:
        if col not in df_master.columns:
            df_master[col] = 0.0  # Default to 0 if missing

    # --- AGGREGATE SHIFT DATA INTO DAILY TOTALS/AVERAGES ---
    # Sum production, Mean (average) for everything else
    agg_funcs = {col: 'mean' for col in df_master.columns if col != 'Date'}
    agg_funcs['Prod.'] = 'sum'  # We want total daily production, not average
    
    df_daily = df_master.groupby('Date').agg(agg_funcs).reset_index()
    df_daily = df_daily.sort_values('Date')
    
    return df_daily

try:
    df = load_data()
    
    # -- SIDEBAR DATE SELECTOR --
    st.sidebar.header("📅 Select Parameters")
    latest_date = df['Date'].max()
    selected_date = st.sidebar.date_input("Analysis Date", latest_date)
    selected_date = pd.to_datetime(selected_date)
    
    # Get today and yesterday's data for comparison Deltas
    daily_data = df[df['Date'] == selected_date]
    yesterday_data = df[df['Date'] == (selected_date - timedelta(days=1))]
    
    if not daily_data.empty:
        # Helper function to get value safely
        def get_val(data, col): return data[col].values[0] if not data.empty and col in data else 0
        def get_delta(col): return float(get_val(daily_data, col) - get_val(yesterday_data, col))

        # -- UI TABS --
        tab1, tab2, tab3 = st.tabs(["📊 Production & Quality", "🧪 Synthesis & Recovery", "📈 7-Day Trends"])
        
        # ==========================================
        # TAB 1: PRODUCTION & PRODUCT QUALITY
        # ==========================================
        with tab1:
            st.subheader(f"Plant Overview for {selected_date.strftime('%d %B %Y')}")
            
            # Row 1: Production KPIs
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total Production", f"{get_val(daily_data, 'Prod.'):,.0f} MT", f"{get_delta('Prod.'):.0f} MT")
            c2.metric("Avg Plant Load", f"{get_val(daily_data, 'Load'):.1f} %", f"{get_delta('Load'):.1f} %")
            c3.metric("Avg Moisture", f"{get_val(daily_data, 'Moisture %'):.3f} %", f"{get_delta('Moisture %'):.3f} %", delta_color="inverse")
            c4.metric("Avg Biuret", f"{get_val(daily_data, 'Biuret %'):.2f} %", f"{get_delta('Biuret %'):.2f} %", delta_color="inverse")
            c5.metric("Avg APS", f"{get_val(daily_data, 'APS mm'):.2f} mm", f"{get_delta('APS mm'):.2f} mm")

        # ==========================================
        # TAB 2: REACTOR & EFFICIENCIES
        # ==========================================
        with tab2:
            st.subheader("Synthesis Loop & Recovery Performance")
            
            # Top Row: Reactor Stats
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("Reactor N/C Ratio", f"{get_val(daily_data, 'N/C'):.2f}", f"{get_delta('N/C'):.2f}")
            rc2.metric("Reactor H/C Ratio", f"{get_val(daily_data, 'H/C'):.2f}", f"{get_delta('H/C'):.2f}")
            
            co2_conv = get_val(daily_data, 'CO2 Conversion')
            # If CO2 conv is in decimals (0.56), multiply by 100. If already %, leave it.
            if co2_conv < 2.0: co2_conv *= 100 
            rc3.metric("CO2 Conversion", f"{co2_conv:.1f} %")
            
            st.markdown("---")
            
            # Middle Row: Absorber Stats
            ac1, ac2, ac3, ac4 = st.columns(4)
            ac1.metric("HPA N/C Ratio", f"{get_val(daily_data, 'HPA N/C'):.2f}")
            ac2.metric("HPA H/C Ratio", f"{get_val(daily_data, 'HPA H/C'):.2f}")
            ac3.metric("LPA N/C Ratio", f"{get_val(daily_data, 'LPA N/C'):.2f}")
            ac4.metric("LPA H/C Ratio", f"{get_val(daily_data, 'LPA H/C'):.2f}")
            
            st.markdown("---")
            
            # Bottom Row: Beautiful Gauge Charts for Efficiencies
            st.markdown("#### Equipment Efficiencies")
            gc1, gc2, gc3 = st.columns(3)
            
            def make_gauge(val, title):
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = val,
                    title = {'text': title},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#1E3A8A"},
                        'steps': [
                            {'range': [0, 60], 'color': "lightgray"},
                            {'range': [60, 85], 'color': "gray"}],
                    }
                ))
                fig.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=10))
                return fig
                
            with gc1: st.plotly_chart(make_gauge(get_val(daily_data, 'Stripper Eff'), "Stripper Efficiency %"), use_container_width=True)
            with gc2: st.plotly_chart(make_gauge(get_val(daily_data, 'HPD Eff'), "HPD Efficiency %"), use_container_width=True)
            with gc3: st.plotly_chart(make_gauge(get_val(daily_data, 'LPD Eff'), "LPD Efficiency %"), use_container_width=True)

        # ==========================================
        # TAB 3: 7-DAY TRENDS
        # ==========================================
        with tab3:
            st.subheader("Last 7 Days Operational Trends")
            
            # Filter data for last 7 days
            mask_7d = (df['Date'] <= selected_date) & (df['Date'] > selected_date - timedelta(days=7))
            df_7d = df.loc[mask_7d]
            
            tc1, tc2 = st.columns(2)
            
            with tc1:
                fig_moist = px.line(df_7d, x='Date', y='Moisture %', markers=True, title='Avg Moisture Trend', line_shape='spline')
                fig_moist.update_traces(line_color='#00b4d8')
                st.plotly_chart(fig_moist, use_container_width=True)
                
                fig_aps = px.line(df_7d, x='Date', y='APS mm', markers=True, title='Avg APS Trend', line_shape='spline')
                fig_aps.update_traces(line_color='#ff9f1c')
                st.plotly_chart(fig_aps, use_container_width=True)
                
            with tc2:
                fig_biuret = px.line(df_7d, x='Date', y='Biuret %', markers=True, title='Avg Biuret Trend', line_shape='spline')
                fig_biuret.update_traces(line_color='#e63946')
                st.plotly_chart(fig_biuret, use_container_width=True)
                
                fig_nc = px.line(df_7d, x='Date', y='N/C', markers=True, title='Reactor N/C Ratio Trend', line_shape='spline')
                fig_nc.update_traces(line_color='#2a9d8f')
                st.plotly_chart(fig_nc, use_container_width=True)

    else:
        st.warning("No data found for the selected date. Please pick another date from the sidebar.")

except Exception as e:
    st.error(f"Error processing the dashboard. Details: {e}")
