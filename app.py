import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from functools import reduce

st.set_page_config(layout="wide", page_title="자산관리 대시보드", page_icon="logo.png")

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

RAP_SHEET_GID = "1303130540" 
REP_SHEET_GID = "1430586087" 
PENSION_SHEET_GID = "951679806" 
STOCK_SHEET_GID = "1558094314" 

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

# ==========================================
# 🛡️ 데이터 로드 함수들
# ==========================================
@st.cache_data(ttl=60)
def load_rep_data():
    if not REP_SHEET_GID: return pd.DataFrame()
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={REP_SHEET_GID}"
    try:
        df = pd.read_csv(url, on_bad_lines='skip')
        if df.empty or (len(df.columns) > 0 and '<html' in str(df.columns[0]).lower()): return pd.DataFrame()
        
        df.columns = [str(c).replace('\n', '').strip() for c in df.columns]
        
        if '상품명' in df.columns:
            df['상품명'] = df['상품명'].apply(lambda x: str(x).strip())
            def is_valid(name):
                if len(name) < 2: return False
                if name in ['1M', '3M', '6M', '1Y', '(단위:억원)', '수익률', '상품명', '기준일', 'nan', 'None']: return False
                try:
                    float(name.replace(',', ''))
                    return False
                except:
                    return True
            df = df[df['상품명'].apply(is_valid)]
            
        for col in df.columns:
            if col not in ['상품명', '기준일']:
                df[col] = df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        if '기준일' in df.columns:
            df['기준일'] = pd.to_datetime(df['기준일'], errors='coerce')
        return df
    except: 
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_rap_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={RAP_SHEET_GID}"
    try:
        df = pd.read_csv(url, on_bad_lines='skip')
        if df.empty or (len(df.columns) > 0 and '<html' in str(df.columns[0]).lower()): return pd.DataFrame()
        
        df.columns = [str(c).replace(' ', '').strip() for c in df.columns]
        
        if '총수익률(%)' in df.columns: df.rename(columns={'총수익률(%)': '수익률(%)'}, inplace=True)
        if '랩종류' in df.columns and '계좌명' not in df.columns: df.rename(columns={'랩종류': '계좌명'}, inplace=True)
        
        if '고객명' in df.columns:
            df['고객명'] = df['고객명'].apply(lambda x: str(x).strip())
            df = df[(df['고객명'] != '') & (df['고객명'] != 'nan') & (df['고객명'] != 'None')]
            df = df.dropna(subset=['고객명'])
            
        if '계좌명' not in df.columns: df['계좌명'] = '기본투자'
        df['계좌명'] = df['계좌명'].apply(lambda x: str(x).replace('랩', '투자'))
        
        cols_to_clean = ['초기투자금', '추가투자금', '정산수익금', '누적수익금', '투자원금', '총투자금', '평가자산', '원금대비수익률(%)', '수익률(%)']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        if '날짜' in df.columns: df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_pension_data():
    if not PENSION_SHEET_GID: return pd.DataFrame()
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={PENSION_SHEET_GID}"
    try:
        df = pd.read_csv(url, on_bad_lines='skip')
        if df.empty or (len(df.columns) > 0 and '<html' in str(df.columns[0]).lower()): return pd.DataFrame()
        
        df.columns = [str(c).replace(' ', '').strip() for c in df.columns]
        
        if '고객명' in df.columns:
            df['고객명'] = df['고객명'].apply(lambda x: str(x).strip())
            df = df[(df['고객명'] != '') & (df['고객명'] != 'nan') & (df['고객명'] != 'None')]
            df = df.dropna(subset=['고객명'])
            
        if '계좌명' in df.columns and '고객명' in df.columns and '날짜' in df.columns and not df.empty:
            df['temp_count'] = df.groupby(['고객명', '날짜', '계좌명']).cumcount() + 1
            df['계좌명'] = df.apply(lambda x: f"{x['계좌명']}_{x['temp_count']}" if x['temp_count'] > 1 else x['계좌명'], axis=1)
            
        cols_to_clean = ['납입원금', '평가금액', '올해납입액', '수익률(%)']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        if '날짜' in df.columns: df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_stock_data():
    if not STOCK_SHEET_GID: return pd.DataFrame()
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={STOCK_SHEET_GID}"
    try:
        df = pd.read_csv(url, on_bad_lines='skip')
        if df.empty or (len(df.columns) > 0 and '<html' in str(df.columns[0]).lower()): return pd.DataFrame()
        
        df.columns = [str(c).replace(' ', '').strip() for c in df.columns]
        
        if '고객명' in df.columns:
            df['고객명'] = df['고객명'].apply(lambda x: str(x).strip())
            df = df[(df['고객명'] != '') & (df['고객명'] != 'nan') & (df['고객명'] != 'None')]
            df = df.dropna(subset=['고객명'])
            
        if '원금' in df.columns and '투자원금' not in df.columns:
            df.rename(columns={'원금': '투자원금'}, inplace=True)
            
        if '날짜' in df.columns: df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        
        if '고객명' in df.columns and '날짜' in df.columns and not df.empty:
            df['계좌순번'] = df.groupby(['고객명', '날짜']).cumcount() + 1
            df['계좌명'] = df['계좌순번'].apply(lambda x: f"위탁계좌 {x}")
            
        cols_to_clean = ['투자원금', '평가금액', '수익률(%)', '갯수']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 🖥️ 메인 화면 구성
# ==========================================
st.title("👑 VVIP 종합 자산관리 대시보드")

df_rap = load_rap_data()
df_pen = load_pension_data()
df_stock = load_stock_data()
rep_df = load_rep_data()

if df_rap.empty and df_pen.empty and df_stock.empty:
    st.error("🚨 데이터를 불러올 수 없습니다! 구글 시트 우측 상단 [공유] 버튼을 눌러 **'링크가 있는 모든 사용자(뷰어)'**로 다시 변경해 주세요!")

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

tab_titles = ["🔍 VVIP 고객 포트폴리오 검색", "🏆 랩어카운트 평균수익률", "🏢 본사 대표계좌 운용성과"]
tabs = st.tabs(tab_titles)

with tabs[0]:
    st.header("🔍 개별 고객 종합 포트폴리오 검색")
    all_clients = set()
    if not df_rap.empty and '고객명' in df_rap.columns: all_clients.update(df_rap["고객명"].dropna().unique())
    if not df_pen.empty and '고객명' in df_pen.columns: all_clients.update(df_pen["고객명"].dropna().unique())
    if not df_stock.empty and '고객명' in df_stock.columns: all_clients.update(df_stock["고객명"].dropna().unique())
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
        total_irp_asset, total_irp_prin, total_irp_tax_paid = 0, 0, 0 
        total_stock_asset, total_stock_prin = 0, 0
        
        active_rap_accounts = []
        terminated_rap_accounts = []
        detailed_rows = []
        
        if not c_rap.empty:
            for acc in c_rap['계좌명'].unique():
                acc_df = c_rap[c_rap['계좌명'] == acc]
                latest = acc_df.iloc[-1]
                if str(latest.get('비고', '운용중')).strip() == '해지':
                    terminated_rap_accounts.append(acc)
                else:
                    active_rap_accounts.append(acc)
                    eval_amt = latest.get('평가자산', 0)
                    prin_amt = latest.get('투자원금', 0)
                    total_rap_asset += eval_amt
                    total_rap_prin += prin_amt
                    ret = ((eval_amt - prin_amt) / prin_amt * 100) if prin_amt else 0
                    detailed_rows.append({"구분": "🟦 랩", "계좌": acc, "원금": prin_amt, "평가액": eval_amt, "수익률": ret})
                    
        if not c_pen.empty:
            for acc in c_pen['계좌명'].unique():
                latest = c_pen[c_pen['계좌명'] == acc].iloc[-1]
                eval_amt = latest.get('평가금액', 0)
                prin_amt = latest.get('납입원금', 0)
                ret = ((eval_amt - prin_amt) / prin_amt * 100) if prin_amt else 0
                
                if 'IRP' in str(acc).upper():
                    total_irp_asset += eval_amt
                    total_irp_prin += prin_amt
                    total_irp_tax_paid += latest.get('올해납입액', 0)
                    detailed_rows.append({"구분": "🟩 IRP", "계좌": acc, "원금": prin_amt, "평가액": eval_amt, "수익률": ret})
                else:
                    total_pen_asset += eval_amt
                    total_pen_prin += prin_amt
                    total_tax_paid += latest.get('올해납입액', 0)
                    detailed_rows.append({"구분": "🟩 연금저축", "계좌": acc, "원금": prin_amt, "평가액": eval_amt, "수익률": ret})
                
        if not c_stock.empty:
            for acc in c_stock['계좌명'].unique():
                latest = c_stock[c_stock['계좌명'] == acc].iloc[-1]
                eval_amt = latest.get('평가금액', 0)
                prin_amt = latest.get('투자원금', 0)
                ret = ((eval_amt - prin_amt) / prin_amt * 100) if prin_amt else 0
                total_stock_asset += eval_amt
                total_stock_prin += prin_amt
                detailed_rows.append({"구분": "🟧 위탁(주식)", "계좌": acc, "원금": prin_amt, "평가액": eval_amt, "수익률": ret})
                
        total_asset = total_rap_asset + total_pen_asset + total_irp_asset + total_stock_asset
        total_prin = total_rap_prin + total_pen_prin + total_irp_prin + total_stock_prin
        
        st.markdown(f"## 👑 {safe_client_name} 고객님 종합 자산 브리핑")
        
        c_title1, c_title2 = st.columns([1, 1])
        with c_title1:
            st.markdown(f"### 💰 총 운용 금융자산: **<span style='color:#CD2E3A;'>{total_asset:,.0f}원</span>**", unsafe_allow_html=True)
        with c_title2:
            tax_limit = 9000000
            total_tax_all = total_tax_paid + total_irp_tax_paid
            progress = min(total_tax_all / tax_limit, 1.0)
            st.markdown(f"**🛡️ 올해 연금/IRP 세액공제 납입: <span style='color:#1F77B4;'>{total_tax_all:,.0f}원</span> / 한도 900만 원**", unsafe_allow_html=True)
            st.progress(progress)
            
        if terminated_rap_accounts:
            st.warning(f"🛑 해지된 랩어카운트 내역이 존재하여 위 자산 합산에서는 제외되었습니다.")
        st.markdown("---")
        
        col_chart, col_detail = st.columns([1, 1.3])
        
        pie_data = pd.DataFrame({
            '자산 구분': ['투자자산(랩)', '노후자산(연금)', '노후자산(IRP)', '위탁자산(주식)'],
            '금액': [total_rap_asset, total_pen_asset, total_irp_asset, total_stock_asset]
        })
        pie_data = pie_data[pie_data['금액'] > 0]
        
        with col_chart:
            if not pie_data.empty:
                current_textposition = 'inside' if len(pie_data) == 1 else 'outside'
                
                fig_pie = px.pie(pie_data, values='금액', names='자산 구분', hole=0.5,
                                 color='자산 구분', color_discrete_map={'투자자산(랩)':'#1F77B4', '노후자산(연금)':'#2CA02C', '노후자산(IRP)':'#98DF8A', '위탁자산(주식)':'#FF7F0E'})
                fig_pie.update_traces(textposition=current_textposition, textinfo='label+percent', textfont_size=15, pull=[0.02]*len(pie_data))
                fig_pie.update_layout(showlegend=False, margin=dict(t=40, b=40, l=40, r=40), height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
                
        with col_detail:
            st.markdown("#### 📋 자산별 운용 세부 현황")
            html_table = '''
            <div style="padding-top: 15px;">
            <table style="width: 100%; text-align: center; border-collapse: collapse; font-size: 16px; font-family: 'Malgun Gothic', sans-serif;">
                <thead>
                    <tr style="background-color: #f0f2f6; border-bottom: 2px solid #ccc;">
                        <th style="padding: 12px; font-weight: bold; color: #333;">구분</th>
                        <th style="padding: 12px; font-weight: bold; color: #333;">계좌명</th>
                        <th style="padding: 12px; font-weight: bold; color: #333;">투자원금</th>
                        <th style="padding: 12px; font-weight: bold; color: #333;">현재평가액</th>
                        <th style="padding: 12px; font-weight: bold; color: #333;">수익률</th>
                    </tr>
                </thead>
                <tbody>
            '''
            for r in detailed_rows:
                html_table += f"<tr><td style='padding: 10px; border-bottom: 1px solid #eaeaea;'>{r['구분']}</td>"
                html_table += f"<td style='padding: 10px; border-bottom: 1px solid #eaeaea;'>{r['계좌']}</td>"
                html_table += f"<td style='padding: 10px; border-bottom: 1px solid #eaeaea;'>{r['원금']:,.0f}</td>"
                html_table += f"<td style='padding: 10px; border-bottom: 1px solid #eaeaea;'>{r['평가액']:,.0f}</td>"
                html_table += f"<td style='padding: 10px; border-bottom: 1px solid #eaeaea;'>{r['수익률']:.2f}%</td></tr>"
            
            tot_ret = ((total_asset - total_prin) / total_prin * 100) if total_prin else 0
            html_table += f'''
                <tr style="background-color: #e6f0ff; border-top: 2px solid #4a90e2; font-size: 18px;">
                    <td colspan="2" style="padding: 15px; font-weight: bold; color: #000;">✨ 총 합계</td>
                    <td style="padding: 15px; font-weight: bold; color: #000;">{total_prin:,.0f}</td>
                    <td style="padding: 15px; font-weight: bold; color: #CD2E3A;">{total_asset:,.0f}</td>
                    <td style="padding: 15px; font-weight: bold; color: #CD2E3A;">{tot_ret:.2f}%</td>
                </tr>
                </tbody>
            </table>
            </div>
            '''
            st.markdown(html_table, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
        st.markdown("---")
        
        st.markdown("#### 📈 고객 총자산 성장 추이")
        
        def get_clean_history(df, eval_col, prin_col):
            df_clean = df.dropna(subset=['날짜']).copy()
            if df_clean.empty: return pd.DataFrame()
            
            if '비고' in df_clean.columns:
                mask = df_clean['비고'].astype(str).str.strip() == '해지'
                df_clean.loc[mask, eval_col] = 0
                df_clean.loc[mask, prin_col] = 0
            
            p_eval = df_clean.pivot_table(index='날짜', columns='계좌명', values=eval_col, aggfunc='last').ffill().fillna(0)
            p_prin = df_clean.pivot_table(index='날짜', columns='계좌명', values=prin_col, aggfunc='last').ffill().fillna(0)
            
            res = pd.DataFrame({
                '날짜': p_eval.index,
                f'{eval_col}_sum': p_eval.sum(axis=1).values,
                f'{prin_col}_sum': p_prin.sum(axis=1).values
            })
            return res

        dfs_to_merge = []
        if not c_rap.empty:
            rap_hist = get_clean_history(c_rap, '평가자산', '투자원금')
            if not rap_hist.empty:
                rap_hist.rename(columns={'평가자산_sum': '랩_평가', '투자원금_sum': '랩_원금'}, inplace=True)
                dfs_to_merge.append(rap_hist)
                
        if not c_pen.empty:
            pen_hist = get_clean_history(c_pen, '평가금액', '납입원금')
            if not pen_hist.empty:
                pen_hist.rename(columns={'평가금액_sum': '연금_평가', '납입원금_sum': '연금_원금'}, inplace=True)
                dfs_to_merge.append(pen_hist)
                
        if not c_stock.empty:
            stock_hist = get_clean_history(c_stock, '평가금액', '투자원금')
            if not stock_hist.empty:
                stock_hist.rename(columns={'평가금액_sum': '주식_평가', '투자원금_sum': '주식_원금'}, inplace=True)
                dfs_to_merge.append(stock_hist)
            
        if dfs_to_merge:
            merged = reduce(lambda left, right: pd.merge(left, right, on=['날짜'], how='outer'), dfs_to_merge)
            merged = merged.sort_values('날짜').ffill().fillna(0)
            
            eval_cols = [c for c in merged.columns if '_평가' in c]
            prin_cols = [c for c in merged.columns if '_원금' in c]
            
            merged['총자산_평가'] = merged[eval_cols].sum(axis=1)
            merged['총자산_원금'] = merged[prin_cols].sum(axis=1)
            
            merged['수익률(%)'] = 0.0
            mask = merged['총자산_원금'] > 0
            merged.loc[mask, '수익률(%)'] = ((merged.loc[mask, '총자산_평가'] - merged.loc[mask, '총자산_원금']) / merged.loc[mask, '총자산_원금']) * 100
            
            fig_trend = px.area(merged, x='날짜', y='총자산_평가', title="날짜별 금융자산 합산 우상향 지표", color_discrete_sequence=['#CD2E3A'])
            fig_trend.update_traces(
                mode='lines+markers', 
                marker=dict(size=6),
                hovertemplate="<b><span style='font-size:18px;'>%{x|%Y년 %m월 %d일}</span></b><br><br>" +
                              "<b><span style='font-size:22px;'>💰 총 평가금액: %{y:,.0f}원</span></b><br>" +
                              "<b><span style='font-size:22px; color:#1F77B4;'>📈 총 수익률: %{customdata[0]:.2f}%</span></b><extra></extra>",
                customdata=merged[['수익률(%)']]
            )
            fig_trend.update_layout(hoverlabel=dict(font=dict(size=18)))
            fig_trend.update_xaxes(tickformat="%y년 %m월", dtick="M1") 
            fig_trend.update_yaxes(title="총자산")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("자산 성장 추이를 그릴 과거 날짜 데이터가 부족합니다.")

        st.markdown("---")
        
        sub_tabs = st.tabs(["📈 랩어카운트 상세", "🛡️ 연금 및 IRP 상세", "📊 위탁계좌(주식) 상세"])
        
        with sub_tabs[0]:
            if not c_rap.empty:
                for acc in c_rap['계좌명'].unique():
                    acc_df = c_rap[c_rap['계좌명'] == acc].copy()
                    latest = acc_df.iloc[-1]
                    status = str(latest.get('비고', '운용중')).strip()
                    
                    if status == '해지':
                        st.markdown(f"#### 🛑 [{acc}] <span style='color:red; font-size:16px;'>(해지)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"#### 📊 [{acc}]")
                        
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("평가자산", f"{latest.get('평가자산', 0):,.0f}원")
                    c2.metric("투자원금", f"{latest.get('투자원금', 0):,.0f}원")
                    
                    val_tot_ret = latest.get('수익률(%)', 0)
                    val_prin_ret = latest.get('원금대비수익률(%)', val_tot_ret) 
                    c3.metric("원금대비 수익률", f"{val_prin_ret}%")
                    c4.metric("총 수익률", f"{val_tot_ret}%")
                    
                    # 💡 피드백 반영: 잃어버렸던 '정산수익금' 아코디언(화살표) 메뉴 완벽 복구!
                    if '정산수익금' in acc_df.columns and acc_df['정산수익금'].sum() > 0:
                        with st.expander(f"💵 {acc} 연도별 정산수익금 내역 보기"):
                            acc_df_settle = acc_df[acc_df['정산수익금'] > 0].copy()
                            acc_df_settle['연도'] = acc_df_settle['날짜'].dt.year.astype(str) + "년"
                            yearly_settle = acc_df_settle.groupby('연도')['정산수익금'].sum().reset_index()
                            
                            settle_html = "<table style='width: 100%; text-align: center; border-collapse: collapse; font-size: 16px;'>"
                            settle_html += "<tr style='background-color: #f0f2f6; border-bottom: 2px solid #ccc;'><th>정산 연도</th><th>정산수익금 합계</th></tr>"
                            for _, row in yearly_settle.iterrows():
                                settle_html += f"<tr><td style='padding: 10px; border-bottom: 1px solid #eaeaea;'>{row['연도']}</td><td style='padding: 10px; border-bottom: 1px solid #eaeaea; color: #CD2E3A; font-weight: bold;'>{row['정산수익금']:,.0f}원</td></tr>"
                            settle_html += "</table><br>"
                            st.markdown(settle_html, unsafe_allow_html=True)
                    
                    if "원금대비수익률(%)" in acc_df.columns:
                        color = '#888888' if status == '해지' else '#FF7F0E'
                        fig1 = px.line(acc_df, x="날짜", y="원금대비수익률(%)", markers=True, title=f"🟠 {acc} 수익률 추이")
                        fig1.update_traces(line=dict(width=3, color=color))
                        fig1.update_xaxes(tickformat="%y년 %m월", dtick="M1")
                        st.plotly_chart(fig1, use_container_width=True)
                    st.markdown("<hr style='border: 1px dashed #ddd;'>", unsafe_allow_html=True)
            else: st.info("내역이 없습니다.")
                
        with sub_tabs[1]:
            if not c_pen.empty:
                for acc in c_pen['계좌명'].unique():
                    acc_df = c_pen[c_pen['계좌명'] == acc]
                    latest = acc_df.iloc[-1]
                    st.markdown(f"#### 🛡️ [{acc}]")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("평가금액", f"{latest.get('평가금액', 0):,.0f}원")
                    c2.metric("납입원금", f"{latest.get('납입원금', 0):,.0f}원")
                    c3.metric("총 수익률(%)", f"{latest.get('수익률(%)', 0)}%")
                    
                    if "수익률(%)" in acc_df.columns:
                        fig2 = px.line(acc_df, x="날짜", y="수익률(%)", markers=True, title=f"🟢 {acc} 총 수익률 추이")
                        fig2.update_traces(line=dict(width=3, color='#2CA02C'))
                        fig2.update_xaxes(tickformat="%y년 %m월", dtick="M1")
                        st.plotly_chart(fig2, use_container_width=True)
                        
                    st.markdown("<hr style='border: 1px dashed #ddd;'>", unsafe_allow_html=True)
            else: st.info("내역이 없습니다.")
            
        with sub_tabs[2]:
            if not c_stock.empty:
                for acc in c_stock['계좌명'].unique():
                    acc_df = c_stock[c_stock['계좌명'] == acc]
                    latest = acc_df.iloc[-1]
                    st.markdown(f"#### 📈 [{acc}]")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("평가금액", f"{latest.get('평가금액', 0):,.0f}원")
                    c2.metric("투자원금", f"{latest.get('투자원금', 0):,.0f}원")
                    c3.metric("총 수익률(%)", f"{latest.get('수익률(%)', 0)}%")
                    
                    if '갯수' in acc_df.columns:
                        cnt = int(latest.get('갯수', 0))
                        if cnt > 0:
                            st.caption(f"📌 보유 종목 갯수: {cnt}개")
                            
                    if "수익률(%)" in acc_df.columns:
                        fig3 = px.line(acc_df, x="날짜", y="수익률(%)", markers=True, title=f"🔵 {acc} 총 수익률 추이")
                        fig3.update_traces(line=dict(width=3, color='#1F77B4'))
                        fig3.update_xaxes(tickformat="%y년 %m월", dtick="M1")
                        st.plotly_chart(fig3, use_container_width=True)
                        
                    st.markdown("<hr style='border: 1px dashed #ddd;'>", unsafe_allow_html=True)
            else: st.info("위탁계좌 내역이 없습니다.")
    else:
        st.info("👆 위 검색창을 클릭하여 조회할 고객을 선택해 주세요.")

# ==========================================
# 2️⃣ 두 번째 탭: 랩어카운트 평균수익률
# ==========================================
with tabs[1]:
    st.header("🏆 가입 연도 및 투자 종류별 평균 수익률")
    if not df_rap.empty:
        if '수익률(%)' in df_rap.columns:
            active_df = df_rap[df_rap['비고'] != '해지'].copy() if '비고' in df_rap.columns else df_rap.copy()
            if not active_df.empty:
                if '투자시작일' in active_df.columns:
                    latest_df = active_df.sort_values('날짜').groupby(['고객명', '계좌명']).tail(1).copy()
                    latest_df['가입연도'] = latest_df['투자시작일'].astype(str).str.strip().str[:4] + "년"
                    cols_to_mean = [c for c in ['원금대비수익률(%)', '수익률(%)'] if c in latest_df.columns]
                    yearly_avg = latest_df.groupby(['가입연도', '계좌명'])[cols_to_mean].mean().reset_index().round(2)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    fig_bar = px.bar(
                        yearly_avg, 
                        x='가입연도', 
                        y='수익률(%)', 
                        color='계좌명', 
                        barmode='group',
                        text='수익률(%)',
                        color_discrete_map={'미국투자': '#1F77B4', '국내투자': '#FF7F0E'},
                        title="📊 연도별 랩어카운트 평균 수익률 시각화"
                    )
                    fig_bar.update_traces(texttemplate='%{text}%', textposition='outside')
                    fig_bar.update_layout(height=450, hoverlabel=dict(font_size=16), yaxis_title="평균 수익률(%)")
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                    st.markdown("<hr style='border: 1px dashed #ddd;'>", unsafe_allow_html=True)
                    st.markdown("#### 📌 상세 수익률 현황 (미국 vs 국내)")
                    
                    us_df = yearly_avg[yearly_avg['계좌명'].str.contains('미국')].copy()
                    kr_df = yearly_avg[yearly_avg['계좌명'].str.contains('국내')].copy()
                    
                    col_us, col_kr = st.columns(2)
                    
                    with col_us:
                        st.markdown("##### 🇺🇸 미국투자 평균 수익률")
                        if not us_df.empty:
                            us_html = "<table style='width: 100%; text-align: center; border-collapse: collapse; font-size: 16px;'>"
                            us_html += "<tr style='background-color: #e6f2ff; border-bottom: 2px solid #1F77B4;'><th>가입연도</th><th>원금대비수익률</th><th>총 수익률</th></tr>"
                            for _, row in us_df.iterrows():
                                val1 = row.get('원금대비수익률(%)', row['수익률(%)'])
                                val2 = row['수익률(%)']
                                us_html += f"<tr><td style='padding: 12px; border-bottom: 1px solid #ddd;'><b>{row['가입연도']}</b></td><td style='padding: 12px; border-bottom: 1px solid #ddd; color: #CD2E3A;'>{val1:.2f}%</td><td style='padding: 12px; border-bottom: 1px solid #ddd; color: #CD2E3A; font-weight: bold; font-size: 18px;'>{val2:.2f}%</td></tr>"
                            us_html += "</table>"
                            st.markdown(us_html, unsafe_allow_html=True)
                        else:
                            st.info("미국투자 데이터가 없습니다.")
                            
                    with col_kr:
                        st.markdown("##### 🇰🇷 국내투자 평균 수익률")
                        if not kr_df.empty:
                            kr_html = "<table style='width: 100%; text-align: center; border-collapse: collapse; font-size: 16px;'>"
                            kr_html += "<tr style='background-color: #fff0e6; border-bottom: 2px solid #FF7F0E;'><th>가입연도</th><th>원금대비수익률</th><th>총 수익률</th></tr>"
                            for _, row in kr_df.iterrows():
                                val1 = row.get('원금대비수익률(%)', row['수익률(%)'])
                                val2 = row['수익률(%)']
                                kr_html += f"<tr><td style='padding: 12px; border-bottom: 1px solid #ddd;'><b>{row['가입연도']}</b></td><td style='padding: 12px; border-bottom: 1px solid #ddd; color: #CD2E3A;'>{val1:.2f}%</td><td style='padding: 12px; border-bottom: 1px solid #ddd; color: #CD2E3A; font-weight: bold; font-size: 18px;'>{val2:.2f}%</td></tr>"
                            kr_html += "</table>"
                            st.markdown(kr_html, unsafe_allow_html=True)
                        else:
                            st.info("국내투자 데이터가 없습니다.")

                else:
                    st.warning("투자시작일 데이터가 필요합니다.")
            else:
                st.info("현재 운용중인 데이터가 없습니다.")
        else:
            st.warning("데이터에 '수익률(%)' 열이 없습니다.")
    else:
        st.info("현재 분석 가능한 랩어카운트 데이터가 없습니다.")

# ==========================================
# 3️⃣ 세 번째 탭: 본사 대표계좌 운용성과
# ==========================================
with tabs[2]:
    st.header("🏢 본사 대표계좌 운용성과")
    if not rep_df.empty and '기준일' in rep_df.columns:
        clean_rep_df = rep_df.dropna(subset=['기준일']).copy()
        
        if not clean_rep_df.empty:
            latest_date = clean_rep_df['기준일'].max()
            latest_date_str = latest_date.strftime('%Y년 %m월 %d일') if isinstance(latest_date, pd.Timestamp) else str(latest_date)
            st.markdown(f"#### 📅 최근 업데이트 기준일: **{latest_date_str}**")
            
            latest_df = clean_rep_df[clean_rep_df['기준일'] == latest_date].copy()
            display_df = latest_df.copy()
            display_df['기준일'] = display_df['기준일'].dt.strftime('%Y-%m-%d') if pd.api.types.is_datetime64_any_dtype(display_df['기준일']) else display_df['기준일']
            
            dynamic_table_height = (len(display_df) * 36) + 42 
            st.dataframe(display_df, use_container_width=True, height=dynamic_table_height)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("#### 📈 과거부터 현재까지 1Y 수익률 추이")
            
            if len(clean_rep_df['기준일'].unique()) > 1:
                trend_df = clean_rep_df.dropna(subset=['1Y']).sort_values('기준일')
                
                fig_trend = px.line(trend_df, x='기준일', y='1Y', color='상품명', markers=True)
                fig_trend.update_xaxes(title=None, tickformat="%y년 %m월 %d일")
                fig_trend.update_yaxes(title="1Y 수익률(%)")
                
                fig_trend.update_traces(
                    line=dict(width=4), 
                    hovertemplate="<b><span style='font-size:16px;'>%{x|%Y년 %m월 %d일}</span></b><br>" +
                                  "<b><span style='font-size:20px; color:#1F77B4;'>수익률: %{y:.2f}%</span></b><extra></extra>"
                )
                
                fig_trend.update_layout(height=900, hoverlabel=dict(font=dict(size=18)))
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("💡 과거 데이터가 앞으로 더 누적되면 여기에 시계열 추이 선 그래프가 화려하게 나타납니다.")
        else:
            st.info("데이터를 불러오는 중이거나 아직 입력되지 않았습니다.")
    else:
        st.info("데이터를 불러오는 중이거나 아직 입력되지 않았습니다.")
