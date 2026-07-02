import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# ... (앞부분 load_data, get_market_data 함수는 그대로 유지) ...

if menu == "메인 대시보드":
    # (시장 지수 코드 생략 - 이전과 동일)
    
    st.subheader("📊 랩 연도별 원금 대비 수익률")
    df['수익률_num'] = df['원금대비수익률'].astype(str).str.replace('%', '').str.replace('None', '0').astype(float)
    df['연도'] = pd.to_datetime(df['투자시작일']).dt.year
    
    # 💡 1. 국기 테마 색상 설정
    # 미국 국기 테마: Navy Blue & Red
    # 한국 국기 테마: Taegeuk Blue & Red (태극 문양 색상)
    color_map = {
        "미국랩": "#3C3B6E",  # 미국 성조기 짙은 파랑
        "국내랩": "#CD2E3A"   # 태극기 빨강 (혹은 한국적인 붉은 계열)
    }
    
    # 💡 2. 그래프 설정: 막대를 얇게(bargap)하고 수치를 명확하게(text_auto)
    fig = px.bar(
        df, x='연도', y='수익률_num', color='계좌명', 
        barmode='group', 
        color_discrete_map=color_map,
        text_auto='.1f' # 막대 위에 수익률 수치를 1자리 소수점으로 명확히 표시
    )
    
    # 💡 3. 레이아웃 조정: 막대 두께와 범례 위치
    fig.update_layout(
        bargap=0.6,          # 막대 간격을 넓혀서 막대 두께를 얇게 만듦
        bargroupgap=0.1,     # 그룹 내 간격
        plot_bgcolor='white', # 배경을 깔끔하게 흰색으로
        font=dict(size=14)   # 텍스트 크기 키우기
    )
    
    # 막대 위 숫자 텍스트 위치 조절
    fig.update_traces(textposition='outside')
    
    st.plotly_chart(fig, use_container_width=True)
