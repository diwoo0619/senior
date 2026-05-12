import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# 페이지 설정
st.set_page_config(page_title="고령인구 복지시설 분석", layout="wide")

# 1. DB 존재 여부 확인
db_path = 'senior.db'
if not os.path.exists(db_path):
    st.error(f"❌ 데이터베이스 파일('{db_path}')을 찾을 수 없습니다. 파일이 같은 폴더에 있는지 확인해주세요.")
    st.stop()

# DB 연결 함수
def run_query(query):
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql(query, conn)

st.title("👵 고령인구 및 복지시설 분석 대시보드")
st.markdown("자치구별 고령화 현황과 복지시설 공급 현황을 분석합니다.")

# ---------------------------------------------------------
# 차트 1. 자치구별 고령화율 vs 재가복지시설 수
# ---------------------------------------------------------
st.header("1. 자치구별 고령화율 및 재가복지시설 현황")
st.info("고령화율이 높은 지역에 재가복지시설이 충분히 배치되어 있는지 확인합니다.")

sql1 = """
SELECT 
    p.자치구,
    CAST(p.고령인구 AS FLOAT) / p.전체인구 * 100 AS 고령화율,
    COUNT(DISTINCT f.시설코드) AS 재가시설수, 
    ROUND(CAST(p.고령인구 AS FLOAT) / COUNT(DISTINCT f.시설코드), 0) AS 시설당노인수
FROM population p
LEFT JOIN 재가노인복지시설 f ON p.자치구 = f.자치구
GROUP BY p.자치구
ORDER BY 고령화율 DESC
"""
df1 = run_query(sql1)

# 시각화 (이중축 차트)
fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(
    go.Bar(x=df1['자치구'], y=df1['고령화율'], name="고령화율 (%)", marker_color='lightblue'),
    secondary_y=False,
)
fig1.add_trace(
    go.Scatter(x=df1['자치구'], y=df1['재가시설수'], name="재가시설 수", mode='lines+markers', line=dict(color='red')),
    secondary_y=True,
)
fig1.update_layout(title_text="자치구별 고령화율(막대) vs 재가시설 수(선)")
st.plotly_chart(fig1, use_container_width=True)

with st.expander("🔍 SQL 및 인사이트 보기"):
    st.code(sql1, language='sql')
    st.write("""
- **인사이트 1:** 고령화율이 가장 높은 자치구가 반드시 가장 많은 재가시설을 보유하고 있지는 않음을 알 수 있습니다.
노원구를 보면 고령화율은 중간 수준인데에 비해 재가시설수가 더 많은 것을 볼 수 있다.
이를 통해 고령화율보다는 고령인구의 절대수가 시설 공급에 더 큰 영향을 줄 수 있다는 것을 알 수 있다.
""")
    st.write("""
- **인사이트 2:** 강북구/도봉구를 보면 고령화율이 1-2위인데 재가시설 수는 평균 수준 이하로 나타나고 있다.
이는 재가시설 공급이 부족한 복지 사각지대일 가능성이 존재한다는 것을 알 수 있다.
""")


# ---------------------------------------------------------
# 차트 2. 자치구별 의료복지시설 1개당 고령인구 수
# ---------------------------------------------------------
st.header("2. 의료복지시설 1개당 담당 고령인구 수")
st.info("시설 1개당 담당하는 노인 수가 많을수록 의료 서비스 공급이 부족함을 의미합니다.")

sql2 = """
SELECT 
    p.자치구, 
    COUNT(DISTINCT m.시설코드) AS 의료시설수,
    (CAST(p.고령인구 AS FLOAT) / COUNT(DISTINCT m.시설코드)) as 시설당노인수
FROM population p
LEFT JOIN 노인의료복지시설 m ON p.자치구 = m.자치구GROUP BY p.자치구
ORDER BY 시설당노인수 DESC
"""
df2 = run_query(sql2)

# 시각화 (가로 막대 차트)
fig2 = px.bar(df2, x='시설당노인수', y='자치구', orientation='h',
             title="자치구별 의료시설 1개당 고령인구 수 (상위일수록 부족)",
             color='시설당노인수', color_continuous_scale='Reds')
st.plotly_chart(fig2, use_container_width=True)

with st.expander("🔍 SQL 및 인사이트 보기"):
    st.code(sql2, language='sql')
    st.write("- **인사이트 1:** 상단에 위치한 자치구는 시설 하나가 감당해야 할 어르신 인구가 많아 의료 서비스 과부하가 우려됩니다.")
    st.write("- **인사이트 2:** 하단 지역과 비교했을 때 지역별 의료 인프라 편차가 존재함을 확인 수 있습니다.")


# ---------------------------------------------------------
# 차트 3. 자치구별 재가시설 vs 의료시설 수 비교
# ---------------------------------------------------------
st.header("3. 자치구별 재가시설 vs 의료시설 수 비교")
st.info("거주형태(재가)와 치료형태(의료) 시설의 공급 균형을 비교합니다.")

sql3 = """
SELECT 
    p.자치구, 
    (SELECT COUNT(*) FROM 재가노인복지시설 WHERE 자치구 = p.자치구) as 재가시설수,
    (SELECT COUNT(*) FROM 노인의료복지시설 WHERE 자치구 = p.자치구) as 의료시설수
FROM population p
ORDER BY 재가시설수 DESC
"""
df3 = run_query(sql3)

# 시각화 (그룹 막대 차트)
fig3 = px.bar(df3, x='자치구', y=['재가시설수', '의료시설수'],
             barmode='group', title="자치구별 복지시설 유형별 비교")
st.plotly_chart(fig3, use_container_width=True)

with st.expander("🔍 SQL 및 인사이트 보기"):
    st.code(sql3, language='sql')
    st.write("- **인사이트 1:** 대부분의 자치구에서 재가시설의 수가 의료시설보다 월등히 많은 경향을 보입니다.")
    st.write("- **인사이트 2:** '내 집에서 돌봄'을 선호하는 정책 방향과 수요가 시설 수에 반영되어 있음을 추정할 수 있습니다.")
