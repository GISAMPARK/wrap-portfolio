import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="wide", page_title="랩어카운트 대시보드")
SHEET_ID = "1kQGu9NH2iKmBTYDMTEHxxlPnTIFOEoTyB9fN6Cf-gek"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
    # 공백 제거
    df.columns = df.columns.str.replace(' ', '').str.strip()
    return df

st.title("데이터 구조 확인하기")
try:
    df = load_data()
    st.write("### 🔍 현재 시트에 있는 데이터 제목(컬럼)들:")
    st.write(df.columns.tolist())
    st.write("### 🔍 데이터 내용 미리보기:")
    st.dataframe(df.head())
except Exception as e:
    st.error(f"오류: {e}")
