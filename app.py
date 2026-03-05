import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")

# 💡 기삼님의 시트 아이디
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

# 🛡️ 고객 보호를 위한 '이름 자동 마스킹' 함수
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
    
    if '고객명' in df.columns:
        df = df.dropna(subset=['고객명'])
        df = df[df['고객명'].str.strip() != '']
        df['고객명'] = df['고객명'].apply(mask_name)
    
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
            
            # ⭐ 수정 요청사항: 막대를 얇게(width=0.4), 글씨를 크고 진하게!
            fig_year.update_traces(
                texttemplate='<b>%{text:.2f}%</b>', 
                textposition='outside',
                textfont=dict(size=22, color='black'),
                width=0.4
            )
            
            y_max = yearly_avg['평균 수익률(%)'].max()
            y_min = yearly_avg['평균 수익률(%)'].min()
            # 글씨가 잘리지 않게 위쪽 공간을 넉넉히 확보합니다.
            fig_year.update_layout(yaxis=dict(range=[min(0, y_min * 1.2), y_max * 1.4]))
            st.plotly_chart(fig_year, use_container_width=True)
            
            # ⭐ 수정 요청사항: 기삼님 시트 로직에 맞춘 1000만 원 시뮬레이션
            st.markdown("---")
            st.subheader("💡 가입 연도별 1,000만 원 투자 시뮬레이션")
            
            cols = st.columns(len(yearly_avg))
            for idx, row in yearly_avg.iterrows():
                year = row['가입연도']
                avg_return = row['평균 수익률(%)']
                
                # 원금에 퍼센트를 그대로 곱합니다. (예: 1000만 * 99.44% = 994만4천원)
                simul_amount = 10000000 * (avg_return / 100)
                
                with cols[idx]:
                    st.markdown(f"**{year} 가입자 평균**")
                    if avg_return >= 100:
                        st.success(f"평균 {avg_return}% 📈\n\n**{simul_amount:,.0f}원**")
                    else:
                        st.warning(f"평균 {avg_return}% 📉\n\n**{simul_amount:,.0f}원**")
        
        # --- 나머지 탭: 개별 고객 그래프 ---
        for i, client in enumerate(client_list):
            with tabs[i+1]:
                client_df = df[df["고객명"] == client].sort_values(by="날짜")
                latest_data = client_df.iloc[-1]
                
                c_start = latest_data.get("투자시작일", "정보없음")
                st.info(f"👤 **{client}** 고객님 | 📅 투자 시작일: **{c_start}**")
                
                col1, col2, col3, col4 = st.columns(4)
                if "초기투자금" in df.columns:
                    col1.metric("초기투자금", f"{latest_data['초기투자금']:,.0f}원")
                if "추가투자금" in df.columns:
                    col2.metric("추가투자금", f"{latest_data['추가투자금']:,.0f}원")
                if "총투자금" in df.columns:
                    col3.metric("총투자금", f"{latest_data['총투자금']:,.0f}원")
                if "평가자산" in df.columns:
                    col4.metric("현재 평가자산", f"{latest_data['평가자산']:,.0f}원", f"{latest_data['수익률(%)']}%")
                
                fig = px.line(client_df, x="날짜", y="수익률(%)", markers=True, 
                              title=f"{client} 고객님 누적 수익률 추이")
                fig.update_traces(line=dict(width=3), marker=dict(size=8))
                st.plotly_chart(fig, use_container_width=True)
                
                # ⭐ 개별 고객 시뮬레이션 수정
                latest_return = latest_data["수익률(%)"]
                simul_amount = 10000000 * (latest_return / 100)
                
                st.markdown("---")
                st.subheader("💡 1,000만 원 투자 시뮬레이션")
                if latest_return >= 100:
                    st.success(f"현재 수익률 **{latest_return}%**를 기준으로, 처음에 **1,000만 원**을 투자하셨다면 현재 **{simul_amount:,.0f}원**이 되어있습니다. 📈")
                else:
                    st.warning(f"현재 수익률 **{latest_return}%**를 기준으로, 처음에 **1,000만 원**을 투자하셨다면 현재 **{simul_amount:,.0f}원**입니다. 장기적인 관점에서 회복을 기대할 수 있습니다. 📉")
    else:
        st.info("구글 스프레드시트에 아직 입력된 데이터가 없습니다.")

except Exception as e:
    st.error("데이터를 불러오거나 계산하는 중 오류가 발생했습니다.")
    st.write("🔧 상세 에러:", e)
