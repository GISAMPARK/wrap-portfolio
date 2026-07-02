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

# --- 메인 실행 ---
st.title("📈 랩어카운트 수익 관리 대시보드")
df = load_data()

# 1. 메인 화면: 전체 랩 평균 수익률 (평균 수익률 계산)
st.subheader("📊 전체 랩 평균 수익률")
# 숫자가 아닌 'W' 등 제거 후 평균 계산
df['총수익률_num'] = df['총수익률'].astype(str).str.replace('%', '').astype(float)
avg_yield = df['총수익률_num'].mean()
st.metric(label="현재 전체 평균 수익률", value=f"{avg_yield:.2f}%")

st.markdown("---")

# 2. 고객 선택 및 상세 정보 (고객별 정산수익금/수익률)
st.subheader("👤 고객별 상세 관리")
client_list = df['고객명'].dropna().unique()
selected_client = st.selectbox("고객을 선택하세요", client_list)
client_df = df[df['고객명'] == selected_client]

st.markdown(f"### {selected_client}님 상세 현황")

# 최초가입일
st.markdown("📅 **계좌별 최초 가입일**")
for _, row in client_df.drop_duplicates('계좌명').iterrows():
    st.write(f"- {row['계좌명']}: {row['투자시작일']}")

# 정산 수익금 및 수익률
st.markdown("💰 **정산 상세 정보**")
found = False
for _, row in client_df.iterrows():
    # 데이터가 유효한 경우만 출력
    val = str(row['정산수익금']).replace('W', '').replace(',', '').strip()
    if val and val != 'None' and val != '0' and val != 'nan':
        st.write(f"- 정산 수익금: {row['정산수익금']} | 원금대비 수익률: {row['원금대비수익률']} | 총 수익률: {row['총수익률']}")
        found = True

if not found:
    st.write("해당 고객의 정산 내역이 없습니다.")
