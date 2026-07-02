import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
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

st.title("📈 랩어카운트 수익 관리 대시보드")
df = load_data()
market_data, total_change = get_market_data()

# 고객 선택
client_list = df['고객명'].dropna().unique()
selected_client = st.selectbox("고객을 선택하세요", client_list)
client_df = df[df['고객명'] == selected_client]

# 정산 이력 - 데이터 강제 출력 (핵심 수정)
st.markdown("### 💰 정산 이력")
found = False
for _, row in client_df.iterrows():
    # 데이터에서 'W'나 ','를 제거하고 숫자로 강제 변환하여 체크
    raw_val = str(row['정산수익금']).replace('W', '').replace(',', '').strip()
    try:
        val_float = float(raw_val)
        if val_float > 0: # 0보다 큰 수익금이 있으면 표시
            st.write(f"- 정산 발생: 수익금 {row['정산수익금']} | 원금대비 {row['원금대비수익률']} | 총수익률 {row['총수익률']}")
            found = True
    except:
        continue # 숫자가 아니면 패스

if not found:
    st.write("해당 고객의 정산 내역이 없습니다.")
