import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

# 🐻 곰돌이 캐릭터 및 증시 데이터
@st.cache_data(ttl=900)
def get_market_data():
    tickers = {"코스피": "^KS11", "코스닥": "^KQ11", "S&P 500": "^GSPC", "나스닥": "^IXIC"}
    results = {}
    total_change = 0
    for name, ticker in tickers.items():
        tk = yf.Ticker(ticker)
        hist = tk.history(period="2d")
        if len(hist) >= 2:
            change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            results[name] = change
            total_change += change
    return results, total_change

@st.cache_data(ttl=60)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.replace(' ', '').str.strip()
    return df

# --- 메인 화면 ---
st.title("📈 랩어카운트 수익 관리 대시보드")
df = load_data()
market_data, total_change = get_market_data()

# 곰돌이 섹션
col1, col2 = st.columns([1, 4])
with col1:
    if total_change >= 0:
        st.markdown("## 🐻☀️")
        st.write("오늘은 상승장! 웃는 곰돌이")
    else:
        st.markdown("## 🐻☔")
        st.write("오늘은 하락장... 비 오는 곰돌이")
with col2:
    for name, change in market_data.items():
        st.write(f"**{name}**: {change:+.2f}%")

# 1. 최초 가입일 분리 및 정산 문구 (데이터가 '계좌명'과 '최초가입일' 컬럼을 가지고 있다고 가정)
st.subheader("고객 상세 현황")
selected_client = st.selectbox("고객을 선택하세요", df['고객명'].unique())
client_df = df[df['고객명'] == selected_client]

# 요청하신 1번: 계좌별 최초 가입일 기재
# 📅 계좌별 최초 가입일 표시 부분
st.markdown("#### 📅 계좌별 최초 가입일")
for _, row in client_df.drop_duplicates('계좌명').iterrows():
    # 여기서 '최초가입일'이라는 글자를 실제 기삼님 구글 시트의 제목과 똑같이 고쳐주세요!
    # 예: 만약 시트 제목이 '투자시작일'이라면 '최초가입일' 대신 '투자시작일'이라고 쓰세요.
    reg_date = row.get('최초가입일', '정보없음') 
    st.write(f"- {row['계좌명']} 최초가입일: {reg_date}")

# 요청하신 2번: 정산 문구
st.markdown("#### 💰 정산 이력")
for _, row in client_df.iterrows():
    if row.get('정산금액', 0) > 0:
        year = row['연차']
        yield_rate = row['원금대비수익률(%)']
        total_yield = row.get('총투자금대비수익률(%)', 0)
        st.write(f"- {year}차 정산 - 원금대비 수익률 {yield_rate}%, 총 투자금 대비 수익률 {total_yield}%")
