import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
    df.columns = ['투자시작일', '날짜', '계좌명', '고객명', '초기투자금', '추가투자금', '정산수익금', '누적수익금', '투자원금', '총투자금', '평가자산', '원금대비수익률', '총수익률']
    # 날짜 데이터 변환
    df['날짜'] = pd.to_datetime(df['날짜'])
    return df

# (get_market_data 함수는 그대로 유지)

df = load_data()
menu = st.sidebar.radio("메뉴 선택", ["메인 대시보드", "고객별 상세 조회"])

if menu == "메인 대시보드":
    st.title("📈 랩어카운트 통합 대시보드")
    # ... (시장 지수 부분 그대로)
    
    st.subheader("📊 랩 연도별 원금 대비 수익률 (최신 기준)")
    
    # 1. 마지막 날짜 기준 데이터 필터링
    latest_date = df['날짜'].max()
    df_latest = df[df['날짜'] == latest_date].copy()
    df_latest['수익률_num'] = df_latest['원금대비수익률'].astype(str).str.replace('%', '').str.replace('None', '0').astype(float)
    df_latest['연도'] = df_latest['날짜'].dt.year

    # 2. 그래프 그리기 (텍스트 크기를 크게 조정)
    color_map = {"미국랩": "#3C3B6E", "국내랩": "#CD2E3A"}
    fig = px.bar(df_latest, x='연도', y='수익률_num', color='계좌명', 
                 barmode='group', color_discrete_map=color_map, text_auto='.1f')
    
    # 💡 숫자를 훨씬 크고 명확하게 보이게 설정
    fig.update_traces(textfont_size=18, textposition='outside', cliponaxis=False)
    fig.update_layout(bargap=0.6, bargroupgap=0.1, plot_bgcolor='white', showlegend=True)
    
    st.plotly_chart(fig, use_container_width=True)

# ... (고객별 상세 조회 부분 그대로)
