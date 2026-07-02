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

# 데이터 로드
df = load_data()

# 1. 메인 화면: 전체 현황
st.title("📈 랩어카운트 수익 관리 대시보드")
st.markdown("---")
st.subheader("📊 전체 랩 운용 현황")

# 평균 수익률 계산
temp_df = df['총수익률'].astype(str).str.replace('%', '').replace('None', '0')
avg_yield = pd.to_numeric(temp_df).mean()

col1, col2 = st.columns(2)
col1.metric("전체 평균 수익률", f"{avg_yield:.2f}%")
col2.metric("총 관리 고객수", f"{df['고객명'].nunique()}명")

st.markdown("---")

# 2. 개별 상세 관리
st.subheader("👤 고객별 상세 관리")
client_list = df['고객명'].dropna().unique()
selected_client = st.selectbox("조회할 고객을 선택하세요", client_list)
client_df = df[df['고객명'] == selected_client]

st.markdown(f"### 📋 {selected_client}님 상세 현황")

# 계좌별 가입일 표시
st.markdown("📅 **계좌별 최초 가입일**")
for _, row in client_df.drop_duplicates('계좌명').iterrows():
    st.write(f"- {row['계좌명']}: {row['투자시작일']}")

# 정산 정보 (숫자값만 깔끔하게 출력)
st.markdown("💰 **정산 상세 정보**")
details = client_df[client_df['정산수익금'].astype(str) != 'W0'][['정산수익금', '원금대비수익률', '총수익률']]

if not details.empty:
    st.table(details.rename(columns={'정산수익금': '수익금', '원금대비수익률': '원금대비(%)', '총수익률': '총수익(%)'}))
else:
    st.write("해당 고객의 정산 내역이 없습니다.")
