import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
    
    # 💡 핵심: 시트의 실제 제목이 무엇이든, 순서대로 우리만의 깔끔한 이름으로 재지정합니다.
    # 기삼님의 시트 열 순서에 맞춰 이름을 다시 정의했습니다.
    df.columns = [
        '투자시작일', '날짜', '계좌명', '고객명', '초기투자금', '추가투자금', 
        '정산수익금', '누적수익금', '투자원금', '총투자금', '평가자산', 
        '원금대비수익률', '총수익률'
    ]
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

    # 고객 선택
    client_list = df['고객명'].dropna().unique()
    selected_client = st.selectbox("고객을 선택하세요", client_list)
    client_df = df[df['고객명'] == selected_client]

    st.markdown("### 📅 계좌별 최초 가입일")
    for _, row in client_df.drop_duplicates('계좌명').iterrows():
        st.write(f"- **{row['계좌명']}** 최초가입일: {row['투자시작일']}")

    st.markdown("### 💰 정산 이력")
    # 정산수익금 열이 숫자인 경우만 표시
    has_data = False
    for _, row in client_df.iterrows():
        # 데이터가 'None' 텍스트이거나 비어있으면 건너뜁니다.
        val = str(row['정산수익금']).strip()
        if val and val != 'None' and val != 'nan':
            st.write(f"- 정산 발생 - 원금대비: {row['원금대비수익률']}, 총수익률: {row['총수익률']}")
            has_data = True
    
    if not has_data:
        st.write("정산 내역이 없습니다.")

except Exception as e:
    st.error(f"오류: {e}")
