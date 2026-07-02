import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.replace(' ', '').str.replace('"', '').str.strip()
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

# --- 메인 실행 ---
st.title("📈 랩어카운트 수익 관리 대시보드")
try:
    df = load_data()
    market_data, total_change = get_market_data()

    # 곰돌이 지수
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("## " + ("🐻☀️" if total_change >= 0 else "🐻☔"))
    with col2:
        for name, change in market_data.items():
            if change is not None:
                st.write(f"**{name}**: {change:+.2f}%")

    client_list = df['고객명'].dropna().unique()
    selected_client = st.selectbox("고객을 선택하세요", client_list)
    client_df = df[df['고객명'] == selected_client]

    st.markdown("### 📅 계좌별 최초 가입일")
    for _, row in client_df.drop_duplicates('계좌명').iterrows():
        # 데이터가 없을 경우를 대비하여 .get() 사용
        date_val = row.get('투자시작일', '정보없음')
        st.write(f"- **{row['계좌명']}** 최초가입일: {date_val}")

    st.markdown("### 💰 정산 이력")
    # 정산수익금이 'None'이거나 비어있지 않은 것만 필터링
    filtered_df = client_df[client_df['정산수익금'].notnull() & (client_df['정산수익금'] != 'None')]
    
    if not filtered_df.empty:
        for _, row in filtered_df.iterrows():
            y1 = row.get('원금대비수익률(%)', '0')
            y2 = row.get('총수익률(%)', '0')
            st.write(f"- 정산 발생 - 원금대비: {y1}, 총수익률: {y2}")
    else:
        st.write("정산 이력이 없습니다.")

except Exception as e:
    st.error(f"코드 오류: {e}")
