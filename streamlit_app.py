import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page configuration
st.set_page_config(
    page_title="2025년 1월 대기질 대시보드",
    page_icon="🌬️",
    layout="wide"
)

# Constants
# Use script's directory to find the file locally
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "202501-air.csv")

# Function to load data
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"데이터 파일을 찾을 수 없습니다: {file_path}")
        return None
    
    # Load correctly with UTF-8 encoding (previously verified)
    df = pd.read_csv(file_path, encoding='utf-8')
    
    # Preprocess measurement time (측정일시)
    # Format is YYYYMMDDHH, e.g., 2025010101
    # Convert '측정일시' to string first
    df['측정일시'] = df['측정일시'].astype(str)
    
    # Clean up measurement time and create datetime column
    # If the hour is 24, convert it to 00 of the next day or handle accordingly.
    # Often, 2025010124 is interpreted by Korean air quality data as 24:00 of the 1st
    
    def parse_korean_date(date_str):
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        hour = date_str[8:10]
        
        # Handle 24h format (common in these CSVs)
        if hour == '24':
            return pd.to_datetime(f"{year}-{month}-{day}") + pd.Timedelta(days=1)
        else:
            return pd.to_datetime(f"{year}-{month}-{day} {hour}:00:00")

    df['datetime'] = df['측정일시'].apply(parse_korean_date)
    return df

# Load data
df = load_data(DATA_PATH)

if df is not None:
    # Sidebar filters
    st.sidebar.header("필터 설정")
    
    # Region filter
    regions = sorted(df['지역'].unique())
    selected_region = st.sidebar.selectbox("지역 선택", ["전체"] + regions)
    
    if selected_region != "전체":
        filtered_df = df[df['지역'] == selected_region]
    else:
        filtered_df = df
        
    # Station filter (within selected region)
    stations = sorted(filtered_df['측정소명'].unique())
    selected_station = st.sidebar.selectbox("측정소 선택", ["전체"] + stations)
    
    if selected_station != "전체":
        filtered_df = filtered_df[filtered_df['측정소명'] == selected_station]

    # Pollutant selection for analysis
    pollutants = ['PM10', 'PM25', 'O3', 'NO2', 'CO', 'SO2']
    selected_pollutant = st.sidebar.selectbox("기타 대기 오염 물질 선택", pollutants)

    # UI Header
    st.title("🌬️ 2025년 1월 대기질 대시보드")
    st.markdown(f"**선택된 지역:** {selected_region} | **선택된 측정소:** {selected_station}")

    # Layout with Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    
    # Calculate averages for metrics
    avg_pm10 = filtered_df['PM10'].mean()
    avg_pm25 = filtered_df['PM25'].mean()
    avg_o3 = filtered_df['O3'].mean()
    avg_no2 = filtered_df['NO2'].mean()

    m1.metric("평균 PM10", f"{avg_pm10:.2f} ㎍/㎥")
    m2.metric("평균 PM2.5", f"{avg_pm25:.2f} ㎍/㎥")
    m3.metric("평균 O3", f"{avg_o3:.3f} ppm")
    m4.metric("평균 NO2", f"{avg_no2:.3f} ppm")

    # Main Visualizations
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("미세먼지(PM10) 및 초미세먼지(PM2.5) 추이")
        # Line chart for PM10 and PM2.5
        fig_pm = px.line(filtered_df.groupby('datetime')[['PM10', 'PM25']].mean().reset_index(), 
                         x='datetime', y=['PM10', 'PM25'],
                         labels={'value': '농도 (㎍/㎥)', 'datetime': '날짜/시간'},
                         template='plotly_white')
        st.plotly_chart(fig_pm, use_container_width=True)
        
    with col2:
        st.subheader(f"대기 오염 물질({selected_pollutant}) 분포")
        # Histogram for selected pollutant
        fig_hist = px.histogram(filtered_df, x=selected_pollutant,
                                labels={selected_pollutant: f'{selected_pollutant} 농도'},
                                template='plotly_white', color_discrete_sequence=['indianred'])
        st.plotly_chart(fig_hist, use_container_width=True)

    # Detailed Trend for the selected pollutant
    st.subheader(f"시간대별 {selected_pollutant} 변화")
    # Group by hour to see daily patterns
    filtered_df['hour'] = filtered_df['datetime'].dt.hour
    hourly_avg = filtered_df.groupby('hour')[selected_pollutant].mean().reset_index()
    fig_hourly = px.bar(hourly_avg, x='hour', y=selected_pollutant,
                        labels={'hour': '시간 (0-23)', selected_pollutant: f'{selected_pollutant} 평균 농도'},
                        template='plotly_dark')
    st.plotly_chart(fig_hourly, use_container_width=True)

    # Comparison by Station (if whole region selected)
    if selected_station == "전체" and selected_region != "전체":
        st.subheader("측정소별 오염도 비교 (상위 10개)")
        station_comparison = filtered_df.groupby('측정소명')[['PM10', 'PM25']].mean().reset_index()
        station_comparison = station_comparison.sort_values(by='PM10', ascending=False).head(10)
        
        fig_station = px.bar(station_comparison, x='측정소명', y=['PM10', 'PM25'], barmode='group',
                             labels={'value': '평균 농도', '측정소명': '측정소'},
                             template='plotly_white')
        st.plotly_chart(fig_station, use_container_width=True)

    # Data Table
    if st.checkbox("원본 데이터 보기"):
        st.dataframe(filtered_df.head(100))
