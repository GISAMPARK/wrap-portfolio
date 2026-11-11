import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

st.set_page_config(layout="wide", page_title="VVIP 종합 자산관리 대시보드")

# ==========================================
# 🔒 프라이빗 보안: 비밀번호 잠금 기능
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔒 VVIP 프라이빗 자산관리")
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
# 💡 데이터 연동 설정
# ==========================================
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

# 👇👇 [중요] 여기에 본사 대표계좌 시트의 GID 숫자를 입력해주세요! 👇👇
REP_SHEET_GID = "" 
# 👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆

PENSION_SHEET_GID = "951679806" # 새로 만드신 연금저축/IRP 탭의 GID

def mask_name(name):
    name = str(name).strip()
    if len(name) <= 1: return name
    elif len(name) == 2: return name[0] + "*"
    else: return name[0] + "*" * (len(name) - 2) + name[-1]

@st.cache_data(ttl=900)
def get_market_indices():
    indices = {"코스피": "^KS11", "코스닥": "^KQ11", "S&P 500": "^GSPC", "나스닥": "^IXIC"}
    data = {}
    for name, ticker in indices.items():
        try:
            tk = yf.Ticker(ticker)
            hist = tk.history(period="10d").dropna(subset=['Close'])
            if len(hist) >= 2:
                data[name] = (hist['Close'].iloc[-1], ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100)
            else:
                data[name] = (hist['Close'].iloc[-1] if len(hist)==1 else 0, 0.0)
        except:
            data[name] = (0, 0)
    return data

@st.cache_data(ttl=60)
def load_rep_data():
    if not REP_SHEET_GID: return pd.DataFrame()
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={REP_SHEET_GID}"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.replace('\n', '')
        for col in df.columns:
            if col != '상품명':
                df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def load_rap_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.replace(' ', '').str.strip()
        if '총수익률(%)' in df.columns: df.rename(columns={'총수익률(%)': '수익률(%)'}, inplace=True)
        if '랩종류' in df.columns and '계좌명' not in df.columns: df.rename(columns={'랩종류': '계좌명'}, inplace=True)
        df = df.dropna(subset=['고객명'])
        df = df[df['고객명'].str.strip() != '']
        if '계좌명' not in df.columns: df['계좌명'] = '기본투자'
        df['계좌명'] = df['계좌명'].astype(str).str.replace('랩', '투자')
        
        cols_to_clean = ['초기투자금', '추가투자금', '정산수익금', '누적수익금', '투자원금', '총투자금', '평가자산', '원금대비수익률(%)', '수익률(%)']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        if '날짜' in df.columns: df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def load_pension_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={PENSION_SHEET_GID}"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.replace(' ', '').str.strip()
        df = df.dropna(subset=['고객명'])
        cols_to_clean = ['납입원금', '평가금액', '올해납입액', '수익률(%)']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        if '날짜' in df.columns: df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        return df
    except: return pd.DataFrame()

# ==========================================
# 🖥️ 메인 화면 구성
# ==========================================
st.title("👑 VVIP 종합 자산관리 대시보드")
st.caption("※ 랩어카운트 및 연금/IRP 자산 통합 관리 시스템")

df_rap = load_rap_data()
df_pen = load_pension_data()
rep_df = load_rep_data()

st.markdown("---")
market_data = get_market_indices()
col_kr, col_us = st.columns(2)
with col_kr:
    st.markdown(f"#### 🇰🇷 국내 증시", unsafe_allow_html=True)
    k1, k2 = st.columns(2)
    k1.metric(label="코스피", value=f"{market_data['코스피'][0]:,.2f}", delta=f"{market_data['코스피'][1]:.2f}%")
    k2.metric(label="코스닥", value=f"{market_data['코스닥'][0]:,.2f}", delta=f"{market_data['코스닥'][1]:.2f}%")
with col_us:
    st.markdown(f"#### 🇺🇸 미국 증시", unsafe_allow_html=True)
    u1, u2 = st.columns(2)
    u1.metric(label="S&P 500", value=f"{market_data['S&P 500'][0]:,.2f}", delta=f"{market_data['S&P 500'][1]:.2f}%")
    u2.metric(label="나스닥", value=f"{market_data['나스닥'][0]:,.2f}", delta=f"{market_data['나스닥'][1]:.2f}%")
st.markdown("---")

tab_titles = ["🔍 VVIP 고객 포트폴리오 검색", "🏆 랩어카운트 전체 요약", "🏢 본사 대표 운용성과"]
tabs = st.tabs(tab_titles)

# ==========================================
# 1️⃣ 첫 번째 탭: 개별 고객 종합 자산 검색
# ==========================================
with tabs[0]:
    st.header("🔍 개별 고객 종합 포트폴리오 검색")
    
    all_clients = set()
    if not df_rap.empty: all_clients.update(df_rap["고객명"].dropna().unique())
    if not df_pen.empty: all_clients.update(df_pen["고객명"].dropna().unique())
    client_list = sorted(list(all_clients))
    
    selected_client = st.selectbox("👤 고객명 검색:", ["--- 고객을 선택하세요 ---"] + client_list)
    
    if selected_client != "--- 고객을 선택하세요 ---":
        client = selected_client
        safe_client_name = mask_name(client)
        
        # 데이터 필터링
        c_rap = df_rap[df_rap["고객명"] == client].sort_values(by="날짜") if not df_rap.empty else pd.DataFrame()
        c_pen = df_pen[df_pen["고객명"] == client].sort_values(by="날짜") if not df_pen.empty else pd.DataFrame()
        
        # 최신 자산 합산 계산
        total_rap_asset = 0
        total_pen_asset = 0
        
        if not c_rap.empty:
            for acc in c_rap['계좌명'].unique():
                total_rap_asset += c_rap[c_rap['계좌명'] == acc].iloc[-1].get('평가자산', 0)
                
        if not c_pen.empty:
            for acc in c_pen['계좌명'].unique():
                total_pen_asset += c_pen[c_pen['계좌명'] == acc].iloc[-1].get('평가금액', 0)
                
        total_asset = total_rap_asset + total_pen_asset
        
        # 👑 통합 자산 브리핑 (상단)
        st.markdown(f"## 👑 {safe_client_name} 고객님 종합 자산 브리핑")
        st.markdown(f"### 총 금융자산 평가액: **<span style='color:#CD2E3A;'>{total_asset:,.0f}원</span>**", unsafe_allow_html=True)
        
        # 📊 자산 비중 도넛 차트
        if total_asset > 0:
            pie_data = pd.DataFrame({
                '자산 구분': ['투자 자산 (랩어카운트)', '노후 자산 (연금/IRP)'],
                '금액': [total_rap_asset, total_pen_asset]
            })
            pie_data = pie_data[pie_data['금액'] > 0]
            
            fig_pie = px.pie(pie_data, values='금액', names='자산 구분', hole=0.5,
                             color='자산 구분', color_discrete_map={'투자 자산 (랩어카운트)':'#1F77B4', '노후 자산 (연금/IRP)':'#2CA02C'})
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_size=16)
            fig_pie.update_layout(showlegend=False, margin=dict(t=30, b=30, l=0, r=0))
            
            pc1, pc2, pc3 = st.columns([1, 2, 1])
            with pc2:
                st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("---")
        
        # 📑 자산별 상세 현황 탭
        sub_tabs = st.tabs(["📈 랩어카운트 상세", "🛡️ 연금 및 IRP 상세"])
        
        with sub_tabs[0]:
            if not c_rap.empty:
                account_list = c_rap['계좌명'].unique()
                for acc in account_list:
                    st.markdown(f"#### 📊 [{acc}] 운용 현황")
                    acc_df = c_rap[c_rap['계좌명'] == acc]
                    latest_data = acc_df.iloc[-1]
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("💎 평가자산", f"{latest_data.get('평가자산', 0):,.0f}원")
                    c2.metric("🟰 투자원금", f"{latest_data.get('투자원금', 0):,.0f}원")
                    c3.metric("🔵 총 수익률", f"{latest_data.get('수익률(%)', 0)}%")
                    
                    if "원금대비수익률(%)" in acc_df.columns:
                        fig1 = px.line(acc_df, x="날짜", y="원금대비수익률(%)", markers=True, title=f"🟠 {acc} 원금대비 수익률 추이")
                        fig1.update_traces(line=dict(width=3, color='#FF7F0E'))
                        st.plotly_chart(fig1, use_container_width=True)
                    st.markdown("<hr style='border: 1px dashed #ddd;'>", unsafe_allow_html=True)
            else:
                st.info("랩어카운트 투자 내역이 없습니다.")
                
        with sub_tabs[1]:
            if not c_pen.empty:
                pen_accounts = c_pen['계좌명'].unique()
                for acc in pen_accounts:
                    st.markdown(f"#### 🛡️ [{acc}] 자산 현황")
                    acc_df = c_pen[c_pen['계좌명'] == acc]
                    latest_data = acc_df.iloc[-1]
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("💎 평가금액", f"{latest_data.get('평가금액', 0):,.0f}원")
                    c2.metric("납입원금", f"{latest_data.get('납입원금', 0):,.0f}원")
                    c3.metric("📈 수익률(%)", f"{latest_data.get('수익률(%)', 0)}%")
                    
                    # 올해 세액공제 한도 진행률 바
                    yearly_paid = latest_data.get('올해납입액', 0)
                    progress = min(yearly_paid / 6000000, 1.0) # 연금저축 한도 600만원 기준 시각화
                    st.markdown(f"**💰 올해 납입액 (세액공제용):** {yearly_paid:,.0f}원 / 한도 6,000,000원")
                    st.progress(progress)
                    
                    if "수익률(%)" in acc_df.columns and len(acc_df) > 1:
                        fig2 = px.line(acc_df, x="날짜", y="수익률(%)", markers=True, title=f"🟢 {acc} 수익률 추이")
                        fig2.update_traces(line=dict(width=3, color='#2CA02C'))
                        st.plotly_chart(fig2, use_container_width=True)
                    st.markdown("<hr style='border: 1px dashed #ddd;'>", unsafe_allow_html=True)
            else:
                st.info("연금 및 IRP 자산 내역이 없습니다.")
    else:
        st.info("👆 위 검색창을 클릭하여 조회할 고객을 선택해 주세요.")

# ==========================================
# 2️⃣ 두 번째 탭: 랩어카운트 전체 요약 (기존 유지)
# ==========================================
with tabs[1]:
    st.header("🏆 가입 연도 및 투자 종류별 평균 수익률")
    if not df_rap.empty and '수익률(%)' in df_rap.columns:
        latest_df = df_rap.sort_values('날짜').groupby(['고객명', '계좌명']).tail(1).copy()
        if '투자시작일' in latest_df.columns:
            latest_df['가입연도'] = latest_df['투자시작일'].astype(str).str.strip().str[:4] + "년"
            yearly_avg = latest_df.groupby(['가입연도', '계좌명'])[['원금대비수익률(%)', '수익률(%)']].mean().reset_index().round(2)
            st.dataframe(yearly_avg, use_container_width=True)
            
            fig_bar = px.bar(yearly_avg, x='가입연도', y='수익률(%)', color='계좌명', barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("투자시작일 데이터가 필요합니다.")
    else:
        st.info("데이터를 불러오는 중이거나 아직 입력되지 않았습니다.")

# ==========================================
# 3️⃣ 세 번째 탭: 본사 대표 운용성과 (기존 유지)
# ==========================================
with tabs[2]:
    st.header("🏢 본사 대표계좌 운용성과")
    if not rep_df.empty:
        st.dataframe(rep_df, use_container_width=True)
        y1_cols = [c for c in rep_df.columns if '1Y' in c.upper()]
        if y1_cols and '상품명' in rep_df.columns:
            y1_col = y1_cols[0]
            plot_df = rep_df.dropna(subset=[y1_col]).sort_values(by=y1_col, ascending=False)
            fig_rep = px.bar(plot_df, x='상품명', y=y1_col, text=y1_col, color=y1_col, color_continuous_scale=px.colors.diverging.RdYlBu[::-1])
            st.plotly_chart(fig_rep, use_container_width=True)
    else:
        st.info("💡 구글 스프레드시트에 본사 성과 데이터를 입력하고 `REP_SHEET_GID`를 설정해주세요.")
