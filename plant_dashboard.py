import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# -- PAGE CONFIGURATION --
st.set_page_config(page_title="AgriTech UREA Plant", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .section-header { color: #1E3A8A; margin-top: 30px; margin-bottom: 10px; font-weight: 600; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px;}
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 UREA Plant Daily Operations Dashboard")

# -- SMART DATA EXTRACTOR --
def read_sheet_robust(file_name, sheet_name):
    """Scans an Excel sheet to automatically find where the actual data starts."""
    try:
        # Read without headers to find the 'Date' row
        temp_df = pd.read_excel(file_name, sheet_name=sheet_name, header=None)
        header_row_index = 0
        
        for i, row in temp_df.iterrows():
            # Check if any cell in this row contains the word 'Date'
            if any('date' == str(val).strip().lower() for val in row.values):
                header_row_index = i
                break
                
        # Now read the sheet properly using the found header row
        df = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=header_row_index)
        df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
        
        # Convert Date column to actual datetime, ignoring errors
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date']) # Drop rows without a valid date
            
        return df
    except Exception as e:
        return pd.DataFrame() # Return empty if sheet doesn't exist yet

@st.cache_data(ttl=600)
def load_data():
    file_name = "UREA Lab Analysis Dashboard.xlsx"
    
    # 1. Read all sheets using the smart extractor
    df_pq = read_sheet_robust(file_name, "PQ Trends")
    df_rx = read_sheet_robust(file_name, "Reactor")
    df_eff = read_sheet_robust(file_name, "Efficiencies")
    
    # 2. Merge them all together safely based on Date
    df_master = df_pq
    if not df_rx.empty:
        df_master = pd.merge(df_master, df_rx, on='Date', how='outer')
    if not df_eff.empty:
        df_master = pd.merge(df_master, df_eff, on='Date', how='outer')
        
    # Drop rows where there is no Date
    df_master = df_master.dropna(subset=['Date'])
    
    # Fill missing numeric values with 0 to prevent math errors
    numeric_cols = df_master.select_dtypes(include=['number']).columns
    df_master[numeric_cols] = df_master[numeric_cols].fillna(0)
            
    # Aggregation Logic: Sum Production, Average everything else
    agg_funcs = {}
    for col in df_master.columns:
        if col == 'Date': continue
        elif 'prod' in col.lower(): agg_funcs[col] = 'sum'
        elif col in numeric_cols: agg_funcs[col] = 'mean'
        else: agg_funcs[col] = 'first' # Keep remarks text
            
    df_daily = df_master.groupby('Date').agg(agg_funcs).reset_index()
    df_daily = df_daily.sort_values('Date')
    return df_daily

try:
    df = load_data()
    
    if df.empty:
        st.error("No valid data found. Please ensure your Excel file has a 'Date' column in the sheets.")
    else:
        # -- SIDEBAR --
        st.sidebar.header("📅 Dashboard Controls")
        latest_date = df['Date'].max()
        selected_date = st.sidebar.date_input("Select Shift Date", latest_date)
        selected_date = pd.to_datetime(selected_date)
        
        daily_data = df[df['Date'] == selected_date]
        yesterday_data = df[df['Date'] == (selected_date - timedelta(days=1))]
        
        if not daily_data.empty:
            
            # --- SMART COLUMN FINDER ---
            # This looks for keywords in your columns so you don't have to rename your Excel headers!
            def find_val(data_row, keywords):
                if data_row.empty: return 0.0
                for col in data_row.columns:
                    if all(k.lower() in col.lower() for k in keywords):
                        return float(data_row[col].values[0])
                return 0.0
                
            def get_delta(keywords):
                return find_val(daily_data, keywords) - find_val(yesterday_data, keywords)

            # Check for Remarks
            remarks_col = next((c for c in daily_data.columns if 'remark' in c.lower()), None)
            if remarks_col and pd.notna(daily_data[remarks_col].values[0]) and str(daily_data[remarks_col].values[0]).strip() not in ["0", "0.0", ""]:
                st.info(f"📝 **Shift Log/Remarks:** {daily_data[remarks_col].values[0]}")

            # ==========================================
            # SECTION 1: PRODUCTION & QUALITY
            # ==========================================
            st.markdown(f"<h3 class='section-header'>📊 Production & Quality Averages ({selected_date.strftime('%d %b %Y')})</h3>", unsafe_allow_html=True)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total Production", f"{find_val(daily_data, ['prod']):,.0f} MT", f"{get_delta(['prod']):.0f} MT")
            c2.metric("Avg Plant Load", f"{find_val(daily_data, ['load']):.1f} %", f"{get_delta(['load']):.1f} %")
            c3.metric("Avg Moisture", f"{find_val(daily_data, ['moist']):.3f} %", f"{get_delta(['moist']):.3f} %", delta_color="inverse")
            c4.metric("Avg Biuret", f"{find_val(daily_data, ['biuret']):.2f} %", f"{get_delta(['biuret']):.2f} %", delta_color="inverse")
            c5.metric("Avg APS", f"{find_val(daily_data, ['aps']):.2f} mm", f"{get_delta(['aps']):.2f} mm")

            # ==========================================
            # SECTION 2: SYNTHESIS LOOP LAB RESULTS
            # ==========================================
            st.markdown("<h3 class='section-header'>🧪 Synthesis Loop & Absorbers</h3>", unsafe_allow_html=True)
            r1, r2, r3, r4, r5, r6 = st.columns(6)
            
            # Auto-format CO2 conversion
            co2_conv = find_val(daily_data, ['co2', 'conv'])
            if co2_conv > 0 and co2_conv < 2.0: co2_conv *= 100 
            
            # Look specifically for HPA/LPA vs standard Reactor N/C
            rx_nc = next((float(daily_data[c].values[0]) for c in daily_data.columns if 'n/c' in c.lower() and 'hpa' not in c.lower() and 'lpa' not in c.lower()), 0.0)
            
            r1.metric("CO2 Conversion", f"{co2_conv:.1f} %")
            r2.metric("Reactor N/C", f"{rx_nc:.2f}")
            r3.metric("HPA N/C", f"{find_val(daily_data, ['hpa', 'n/c']):.2f}")
            r4.metric("HPA H/C", f"{find_val(daily_data, ['hpa', 'h/c']):.2f}")
            r5.metric("LPA N/C", f"{find_val(daily_data, ['lpa', 'n/c']):.2f}")
            r6.metric("LPA H/C", f"{find_val(daily_data, ['lpa', 'h/c']):.2f}")

            # ==========================================
            # SECTION 3: EQUIPMENT EFFICIENCIES (GAUGES)
            # ==========================================
            st.markdown("<h3 class='section-header'>⚙️ Equipment Efficiencies</h3>", unsafe_allow_html=True)
            g1, g2, g3 = st.columns(3)
            
            def make_gauge(val, title):
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = val,
                    title = {'text': title, 'font': {'size': 18}},
                    number = {'suffix': "%", 'font': {'size': 24}},
                    gauge = {
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                        'bar': {'color': "#2a9d8f"},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [{'range': [0, 60], 'color': "#e63946"}, {'range': [60, 85], 'color': "#ffb703"}],
                    }
                ))
                fig.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=10))
                return fig
                
            with g1: st.plotly_chart(make_gauge(find_val(daily_data, ['stripper']), "Stripper Efficiency"), use_container_width=True)
            with g2: st.plotly_chart(make_gauge(find_val(daily_data, ['hpd']), "HPD Efficiency"), use_container_width=True)
            with g3: st.plotly_chart(make_gauge(find_val(daily_data, ['lpd']), "LPD Efficiency"), use_container_width=True)

            st.markdown("---")

            # ==========================================
            # SECTION 4: 7-DAY TRENDS
            # ==========================================
            st.markdown("<h3 class='section-header'>📈 Last 7 Days Operational Trends</h3>", unsafe_allow_html=True)
            
            mask_7d = (df['Date'] <= selected_date) & (df['Date'] > selected_date - timedelta(days=7))
            df_7d = df.loc[mask_7d]
            
            # Find exact column names for graphing
            col_moist = next((c for c in df.columns if 'moist' in c.lower()), None)
            col_aps = next((c for c in df.columns if 'aps' in c.lower()), None)
            col_biuret = next((c for c in df.columns if 'biuret' in c.lower()), None)
            col_nc = next((c for c in df.columns if 'n/c' in c.lower() and 'hpa' not in c.lower() and 'lpa' not in c.lower()), None)
            
            t1, t2 = st.columns(2)
            
            with t1:
                if col_moist:
                    fig_moist = px.line(df_7d, x='Date', y=col_moist, markers=True, title='Average Moisture Trend', line_shape='spline')
                    fig_moist.update_traces(line_color='#00b4d8', line_width=3, marker_size=8)
                    st.plotly_chart(fig_moist, use_container_width=True)
                
                if col_aps:
                    fig_aps = px.line(df_7d, x='Date', y=col_aps, markers=True, title='Average APS Trend', line_shape='spline')
                    fig_aps.update_traces(line_color='#ff9f1c', line_width=3, marker_size=8)
                    st.plotly_chart(fig_aps, use_container_width=True)
                
            with t2:
                if col_biuret:
                    fig_biuret = px.line(df_7d, x='Date', y=col_biuret, markers=True, title='Average Biuret Trend', line_shape='spline')
                    fig_biuret.update_traces(line_color='#e63946', line_width=3, marker_size=8)
                    st.plotly_chart(fig_biuret, use_container_width=True)
                
                if col_nc:
                    fig_nc = px.line(df_7d, x='Date', y=col_nc, markers=True, title='Reactor N/C Ratio Trend', line_shape='spline')
                    fig_nc.update_traces(line_color='#2a9d8f', line_width=3, marker_size=8)
                    st.plotly_chart(fig_nc, use_container_width=True)

        else:
            st.warning("No data found for the selected date. Please pick another date from the sidebar.")

except Exception as e:
    st.error(f"Error processing the dashboard. Details: {e}")
