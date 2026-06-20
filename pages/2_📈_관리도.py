import streamlit as st
import pandas as pd
import numpy as np
import sys, os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.data_generator import generate_value_data, generate_count_data
from utils.control_chart import generate_value_chart, generate_count_chart, detect_out_of_control
from utils.visualization import plot_control_chart

st.set_page_config(page_title="관리도 (SPC)", page_icon="📈", layout="wide")

# ─── 커스텀 CSS ───
st.markdown("""
<style>
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2d3436;
        border-left: 4px solid #00b894;
        padding-left: 0.8rem;
        margin: 1.5rem 0 1rem 0;
    }
    .divider {
        height: 2px;
        background: linear-gradient(90deg, #00b894, #00cec9);
        border-radius: 2px;
        margin: 1.5rem 0;
    }
    .ooc-alert {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📈 관리도 (SPC)")
st.markdown("**Statistical Process Control** — 관리도를 생성하고 공정 이상을 탐지합니다.")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
#  사이드바: 데이터 입력
# ════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ 관리도 설정")

    data_type = st.radio("데이터 유형", ["계량형 (Variable)", "계수형 (Attribute)"], index=0)

    st.markdown("---")

    input_mode = st.radio("입력 방식", ["시뮬레이션 생성", "CSV 업로드"], index=0)

    st.markdown("---")

    if data_type == "계량형 (Variable)":
        chart_type = st.selectbox(
            "관리도 유형",
            ["Xbar-R", "Xbar-s", "I-MR"],
            index=0,
            help="Xbar-R/Xbar-s: 부분군 크기 ≥ 2, I-MR: 부분군 크기 = 1"
        )

        if input_mode == "시뮬레이션 생성":
            st.subheader("📐 시뮬레이션 파라미터")
            var_name = st.text_input("변수명", value="Length", key="v_var")
            target = st.number_input("목표값", value=10.0, format="%.2f", key="v_target")
            sg_name = st.text_input("부분군명", value="Lot", key="v_sg")
            num_sg = st.slider("부분군 수", 5, 50, 20, key="v_numsg")

            if chart_type == "I-MR":
                sg_size = 1
                sg_size_variation = 0
                st.info("I-MR 관리도: 부분군 크기 = 1")
                window = st.slider("이동범위 윈도우", 2, 5, 3)
            else:
                sg_size = st.slider("부분군 크기", 2, 20, 5, key="v_sgsize")
                sg_size_variation = st.slider("부분군 크기 변동", 0, 3, 0, key="v_sgvar")
                window = 3

            sg_std = st.number_input("표준편차", value=1.0, format="%.4f", key="v_std")
            mean_shift = st.slider("평균 이동", 0.0, 5.0, 0.5, step=0.1, key="v_shift")
            seed = st.number_input("랜덤 시드", value=42, min_value=0, step=1, key="v_seed")

            if st.button("🔄 데이터 생성", use_container_width=True, type="primary", key="btn_v"):
                np.random.seed(seed)
                df_gen = generate_value_data(
                    var_name=var_name, target=target, sg_name=sg_name,
                    num_sg=num_sg, sg_size=sg_size, sg_std=sg_std,
                    mean_shift=mean_shift, sg_size_variation=sg_size_variation
                )
                st.session_state.spc_df = df_gen
                st.session_state.spc_var_name = var_name
                st.session_state.spc_sg_name = sg_name
                st.session_state.spc_data_type = "variable"
                st.session_state.spc_chart_type = chart_type
                st.session_state.spc_window = window
                st.success("✅ 계량형 데이터가 생성되었습니다!")

        else:  # CSV 업로드
            uploaded = st.file_uploader("CSV 파일", type=["csv"], key="csv_v")
            if uploaded:
                df_up = pd.read_csv(uploaded)
                sg_name = st.selectbox("부분군 컬럼", df_up.columns.tolist(), key="csv_v_sg")
                var_name = st.selectbox("측정값 컬럼", df_up.columns.tolist(), index=1, key="csv_v_var")
                window = 3
                if chart_type == "I-MR":
                    window = st.slider("이동범위 윈도우", 2, 5, 3, key="csv_v_window")

                if st.button("📥 적용", use_container_width=True, type="primary", key="btn_csv_v"):
                    st.session_state.spc_df = df_up[[sg_name, var_name]].copy()
                    st.session_state.spc_var_name = var_name
                    st.session_state.spc_sg_name = sg_name
                    st.session_state.spc_data_type = "variable"
                    st.session_state.spc_chart_type = chart_type
                    st.session_state.spc_window = window
                    st.success("✅ 데이터가 적용되었습니다!")

    else:  # 계수형
        chart_type = st.selectbox(
            "관리도 유형",
            ["NP", "P", "C", "U"],
            index=0,
            help="NP/P: 불량, C/U: 결점"
        )

        if input_mode == "시뮬레이션 생성":
            st.subheader("📐 시뮬레이션 파라미터")
            var_name = st.text_input("변수명", value="Defectives", key="c_var")
            sg_name = st.text_input("부분군명", value="Lot", key="c_sg")
            num_sg = st.slider("부분군 수", 5, 50, 20, key="c_numsg")
            sg_size = st.slider("표본 크기", 50, 1000, 200, key="c_sgsize")
            p = st.number_input("불량률/결함률", value=0.02, format="%.4f",
                                min_value=0.0001, max_value=0.5, key="c_p")

            if chart_type in ["P", "U"]:
                sg_size_variation = st.slider("표본 크기 변동", 0, 100, 20, key="c_sgvar")
            else:
                sg_size_variation = 0
                st.info(f"{chart_type} 관리도: 표본 크기 일정")

            seed = st.number_input("랜덤 시드", value=42, min_value=0, step=1, key="c_seed")

            if st.button("🔄 데이터 생성", use_container_width=True, type="primary", key="btn_c"):
                np.random.seed(seed)
                df_gen = generate_count_data(
                    var_name=var_name, sg_name=sg_name,
                    num_sg=num_sg, sg_size=sg_size, p=p,
                    sg_size_variation=sg_size_variation
                )
                st.session_state.spc_df = df_gen
                st.session_state.spc_var_name = var_name
                st.session_state.spc_sg_name = sg_name
                st.session_state.spc_data_type = "attribute"
                st.session_state.spc_chart_type = chart_type
                st.success("✅ 계수형 데이터가 생성되었습니다!")

        else:  # CSV 업로드
            uploaded = st.file_uploader("CSV 파일", type=["csv"], key="csv_c")
            if uploaded:
                df_up = pd.read_csv(uploaded)
                sg_name = st.selectbox("부분군 컬럼", df_up.columns.tolist(), key="csv_c_sg")
                sample_col = st.selectbox("표본크기 컬럼", df_up.columns.tolist(), index=1, key="csv_c_n")
                var_name = st.selectbox("측정값 컬럼", df_up.columns.tolist(), index=2, key="csv_c_var")

                if st.button("📥 적용", use_container_width=True, type="primary", key="btn_csv_c"):
                    st.session_state.spc_df = df_up[[sg_name, sample_col, var_name]].copy()
                    st.session_state.spc_var_name = var_name
                    st.session_state.spc_sg_name = sg_name
                    st.session_state.spc_data_type = "attribute"
                    st.session_state.spc_chart_type = chart_type
                    st.success("✅ 데이터가 적용되었습니다!")


# ════════════════════════════════════════════
#  메인 영역: 관리도
# ════════════════════════════════════════════

if 'spc_df' not in st.session_state:
    st.info("👈 왼쪽 사이드바에서 데이터를 입력해주세요.")
    st.stop()

df = st.session_state.spc_df
var_name = st.session_state.spc_var_name
sg_name = st.session_state.spc_sg_name
data_type = st.session_state.spc_data_type
chart_type = st.session_state.spc_chart_type

# ─── 1. 데이터 확인 ───
st.markdown('<div class="section-header">1️⃣ 데이터 확인</div>', unsafe_allow_html=True)
st.dataframe(df, use_container_width=True, height=250)
st.caption(f"데이터 유형: {'계량형' if data_type == 'variable' else '계수형'} | "
           f"관리도: {chart_type} | 데이터 수: {len(df)}")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── 2. 관리도 생성 ───
st.markdown('<div class="section-header">2️⃣ 관리도 생성</div>', unsafe_allow_html=True)

try:
    if data_type == "variable":
        window = st.session_state.get('spc_window', 3)
        charts = generate_value_chart(df, chart_type=chart_type, window=window)
    else:
        charts = generate_count_chart(df, chart_type=chart_type)

    # 관리도 시각화
    fig = plot_control_chart(charts, chart_type, var_name)
    st.plotly_chart(fig, use_container_width=True)

    # 세션 상태에 차트 저장
    st.session_state.spc_charts = charts
    st.session_state.spc_chart_fig = fig

except Exception as e:
    st.error(f"관리도 생성 중 오류가 발생했습니다: {e}")
    st.stop()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── 3. 이상 판정 ───
st.markdown('<div class="section-header">3️⃣ 이상 판정</div>', unsafe_allow_html=True)

all_ooc = []
for i, chart_df in enumerate(charts):
    ooc = detect_out_of_control(chart_df)
    chart_label = chart_type.split('-')[i] if '-' in chart_type and i < len(chart_type.split('-')) else chart_type
    if len(ooc) > 0:
        all_ooc.extend(ooc)
        st.warning(f"⚠️ **{chart_label} 차트**: {len(ooc)}개 이상점 탐지 — 부분군: {ooc}")
    else:
        st.success(f"✅ **{chart_label} 차트**: 이상점 없음 — 공정이 관리 상태에 있습니다.")

# 이상점 상세 정보
if len(all_ooc) > 0:
    with st.expander("📋 이상점 상세 정보"):
        for i, chart_df in enumerate(charts):
            ooc = detect_out_of_control(chart_df)
            if len(ooc) > 0:
                chart_label = chart_type.split('-')[i] if '-' in chart_type and i < len(chart_type.split('-')) else chart_type
                st.markdown(f"**{chart_label} 차트 이상점:**")
                ooc_data = chart_df.loc[ooc, ['point', 'CL', 'LCL', 'UCL']].copy()
                ooc_data['이탈 방향'] = ooc_data.apply(
                    lambda r: '⬆️ UCL 초과' if r['point'] > r['UCL'] else '⬇️ LCL 미만', axis=1
                )
                st.dataframe(ooc_data, use_container_width=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── 4. 이상치 제거 및 재작성 ───
if data_type == "variable" and len(all_ooc) > 0:
    st.markdown('<div class="section-header">4️⃣ 이상치 제거 및 관리도 재작성</div>', unsafe_allow_html=True)

    st.markdown("""
    > 관리도에서 이상점이 발견되면, 이상원인을 분석하여 제거하고 관리한계를 재계산하는 절차가 필요합니다.
    > 이상치가 제거된 관리한계는 기존보다 폭이 좁아집니다.
    """)

    # 첫 번째 차트(Xbar 또는 I)에서 이상점 찾기
    first_chart = charts[0]
    ooc_indices = detect_out_of_control(first_chart)

    if len(ooc_indices) > 0:
        if st.button("🔄 이상치 제거 후 관리도 재작성", type="primary", use_container_width=True):
            # 이상 부분군 제거
            df_cleaned = df[~df[sg_name].isin(ooc_indices)].copy()

            st.info(f"이상 부분군 {ooc_indices} 제거: {len(df)}개 → {len(df_cleaned)}개 데이터")

            try:
                # 재작성
                if data_type == "variable":
                    charts_revised = generate_value_chart(df_cleaned, chart_type=chart_type,
                                                         window=st.session_state.get('spc_window', 3))
                else:
                    charts_revised = generate_count_chart(df_cleaned, chart_type=chart_type)

                # 비교
                tab_before, tab_after, tab_compare = st.tabs(["📊 이전 관리도", "📊 재작성 관리도", "📋 관리한계 비교"])

                with tab_before:
                    st.plotly_chart(fig, use_container_width=True)

                with tab_after:
                    fig_revised = plot_control_chart(charts_revised, chart_type, var_name)
                    fig_revised.update_layout(title=f'{chart_type} 관리도 (이상치 제거 후) - {var_name}')
                    st.plotly_chart(fig_revised, use_container_width=True)

                    # 재작성 후 이상점 확인
                    for j, chart_df_r in enumerate(charts_revised):
                        ooc_r = detect_out_of_control(chart_df_r)
                        lbl = chart_type.split('-')[j] if '-' in chart_type and j < len(chart_type.split('-')) else chart_type
                        if len(ooc_r) > 0:
                            st.warning(f"⚠️ 재작성 후 {lbl}: {len(ooc_r)}개 이상점 여전히 존재 — {ooc_r}")
                        else:
                            st.success(f"✅ 재작성 후 {lbl}: 이상점 없음")

                with tab_compare:
                    st.markdown("**관리한계 비교**")
                    compare_data = []
                    for j in range(len(charts)):
                        lbl = chart_type.split('-')[j] if '-' in chart_type and j < len(chart_type.split('-')) else chart_type
                        compare_data.append({
                            '차트': lbl,
                            '초기 UCL': f"{charts[j]['UCL'].iloc[0]:.4f}",
                            '초기 CL': f"{charts[j]['CL'].iloc[0]:.4f}",
                            '초기 LCL': f"{charts[j]['LCL'].iloc[0]:.4f}",
                            '수정 UCL': f"{charts_revised[j]['UCL'].iloc[0]:.4f}",
                            '수정 CL': f"{charts_revised[j]['CL'].iloc[0]:.4f}",
                            '수정 LCL': f"{charts_revised[j]['LCL'].iloc[0]:.4f}",
                        })
                    st.dataframe(pd.DataFrame(compare_data), use_container_width=True)
                    st.info("→ 이상치 제거 후 관리한계 폭이 좁아진 것을 확인할 수 있습니다.")

            except Exception as e:
                st.error(f"재작성 중 오류: {e}")

# ─── 관리도 상세 데이터 ───
with st.expander("📋 관리도 상세 데이터"):
    for i, chart_df in enumerate(charts):
        chart_label = chart_type.split('-')[i] if '-' in chart_type and i < len(chart_type.split('-')) else chart_type
        st.markdown(f"**{chart_label} 차트 데이터**")
        st.dataframe(chart_df.style.format("{:.4f}"), use_container_width=True)
