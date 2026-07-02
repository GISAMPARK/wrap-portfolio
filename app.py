import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# ... (load_data 및 get_market_data 함수는 이전과 동일) ...

if menu == "메인 대시보드":
    # ... (시장 지수 코드 동일) ...
    
    st.subheader("📊 랩 연도별 원금 대비 수익률")
    df['수익률_num'] = df['원금대비수익률'].astype(str).str.replace('%', '').str.replace('None', '0').astype(float)
    df['연도'] = pd.to_datetime(df['투자시작일']).dt.year
    
    # 💡 1. 색상 지정 (미국 국기 테마: 짙은 파랑, 진한 빨강)
    color_map = {"미국랩": "#3C3B6E", "국내랩": "#B22234"}
    
    # 💡 2. 얇은 막대(bargap)와 수치 표시(text_auto) 추가
    fig = px.bar(
        df, x='연도', y='수익률_num', color='계좌명', 
        barmode='group', 
        color_discrete_map=color_map,
        text_auto='.2f' # 막대 위에 숫자가 직접 뜨게 함
    )
    
    fig.update_layout(
        bargap=0.4,  # 막대 사이 간격 넓히기 (막대 자체가 얇아짐)
        bargroupgap=0.1
    )
    
    st.plotly_chart(fig, use_container_width=True)
