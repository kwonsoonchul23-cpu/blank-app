import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 페이지 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="🌬️ 2025년 1월 대기질 인사이트",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 커스텀 CSS (대기질 테마 - 블루/에메랄드 다크)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── 메트릭 카드 ── */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1B2631 0%, #2E4053 100%);
    border: 1px solid rgba(72, 201, 176, 0.2);
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(72, 201, 176, 0.2);
    border-color: rgba(72, 201, 176, 0.5);
}
div[data-testid="stMetric"] label {
    color: #AED6F1 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #FDFEFE !important;
}

/* ── 사이드바 ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #17202A 0%, #1B2631 100%);
    border-right: 1px solid rgba(72, 201, 176, 0.15);
}

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(27, 38, 49, 0.5);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 500;
    transition: all 0.3s ease;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(72, 201, 176, 0.15) !important;
    border-color: transparent !important;
}

/* ── 차트 컨테이너 ── */
div[data-testid="stPlotlyChart"] {
    background: rgba(27, 38, 49, 0.4);
    border-radius: 12px;
    padding: 8px;
    border: 1px solid rgba(72, 201, 176, 0.1);
    transition: border-color 0.3s ease;
}
div[data-testid="stPlotlyChart"]:hover {
    border-color: rgba(72, 201, 176, 0.3);
}

/* ── 커스텀 타이틀 ── */
.gradient-title {
    background: linear-gradient(120deg, #48C9B0 0%, #5DADE2 50%, #48C9B0 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradient-shift 4s ease infinite;
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}
@keyframes gradient-shift {
    0% { background-position: 0% center; }
    50% { background-position: 100% center; }
    100% { background-position: 0% center; }
}
.page-subtitle { color: #85929E; font-size: 1rem; margin-bottom: 2rem; }
.section-header {
    color: #AED6F1;
    font-size: 1.15rem;
    font-weight: 600;
    margin: 1.5rem 0 1rem 0;
    padding-left: 12px;
    border-left: 3px solid #48C9B0;
}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 차트 공통 설정 및 헬퍼 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLORS = ["#48C9B0", "#5DADE2", "#F4D03F", "#EB984E", "#AF7AC5", "#EC7063"]
DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Pretendard, sans-serif", color="#E5E8E8", size=12),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11),
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(gridcolor="rgba(72,201,176,0.08)", zerolinecolor="rgba(72,201,176,0.1)"),
    yaxis=dict(gridcolor="rgba(72,201,176,0.08)", zerolinecolor="rgba(72,201,176,0.1)"),
    hoverlabel=dict(bgcolor="#1B2631", font_size=12, font_color="#EBEDEF"),
)

def apply_dark(fig, title=""):
    fig.update_layout(**DARK_LAYOUT)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=16, color="#48C9B0")))
    return fig

def section_header(text):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 데이터 로드 및 전처리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "202501-air.csv")

@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path, encoding='utf-8')
    df['측정일시'] = df['측정일시'].astype(str)
    
    def parse_korean_date(date_str):
        year, month, day, hour = date_str[:4], date_str[4:6], date_str[6:8], date_str[8:10]
        if hour == '24':
            return pd.to_datetime(f"{year}-{month}-{day}") + pd.Timedelta(days=1)
        return pd.to_datetime(f"{year}-{month}-{day} {hour}:00:00")

    df['datetime'] = df['측정일시'].apply(parse_korean_date)
    df['hour'] = df['datetime'].dt.hour
    df['day_name'] = df['datetime'].dt.day_name()
    return df

df = load_data(DATA_PATH)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 사이드바 - 필터링
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if df is not None:
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:1rem 0 1.5rem 0;">
            <div style="font-size:2.5rem; margin-bottom:4px;">🌬️</div>
            <div style="font-size:1.1rem; font-weight:700; color:#48C9B0; letter-spacing:1px;">
                AIR QUALITY HUB</div>
            <div style="font-size:0.75rem; color:#85929E; margin-top:2px;">
                2025년 1월 대기질 인사이트</div>
        </div>""", unsafe_allow_html=True)
        st.divider()

        st.header("📍 위치 필터")
        regions = sorted(df['지역'].unique())
        selected_region = st.selectbox("지역 (시/군/구)", ["전체"] + regions)
        
        filtered_df = df if selected_region == "전체" else df[df['지역'] == selected_region]
        
        stations = sorted(filtered_df['측정소명'].unique())
        selected_station = st.selectbox("측정소", ["전체"] + stations)
        
        if selected_station != "전체":
            filtered_df = filtered_df[filtered_df['측정소명'] == selected_station]

        st.divider()
        st.header("📊 분석 설정")
        pollutants = ['PM10', 'PM25', 'O3', 'NO2', 'CO', 'SO2']
        selected_pollutant = st.selectbox("집중 분석 항목", pollutants, index=0)
        
        st.divider()
        st.markdown('<div style="text-align:center; color:#85929E; font-size:0.75rem;">'
                    '© 2025 Air Quality Insight<br>Powered by Antigravity</div>', unsafe_allow_html=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6. 메인 화면 구성
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.markdown('<div class="gradient-title">🌬️ 2025년 1월 대기질 인사이트 대시보드</div>'
                '<div class="page-subtitle">실시간 대기질 데이터 기반 정밀 분석 및 시각화</div>',
                unsafe_allow_html=True)

    # 요약 KPI
    k1, k2, k3, k4 = st.columns(4)
    avg_pm10 = filtered_df['PM10'].mean()
    avg_pm25 = filtered_df['PM25'].mean()
    avg_o3 = filtered_df['O3'].mean()
    avg_no2 = filtered_df['NO2'].mean()

    with k1:
        st.metric("평균 PM10", f"{avg_pm10:.1f} ㎍/㎥")
    with k2:
        st.metric("평균 PM2.5", f"{avg_pm25:.1f} ㎍/㎥")
    with k3:
        st.metric("평균 O3", f"{avg_o3:.3f} ppm")
    with k4:
        st.metric("평균 NO2", f"{avg_no2:.3f} ppm")

    st.divider()

    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 시계열 추이", "🕙 시간대별 분석", "🗺️ 지역별 비교", "🗂️ 원본 상세"]
    )

    # 탭 1: 시계열 추이
    with tab1:
        section_header(f"{selected_region} | {selected_station} - 미세먼지 및 주요 오염도 추이")
        
        # Line Chart
        trend_data = filtered_df.groupby('datetime')[['PM10', 'PM25', 'O3', 'NO2']].mean().reset_index()
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=trend_data['datetime'], y=trend_data['PM10'], name="PM10", 
                                       line=dict(color="#48C9B0", width=2)))
        fig_trend.add_trace(go.Scatter(x=trend_data['datetime'], y=trend_data['PM25'], name="PM2.5", 
                                       line=dict(color="#5DADE2", width=2)))
        apply_dark(fig_trend, "시간별 미세먼지 농도 변화")
        st.plotly_chart(fig_trend, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            section_header(f"{selected_pollutant} 분포 히스토그램")
            fig_hist = px.histogram(filtered_df, x=selected_pollutant, 
                                    color_discrete_sequence=[COLORS[0]],
                                    marginal="box")
            apply_dark(fig_hist)
            st.plotly_chart(fig_hist, use_container_width=True)
        with col2:
            section_header(f"{selected_pollutant} 이상치 분석 (Box Plot)")
            fig_box = px.box(filtered_df, y=selected_pollutant, 
                             color_discrete_sequence=[COLORS[1]])
            apply_dark(fig_box)
            st.plotly_chart(fig_box, use_container_width=True)

    # 탭 2: 시간대별 분석
    with tab2:
        section_header(f"하루 시간대별 {selected_pollutant} 평균 농도")
        hourly_data = filtered_df.groupby('hour')[selected_pollutant].mean().reset_index()
        fig_hourly = px.bar(hourly_data, x='hour', y=selected_pollutant,
                            color=selected_pollutant,
                            color_continuous_scale="Viridis",
                            labels={'hour': '시간 (H)', selected_pollutant: '평균 농도'})
        apply_dark(fig_hourly)
        fig_hourly.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_hourly, use_container_width=True)

        section_header("요일별 오염도 히트맵 (Day vs Hour)")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heat_data = filtered_df.groupby(['day_name', 'hour'])[selected_pollutant].mean().unstack()
        heat_data = heat_data.reindex(day_order)
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=heat_data.values,
            x=heat_data.columns,
            y=heat_data.index,
            colorscale='YlGnBu'
        ))
        apply_dark(fig_heat, f"요일/시간대별 {selected_pollutant} 히트맵")
        st.plotly_chart(fig_heat, use_container_width=True)

    # 탭 3: 지역별 비교
    with tab3:
        if selected_region == "전체":
            section_header("전국 주요 지역별 평균 PM10 농도")
            region_comp = df.groupby('지역')['PM10'].mean().sort_values(ascending=False).head(15).reset_index()
            fig_reg = px.bar(region_comp, x='지역', y='PM10', color='PM10', 
                             color_continuous_scale="Tealgrn")
            apply_dark(fig_reg)
            st.plotly_chart(fig_reg, use_container_width=True)
        else:
            section_header(f"{selected_region} 내 측정소별 오염도 비교")
            station_comp = filtered_df.groupby('측정소명')[['PM10', 'PM25']].mean().sort_values(by='PM10', ascending=False).reset_index()
            fig_stat = px.bar(station_comp, x='측정소명', y=['PM10', 'PM25'], barmode='group',
                              color_discrete_sequence=[COLORS[0], COLORS[1]])
            apply_dark(fig_stat)
            st.plotly_chart(fig_stat, use_container_width=True)

    # 탭 4: 원본 상세
    with tab4:
        section_header("데이터 테이블 (Top 1000 Rows)")
        st.dataframe(filtered_df.head(1000), use_container_width=True)
        
        # Download Data button
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 데이터 다운로드 (CSV)",
            data=csv,
            file_name='air_quality_data.csv',
            mime='text/csv',
        )

else:
    st.error("데이터 파일을 로드할 수 없습니다. 파일 경로 및 파일명을 확인해 주세요.")
