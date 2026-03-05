import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="랩어카운트 관리")

DATA_FILE = "wrap_account_data.csv"

# 가운데 글자 마스킹 함수
def mask_name(name):
    if len(name) >= 3:
        return name[0] + "*" * (len(name)-2) + name[-1]
    elif len(name) == 2:
        return name[0] + "*"
    return name

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["투자시작일", "날짜", "고객명", "총투자금", "평가금액", "수익률(%)"])

st.title("📈 랩어카운트 수익 관리 대시보드")

col_left, col_right = st.columns([4, 6]) 

# ================= 왼쪽: 입력 및 삭제 =================
with col_left:
    st.header("📝 평가금액 입력")
    with st.form("input_form"):
        start_date = st.date_input("투자 시작일 (최초 가입일)")
        date = st.date_input("현재 평가 날짜")
        raw_client_name = st.text_input("고객명 (본명 입력 시 자동 * 처리)")
        total_invest = st.number_input("총 투자금 (원)", min_value=0, step=100000)
        eval_amount = st.number_input("현재 평가금액 (원)", min_value=0, step=100000)
        
        submit_button = st.form_submit_button(label="데이터 저장하기")

        if submit_button and raw_client_name:
            client_name = mask_name(raw_client_name)
            if total_invest > 0:
                return_rate = ((eval_amount - total_invest) / total_invest) * 100
            else:
                return_rate = 0.0
                
            new_data = pd.DataFrame([{
                "투자시작일": start_date.strftime("%Y-%m-%d"),
                "날짜": date.strftime("%Y-%m-%d"),
                "고객명": client_name,
                "총투자금": total_invest,
                "평가금액": eval_amount,
                "수익률(%)": round(return_rate, 2)
            }])
            
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.rerun()

    st.header("🗑️ 데이터 수정 및 삭제")
    st.caption("탭을 선택해 특정 고객의 데이터를 확인하고 수정/삭제(Delete키) 할 수 있습니다.")
    
    if not df.empty:
        client_list = df["고객명"].unique()
        # [요청 1] 데이터 삭제 메뉴도 고객별 탭으로 나누기
        edit_tabs = st.tabs(["전체보기"] + list(client_list))
        
        with edit_tabs[0]:
            edited_all = st.data_editor(df, num_rows="dynamic", key="ed_all", use_container_width=True)
            if not edited_all.equals(df):
                edited_all.to_csv(DATA_FILE, index=False)
                st.rerun()
                
        for i, client in enumerate(client_list):
            with edit_tabs[i+1]:
                c_df = df[df["고객명"] == client]
                edited_c = st.data_editor(c_df, num_rows="dynamic", key=f"ed_{client}", use_container_width=True)
                if not edited_c.equals(c_df):
                    new_df = df[df["고객명"] != client].copy()
                    new_df = pd.concat([new_df, edited_c], ignore_index=True)
                    new_df.to_csv(DATA_FILE, index=False)
                    st.rerun()

# ================= 오른쪽: 대시보드 및 시뮬레이션 =================
with col_right:
    st.header("📊 수익률 대시보드")
    if not df.empty:
        client_list = df["고객명"].unique()
        
        # [요청 2] 가입연도별 평균 수익률 탭을 가장 앞에 추가
        tabs = st.tabs(["🏆 가입연도별 평균"] + list(client_list))
        
        # --- 첫 번째 탭: 가입연도별 평균 수익률 ---
        with tabs[0]:
            st.subheader("📅 가입 연도별 고객 평균 수익률 (최신 기준)")
            # 각 고객의 가장 최근 데이터만 뽑아내기
            latest_df = df.sort_values('날짜').groupby('고객명').tail(1).copy()
            # 연도 추출
            latest_df['가입연도'] = latest_df['투자시작일'].astype(str).str[:4] + "년"
            
            # 연도별 평균 계산
            yearly_avg = latest_df.groupby('가입연도')['수익률(%)'].mean().reset_index()
            yearly_avg.rename(columns={'수익률(%)': '평균 수익률(%)'}, inplace=True)
            yearly_avg['평균 수익률(%)'] = yearly_avg['평균 수익률(%)'].round(2)
            
            # 막대 그래프 그리기
            fig_year = px.bar(yearly_avg, x='가입연도', y='평균 수익률(%)', text='평균 수익률(%)', 
                              color='가입연도', title="가입 연도에 따른 현재 평균 수익률")
            fig_year.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            # y축 범위 여유있게 설정 (글씨가 잘리지 않게)
            fig_year.update_layout(yaxis=dict(range=[yearly_avg['평균 수익률(%)'].min() * 1.2, yearly_avg['평균 수익률(%)'].max() * 1.3]))
            st.plotly_chart(fig_year, use_container_width=True)
            
            st.caption("※ 각 고객의 가장 최근 평가금액을 기준으로 연도별 평균을 계산한 자료입니다.")
        
        # --- 나머지 탭: 개별 고객 그래프 및 시뮬레이션 ---
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
                
                # [요청 3] 1000만원 투자 시뮬레이션 (최신 수익률 기준)
                if not client_df.empty:
                    latest_return = client_df.iloc[-1]["수익률(%)"]
                    # 1000만원 + (1000만원 * 수익률%)
                    simul_amount = 10000000 * (1 + (latest_return / 100))
                    
                    st.markdown("---")
                    st.subheader("💡 1,000만 원 투자 시뮬레이션")
                    if latest_return >= 0:
                        st.success(f"현재 누적 수익률 **{latest_return}%**를 기준으로, 처음에 **1,000만 원**을 투자하셨다면 현재 **{simul_amount:,.0f}원**이 되어있습니다. 📈")
                    else:
                        st.warning(f"현재 누적 수익률 **{latest_return}%**를 기준으로, 처음에 **1,000만 원**을 투자하셨다면 현재 **{simul_amount:,.0f}원**입니다. 장기적인 관점에서 회복을 기대할 수 있습니다. 📉")
    else:
        st.info("왼쪽에서 평가 데이터를 먼저 입력해 주세요. (입력 시 그래프가 자동 생성됩니다)")