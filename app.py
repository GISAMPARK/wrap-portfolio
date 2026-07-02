import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
    # 데이터 제목 강제 고정
    df.columns = ['투자시작일', '날짜', '계좌명', '고객명', '초기투자금', '추가투자금', '정산수익금', '누적수익금', '투자원금', '총투자금', '평가자산', '원금대비수익률', '총수익률']
    return df

@st.cache_data(ttl=900)
def get_market_data():
    tickers = {"코스피": "^KS11", "코스닥": "^KQ11", "S&P 500": "^GSPC", "나스닥": "^IXIC"}
    results = {}
    total_change = 0
    for name, ticker in tickers.items():
        try:
            tk = yf.Ticker(ticker)
            hist = tk.history(period="2d")
            if len(hist) >= 2:
                change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                results[name] = change
                total_change += change
        except:
            results[name] = None
    return results, total_change

# 메인 실행
st.title("📈 랩어카운트 수익 관리 대시보드")
df = load_data()
market_data, total_change = get_market_data()

# 곰돌이 출력
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("## " + ("🐻☀️" if total_change >= 0 else "🐻☔"))
with col2:
    for name, change in market_data.items():
        if change is not None:
            st.write(f"**{name}**: {change:+.2f}%")

# 고객 선택
client_list = df['고객명'].dropna().unique()
selected_client = st.selectbox("고객을 선택하세요", client_list)
client_df = df[df['고객명'] == selected_client]

st.markdown("### 📅 계좌별 최초 가입일")
for _, row in client_df.drop_duplicates('계좌명').iterrows():
    st.write(f"- **{row['계좌명']}** 최초가입일: {row['투자시작일']}")

st.markdown("### 💰 정산 이력")
found = False
for _, row in client_df.iterrows():
    val = str(row['정산수익금']).replace('W', '').replace(',', '').strip()
    try:
        if float(val) > 0:
            st.write(f"- 정산 발생: 수익금 {row['정산수익금']} | 원금대비 {row['원금대비수익률']} | 총수익률 {row['총수익률']}")
            found = True
    except:
        continue

if not found:
    st.write("선택하신 고객은 정산 내역이 없습니다.")
