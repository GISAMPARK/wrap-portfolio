import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from functools import reduce

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

REP_SHEET_GID = "" 
PENSION_SHEET_GID = "951679806" 

# 👇 나중에 시트에 '주식' 탭을 만드시고 그 GID를 여기에 넣으시면 자동 연동됩니다!
STOCK_SHEET_GID = "" 

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
    if not PENSION_SHEET_GID: return pd.DataFrame()
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

@st.cache_data(ttl=60)
def load_stock_data():
    if not STOCK_SHEET_GID: return pd.DataFrame()
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={STOCK_SHEET_GID}"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.replace(' ', '').str.strip()
        df = df.dropna(subset=['고객명'])
        cols_to_clean = ['투자원금', '평가금액', '수익률(%)']
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

df_rap = load_rap_data()
df_pen = load_pension_data()
df_stock = load_stock_data()
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
    if not df_stock.empty: all_clients.update(df_stock["고객명"].dropna().unique())
    client_list = sorted(list(all_clients))
    
    selected_client = st.selectbox("👤 고객명 검색:", ["--- 고객을 선택하세요 ---"] + client_list)
    
    if selected_client != "--- 고객을 선택하세요 ---":
        client = selected_client
        safe_client_name = mask_name(client)
        
        c_rap = df_rap[df_rap["고객명"] == client].sort_values(by="날짜") if not df_rap.empty else pd.DataFrame()
        c_pen = df_pen[df_pen["고객명"] == client].sort_values(by="날짜") if not df_pen.empty else pd.DataFrame()
        c_stock = df_stock[df_stock["고객명"] == client].sort_values(by="날짜") if not df_stock.empty else pd.DataFrame()
        
        total_rap_asset, total_rap_prin = 0, 0
        total_pen_asset, total_pen_prin, total_tax_paid = 0, 0, 0
        total_stock_asset, total_stock_prin = 0, 0
        
        active_rap_accounts = []
        terminated_rap_accounts = []
        
        # 랩어카운트 집계
        if not c_rap.empty:
            for acc in c_rap['계좌명'].unique():
                acc_df = c_rap[c_rap['계좌명'] == acc]
                latest = acc_df.iloc[-1]
                if str(latest.get('비고', '운용중')).strip() == '해지':
                    terminated_rap_accounts.append(acc)
                else:
                    active_rap_accounts.append(acc)
                    total_rap_asset += latest.get('평가자산', 0)
                    total_rap_prin += latest.get('투자원금', 0)
                    
        # 연금/IRP 집계
        if not c_pen.empty:
            for acc in c_pen['계좌명'].unique():
                latest = c_pen[c_pen['계좌명'] == acc].iloc[-1]
                total_pen_asset += latest.get('평가금액', 0)
                total_pen_prin += latest.get('납입원금', 0)
                total_tax_paid += latest.get('올해납입액', 0)
                
        # 주식 집계
        if not c_stock.empty:
            for acc in c_stock['계좌명'].unique():
                latest = c_stock[c_stock['계좌명'] == acc].iloc[-1]
                total_stock_asset += latest.get('평가금액', 0)
                total_stock_prin += latest.get('투자원금', 0)
                
        total_asset = total_rap_asset + total_pen_asset + total_stock_asset
        total_prin = total_rap_prin + total_pen_prin + total_stock_prin
        
        # 👑 상단 요약 및 세액공제
        st.markdown(f"## 👑 {safe_client_name} 고객님 종합 자산 브리핑")
        
        c_title1, c_title2 = st.columns([1, 1])
        with c_title1:
            st.markdown(f"### 💰 총 운용 금융자산: **<span style='color:#CD2E3A;'>{total_asset:,.0f}원</span>**", unsafe_allow_html=True)
        with c_title2:
            tax_limit = 9000000
            progress = min(total_tax_paid / tax_limit, 1.0)
            st.markdown(f"**🛡️ 올해 연금/IRP 세액공제 납입: <span style='color:#1F77B4;'>{total_tax_paid:,.0f}원</span> / 한도 900만 원**", unsafe_allow_html=True)
            st.progress(progress)
            
        if terminated_rap_accounts:
            st.warning(f"🛑 해지된 랩어카운트 내역이 존재하여 위 자산 합산에서는 제외되었습니다.")
        st.markdown("---")
        
        # 📊 도넛 차트 & 자산별 상세 표 (좌/우 배치)
        col_chart, col_detail = st.columns([1, 1.2])
        
        pie_data = pd.DataFrame({
            '자산 구분': ['투자자산(랩)', '노후자산(연금/IRP)', '주식자산'],
            '금액': [total_rap_asset, total_pen_asset, total_stock_asset]
        })
        pie_data = pie_data[pie_data['금액'] > 0]
        
        with col_chart:
            if not pie_data.empty:
                fig_pie = px.pie(pie_data, values='금액', names='자산 구분', hole=0.5,
                                 color='자산 구분', color_discrete_map={'투자자산(랩)':'#1F77B4', '노후자산(연금/IRP)':'#2CA02C', '주식자산':'#FF7F0E'})
                fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_size=16)
                fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=380)
                st.plotly_chart(fig_pie, use_container_width=True)
                
        with col_detail:
            st.markdown("#### 📋 자산별 운용 세부 현황")
            
            # 💡 기존의 작은 표(DataFrame) 대신 HTML/CSS를 사용하여 크고 화려한 표로 교체!
            html_table = '''
            <div style="padding-top: 15px;">
            <table style="width: 100%; text-align: center; border-collapse: collapse; font-size: 17px; font-family: 'Malgun Gothic', sans-serif;">
                <thead>
                    <tr style="background-color: #f0f2f6; border-bottom: 2px solid #ccc;">
                        <th style="padding: 15px; font-weight: bold; color: #333;">자산 종류</th>
                        <th style="padding: 15px; font-weight: bold; color: #333;">투자원금</th>
                        <th style="padding: 15px; font-weight: bold; color: #333;">현재평가액</th>
                        <th style="padding: 15px; font-weight: bold; color: #333;">수익률</th>
                    </tr>
                </thead>
                <tbody>
            '''
            
            if total_rap_asset > 0:
                ret = ((total_rap_asset - total_rap_prin) / total_rap_prin * 100) if total_rap_prin else 0
                html_table += f"<tr><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>🟦 랩어카운트</td><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>{total_rap_prin:,.0f}</td><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>{total_rap_asset:,.0f}</td><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>{ret:.2f}%</td></tr>"
            
            if total_pen_asset > 0:
                ret = ((total_pen_asset - total_pen_prin) / total_pen_prin * 100) if total_pen_prin else 0
                html_table += f"<tr><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>🟩 연금/IRP</td><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>{total_pen_prin:,.0f}</td><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>{total_pen_asset:,.0f}</td><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>{ret:.2f}%</td></tr>"
            
            if total_stock_asset > 0:
                ret = ((total_stock_asset - total_stock_prin) / total_stock_prin * 100) if total_stock_prin else 0
                html_table += f"<tr><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>🟧 주식</td><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>{total_stock_prin:,.0f}</td><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>{total_stock_asset:,.0f}</td><td style='padding: 15px; border-bottom: 1px solid #eaeaea;'>{ret:.2f}%</td></tr>"
            
            # 총 합계 열 (하이라이트 강조)
            tot_ret = ((total_asset - total_prin) / total_prin * 100) if total_prin else 0
            html_table += f'''
                <tr style="background-
