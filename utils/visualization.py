"""
SPC 웹앱 시각화 유틸리티 모듈
=================================
모든 Plotly 시각화 함수를 포함합니다.
차트 제목과 레이블은 한국어로 표시됩니다.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats


# ──────────────────────────────────────────────
# 1. 박스플롯 (Box Plot)
# ──────────────────────────────────────────────
def plot_boxplot(data: pd.DataFrame, LSL=None, USL=None) -> go.Figure:
    """부분군별 박스플롯을 생성합니다.

    Parameters
    ----------
    data : DataFrame
        2개 컬럼 [sg_name, var_name] 을 가진 데이터프레임
    LSL : float, optional
        규격 하한 (Lower Specification Limit)
    USL : float, optional
        규격 상한 (Upper Specification Limit)

    Returns
    -------
    fig : plotly.graph_objects.Figure
    """
    # 부분군명과 변수명 추출
    sg_name, var_name = data.columns

    # Plotly Express 박스플롯 생성
    fig = px.box(
        data,
        x=sg_name,               # x축: 부분군
        y=var_name,              # y축: 측정값
        color=sg_name,           # 부분군별 색상 구분
        title=f'{var_name} 박스플롯',
        points='all',            # 모든 관측치 표시
    )

    # 규격 하한선 추가
    if LSL is not None:
        fig.add_hline(
            y=LSL,
            line_width=1.5,
            line_dash='dash',
            line_color='red',
            annotation_text='LSL',
            annotation_position='top left',
        )

    # 규격 상한선 추가
    if USL is not None:
        fig.add_hline(
            y=USL,
            line_width=1.5,
            line_dash='dash',
            line_color='red',
            annotation_text='USL',
            annotation_position='top left',
        )

    # 레이아웃 설정
    fig.update_layout(
        template='plotly_white',
        width=800,
        height=450,
        xaxis_title='부분군',
        yaxis_title=var_name,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=False,
    )

    return fig


# ──────────────────────────────────────────────
# 2. 히스토그램 (Histogram)
# ──────────────────────────────────────────────
def plot_histogram(data: pd.DataFrame, LSL: float, USL: float) -> go.Figure:
    """부분군별 히스토그램을 생성하고 규격선을 표시합니다.

    Parameters
    ----------
    data : DataFrame
        2개 컬럼 [sg_name, var_name]
    LSL : float
        규격 하한
    USL : float
        규격 상한

    Returns
    -------
    fig : plotly.graph_objects.Figure
    """
    # 부분군명과 변수명 추출
    sg_name, var_name = data.columns

    # 히스토그램 생성 (부분군별 facet_row)
    fig = px.histogram(
        data,
        x=var_name,
        nbins=20,
        facet_row=sg_name,           # 부분군별로 행을 나누어 표시
        title=f'{var_name} 히스토그램',
        opacity=0.7,
    )

    # LSL 수직선 추가 (빨간 점선)
    fig.add_vline(
        x=LSL,
        line_width=1.5,
        line_dash='dash',
        line_color='red',
        annotation_text='LSL',
    )

    # USL 수직선 추가 (빨간 점선)
    fig.add_vline(
        x=USL,
        line_width=1.5,
        line_dash='dash',
        line_color='red',
        annotation_text='USL',
    )

    # 레이아웃 설정
    fig.update_layout(
        template='plotly_white',
        width=700,
        height=500,
        margin=dict(l=50, r=50, t=80, b=30),
    )

    return fig


# ──────────────────────────────────────────────
# 3. Q-Q 플롯 (Q-Q Plot)
# ──────────────────────────────────────────────
def plot_qq(data: pd.DataFrame) -> go.Figure:
    """데이터의 정규성을 시각적으로 확인하기 위한 Q-Q 플롯을 생성합니다.

    Parameters
    ----------
    data : DataFrame
        2개 컬럼 [sg_name, var_name]

    Returns
    -------
    fig : plotly.graph_objects.Figure
    """
    # 부분군명, 변수명 추출
    sg_name, var_name = data.columns

    # NaN 제거 후 Z-score 계산
    values = data[var_name].dropna().values
    z_value = stats.zscore(values)

    # Q-Q plot 데이터 생성 (이론적 분위수 vs 표본 분위수)
    (theoretical_quantiles, sample_quantiles), _ = stats.probplot(
        z_value, dist='norm'
    )

    # Q-Q 산점도 생성
    fig = px.scatter(
        x=theoretical_quantiles,
        y=sample_quantiles,
        title='Q-Q Plot',
        labels={
            'x': '이론적 분위수 (Theoretical Quantiles)',
            'y': '표본 분위수 (Sample Quantiles)',
        },
    )

    # y = x 기준선 추가 (빨간색)
    fig.add_shape(
        type='line',
        x0=-3, y0=-3,
        x1=3, y1=3,
        line=dict(color='red', width=2),
    )

    # 레이아웃 설정
    fig.update_layout(
        template='plotly_white',
        width=450,
        height=450,
        margin=dict(l=50, r=30, t=60, b=50),
    )

    return fig


# ──────────────────────────────────────────────
# 4. 공정능력분석 그래프 (Process Capability)
# ──────────────────────────────────────────────
def plot_process_capability(
    data: pd.DataFrame,
    LSL: float,
    USL: float,
    cap_result: dict,
) -> go.Figure:
    """공정능력분석 히스토그램 + 정규분포 곡선 + 능력지수 표시를 생성합니다.

    Parameters
    ----------
    data : DataFrame
        2개 컬럼 [sg_name, var_name]
    LSL : float
        규격 하한
    USL : float
        규격 상한
    cap_result : dict
        {'Cp': ..., 'Cpk': ..., 'Pp': ..., 'Ppk': ...}

    Returns
    -------
    fig : plotly.graph_objects.Figure
    """
    from scipy.stats import norm

    # 부분군명, 변수명 추출
    sg_name, var_name = data.columns

    # ── 히스토그램 생성 (marginal='box') ──
    fig = px.histogram(
        data,
        x=var_name,
        nbins=20,
        color=sg_name,
        marginal='box',
        title=f'{var_name} 공정능력분석',
        opacity=0.5,
    )

    # ── 정규분포 곡선 오버레이 ──
    x_range = np.linspace(
        data[var_name].min() - data[var_name].std(),
        data[var_name].max() + data[var_name].std(),
        300,
    )
    y_pdf = norm.pdf(
        x_range,
        loc=data[var_name].mean(),
        scale=data[var_name].std(),
    )

    # 히스토그램 밀도에 맞게 스케일 조정
    bin_width = (data[var_name].max() - data[var_name].min()) / 20
    y_scaled = y_pdf * len(data) * bin_width

    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=y_scaled,
            mode='lines',
            line=dict(color='navy', width=2, dash='solid'),
            name='정규분포',
            showlegend=True,
        )
    )

    # ── LSL / USL 수직선 추가 ──
    fig.add_vline(
        x=LSL,
        line_width=1.5,
        line_dash='dash',
        line_color='red',
        annotation_text='LSL',
    )
    fig.add_vline(
        x=USL,
        line_width=1.5,
        line_dash='dash',
        line_color='red',
        annotation_text='USL',
    )

    # ── 공정능력지수 주석 상자 ──
    Cp = cap_result.get('Cp', 0)
    Cpk = cap_result.get('Cpk', 0)
    Pp = cap_result.get('Pp', 0)
    Ppk = cap_result.get('Ppk', 0)

    fig.add_annotation(
        xref='paper', yref='paper',
        x=1.14, y=0.0,
        text=(
            f"Cp ={Cp:.4f}<br>"
            f"Cpk={Cpk:.4f}<br>"
            f"Pp ={Pp:.4f}<br>"
            f"Ppk={Ppk:.4f}"
        ),
        align='right',
        showarrow=False,
        bordercolor='black',
        borderwidth=1,
        borderpad=6,
        font=dict(family='monospace', size=12),
    )

    # ── 레이아웃 설정 ──
    fig.update_layout(
        template='plotly_white',
        width=800,
        height=500,
        margin=dict(l=50, r=100, t=80, b=50),
    )

    return fig


# ──────────────────────────────────────────────
# 5. 관리도 (Control Chart)
# ──────────────────────────────────────────────
def plot_control_chart(
    charts: tuple,
    chart_name: str,
    var_name: str = 'value',
) -> go.Figure:
    """Shewhart 관리도 (Xbar-R, I-MR, NP, P, C, U 등)를 시각화합니다.

    Parameters
    ----------
    charts : tuple of DataFrames
        각 DataFrame은 [point, CL, LCL, UCL] 컬럼을 포함
    chart_name : str
        관리도 이름 (예: 'Xbar-R', 'I-MR', 'NP')
    var_name : str
        측정 변수명

    Returns
    -------
    fig : plotly.graph_objects.Figure
    """
    num_charts = len(charts)
    # 차트 이름을 '-'로 분리하여 각 서브플롯의 y축 제목으로 사용
    chart_labels = chart_name.split('-')

    # 서브플롯 생성 (행 개수 = 차트 수)
    fig = make_subplots(
        rows=num_charts, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
    )

    for i in range(num_charts):
        chart_df = charts[i]

        # ── 관측치 (lines + markers) ──
        fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df['point'],
                mode='lines+markers',
                marker=dict(size=8, color='#1f77b4'),
                line=dict(color='#1f77b4'),
                name=chart_labels[i] if i < len(chart_labels) else f'Chart {i+1}',
            ),
            row=i + 1, col=1,
        )

        # ── 중심선 CL (초록색 dash-dot) ──
        fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df['CL'],
                mode='lines',
                line=dict(color='green', dash='dashdot'),
                name='CL',
                showlegend=False,
            ),
            row=i + 1, col=1,
        )

        # ── 하한선 LCL (빨간색 dotted) ──
        fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df['LCL'],
                mode='lines',
                line=dict(color='red', dash='dot'),
                name='LCL',
                showlegend=False,
            ),
            row=i + 1, col=1,
        )

        # ── 상한선 UCL (마젠타 dotted) ──
        fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df['UCL'],
                mode='lines',
                line=dict(color='magenta', dash='dot'),
                name='UCL',
                showlegend=False,
            ),
            row=i + 1, col=1,
        )

        # ── 관리 이탈점 강조 (빨간 마커, 크기 12) ──
        ooc_mask = (chart_df['point'] > chart_df['UCL']) | (
            chart_df['point'] < chart_df['LCL']
        )
        ooc_data = chart_df[ooc_mask]

        if len(ooc_data) > 0:
            fig.add_trace(
                go.Scatter(
                    x=ooc_data.index,
                    y=ooc_data['point'],
                    mode='markers',
                    marker=dict(size=12, color='red', symbol='circle'),
                    name='이상점',
                    showlegend=False,
                ),
                row=i + 1, col=1,
            )

        # ── y축 제목 설정 ──
        y_label = chart_labels[i] if i < len(chart_labels) else f'Chart {i+1}'
        fig.update_yaxes(title=y_label, row=i + 1, col=1)

        # ── 마지막 관측치 위치에 CL, LCL, UCL 값 주석 표시 ──
        last_index = chart_df.index[-1]
        cl_val = chart_df['CL'].iloc[-1]
        lcl_val = chart_df['LCL'].iloc[-1]
        ucl_val = chart_df['UCL'].iloc[-1]

        # UCL 주석
        fig.add_annotation(
            x=last_index + 2 if isinstance(last_index, (int, float, np.integer)) else last_index,
            y=ucl_val,
            text=f'{ucl_val:.4f}',
            showarrow=False,
            font=dict(color='magenta', size=10),
            row=i + 1, col=1,
        )
        # CL 주석
        fig.add_annotation(
            x=last_index + 2 if isinstance(last_index, (int, float, np.integer)) else last_index,
            y=cl_val,
            text=f'{cl_val:.4f}',
            showarrow=False,
            font=dict(color='green', size=10),
            row=i + 1, col=1,
        )
        # LCL 주석
        fig.add_annotation(
            x=last_index + 2 if isinstance(last_index, (int, float, np.integer)) else last_index,
            y=lcl_val,
            text=f'{lcl_val:.4f}',
            showarrow=False,
            font=dict(color='red', size=10),
            row=i + 1, col=1,
        )

    # ── x축 / y축 눈금선 설정 ──
    fig.update_xaxes(ticks='outside', minor_showgrid=True)
    fig.update_yaxes(ticks='outside', minor_showgrid=True)

    # ── 전체 레이아웃 설정 ──
    fig.update_layout(
        template='seaborn',
        width=800,
        height=100 + 300 * num_charts,
        showlegend=False,
        title=f'{chart_name} 관리도 - {var_name}',
        margin=dict(l=50, r=60, t=80, b=50),
    )

    return fig


# ──────────────────────────────────────────────
# 6. Box-Cox 변환 전후 비교 (Box-Cox Comparison)
# ──────────────────────────────────────────────
def plot_boxcox_comparison(
    data_original: np.ndarray,
    data_transformed: np.ndarray,
    lambda_val: float,
) -> go.Figure:
    """Box-Cox 변환 전후 히스토그램을 나란히 비교합니다.

    Parameters
    ----------
    data_original : array-like
        원본 데이터
    data_transformed : array-like
        Box-Cox 변환된 데이터
    lambda_val : float
        변환에 사용된 λ 값

    Returns
    -------
    fig : plotly.graph_objects.Figure
    """
    # 서브플롯 생성 (1행 2열)
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            '원본 데이터 (비대칭)',
            f'Box-Cox 변환 (λ={lambda_val:.2f})',
        ],
    )

    # 원본 데이터 히스토그램
    fig.add_trace(
        go.Histogram(
            x=data_original,
            nbinsx=20,
            name='원본',
            marker_color='indianred',
            opacity=0.7,
        ),
        row=1, col=1,
    )

    # 변환 데이터 히스토그램
    fig.add_trace(
        go.Histogram(
            x=data_transformed,
            nbinsx=20,
            name='변환',
            marker_color='steelblue',
            opacity=0.7,
        ),
        row=1, col=2,
    )

    # 레이아웃 설정
    fig.update_layout(
        template='plotly_white',
        title='Box-Cox 변환 전후 비교',
        height=380,
        width=750,
        showlegend=False,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    return fig


# ──────────────────────────────────────────────
# 7. 공정능력 게이지 (Capability Gauge)
# ──────────────────────────────────────────────
def plot_capability_gauge(value: float, title: str = 'Cpk') -> go.Figure:
    """공정능력지수를 게이지 차트(Indicator)로 시각화합니다.

    Parameters
    ----------
    value : float
        표시할 공정능력지수 값
    title : str
        게이지 차트 제목 (예: 'Cp', 'Cpk', 'Pp', 'Ppk')

    Returns
    -------
    fig : plotly.graph_objects.Figure
    """
    fig = go.Figure(
        go.Indicator(
            mode='gauge+number',
            value=value,
            title={'text': title, 'font': {'size': 20}},
            number={'font': {'size': 36}},
            gauge=dict(
                axis=dict(range=[0, 2.5], tickwidth=1),
                bar=dict(color='darkblue'),
                bgcolor='white',
                steps=[
                    # 빨간색: 능력 부족 (0 ~ 1.0)
                    dict(range=[0, 1.0], color='#ff4d4d'),
                    # 노란색: 보통 (1.0 ~ 1.33)
                    dict(range=[1.0, 1.33], color='#ffd633'),
                    # 초록색: 양호 (1.33 ~ 2.5)
                    dict(range=[1.33, 2.5], color='#33cc33'),
                ],
                threshold=dict(
                    line=dict(color='black', width=3),
                    thickness=0.8,
                    value=value,
                ),
            ),
        )
    )

    fig.update_layout(
        width=320,
        height=260,
        margin=dict(l=30, r=30, t=60, b=20),
    )

    return fig
