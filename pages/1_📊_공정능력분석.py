import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import shapiro, boxcox
import sys, os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.data_generator import generate_data
from utils.capability_analysis import normality_test, process_capability, judge_capability
from utils.unbiased_constants import calc_unbiased_const
from utils.visualization import (
    plot_boxplot, plot_histogram, plot_qq,
    plot_process_capability, plot_boxcox_comparison, plot_capability_gauge
)

st.set_page_config(page_title="공정능력분석", page_icon="📊", layout="wide")

# ─── 커스텀 CSS ───
st.markdown("""
<style>
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2d3436;
        border-left: 4px solid #667eea;
        padding-left: 0.8rem;
        margin: 1.5rem 0 1rem 0;
    }
    .result-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        border: 1px solid #e9ecef;
        margin: 0.5rem 0;
    }
    .index-value {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .index-label {
        font-size: 0.85rem;
        color: #636e72;
    }
    .divider {
        height: 2px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 2px;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📊 공정능력분석")
st.markdown("**Process Capability Analysis** — 데이터를 입력하고 공정능력을 분석합니다.")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
#  사이드바: 데이터 입력
# ════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ 데이터 설정")

    input_mode = st.radio(
        "데이터 입력 방식",
        ["시뮬레이션 데이터 생성", "CSV 파일 업로드"],
        index=0
    )

    st.markdown("---")

    if input_mode == "시뮬레이션 데이터 생성":
        st.subheader("📐 시뮬레이션 파라미터")

        var_name = st.text_input("변수명", value="thickness")
        target = st.number_input("목표값 (Target)", value=0.5, format="%.4f")
        tolerance = st.number_input("허용오차 (Tolerance)", value=0.05, format="%.4f")
        sg_name = st.text_input("부분군명", value="line")
        num_sg = st.slider("부분군 개수", 2, 20, 5)
        sg_size = st.slider("부분군 당 표본 크기", 2, 100, 30)
        sg_std = st.number_input("부분군 표준편차", value=0.01, format="%.6f", min_value=0.000001)

        st.markdown("**평균 이동 범위**")
        shift_min = st.number_input("최소 이동", value=-0.01, format="%.4f")
        shift_max = st.number_input("최대 이동", value=0.01, format="%.4f")

        seed = st.number_input("랜덤 시드", value=42, min_value=0, step=1)

        if st.button("🔄 데이터 생성", use_container_width=True, type="primary"):
            np.random.seed(seed)
            df, LSL, USL = generate_data(
                var_name=var_name, target=target, tolerance=tolerance,
                sg_name=sg_name, num_sg=num_sg, sg_size=sg_size,
                sg_std=sg_std, mean_shift=(shift_min, shift_max)
            )
            st.session_state.pca_df = df
            st.session_state.pca_LSL = LSL
            st.session_state.pca_USL = USL
            st.session_state.pca_var_name = var_name
            st.session_state.pca_sg_name = sg_name
            st.success("✅ 데이터가 생성되었습니다!")

    else:  # CSV 업로드
        st.subheader("📁 CSV 파일 업로드")
        uploaded_file = st.file_uploader("CSV 파일 선택", type=["csv"])

        if uploaded_file is not None:
            df_uploaded = pd.read_csv(uploaded_file)
            st.write("**컬럼 목록:**", list(df_uploaded.columns))

            sg_name = st.selectbox("부분군 컬럼", df_uploaded.columns.tolist(), index=0)
            var_name = st.selectbox("측정값 컬럼", df_uploaded.columns.tolist(),
                                   index=min(1, len(df_uploaded.columns) - 1))

            LSL = st.number_input("규격하한 (LSL)", value=0.0, format="%.4f")
            USL = st.number_input("규격상한 (USL)", value=1.0, format="%.4f")

            if st.button("📥 데이터 적용", use_container_width=True, type="primary"):
                df = df_uploaded[[sg_name, var_name]].copy()
                st.session_state.pca_df = df
                st.session_state.pca_LSL = LSL
                st.session_state.pca_USL = USL
                st.session_state.pca_var_name = var_name
                st.session_state.pca_sg_name = sg_name
                st.success("✅ 데이터가 적용되었습니다!")


# ════════════════════════════════════════════
#  메인 영역: 분석 결과
# ════════════════════════════════════════════

if 'pca_df' not in st.session_state:
    st.info("👈 왼쪽 사이드바에서 데이터를 입력해주세요.")
    st.stop()

df = st.session_state.pca_df
LSL = st.session_state.pca_LSL
USL = st.session_state.pca_USL
var_name = st.session_state.pca_var_name
sg_name = st.session_state.pca_sg_name

# ─── 1. 데이터 탐색 ───
st.markdown('<div class="section-header">1️⃣ 데이터 탐색</div>', unsafe_allow_html=True)

tab_data, tab_stats = st.tabs(["📋 원시 데이터", "📊 기술통계량"])

with tab_data:
    st.dataframe(df, use_container_width=True, height=300)
    st.caption(f"총 {len(df)}개 데이터, {df[sg_name].nunique()}개 부분군")

with tab_stats:
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("**전체 통계**")
        overall_stats = df[var_name].describe()
        st.dataframe(overall_stats.to_frame().T, use_container_width=True)
    with col_s2:
        st.markdown("**부분군별 평균/표준편차**")
        sg_stats = df.groupby(sg_name)[var_name].agg(['mean', 'std', 'count'])
        st.dataframe(sg_stats, use_container_width=True)

# 시각화: 박스플롯 + 히스토그램
col_v1, col_v2 = st.columns(2)
with col_v1:
    fig_box = plot_boxplot(df, LSL, USL)
    st.plotly_chart(fig_box, use_container_width=True, key="pca_boxplot")
with col_v2:
    fig_hist = plot_histogram(df, LSL, USL)
    st.plotly_chart(fig_hist, use_container_width=True, key="pca_histogram")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── 2. 정규성 검정 ───
st.markdown('<div class="section-header">2️⃣ 정규성 검정</div>', unsafe_allow_html=True)

with st.expander("ℹ️ 정규성 검정이란?", expanded=False):
    st.markdown("""
    공정능력지수는 **데이터가 정규분포를 따른다는 가정** 하에 계산됩니다.
    - **Shapiro-Wilk 검정**: p-value ≥ 0.05 → 정규성 만족
    - 정규성 불만족 시 **Box-Cox 변환**을 적용하여 정규분포로 변환 후 분석합니다.
    """)

is_normal, stat, p_value = normality_test(df)

col_n1, col_n2, col_n3 = st.columns([1, 1, 2])

with col_n1:
    st.metric("Shapiro-Wilk 통계량", f"{stat:.6f}")
with col_n2:
    st.metric("p-value", f"{p_value:.6f}")
with col_n3:
    if is_normal:
        st.success("🟢 **정규성 만족** (p-value ≥ 0.05) — 공정능력지수 계산이 유효합니다.")
    else:
        st.error("🔴 **정규성 불만족** (p-value < 0.05) — Box-Cox 변환을 적용합니다.")

# Q-Q Plot
fig_qq = plot_qq(df)
st.plotly_chart(fig_qq, use_container_width=True, key="pca_qq")

# Box-Cox 변환 (정규성 불만족 시)
use_transformed = False
if not is_normal:
    st.markdown('<div class="section-header">🔄 Box-Cox 변환</div>', unsafe_allow_html=True)

    data_values = df[var_name].values
    # Box-Cox는 양수 데이터만 가능
    if np.all(data_values > 0):
        data_transformed, lambda_val = boxcox(data_values)
        st.info(f"**Box-Cox 최적 λ = {lambda_val:.4f}**")

        # 변환 후 정규성 재검정
        stat_t, p_t = shapiro(data_transformed)
        if p_t >= 0.05:
            st.success(f"✅ 변환 후 정규성 만족 (p-value = {p_t:.6f})")
            use_transformed = True

            # 변환 전후 비교
            fig_bc = plot_boxcox_comparison(data_values, data_transformed, lambda_val)
            st.plotly_chart(fig_bc, use_container_width=True, key="pca_boxcox_compare")

            # 변환된 데이터로 규격도 변환
            LSL_t = boxcox([LSL], lmbda=lambda_val)[0] if LSL > 0 else LSL
            USL_t = boxcox([USL], lmbda=lambda_val)[0] if USL > 0 else USL

            # 변환된 데이터프레임 생성
            df_transformed = df.copy()
            df_transformed[var_name] = data_transformed
        else:
            st.warning(f"⚠️ Box-Cox 변환 후에도 정규성 불만족 (p-value = {p_t:.6f}). 결과 해석에 주의하세요.")
    else:
        st.warning("⚠️ 데이터에 0 이하 값이 포함되어 Box-Cox 변환을 적용할 수 없습니다.")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── 3. 공정능력지수 계산 ───
st.markdown('<div class="section-header">3️⃣ 공정능력지수 계산</div>', unsafe_allow_html=True)

if use_transformed:
    cap_result = process_capability(df_transformed, LSL_t, USL_t)
    st.info("📌 Box-Cox 변환된 데이터 기준으로 공정능력지수가 계산되었습니다. (무차원 비율이므로 해석 동일)")
else:
    cap_result = process_capability(df, LSL, USL)

# 세션 상태에 저장 (홈/대시보드에서 사용)
st.session_state.cap_result = cap_result

# KPI 카드 표시
col1, col2, col3, col4 = st.columns(4)

for col, key, label, desc in zip(
    [col1, col2, col3, col4],
    ['Cp', 'Cpk', 'Pp', 'Ppk'],
    ['Cp', 'Cpk', 'Pp', 'Ppk'],
    ['잠재 공정능력\n(군내변동, 산포만 고려)', '실제 잠재 공정능력\n(치우침 + 산포)',
     '장기 공정능력\n(군내+군간 변동)', '실제 장기 공정능력\n(모든 변동 반영)']
):
    val = cap_result[key]
    judge_text, judge_color = judge_capability(val)
    with col:
        fig_gauge = plot_capability_gauge(val, label)
        st.plotly_chart(fig_gauge, use_container_width=True, key=f"pca_gauge_{key}")
        st.markdown(f"<div style='text-align:center;'>"
                    f"<span style='color:{judge_color}; font-weight:700; font-size:1.1rem;'>"
                    f"{judge_text}</span></div>", unsafe_allow_html=True)

# 상세 통계
with st.expander("📋 상세 통계 정보"):
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("**공정 통계**")
        st.write(f"- 전체 평균 (X̄): **{cap_result['x_bar']:.6f}**")
        st.write(f"- σ_within (군내변동): **{cap_result['sigma_within']:.6f}**")
        st.write(f"- σ_overall (전체변동): **{cap_result['sigma_overall']:.6f}**")
    with col_d2:
        st.markdown("**규격 정보**")
        if use_transformed:
            st.write(f"- USL (변환 후): **{USL_t:.6f}**")
            st.write(f"- LSL (변환 후): **{LSL_t:.6f}**")
            st.write(f"- USL (원본): **{USL:.6f}**")
            st.write(f"- LSL (원본): **{LSL:.6f}**")
        else:
            st.write(f"- USL: **{USL:.6f}**")
            st.write(f"- LSL: **{LSL:.6f}**")
        st.write(f"- 허용 범위: **{USL - LSL:.6f}**")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── 4. 공정능력분석 종합 그래프 ───
st.markdown('<div class="section-header">4️⃣ 공정능력분석 종합 그래프</div>', unsafe_allow_html=True)

if use_transformed:
    fig_pca = plot_process_capability(df_transformed, LSL_t, USL_t, cap_result)
else:
    fig_pca = plot_process_capability(df, LSL, USL, cap_result)

st.plotly_chart(fig_pca, use_container_width=True, key="pca_overall")

# ─── 판정 및 권장사항 ───
st.markdown('<div class="section-header">5️⃣ 판정 및 권장사항</div>', unsafe_allow_html=True)

cpk = cap_result['Cpk']
ppk = cap_result['Ppk']

if cpk >= 2.0:
    st.info("💡 **Cpk ≥ 2.0**: 공정능력이 과도하게 높습니다. 비용 효율성 관점에서 공정능력과 비용의 균형을 검토하세요.")
elif cpk >= 1.33:
    st.success("✅ **Cpk ≥ 1.33**: 공정능력이 충분합니다. 현재 공정 상태를 유지하세요.")
elif cpk >= 1.0:
    st.warning("⚠️ **1.0 ≤ Cpk < 1.33**: 공정능력이 보통 수준입니다. 4M(사람, 기계, 재료, 방법) 관점에서 원인 분석이 권장됩니다.")
else:
    st.error("❌ **Cpk < 1.0**: 공정능력이 부족합니다. 즉시 개선 조치가 필요합니다.")

if abs(cap_result['Cp'] - cap_result['Cpk']) > 0.3:
    st.warning("⚠️ **Cp와 Cpk의 차이가 큽니다**: 공정 중심이 규격 중심에서 크게 벗어나 있습니다. 중심 조정이 필요합니다.")

if abs(cap_result['Cpk'] - cap_result['Ppk']) > 0.3:
    st.warning("⚠️ **Cpk와 Ppk의 차이가 큽니다**: 군간변동(로트 간 변동)이 큽니다. 장기적인 공정 안정성 개선이 필요합니다.")
