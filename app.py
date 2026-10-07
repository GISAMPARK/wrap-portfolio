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
    if '랩종류'
