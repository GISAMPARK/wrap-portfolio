import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")

# 💡 기삼님이 주신 진짜 완벽한 시트 아이디!
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

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
    
    df.columns = df.columns.str.replace(' ', '')
    df.columns = df.columns.str.strip()
    
    if '총수익률(%)' in df.columns:
        df.rename(columns={'총수익률(%)': '수익률(%)'}, inplace=True)
    if '랩종류' in df.columns and '계좌명' not in df.columns:
        df.rename(columns={'랩종류': '계좌명'}, inplace=True)
    
    if '고객명' in df.columns:
        df = df.dropna(subset=['고객명'])
        df = df[df['고객명'].str.strip() != '']
        
    if '계좌명' not in df.columns:
        df['계좌명'] = '기본랩'
    else:
        df['계좌명'] = df['계좌명'].fillna('기본랩')
    
    cols_to_clean = ['초기투자금', '추가투자금', '정산수익금', '누적수익금', '투자원금', '총투자금', '평가자산', '원금대비수익률(%)', '수익률(%)']
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

st.title("📈 랩어카운트 수익 관리 대시보드")
st.caption("※ 데이터 추가/수정은 구글 스프레드시트에서 진행하시면 1분 내로 이곳에 자동 반영됩니다.")

# 여기서부터 try 문이 시작됩니다!
try:
    df = load_data()
    
    if not df.empty:
        st.success("✅ 구글 스프레드시트와 실시간 연동 중입니다.")
        
        client_list = df["고객명"].unique()
        tab_titles = ["🏆 랩 종류별 연도 평균"] + [mask_name(c) for c in client_list]
        tabs = st.tabs(tab_titles)
        
        # ==========================================
        # 1️⃣ 첫 번째 탭: 메인 요약 화면 (시뮬레이션 상단 배치)
        # ==========================================
        with tabs[0]:
            st.header("🏆 가입 연도 및 랩 종류별 고객 평균 수익률")
            
            latest_df = df.sort_values('날짜').groupby(['고객명', '계좌명']).tail(1).copy()
            latest_df['가입연도'] = latest_df['투자시작일'].astype(str).str.strip().str[:4] + "년"
            
            if '수익률(%)' in latest_df.columns and '원금대비수익률(%)' in latest_df.columns:
                yearly_avg = latest_df.groupby(['가입연도', '계좌명'])[['원금대비수익률(%)', '수익률(%)']].mean().reset_index()
                yearly_avg = yearly_avg.round(2)
                
                account_types = yearly_avg['계좌명'].unique()
                
                for acc in account_types:
                    st.markdown(f"### 📊 [{acc}] 가입 연도별 평균 수익률 비교")
                    acc_data = yearly_avg[yearly_avg['계좌명'] == acc]
                    
                    st.markdown(f"**💡 [{acc}] 1,000만 원 투자 시뮬레이션 (원금대비 기준)**")
                    cols = st.columns(len(acc_data))
                    for idx, (_, row) in enumerate(acc_data.iterrows()):
                        year = row['가입연도']
                        avg_prin = row['원금대비수익률(%)']
                        simul_prin = 10000000 * (avg_prin / 100)
                        
                        with cols[idx]:
                            if avg_prin >= 100:
                                st.success(f"**{year} 가입자 평균**\n\n👉 **{simul_prin:,.0f}원** ({avg_prin}%) 📈")
                            else:
                                st.warning(f"**{year} 가입자 평균**\n\n👉 **{simul_prin:,.0f}원** ({avg_prin}%) 📉")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    acc_data_melted = acc_data.melt(id_vars=['가입연도'], value_vars=['원금대비수익률(%)', '수익률(%)'], 
                                                    var_name='수익률 종류', value_name='평균(%)')
                    
                    acc_data_melted['수익률 종류'] = acc_data_melted['수익률 종류'].replace({
                        '원금대비수익률(%)': '🟠 원금대비 수익률',
                        '수익률(%)': '🔵 총 수익률'
                    })
                    
                    fig_year = px.bar(acc_data_melted, x='가입연도', y='평균(%)', color='수익률 종류', 
                                      barmode='group', text='평균(%)',
                                      color_discrete_map={'🟠 원금대비 수익률': '#FF7F0E', '🔵 총 수익률': '#1F77B4'})
                    
                    fig_year.update_traces(
                        texttemplate='<b>%{text:.2f}%</b>', 
                        textposition='outside',
                        textfont=dict(size=18, color='black')
                    )
                    
                    y_max = acc_data_melted['평균(%)'].max()
                    y_min = acc_data_melted['평균(%)'].min()
                    fig_year.update_layout(yaxis=dict(range=[min(0, y_min * 1.2), y_max * 1.3]), legend_title_text='')
                    st.plotly_chart(fig_year, use_container_width=True)
                    
                    st.markdown("<hr style='border: 2px dashed #bbb;'><br>", unsafe_allow_html=True)
            else:
                st.warning("⚠️ 구글 시트에 '수익률(%)' 또는 '원금대비수익률(%)' 항목이 없습니다.")
        
        # ==========================================
        # 2️⃣ 개별 고객 탭: 이름 마스킹 분리 & 3단 요약
        # ==========================================
        for i, client in enumerate(client_list):
            with tabs[i+1]:
                client_df = df[df["고객명"] == client].sort_values(by="날짜")
                account_list = client_df['계좌명'].unique()
                
                safe_client_name = mask_name(client)
                
                c_start = client_df["투자시작일"].iloc[0] if "투자시작일" in client_df.columns else "정보없음"
                st.info(f"👤 **{safe_client_name}** 고객님 | 📅 최초 투자 시작일: **{c_start}** | 📂 보유 계좌: **{len(account_list)}개**")
                
                for acc_idx, account in enumerate(account_list):
                    st.markdown(f"### 📊 [{account}] 운용 현황")
                    
                    acc_df = client_df[client_df['계좌명'] == account]
                    latest_data = acc_df.iloc[-1]
                    
                    st.markdown("##### 1️⃣ 투자 원금 구성")
                    col1, col2, col3 = st.columns(3)
                    if "초기투자금" in acc_df.columns:
                        col1.metric("초기투자금", f"{latest_data['초기투자금']:,.0f}원")
                    if "추가투자금" in acc_df.columns:
                        col2.metric("➕ 추가투자금", f"{latest_data['추가투자금']:,.0f}원")
                    if "투자원금" in acc_df.columns:
                        col3.metric("🟰 투자원금", f"{latest_data['투자원금']:,.0f}원")
                    
                    st.markdown("##### 2️⃣ 정산 및 운용 자금")
                    col4, col5, col_empty = st.columns(3)
                    if "누적수익금" in acc_df.columns:
                        col4.metric("💰 총 누적(정산)수익금", f"{latest_data['누적수익금']:,.0f}원")
                    if "총투자금" in acc_df.columns:
                        col5.metric("🏦 총투자금", f"{latest_data['총투자금']:,.0f}원")
                        
                    st.markdown("##### 3️⃣ 현재 평가 자산 및 수익률")
                    col6, col7, col8 = st.columns(3)
                    if "평가자산" in acc_df.columns:
                        col6.metric("💎 현재 평가자산", f"{latest_data['평가자산']:,.0f}원")
                    if "원금대비수익률(%)" in acc_df.columns:
                        col7.metric("🟠 원금대비 수익률", f"{latest_data['원금대비수익률(%)']}%")
                    if "수익률(%)" in acc_df.columns:
                        col8.metric("🔵 총 수익률", f"{latest_data['수익률(%)']}%")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if "원금대비수익률(%)" in acc_df.columns:
                        fig1 = px.line(acc_df, x="날짜", y="원금대비수익률(%)", markers=True, 
                                      title=f"🟠 {safe_client_name} 고객님의 [{account}] 원금대비 수익률 추이",
                                      color_discrete_sequence=['#FF7F0E'])
                        fig1.update_traces(line=dict(width=3), marker=dict(size=8))
                        
                        if "정산수익금" in acc_df.columns:
                            settlements = acc_df[acc_df["정산수익금"] != 0]
                            if not settlements.empty:
                                fig1.add_scatter(
                                    x=settlements["날짜"], y=settlements["원금대비수익률(%)"],
                                    mode="markers+text", marker=dict(color="red", size=16, symbol="star"),
                                    text=["<b>💰정산</b>"] * len(settlements), textposition="top center",
                                    textfont=dict(color="red", size=16), name="정산 발생 시점"
                                )
                        st.plotly_chart(fig1, use_container_width=True)
                        
                    if "수익률(%)" in acc_df.columns:
                        fig2 = px.line(acc_df, x="날짜", y="수익률(%)", markers=True, 
                                      title=f"🔵 {safe_client_name} 고객님의 [{account}] 총 수익률 추이",
                                      color_discrete_sequence=['#1F77B4'])
                        fig2.update_traces(line=dict(width=3), marker=dict(size=8))
                        
                        if "정산수익금" in acc_df.columns:
                            settlements = acc_df[acc_df["정산수익금"] != 0]
                            if not settlements.empty:
                                fig2.add_scatter(
                                    x=settlements["날짜"], y=settlements["수익률(%)"],
                                    mode="markers+text", marker=dict(color="red", size=16, symbol="star"),
                                    text=["<b>💰정산</b>"] * len(settlements), textposition="top center",
                                    textfont=dict(color="red", size=16), name="정산 발생 시점"
                                )
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    if "수익률(%)" in acc_df.columns and "원금대비수익률(%)" in acc_df.columns:
                        latest_tot = latest_data["수익률(%)"]
                        latest_prin = latest_data["원금대비수익률(%)"]
                        
                        simul_tot = 10000000 * (latest_tot / 100)
                        simul_prin = 10000000 * (latest_prin / 100)
                        
                        st.markdown("---")
                        st.subheader("💡 1,000만 원 투자 시뮬레이션 비교")
                        scol1, scol2 = st.columns(2)
                        
                        with scol1:
                            st.markdown("##### 🟠 원금대비 수익률 기준")
                            if latest_prin >= 100:
                                st.success(f"현재 수익률 **{latest_prin}%** 기준\n\n👉 **{simul_prin:,.0f}원** 📈")
                            else:
                                st.warning(f"현재 수익률 **{latest_prin}%** 기준\n\n👉 **{simul_prin:,.0f}원** 📉")
                                
                        with scol2:
                            st.markdown("##### 🔵 총 수익률 기준")
                            if latest_tot >= 100:
                                st.success(f"현재 수익률 **{latest_tot}%** 기준\n\n👉 **{simul_tot:,.0f}원** 📈")
                            else:
                                st.warning(f"현재 수익률 **{latest_tot}%** 기준\n\n👉 **{simul_tot:,.0f}원** 📉")
                    
                    if acc_idx < len(account_list) - 1:
                        st.markdown("<hr style='border: 2px dashed #bbb; margin-top: 30px; margin-bottom: 30px;'>", unsafe_allow_html=True)
                        
    else:
        st.info("구글 스프레드시트에 아직 입력된 데이터가 없습니다.")

# 🚨 이 아랫부분(except)이 잘려 나가서 에러가 났던 것입니다! 꼭 끝까지 복사해 주세요!
except Exception as e:
    st.error("데이터를 불러오거나 계산하는 중 오류가 발생했습니다.")
    st.write("🔧 상세 에러:", e)
