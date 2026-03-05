import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")

# 💡 기삼님의 시트 아이디
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

# 🛡️ 이름 자동 마스킹 함수
def mask_name(name):
    name = str(name).strip()
    if len(name) <= 1:
        return name
    elif len(name) == 2:
        return name[0] + "*"
    else:
        return name[0] + "*" * (len(name) - 2) + name[-1]

@st.cache_data(ttl=60)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
    
    # 1. 고객명 빈칸 정리 및 마스킹
    if '고객명' in df.columns:
        df = df.dropna(subset=['고객명'])
        df = df[df['고객명'].str.strip() != '']
        df['고객명'] = df['고객명'].apply(mask_name)
        
    # ⭐ [핵심 방어막] 시트에 '계좌명' 칸이 없거나 비어있으면 '기본랩'으로 묶어줍니다!
    if '계좌명' not in df.columns:
        df['계좌명'] = '기본랩'
    else:
        df['계좌명'] = df['계좌명'].fillna('기본랩')
    
    # 2. 숫자 형식 변환 (₩, %, 쉼표 제거)
    cols_to_clean = ['초기투자금', '추가투자금', '총투자금', '평가자산', '수익률(%)']
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

st.title("📈 랩어카운트 수익 관리 대시보드")
st.caption("※ 데이터 추가/수정은 구글 스프레드시트에서 진행하시면 1분 내로 이곳에 자동 반영됩니다.")

try:
    df = load_data()
    
    if not df.empty:
        st.success("✅ 구글 스프레드시트와 실시간 연동 중입니다.")
        client_list = df["고객명"].unique()
        tabs = st.tabs(["🏆 가입연도별 평균"] + list(client_list))
        
        # ==========================================
        # 1️⃣ 첫 번째 탭: 가입연도 및 랩 종류별 평균
        # ==========================================
        with tabs[0]:
            st.subheader("📅 가입 연도 및 계좌(랩) 종류별 고객 평균 수익률")
            
            # 가입연도와 '계좌명'을 기준으로 최신 데이터를 뽑아냅니다.
            latest_df = df.sort_values('날짜').groupby(['고객명', '계좌명']).tail(1).copy()
            latest_df['가입연도'] = latest_df['투자시작일'].astype(str).str[:4] + "년"
            
            # 연도별 + 계좌별 평균을 냅니다.
            yearly_avg = latest_df.groupby(['가입연도', '계좌명'])['수익률(%)'].mean().reset_index()
            yearly_avg.rename(columns={'수익률(%)': '평균 수익률(%)'}, inplace=True)
            yearly_avg['평균 수익률(%)'] = yearly_avg['평균 수익률(%)'].round(2)
            
            # ⭐ barmode='group'을 써서 국내랩/미국랩 막대를 나란히 비교해줍니다!
            fig_year = px.bar(yearly_avg, x='가입연도', y='평균 수익률(%)', color='계좌명', barmode='group',
                              text='평균 수익률(%)', title="가입 연도 및 랩 종류에 따른 평균 수익률 비교")
            
            fig_year.update_traces(
                texttemplate='<b>%{text:.2f}%</b>', 
                textposition='outside',
                textfont=dict(size=20, color='black'),
                width=0.35  # 막대 굵기 날씬하게 유지!
            )
            
            y_max = yearly_avg['평균 수익률(%)'].max()
            y_min = yearly_avg['평균 수익률(%)'].min()
            fig_year.update_layout(yaxis=dict(range=[min(0, y_min * 1.2), y_max * 1.4]))
            st.plotly_chart(fig_year, use_container_width=True)
            
            # 시뮬레이션 박스 표시
            st.markdown("---")
            st.subheader("💡 랩 종류별 1,000만 원 투자 시뮬레이션")
            
            cols = st.columns(len(yearly_avg))
            for idx, row in yearly_avg.iterrows():
                year = row['가입연도']
                acc = row['계좌명']
                avg_return = row['평균 수익률(%)']
                simul_amount = 10000000 * (avg_return / 100)
                
                with cols[idx]:
                    st.markdown(f"**{year} ({acc})**")
                    if avg_return >= 100:
                        st.success(f"평균 {avg_return}% 📈\n\n**{simul_amount:,.0f}원**")
                    else:
                        st.warning(f"평균 {avg_return}% 📉\n\n**{simul_amount:,.0f}원**")
        
        # ==========================================
        # 2️⃣ 개별 고객 탭: 계좌별로 상단/하단 분리!
        # ==========================================
        for i, client in enumerate(client_list):
            with tabs[i+1]:
                client_df = df[df["고객명"] == client].sort_values(by="날짜")
                account_list = client_df['계좌명'].unique() # 이 고객이 가진 계좌 종류들을 파악!
                
                c_start = client_df["투자시작일"].iloc[0] if "투자시작일" in client_df.columns else "정보없음"
                st.info(f"👤 **{client}** 고객님 | 📅 최초 투자 시작일: **{c_start}** | 📂 보유 계좌: **{len(account_list)}개**")
                
                # 고객이 가진 계좌 개수만큼 아래로 층을 나눠서 그려줍니다.
                for acc_idx, account in enumerate(account_list):
                    st.markdown(f"### 📊 [{account}] 운용 현황")
                    
                    # 해당 계좌 데이터만 쏙 빼냅니다.
                    acc_df = client_df[client_df['계좌명'] == account]
                    latest_data = acc_df.iloc[-1]
                    
                    # 요약 박스 (4칸)
                    col1, col2, col3, col4 = st.columns(4)
                    if "초기투자금" in acc_df.columns:
                        col1.metric("초기투자금", f"{latest_data['초기투자금']:,.0f}원")
                    if "추가투자금" in acc_df.columns:
                        col2.metric("추가투자금", f"{latest_data['추가투자금']:,.0f}원")
                    if "총투자금" in acc_df.columns:
                        col3.metric("총투자금", f"{latest_data['총투자금']:,.0f}원")
                    if "평가자산" in acc_df.columns:
                        col4.metric("현재 평가자산", f"{latest_data['평가자산']:,.0f}원", f"{latest_data['수익률(%)']}%")
                    
                    # 라인 그래프
                    fig = px.line(acc_df, x="날짜", y="수익률(%)", markers=True, 
                                  title=f"{client} 고객님의 [{account}] 누적 수익률 추이")
                    fig.update_traces(line=dict(width=3), marker=dict(size=8))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 시뮬레이션
                    latest_return = latest_data["수익률(%)"]
                    simul_amount = 10000000 * (latest_return / 100)
                    
                    if latest_return >= 100:
                        st.success(f"현재 수익률 **{latest_return}%** 기준, 1,000만 원 투자 시 👉 **{simul_amount:,.0f}원** 📈")
                    else:
                        st.warning(f"현재 수익률 **{latest_return}%** 기준, 1,000만 원 투자 시 👉 **{simul_amount:,.0f}원** 📉")
                    
                    # 계좌가 여러 개면 중간에 예쁜 점선 절취선을 그어줍니다.
                    if acc_idx < len(account_list) - 1:
                        st.markdown("<hr style='border: 2px dashed #bbb; margin-top: 30px; margin-bottom: 30px;'>", unsafe_allow_html=True)
                        
    else:
        st.info("구글 스프레드시트에 아직 입력된 데이터가 없습니다.")

except Exception as e:
    st.error("데이터를 불러오거나 계산하는 중 오류가 발생했습니다.")
    st.write("🔧 상세 에러:", e)
