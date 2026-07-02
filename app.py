import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

# 1. 증시 데이터 및 곰돌이
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

# 2. 데이터 로드
@st.cache_data(ttl=60)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.replace(' ', '').str.strip()
    return df

# --- 메인 실행 ---
st.title("📈 랩어카운트 수익 관리 대시보드")
try:
    df = load_data()
    market_data, total_change = get_market_data()

    # 곰돌이 섹션
    col1, col2 = st.columns([1, 4])
    with col1:
        if total_change >= 0:
            st.markdown("## 🐻☀️")
            st.write("상승장! 웃는 곰돌이")
        else:
            st.markdown("## 🐻☔")
            st.write("하락장... 비 오는 곰돌이")
    with col2:
        for name, change in market_data.items():
            st.write(f"**{name}**: {change:+.2f}%" if change is not None else f"**{name}**: 데이터 없음")

    # 고객 선택
    st.subheader("고객 상세 현황")
    client_list = df['고객명'].unique()
    selected_client = st.selectbox("고객을 선택하세요", client_list)
    client_df = df[df['고객명'] == selected_client]

    # ⚠️ 중요: 구글 시트 제목 확인
    # 기삼님의 시트 제목과 아래 '최초가입일', '정산금액', '연차', '원금대비수익률(%)' 글자가 똑같아야 합니다!
    
    st.markdown("#### 📅 계좌별 최초 가입일")
    for _, row in client_df.drop_duplicates('계좌명').iterrows():
        # 시트 제목이 '최초가입일'이 아니라면 이 이름을 바꾸세요!
        reg_date = row.get('최초가입일', '정보없음') 
        st.write(f"- {row['계좌명']} 최초가입일: {reg_date}")

    st.markdown("#### 💰 정산 이력")
    for _, row in client_df.iterrows():
        # 시트 제목이 '정산금액' 등이 아니라면 수정하세요!
        if row.get('정산금액', 0) > 0:
            year = row.get('연차', '기타')
            yield1 = row.get('원금대비수익률(%)', 0)
            yield2 = row.get('총투자금대비수익률(%)', 0)
            st.write(f"- {year}차 정산 - 원금대비 수익률 {yield1}%, 총 투자금 대비 수익률 {yield2}%")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류 발생: {e}")
    st.write("데이터 컬럼 상태를 확인해보세요:", df.columns.tolist() if 'df' in locals() else "데이터 로드 실패")
