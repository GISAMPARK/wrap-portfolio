import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")

# 👇 여기에 아까 복사해둔 구글 시트 아이디를 따옴표 안에 붙여넣으세요! 👇
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"
# 데이터 불러오기 (1분마다 새로고침)
@st.cache_data(ttl=60)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
    return df

st.title("📈 랩어카운트 수익 관리 대시보드")
st.caption("※ 데이터 추가/수정은 구글 스프레드시트에서 진행하시면 1분 내로 이곳에 자동 반영됩니다.")

try:
    df = load_data()
    
    if not df.empty:
        st.success("✅ 구글 스프레드시트와 실시간 연동 중입니다.")
        client_list = df["고객명"].unique()
        tabs = st.tabs(["🏆 가입연도별 평균"] + list(client_list))
        
        # --- 첫 번째 탭: 가입연도별 평균 ---
        with tabs[0]:
            st.subheader("📅 가입 연도별 고객 평균 수익률")
            latest_df = df.sort_values('날짜').groupby('고객명').tail(1).copy()
            latest_df['가입연도'] = latest_df['투자시작일'].astype(str).str[:4] + "년"
            
            yearly_avg = latest_df.groupby('가입연도')['수익률(%)'].mean().reset_index()
            yearly_avg.rename(columns={'수익률(%)': '평균 수익률(%)'}, inplace=True)
            yearly_avg['평균 수익률(%)'] = yearly_avg['평균 수익률(%)'].round(2)
            
            fig_year = px.bar(yearly_avg, x='가입연도', y='평균 수익률(%)', text='평균 수익률(%)', 
                              color='가입연도', title="가입 연도에 따른 현재 평균 수익률")
            fig_year.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_year.update_layout(yaxis=dict(range=[yearly_avg['평균 수익률(%)'].min() * 1.2, yearly_avg['평균 수익률(%)'].max() * 1.3]))
            st.plotly_chart(fig_year, use_container_width=True)
        
        # --- 나머지 탭: 개별 고객 그래프 ---
        for i, client in enumerate(client_list):
            with tabs[i+1]:
                client_df = df[df["고객명"] == client].sort_values(by="날짜")
                
                if "투자시작일" in client_df.columns and not client_df.empty:
                    c_start = client_df["투자시작일"].iloc[0]
                    st.info(f"👤 **{client}** 고객님 | 📅 투자 시작일: **{c_start}**")
                
                fig = px.line(client_df, x="날짜", y="수익률(%)", markers=True, 
                              title=f"{client} 고객님 누적 수익률 추이")
                fig.update_traces(line=dict(width=3), marker=dict(size=8))
                st.plotly_chart(fig, use_container_width=True)
                
                # 1000만원 투자 시뮬레이션
                latest_return = client_df.iloc[-1]["수익률(%)"]
                simul_amount = 10000000 * (1 + (latest_return / 100))
                
                st.markdown("---")
                st.subheader("💡 1,000만 원 투자 시뮬레이션")
                if latest_return >= 0:
                    st.success(f"현재 누적 수익률 **{latest_return}%**를 기준으로, 처음에 **1,000만 원**을 투자하셨다면 현재 **{simul_amount:,.0f}원**이 되어있습니다. 📈")
                else:
                    st.warning(f"현재 누적 수익률 **{latest_return}%**를 기준으로, 처음에 **1,000만 원**을 투자하셨다면 현재 **{simul_amount:,.0f}원**입니다. 장기적인 관점에서 회복을 기대할 수 있습니다. 📉")
    else:
        st.info("구글 스프레드시트에 아직 입력된 데이터가 없습니다.")

except Exception as e:
    st.error("구글 스프레드시트 연결을 확인해주세요. (시트 아이디가 맞는지, 공유 설정이 '모든 사용자'로 되어있는지 확인)")
