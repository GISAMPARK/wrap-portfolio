import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

st.set_page_config(layout="wide", page_title="투자 수익 관리 대시보드")

# ==========================================
# 🔒 프라이빗 보안: 비밀번호 잠금 기능
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔒 프라이빗 투자 관리")
        st.write("안전한 고객 데이터 관리를 위해 비밀번호를 입력해 주세요.")
        
        pwd = st.text_input("비밀번호", type="password")
        if st.button("입장하기"):
            if pwd == "0311":
                st.session_state["authenticated"] = True
                st.rerun()  
            else:
                st.error("🚨 비밀번호가 틀렸습니다. 다시 확인해 주세요.")
    
    st.stop()  

# ==========================================
# 💡 여기서부터 메인 대시보드 코드 시작
# ==========================================
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

def mask_name(name):
    name = str(name).strip()
    if len(name) <= 1:
        return name
    elif len(name) == 2:
        return name[0] + "*"
    else:
        return name[0] + "*" * (len(name) - 2) + name[-1]

@st.cache_data(ttl=900)
def get_market_indices():
    indices = {"코스피": "^KS11", "코스닥": "^KQ11", "S&P 500": "^GSPC", "나스닥": "^IXIC"}
    data = {}
    for name, ticker in indices.items():
        try:
            tk = yf.Ticker(ticker)
            hist = tk.history(period="10d")
            hist = hist.dropna(subset=['Close'])
            
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change_pct = ((current_price - prev_price) / prev_price) * 100
                data[name] = (current_price, change_pct)
            elif len(hist) == 1:
                data[name] = (hist['Close'].iloc[-1], 0.0)
            else:
                data[name] = (0, 0)
        except Exception:
            data[name] = (0, 0)
    return data

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
        df['계좌명'] = '기본투자'
    else:
        df['계좌명'] = df['계좌명'].fillna('기본투자')
        
    df['계좌명'] = df['계좌명'].astype(str).str.replace('랩', '투자')
    
    cols_to_clean = ['초기투자금', '추가투자금', '정산수익금', '누적수익금', '투자원금', '총투자금', '평가자산', '원금대비수익률(%)', '수익률(%)']
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    if '날짜' in df.columns:
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
            
    return df

st.title("📈 투자 수익 관리 대시보드")
st.caption("※ 데이터 추가/수정은 구글 스프레드시트에서 진행하시면 1분 내로 이곳에 자동 반영됩니다.")

try:
    df = load_data()
    
    if not df.empty:
        st.success("✅ 구글 스프레드시트와 실시간 연동 중입니다.")

        st.markdown("---")
        market_data = get_market_indices()
        
        sunny_bear = "<span style='font-size: 45px; vertical-align: middle;'>🐻☀️</span>"
        rainy_bear = "<span style='font-size: 45px; vertical-align: middle;'>🐻☔</span>"

        kr_trend = market_data['코스피'][1] + market_data['코스닥'][1]
        us_trend = market_data['S&P 500'][1] + market_data['나스닥'][1]
        
        kr_img = sunny_bear if kr_trend >= 0 else rainy_bear
        us_img = sunny_bear if us_trend >= 0 else rainy_bear
        
        col_kr, col_us = st.columns(2)
        
        with col_kr:
            st.markdown(f"#### 🇰🇷 국내 증시 {kr_img}", unsafe_allow_html=True)
            k1, k2 = st.columns(2)
            k1.metric(label="코스피", value=f"{market_data['코스피'][0]:,.2f}", delta=f"{market_data['코스피'][1]:.2f}%")
            k2.metric(label="코스닥", value=f"{market_data['코스닥'][0]:,.2f}", delta=f"{market_data['코스닥'][1]:.2f}%")
            
        with col_us:
            st.markdown(f"#### 🇺🇸 미국 증시 {us_img}", unsafe_allow_html=True)
            u1, u2 = st.columns(2)
            u1.metric(label="S&P 500", value=f"{market_data['S&P 500'][0]:,.2f}", delta=f"{market_data['S&P 500'][1]:.2f}%")
            u2.metric(label="나스닥", value=f"{market_data['나스닥'][0]:,.2f}", delta=f"{market_data['나스닥'][1]:.2f}%")
            
        st.markdown("---")
        
        client_list = df["고객명"].unique()
        tab_titles = ["🏆 투자 종류별 연도 평균"] + [mask_name(c) for c in client_list]
        tabs = st.tabs(tab_titles)
        
        # ==========================================
        # 1️⃣ 첫 번째 탭: 메인 요약 화면
        # ==========================================
        with tabs[0]:
            st.header("🏆 가입 연도 및 투자 종류에 따른 고객 평균 수익률")
            st.markdown("<br>", unsafe_allow_html=True)
            
            latest_df = df.sort_values('날짜').groupby(['고객명', '계좌명']).tail(1).copy()
            latest_df['가입연도'] = latest_df['투자시작일'].astype(str).str.strip().str[:4] + "년"
            
            # ✅ [핵심 기능] 해지/종료 고객 자동 필터링 로직
            if '날짜' in df.columns:
                global_max_date = df['날짜'].dropna().max()
                if pd.notnull(global_max_date):
                    # 고객의 마지막 업데이트 날짜가 최신 기준일보다 30일 이상 차이나면 운용 종료로 판단하고 평균에서 제외
                    latest_df = latest_df[(global_max_date - latest_df['날짜']).dt.days <= 30]
            
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
                                st.success(f"**{year} 현재 운용자 평균**\n\n👉 **{simul_prin:,.0f}원** ({avg_prin}%) 📈")
                            else:
                                st.warning(f"**{year} 현재 운용자 평균**\n\n👉 **{simul_prin:,.0f}원** ({avg_prin}%) 📉")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if '날짜' in df.columns and pd.notnull(global_max_date):
                        formatted_date = f"{global_max_date.year}년 {global_max_date.month}월 {global_max_date.day}일"
                        st.markdown(
                            f"<div style='font-size: 18px; font-weight: bold; margin-bottom: 8px;'>"
                            f"📅 기준일: <span style='color: #1F77B4;'>{formatted_date}</span>"
                            f"</div>", 
                            unsafe_allow_html=True
                        )
                    
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
        # 2️⃣ 개별 고객 탭
        # ==========================================
        for i, client in enumerate(client_list):
            with tabs[i+1]:
                client_df = df[df["고객명"] == client].sort_values(by="날짜")
                account_list = client_df['계좌명'].unique()
                
                safe_client_name = mask_name(client)
                
                c_start = client_df["투자시작일"].iloc[0] if "투자시작일" in client_df.columns else "정보없음"
                
                # 고객의 마지막 데이터가 30일 이상 지났으면 '운용 종료' 라벨 띄우기
                client_max_date = client_df['날짜'].max()
                status_badge = ""
                if '날짜' in df.columns and pd.notnull(global_max_date) and pd.notnull(client_max_date):
                    if (global_max_date - client_max_date).days > 30:
                        status_badge = " 🛑 [운용 종료/해지]"

                st.info(f"👤 **{safe_client_name}** 고객님{status_badge} | 📅 최초 투자 시작일: **{c_start}** | 📂 보유 계좌: **{len(account_list)}개**")
                
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
                        
                        fig1.update_traces(
                            line=dict(width=3), 
                            marker=dict(size=8),
                            hovertemplate="<br> 📅 <b>날짜:</b> %{x|%Y-%m-%d} <br> 📈 <b>수익률:</b> %{y}% <br><extra></extra>"
                        )
                        fig1.update_layout(
                            hoverlabel=dict(font_size=22)
                        )
                        
                        if "정산수익금" in acc_df.columns:
                            settlements = acc_df[acc_df["정산수익금"] != 0]
                            if not settlements.empty:
                                fig1.add_scatter(
                                    x=settlements["날짜"], y=settlements["원금대비수익률(%)"],
                                    mode="markers+text", marker=dict(color="red", size=16, symbol="star"),
                                    text=["<b>💰정산</b>"] * len(settlements), textposition="top center",
                                    textfont=dict(color="red", size=16), name="정산 발생 시점",
                                    hoverinfo='skip' 
                                )
                        st.plotly_chart(fig1, use_container_width=True)
                        
                    if "수익률(%)" in acc_df.columns:
                        fig2 = px.line(acc_df, x="날짜", y="수익률(%)", markers=True, 
                                      title=f"🔵 {safe_client_name} 고객님의 [{account}] 총 수익률 추이",
                                      color_discrete_sequence=['#1F77B4'])
                        
                        fig2.update_traces(
                            line=dict(width=3), 
                            marker=dict(size=8),
                            hovertemplate="<br> 📅 <b>날짜:</b> %{x|%Y-%m-%d} <br> 📈 <b>수익률:</b> %{y}% <br><extra></extra>"
                        )
                        fig2.update_layout(
                            hoverlabel=dict(font_size=22)
                        )
                        
                        if "정산수익금" in acc_df.columns:
                            settlements = acc_df[acc_df["정산수익금"] != 0]
                            if not settlements.empty:
                                fig2.add_scatter(
                                    x=settlements["날짜"], y=settlements["수익률(%)"],
                                    mode="markers+text", marker=dict(color="red", size=16, symbol="star"),
                                    text=["<b>💰정산</b>"] * len(settlements), textposition="top center",
                                    textfont=dict(color="red", size=16), name="정산 발생 시점",
                                    hoverinfo='skip'
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

except Exception as e:
    st.error("데이터를 불러오거나 계산하는 중 오류가 발생했습니다.")
    st.write("🔧 상세 에러:", e)
