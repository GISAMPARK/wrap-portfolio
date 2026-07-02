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
    return df

# 지수 가져오기
@st.cache_data(ttl=900)
def get_market_data():
    tickers = {"코스피": "^KS11", "코스닥": "^KQ11", "S&P 500": "^GSPC", "나스닥": "^IXIC"}
    results = {}
    for name, ticker in tickers.items():
        try:
            tk = yf.Ticker(ticker)
            hist = tk.history(period="2d")
            change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            results[name] = change
        except:
            results[name] = 0
    return results

# 메인 화면 구성
st.title("📈 랩어카운트 통합 대시보드")

# 1. 상단: 증시 지수
market = get_market_data()
cols = st.columns(4)
for i, (name, val) in enumerate(market.items()):
    cols[i].metric(name, f"{val:+.2f}%")

st.markdown("---")

# 2. 랩 연도별 수익률 그래프
df = load_data()
st.subheader("📊 랩 연도별 원금 대비 수익률")

# 숫자 변환을 위한 전처리
df['수익률_num'] = df['원금대비수익률'].astype(str).str.replace('%', '').str.replace('None', '0').astype(float)
df['연도'] = pd.to_datetime(df['투자시작일']).dt.year

fig = px.bar(df, x='연도', y='수익률_num', color='계좌명', barmode='group', title="연도별 수익률 현황")
st.plotly_chart(fig, use_container_width=True)

# 3. 하단: 상세 표
st.dataframe(df[['고객명', '계좌명', '투자시작일', '원금대비수익률', '총수익률']])
