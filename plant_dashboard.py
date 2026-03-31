import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# -- PAGE CONFIGURATION --
st.set_page_config(page_title="AgriTech UREA Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .section-header { color: #1E3A8A; margin-top: 30px; margin-bottom: 10px; font-weight: 600; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px;}
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 UREA Plant Daily Operations Dashboard")

# -- OMNI-READER & DESIGN EXTRACTOR --
@st.cache_data(ttl=600)
def load_data():
    file_name = "UREA Lab Analysis Dashboard.xlsx"
    try:
        xl = pd.ExcelFile(file_name)
    except Exception as e:
        return pd.DataFrame(), {}

    master_df = pd.DataFrame()
    global_design = {}

    # Read absolutely every sheet in the file
    for sheet in xl.sheet_names:
        try:
            temp_df = pd.read_excel(file_name, sheet_name=sheet, header=None)
            header_idx = -1
            design_idx = -1

            # Scan rows to find the Date header and the Design Values
            for i, row in temp_df.iterrows():
                row_strs = [str(val).strip().lower() for val in row.values]
                if any('date' == r for r in row_strs) or any('date' in r for r in row_strs if len(r) < 6):
                    header_idx = i
                if any('design' in r for r in row_strs) or any('reference' in r for r in row_strs):
                    design_idx = i

            if header_idx != -1:
                # Extract the column names
                headers = [str(val).replace('\n', ' ').strip() for val in temp_df.iloc[header_idx].values]
                
                # Extract Design Values and match them to the columns
                if design_idx != -1:
                    for col_name, d_val in zip(headers, temp_df.iloc[design_idx].values):
                        try:
                            if pd.notna(d_val) and isinstance(d_val, (int, float)):
                                global_design[col_name.lower()] = float(d_val)
                        except:
                            pass

                # Read the actual data skipping the title rows
                df = pd.read_excel(file_name, sheet_name=sheet, skiprows=header_idx)
                df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()

                # Standardize Date column
                date_col = next((c for c in df.columns if 'date' in c.lower()), None)
                if date_col:
                    df = df.rename(columns={date_col: 'Date'})
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df = df.dropna(subset=['Date'])
                    
                    # Merge dynamically
                    if master_df.empty:
                        master_df = df
                    else:
                        cols_to_use = df.columns.difference(master_df.columns).tolist() + ['Date']
                        master_df = pd.merge(master_df, df[cols_to_use], on='Date', how='outer')
        except:
            continue # If a sheet is totally blank, just skip it

    if master_df.empty:
        return master_df, {}

    # Fill missing numbers with 0
    numeric_cols = master_df.select_dtypes(include=['number']).columns
    master_df[numeric_cols] = master_df[numeric_cols].fillna(0)
    
    # Aggregate multiple shifts into 1 day
    agg_funcs = {}
    for col in master_df.columns:
        if col == 'Date': continue
        elif 'prod' in col.lower(): agg_funcs[col] = 'sum'
        elif col in numeric_cols: agg_funcs[col] = 'mean'
        else: agg_funcs[col] = 'first'

    df_daily = master_df.groupby('Date').agg(agg_funcs).reset_index()
    df_daily = df_daily.sort_values('Date')
    
    return df_daily, global_design

try:
    df, design_dict = load_data()
    
    if df.empty:
        st.error("No valid data found. Ensure your Excel file has 'Date' columns.")
    else:
        # -- SIDEBAR --
        st.sidebar.header("📅 Dashboard Controls")
        latest_date = df['Date'].max()
        selected_date = st.sidebar.date_input("Select Shift Date", latest_date)
        selected_date = pd.to_datetime(selected_date)
        
        daily_data = df[df['Date'] == selected_date]
        yesterday_data = df[df['Date'] == (selected_date - timedelta(days=1))]
        
        if not daily_data.empty:
            
            # Helper to find values regardless of exact column spelling
            def find_val(data_row, keywords):
                if data_row.empty: return 0.0
                for col in data_row.columns:
                    if all(k.lower() in col.lower() for k in keywords):
                        return float(data_row[col].values[0])
                return 0.0
                
            def get_delta(keywords):
                return find_val(daily_data, keywords) - find_val(yesterday_data, keywords)

            # Helper to find Design Values
            def get_design(keywords):
                for k, v in design_dict.items():
                    if all(key.lower() in k.lower() for key in keywords):
                        return v
                return None
                
            # Helper to format Metric Titles with Design Values
            def format_title(base_title, keywords, is_percent=False):
                d_val = get_design(keywords)
                if d_val is not None:
                    if is_percent and d_val <= 1.0: d_val *= 100
                    suffix = f"{d_val:.1f}%" if is_percent else f"{d_val:.2f}"
                    return f"{base_title} (Ref: {suffix})"
                return base_title

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
            c3.metric(format_title("Avg Moisture", ['moist']), f"{find_val(daily_data, ['moist']):.3f} %", f"{get_delta(['moist']):.3f} %", delta_color="inverse")
            c4.metric(format_title("Avg Biuret", ['biuret']), f"{find_val(daily_data, ['biuret']):.2f} %", f"{get_delta(['biuret']):.2f} %", delta_color="inverse")
            c5.metric("Avg APS", f"{find_val(daily_data, ['aps']):.2f} mm", f"{get_delta(['aps']):.2f} mm")

            # ==========================================
            # SECTION 2: SYNTHESIS LOOP LAB RESULTS
            # ==========================================
            st.markdown("<h3 class='section-header'>🧪 Synthesis Loop & Absorbers</h3>", unsafe_allow_html=True)
            r1, r2, r3, r4, r5, r6 = st.columns(6)
            
            co2_conv = find_val(daily_data, ['co2', 'conv'])
            if co2_conv > 0 and co2_conv <= 1.0: co2_conv *= 100 
            
            rx_nc = next((float(daily_data[c].values[0]) for c in daily_data.columns if 'n/c' in c.lower() and 'hpa' not in c.lower() and 'lpa' not in c.lower()), 0.0)
            
            r1.metric(format_title("CO2 Conversion", ['co2', 'conv'], True), f"{co2_conv:.1f} %")
            r2.metric(format_title("Reactor N/C", ['n/c']), f"{rx_nc:.2f}")
            r3.metric(format_title("HPA N/C", ['hpa', 'n/c']), f"{find_val(daily_data, ['hpa', 'n/c']):.2f}")
            r4.metric(format_title("HPA H/C", ['hpa', 'h/c']), f"{find_val(daily_data, ['hpa', 'h/c']):.2f}")
            r5.metric(format_title("LPA N/C", ['lpa', 'n/c']), f"{find_val(daily_data, ['lpa', 'n/c']):.2f}")
            r6.metric(format_title("LPA H/C", ['lpa', 'h/c']), f"{find_val(daily_data, ['lpa', 'h/c']):.2f}")

            # ==========================================
            # SECTION 3: EQUIPMENT EFFICIENCIES (GAUGES)
            # ==========================================
            st.markdown("<h3 class='section-header'>⚙️ Equipment Efficiencies</h3>", unsafe_allow_html=True)
            g1, g2, g3 = st.columns(3)
            
            def make_gauge(val, title_base, keywords):
                d_val = get_design(keywords)
                title_text = f"{title_base}"
                if d_val is not None:
                    if d_val <= 1.0: d_val *= 100
                    title_text += f"<br><span style='font-size:14px;color:gray'>Ref/Design: {d_val:.1f}%</span>"
                    
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = val,
                    title = {'text': title_text, 'font': {'size': 18}},
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
                fig.update_layout(height=230, margin=dict(l=20, r=20, t=50, b=10))
                return fig
                
            with g1: st.plotly_chart(make_gauge(find_val(daily_data, ['stripper']), "Stripper", ['stripper']), use_container_width=True)
            with g2: st.plotly_chart(make_gauge(find_val(daily_data, ['hpd']), "HPD", ['hpd']), use_container_width=True)
            with g3: st.plotly_chart(make_gauge(find_val(daily_data, ['lpd']), "LPD", ['lpd']), use_container_width=True)

            st.markdown("---")

            # ==========================================
            # SECTION 4: 7-DAY TRENDS
            # ==========================================
            st.markdown("<h3 class='section-header'>📈 Last 7 Days Operational Trends</h3>", unsafe_allow_html=True)
            
            mask_7d = (df['Date'] <= selected_date) & (df['Date'] > selected_date - timedelta(days=7))
            df_7d = df.loc[mask_7d]
            
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
