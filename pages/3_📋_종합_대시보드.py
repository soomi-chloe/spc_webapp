import streamlit as st
import pandas as pd
import numpy as np
import sys, os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.visualization import plot_capability_gauge, plot_control_chart
from utils.control_chart import detect_out_of_control

st.set_page_config(page_title="종합 대시보드", page_icon="📋", layout="wide")

# ─── 커스텀 CSS ───
st.markdown("""
<style>
    .dashboard-title {
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 0.5rem 0;
    }
    .divider {
        height: 2px;
        background: linear-gradient(90deg, #00b894, #00cec9, #667eea);
        border-radius: 2px;
        margin: 1rem 0;
    }
    .status-panel {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        text-align: center;
        margin: 0.5rem 0;
    }
    .traffic-light {
        font-size: 3rem;
        margin: 0.5rem 0;
    }
    .traffic-label {
        font-size: 1rem;
        font-weight: 600;
        color: #2d3436;
    }
    .recommendation-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2d3436;
        border-left: 4px solid #667eea;
        padding-left: 0.8rem;
        margin: 1.5rem 0 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="dashboard-title">📋 종합 대시보드</div>', unsafe_allow_html=True)
st.markdown("공정능력분석과 관리도 결과를 종합적으로 모니터링합니다.")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
#  데이터 확인
# ════════════════════════════════════════════

has_pca = 'cap_result' in st.session_state and st.session_state.cap_result is not None
has_spc = 'spc_charts' in st.session_state and st.session_state.spc_charts is not None

if not has_pca and not has_spc:
    st.info("📌 분석 데이터가 없습니다. **📊 공정능력분석** 또는 **📈 관리도** 페이지에서 먼저 분석을 수행해주세요.")
    st.stop()


# ════════════════════════════════════════════
#  1. 종합 KPI 패널
# ════════════════════════════════════════════
st.markdown('<div class="section-header">1️⃣ 종합 KPI 패널</div>', unsafe_allow_html=True)

if has_pca:
    cap = st.session_state.cap_result

    col1, col2, col3, col4 = st.columns(4)
    for col, key, label in zip(
        [col1, col2, col3, col4],
        ['Cp', 'Cpk', 'Pp', 'Ppk'],
        ['Cp (잠재능력)', 'Cpk (실제잠재)', 'Pp (장기능력)', 'Ppk (실제장기)']
    ):
        val = cap[key]
        with col:
            fig_g = plot_capability_gauge(val, key)
            st.plotly_chart(fig_g, use_container_width=True)
else:
    st.info("📊 공정능력분석을 먼저 수행해주세요.")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════
#  2. 공정 상태 신호등
# ════════════════════════════════════════════
st.markdown('<div class="section-header">2️⃣ 공정 상태 종합 판정</div>', unsafe_allow_html=True)

# 판정 항목들 수집
judgments = {}

# 공정능력 판정
if has_pca:
    cpk = cap['Cpk']
    if cpk >= 1.33:
        judgments['공정능력 (Cpk)'] = ('🟢', '충분', f'{cpk:.4f} ≥ 1.33')
    elif cpk >= 1.0:
        judgments['공정능력 (Cpk)'] = ('🟡', '보통', f'1.00 ≤ {cpk:.4f} < 1.33')
    else:
        judgments['공정능력 (Cpk)'] = ('🔴', '부족', f'{cpk:.4f} < 1.00')

    ppk = cap['Ppk']
    if ppk >= 1.33:
        judgments['장기 공정능력 (Ppk)'] = ('🟢', '충분', f'{ppk:.4f} ≥ 1.33')
    elif ppk >= 1.0:
        judgments['장기 공정능력 (Ppk)'] = ('🟡', '보통', f'1.00 ≤ {ppk:.4f} < 1.33')
    else:
        judgments['장기 공정능력 (Ppk)'] = ('🔴', '부족', f'{ppk:.4f} < 1.00')

# 관리도 이상 판정
if has_spc:
    charts = st.session_state.spc_charts
    total_ooc = 0
    total_points = 0
    for chart_df in charts:
        ooc = detect_out_of_control(chart_df)
        total_ooc += len(ooc)
        total_points += len(chart_df)

    if total_ooc == 0:
        judgments['관리 상태'] = ('🟢', '관리상태', '이상점 0개')
    else:
        judgments['관리 상태'] = ('🔴', '이상 발생', f'이상점 {total_ooc}개 / 전체 {total_points}개')

# 정규성 판정
if 'pca_df' in st.session_state:
    from utils.capability_analysis import normality_test
    is_normal, _, p_val = normality_test(st.session_state.pca_df)
    if is_normal:
        judgments['정규성'] = ('🟢', '만족', f'p-value = {p_val:.4f} ≥ 0.05')
    else:
        judgments['정규성'] = ('🔴', '불만족', f'p-value = {p_val:.4f} < 0.05')

# 신호등 표시
if len(judgments) == 0:
    st.info("판정 항목이 없습니다. 분석 데이터를 확인해주세요.")
    st.stop()

cols = st.columns(len(judgments))
for col, (item, (icon, status, detail)) in zip(cols, judgments.items()):
    with col:
        st.markdown(f"""
        <div class="status-panel">
            <div class="traffic-light">{icon}</div>
            <div class="traffic-label">{item}</div>
            <div style="font-size:1.1rem; font-weight:700; margin:0.3rem 0;">{status}</div>
            <div style="font-size:0.8rem; color:#636e72;">{detail}</div>
        </div>
        """, unsafe_allow_html=True)

# 종합 판정
all_good = all(v[0] == '🟢' for v in judgments.values())
any_bad = any(v[0] == '🔴' for v in judgments.values())

st.markdown("")
if all_good:
    st.success("✅ **종합 판정: 양호** — 모든 항목이 양호합니다. 현재 공정 상태를 유지하세요.")
elif any_bad:
    st.error("❌ **종합 판정: 개선 필요** — 일부 항목이 부적합합니다. 아래 권장사항을 참조하세요.")
else:
    st.warning("⚠️ **종합 판정: 주의** — 일부 항목이 보통 수준입니다. 개선을 검토하세요.")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════
#  3. 관리도 요약
# ════════════════════════════════════════════
if has_spc:
    st.markdown('<div class="section-header">3️⃣ 관리도 요약</div>', unsafe_allow_html=True)

    chart_type = st.session_state.get('spc_chart_type', 'Xbar-R')
    var_name_spc = st.session_state.get('spc_var_name', 'value')

    if 'spc_chart_fig' in st.session_state:
        st.plotly_chart(st.session_state.spc_chart_fig, use_container_width=True)
    else:
        fig_spc = plot_control_chart(charts, chart_type, var_name_spc)
        st.plotly_chart(fig_spc, use_container_width=True)

    # 이상점 요약
    for i, chart_df in enumerate(charts):
        ooc = detect_out_of_control(chart_df)
        lbl = chart_type.split('-')[i] if '-' in chart_type and i < len(chart_type.split('-')) else chart_type
        ooc_pct = len(ooc) / len(chart_df) * 100 if len(chart_df) > 0 else 0
        st.metric(f"{lbl} 이상점 비율", f"{ooc_pct:.1f}%", f"{len(ooc)}개 / {len(chart_df)}개")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════
#  4. 개선 권장사항
# ════════════════════════════════════════════
st.markdown('<div class="section-header">4️⃣ 개선 권장사항</div>', unsafe_allow_html=True)

recommendations = []

if has_pca:
    cpk = cap['Cpk']
    cp = cap['Cp']
    ppk = cap['Ppk']

    if cpk < 1.0:
        recommendations.append({
            'priority': '🔴 높음',
            'area': '공정능력',
            'content': '공정능력이 부족합니다. 4M(사람, 기계, 재료, 방법) 관점에서 원인 분석이 필요합니다.',
            'action': '① 변동 원인 분석 → ② 개선 조치 시행 → ③ 재측정 및 공정능력 재평가'
        })
    elif cpk < 1.33:
        recommendations.append({
            'priority': '🟡 중간',
            'area': '공정능력',
            'content': '공정능력이 보통 수준(3σ)입니다. 1.33 이상을 목표로 개선이 권장됩니다.',
            'action': '산포 감소 및 공정 중심 최적화를 통한 공정능력 향상'
        })

    if cpk > 2.0:
        recommendations.append({
            'priority': '💡 참고',
            'area': '비용 효율',
            'content': '공정능력이 과도하게 높습니다. 비용 효율성 관점에서 공정능력과 비용의 균형을 검토하세요.',
            'action': '과도한 검사 빈도 축소 또는 허용 범위 재검토 가능'
        })

    if abs(cp - cpk) > 0.3:
        recommendations.append({
            'priority': '🟡 중간',
            'area': '공정 중심',
            'content': f'Cp({cp:.4f})와 Cpk({cpk:.4f})의 차이가 큽니다. 공정 중심이 규격 중심에서 벗어나 있습니다.',
            'action': '공정 중심을 규격 중심으로 조정하여 Cpk를 Cp에 근접시키세요.'
        })

    if abs(cpk - ppk) > 0.3:
        recommendations.append({
            'priority': '🟡 중간',
            'area': '장기 안정성',
            'content': f'Cpk({cpk:.4f})와 Ppk({ppk:.4f})의 차이가 큽니다. 군간변동(로트 간 변동)이 큰 상태입니다.',
            'action': '장기적인 공정 안정성 확보를 위해 로트 간 변동 원인을 분석하세요.'
        })

if has_spc:
    charts = st.session_state.spc_charts
    for i, chart_df in enumerate(charts):
        ooc = detect_out_of_control(chart_df)
        if len(ooc) > 0:
            lbl = st.session_state.get('spc_chart_type', 'SPC')
            recommendations.append({
                'priority': '🔴 높음',
                'area': '관리도 이상',
                'content': f'관리도에서 {len(ooc)}개의 이상점이 탐지되었습니다.',
                'action': '① 이상원인 분석 → ② 이상원인 제거 → ③ 이상치 제거 후 관리한계 재설정 → ④ 반복'
            })
            break  # 한 번만 표시

if len(recommendations) == 0:
    st.success("🎉 **현재 공정 상태가 양호합니다.** 특별한 개선 조치가 필요하지 않습니다.")
else:
    for rec in recommendations:
        st.markdown(f"""
        <div class="recommendation-box">
            <strong>{rec['priority']} | {rec['area']}</strong><br>
            📌 {rec['content']}<br>
            <span style="color:#667eea;">🔧 조치: {rec['action']}</span>
        </div>
        """, unsafe_allow_html=True)

# ─── 푸터 ───
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#adb5bd; font-size:0.85rem;">'
    '스마트제조 및 데이터 사이언스 | 공정능력분석 & 통계적공정관리 종합 대시보드'
    '</div>',
    unsafe_allow_html=True
)
