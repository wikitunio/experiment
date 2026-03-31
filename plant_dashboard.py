import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AgriTech Urea Dashboard", layout="wide")
st.title("Urea Plant Operations & Quality Dashboard")

# 1. Load the Data
@st.cache_data(ttl=600) # Caches the data for 10 minutes so it's fast
def load_data():
    file_name = "UREA Lab Analysis Dashboard.xlsx"
    
    # Read PQ Trends sheet (Skipping the top title row)
    df_pq = pd.read_excel(file_name, sheet_name="PQ Trends", skiprows=1)
    
    # Read Reactor sheet (Skipping the top 3 metadata rows)
    df_rx = pd.read_excel(file_name, sheet_name="Reactor", skiprows=3)
    
    # Clean up Date columns to make sure they match
    df_pq['Date'] = pd.to_datetime(df_pq['Date'])
    df_rx['Date'] = pd.to_datetime(df_rx['Date'])
    
    # Merge both sheets into one master table based on the Date
    df_master = pd.merge(df_pq, df_rx, on='Date', how='inner')
    
    # Drop empty rows where no production happened
    df_master = df_master.dropna(subset=['Prod.'])
    df_master = df_master[df_master['Prod.'] > 0]
    
    return df_master

try:
    df = load_data()
    
    # 2. Date Selector
    latest_date = df['Date'].max()
    selected_date = st.date_input("Select Date", latest_date)
    selected_date = pd.to_datetime(selected_date)
    
    daily_data = df[df['Date'] == selected_date]
    
    # 3. Dashboard KPI Cards
    if not daily_data.empty:
        st.subheader(f"Plant Overview: {selected_date.strftime('%Y-%m-%d')}")
        
        prod = daily_data['Prod.'].values[0]
        biuret = daily_data['Biuret\n%'].values[0]
        moisture = daily_data['Moisture\n%'].values[0]
        aps = daily_data['APS\nmm'].values[0]
        co2_conv = daily_data['CO2 Conversion'].values[0] * 100 
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Production", f"{prod:,.0f} MT")
        col2.metric("Biuret", f"{biuret:.2f} %")
        col3.metric("Moisture", f"{moisture:.2f} %")
        col4.metric("APS", f"{aps:.2f} mm")
        col5.metric("CO2 Conversion", f"{co2_conv:.1f} %")
        
        st.markdown("---")
        
        # 4. Interactive Charts
        st.subheader("Last 30 Days Trend")
        
        mask = (df['Date'] <= selected_date) & (df['Date'] >= selected_date - pd.Timedelta(days=30))
        trend_df = df.loc[mask]
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            fig1 = px.line(trend_df, x='Date', y='Prod.', title='Production Trend (MT)', markers=True)
            st.plotly_chart(fig1, use_container_width=True)
            
        with chart_col2:
            fig2 = px.line(trend_df, x='Date', y='Biuret\n%', title='Biuret Trend (%)', markers=True)
            fig2.add_hline(y=1.0, line_dash="dot", line_color="red", annotation_text="Limit")
            st.plotly_chart(fig2, use_container_width=True)
            
        # 5. Lab Remarks
        remarks = daily_data['Remarks'].values[0]
        if pd.notna(remarks):
             st.warning(f"**Operator Remarks:** {remarks}")
             
    else:
        st.info("No data available for the selected date. Please pick another date.")

except Exception as e:
    st.error(f"Error loading file. Details: {e}")
