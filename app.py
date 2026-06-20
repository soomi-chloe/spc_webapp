import streamlit as st

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="SPC & 공정능력분석",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 커스텀 CSS ───
st.markdown("""
<style>
    /* 메인 타이틀 스타일 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #6c757d;
        text-align: center;
        margin-bottom: 2rem;
    }
    /* KPI 카드 스타일 */
    .kpi-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2d3436;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #636e72;
        margin-top: 0.3rem;
    }
    /* 네비게이션 카드 */
    .nav-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        height: 100%;
    }
    .nav-card:hover {
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        transform: translateY(-3px);
    }
    .nav-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .nav-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2d3436;
    }
    .nav-desc {
        font-size: 0.9rem;
        color: #636e72;
        margin-top: 0.5rem;
    }
    /* 상태 배지 */
    .status-badge {
        display: inline-block;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .status-good { background: #d4edda; color: #155724; }
    .status-warn { background: #fff3cd; color: #856404; }
    .status-bad { background: #f8d7da; color: #721c24; }
    /* 구분선 */
    .divider {
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 2px;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # ─── 헤더 ───
    st.markdown('<div class="main-title">🏭 공정능력분석 & 통계적공정관리</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Process Capability Analysis & Statistical Process Control</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ─── 앱 소개 ───
    st.markdown("""
    > **스마트제조**를 위한 공정능력분석(PCA) 및 통계적공정관리(SPC) 통합 분석 도구입니다.  
    > 데이터를 입력하거나 시뮬레이션을 생성하여, 공정의 현재 상태를 분석하고 모니터링할 수 있습니다.
    """)

    # ─── 현재 세션 상태 요약 ───
    st.markdown("### 📊 현재 공정 상태 요약")

    if 'cap_result' in st.session_state and st.session_state.cap_result is not None:
        cap = st.session_state.cap_result

        col1, col2, col3, col4 = st.columns(4)

        def _get_status(val):
            if val >= 1.33:
                return "🟢 충분", "status-good"
            elif val >= 1.0:
                return "🟡 보통", "status-warn"
            else:
                return "🔴 부족", "status-bad"

        for col, key, label in zip(
            [col1, col2, col3, col4],
            ['Cp', 'Cpk', 'Pp', 'Ppk'],
            ['Cp (잠재능력)', 'Cpk (실제잠재)', 'Pp (장기능력)', 'Ppk (실제장기)']
        ):
            val = cap[key]
            status_text, status_class = _get_status(val)
            with col:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{val:.4f}</div>
                    <div class="kpi-label">{label}</div>
                    <div class="status-badge {status_class}">{status_text}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("")  # spacing

        # 종합 판정
        cpk = cap['Cpk']
        if cpk >= 1.33:
            st.success("✅ **종합 판정: 양호** — 공정능력이 충분합니다. 현재 상태를 유지하세요.")
        elif cpk >= 1.0:
            st.warning("⚠️ **종합 판정: 보통** — 공정능력 개선이 권장됩니다. 4M 관점에서 원인을 분석하세요.")
        else:
            st.error("❌ **종합 판정: 부족** — 공정능력이 부족합니다. 즉시 개선 조치가 필요합니다.")
    else:
        st.info("📌 아직 분석된 데이터가 없습니다. 왼쪽 사이드바에서 **📊 공정능력분석** 페이지로 이동하여 데이터를 입력하세요.")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ─── 페이지 네비게이션 ───
    st.markdown("### 🗂️ 기능 안내")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">📊</div>
            <div class="nav-title">공정능력분석</div>
            <div class="nav-desc">
                데이터 입력 및 정규성 검정, Cp/Cpk/Pp/Ppk 공정능력지수 계산, 
                Box-Cox 변환, 공정능력 종합 시각화
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">📈</div>
            <div class="nav-title">관리도 (SPC)</div>
            <div class="nav-desc">
                계량형(Xbar-R, Xbar-S, I-MR) 및 계수형(NP, P, C, U) 관리도 생성,
                이상점 탐지, 이상치 제거 후 재작성
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">📋</div>
            <div class="nav-title">종합 대시보드</div>
            <div class="nav-desc">
                공정능력분석 + 관리도 결과를 한 화면에서 종합 모니터링,
                KPI 패널, 공정 상태 신호등, 개선 권장사항
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ─── 이론 요약 ───
    with st.expander("📚 공정능력분석 & 통계적공정관리 이론 요약", expanded=False):
        tab1, tab2 = st.tabs(["공정능력분석", "통계적공정관리"])

        with tab1:
            st.markdown("""
            #### 공정능력 (Process Capability)
            - 생산시스템(공정)이 **관리상태(state of control)**에 있을 때, 제품의 품질수준을 만족시킬 수 있는 능력
            - 공정능력에 영향을 주는 요인: **4M** (사람, 기계, 재료, 방법)
            
            #### 공정능력지수
            | 지수 | 설명 | 특징 |
            |------|------|------|
            | **Cp** | 잠재 공정능력 | 산포만 고려, 중심 치우침 미반영 |
            | **Cpk** | 실제 잠재 공정능력 | 산포 + 중심 치우침 반영 |
            | **Pp** | 장기 공정능력 | 군내+군간 변동 고려 |
            | **Ppk** | 실제 장기 공정능력 | 모든 변동 반영 |
            
            #### 판정 기준
            - **≥ 1.33**: 🟢 충분 (양호)
            - **1.00 ~ 1.33**: 🟡 보통 (3σ 수준, 개선 권장)
            - **< 1.00**: 🔴 부족 (즉시 개선 필요)
            """)

        with tab2:
            st.markdown("""
            #### 통계적공정관리 (SPC)
            - 데이터를 사용하여 공정의 **변동(Variation)**을 감소시키고 공정 능력이 높은 상태를 유지하기 위한 통계적 관리기법
            
            #### 관리도 종류
            | 카테고리 | 관리도 | 적용 조건 |
            |----------|--------|-----------|
            | 계량형 | Xbar-R | 부분군 크기 ≥ 2 (소규모) |
            | 계량형 | Xbar-S | 부분군 크기 ≥ 2 (대규모) |
            | 계량형 | I-MR | 부분군 크기 = 1 |
            | 계수형 | NP | 불량개수, 표본크기 일정 |
            | 계수형 | P | 불량률, 표본크기 변동 |
            | 계수형 | C | 결점수, 검사단위 일정 |
            | 계수형 | U | 단위당 결점수, 검사단위 변동 |
            
            #### 관리한계선
            - **UCL** = μ + 3σ (관리상한선)
            - **CL** = μ (중심선)
            - **LCL** = μ - 3σ (관리하한선)
            """)

    # ─── 푸터 ───
    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; color:#adb5bd; font-size:0.85rem;">'
        '스마트제조 및 데이터 사이언스 | 공정능력분석 & 통계적공정관리 웹앱'
        '</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
