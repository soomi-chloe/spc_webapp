"""
관리도 모듈 (Control Chart)
=============================
계량형/계수형 관리도 데이터를 생성하고, 이상점을 탐지합니다.

- generate_value_chart: 계량형 관리도 (Xbar-R, Xbar-s, I-MR)
- generate_count_chart: 계수형 관리도 (NP, P, C, U)
- detect_out_of_control: 관리 이탈점 탐지
"""

import numpy as np
import pandas as pd

from utils.unbiased_constants import unbiased_coefficient


def generate_value_chart(
    data: pd.DataFrame,
    chart_type: str = 'Xbar-R',
    window: int = 3,
) -> tuple:
    """
    계량형 관리도 데이터를 생성합니다.

    Parameters
    ----------
    data : pd.DataFrame
        2개 컬럼: [부분군 이름, 측정값]
    chart_type : str
        관리도 유형: 'Xbar-R', 'Xbar-s', 'I-MR'
    window : int
        I-MR 차트의 이동 범위 윈도우 크기 (기본값: 3)

    Returns
    -------
    tuple of pd.DataFrame
        각 DataFrame의 컬럼: [point, CL, LCL, UCL]
        - Xbar-R: (Xbar_chart, R_chart)
        - Xbar-s: (Xbar_chart, s_chart)
        - I-MR: (I_chart, MR_chart)
    """
    sg_col = data.columns[0]  # 부분군 컬럼
    var_col = data.columns[1]  # 측정값 컬럼

    if chart_type == 'Xbar-R':
        return _xbar_r_chart(data, sg_col, var_col)
    elif chart_type == 'Xbar-s':
        return _xbar_s_chart(data, sg_col, var_col)
    elif chart_type == 'I-MR':
        return _i_mr_chart(data, sg_col, var_col, window)
    else:
        raise ValueError(
            f"알 수 없는 차트 유형: '{chart_type}'. "
            f"사용 가능: 'Xbar-R', 'Xbar-s', 'I-MR'"
        )


def _xbar_r_chart(
    data: pd.DataFrame,
    sg_col: str,
    var_col: str,
) -> tuple:
    """Xbar-R 관리도 계산"""
    grouped = data.groupby(sg_col)[var_col]

    # 부분군 통계량
    xbar = grouped.mean()        # 부분군 평균
    r = grouped.max() - grouped.min()  # 부분군 범위
    n_i = grouped.count()        # 부분군 크기

    # 중심선 계산
    xbar_bar = xbar.mean()       # 총 평균
    r_bar = r.mean()             # 평균 범위

    # 최빈 부분군 크기로 계수 선택
    m = int(n_i.mode().iloc[0])

    # 관리도 계수 조회
    A2 = unbiased_coefficient('A2', m)
    D3 = unbiased_coefficient('D3', m)
    D4 = unbiased_coefficient('D4', m)

    # Xbar 관리도 (인덱스는 부분군 ID)
    xbar_chart = pd.DataFrame({
        'point': xbar.values,
        'CL': xbar_bar,
        'LCL': xbar_bar - A2 * r_bar,
        'UCL': xbar_bar + A2 * r_bar,
    }, index=xbar.index)

    # R 관리도 (인덱스는 부분군 ID)
    r_chart = pd.DataFrame({
        'point': r.values,
        'CL': r_bar,
        'LCL': D3 * r_bar,
        'UCL': D4 * r_bar,
    }, index=r.index)

    return (xbar_chart, r_chart)


def _xbar_s_chart(
    data: pd.DataFrame,
    sg_col: str,
    var_col: str,
) -> tuple:
    """Xbar-s 관리도 계산"""
    grouped = data.groupby(sg_col)[var_col]

    # 부분군 통계량
    xbar = grouped.mean()         # 부분군 평균
    s = grouped.std(ddof=1)       # 부분군 표준편차
    n_i = grouped.count()         # 부분군 크기

    # 중심선 계산
    xbar_bar = xbar.mean()        # 총 평균
    s_bar = s.mean()              # 평균 표준편차

    # 최빈 부분군 크기로 계수 선택
    m = int(n_i.mode().iloc[0])

    # 관리도 계수 조회
    A3 = unbiased_coefficient('A3', m)
    B3 = unbiased_coefficient('B3', m)
    B4 = unbiased_coefficient('B4', m)

    # Xbar 관리도 (인덱스는 부분군 ID)
    xbar_chart = pd.DataFrame({
        'point': xbar.values,
        'CL': xbar_bar,
        'LCL': xbar_bar - A3 * s_bar,
        'UCL': xbar_bar + A3 * s_bar,
    }, index=xbar.index)

    # s 관리도 (인덱스는 부분군 ID)
    s_chart = pd.DataFrame({
        'point': s.values,
        'CL': s_bar,
        'LCL': B3 * s_bar,
        'UCL': B4 * s_bar,
    }, index=s.index)

    return (xbar_chart, s_chart)


def _i_mr_chart(
    data: pd.DataFrame,
    sg_col: str,
    var_col: str,
    window: int,
) -> tuple:
    """I-MR (개별값-이동범위) 관리도 계산"""
    values = data[var_col].values
    # 부분군 ID 인덱스 (있으면 사용, 없으면 1-based)
    if sg_col in data.columns:
        idx = data[sg_col].values
    else:
        idx = np.arange(1, len(values) + 1)

    # 전체 평균
    x_bar = np.mean(values)

    # 이동 범위(Moving Range) 계산 — 롤링 윈도우의 최대-최소
    w = window
    mr_values = []
    for i in range(len(values)):
        if i < w - 1:
            mr_values.append(np.nan)  # 윈도우가 채워지기 전
        else:
            window_data = values[i - w + 1: i + 1]
            mr_values.append(np.max(window_data) - np.min(window_data))
    mr_values = np.array(mr_values)

    # MR 평균 (NaN 제외)
    mr_bar = np.nanmean(mr_values)

    # 관리도 계수 조회 (윈도우 크기 w 기준)
    D3 = unbiased_coefficient('D3', w)
    D4 = unbiased_coefficient('D4', w)
    d2 = unbiased_coefficient('d2', w)

    # I (개별값) 관리도 (인덱스는 부분군 ID)
    i_chart = pd.DataFrame({
        'point': values,
        'CL': x_bar,
        'LCL': x_bar - 3 * mr_bar / d2,
        'UCL': x_bar + 3 * mr_bar / d2,
    }, index=idx)

    # MR (이동범위) 관리도 (인덱스는 부분군 ID)
    mr_chart = pd.DataFrame({
        'point': mr_values,
        'CL': mr_bar,
        'LCL': D3 * mr_bar,
        'UCL': D4 * mr_bar,
    }, index=idx)

    return (i_chart, mr_chart)


# ──────────────────────────────────────────────
# 계수형 관리도 (Count Chart)
# ──────────────────────────────────────────────

def generate_count_chart(
    df_raw: pd.DataFrame,
    chart_type: str = 'NP',
) -> tuple:
    """
    계수형 관리도 데이터를 생성합니다.

    Parameters
    ----------
    df_raw : pd.DataFrame
        3개 컬럼: [부분군 이름, sample_size, 불량 수/결점 수]
    chart_type : str
        관리도 유형: 'NP', 'P', 'C', 'U'

    Returns
    -------
    tuple of pd.DataFrame
        각 DataFrame의 컬럼: [point, CL, LCL, UCL]
        인덱스: 부분군 ID
    """
    sg_col = df_raw.columns[0]           # 부분군 컬럼
    sample_size_col = df_raw.columns[1]  # 표본 크기 컬럼
    var_col = df_raw.columns[2]          # 불량 수/결점 수 컬럼

    var = df_raw[var_col].values.astype(float)
    sample_size = df_raw[sample_size_col].values.astype(float)
    idx = df_raw[sg_col].values  # 부분군 ID

    if chart_type == 'NP':
        return _np_chart(var, sample_size, idx)
    elif chart_type == 'P':
        return _p_chart(var, sample_size, idx)
    elif chart_type == 'C':
        return _c_chart(var, idx)
    elif chart_type == 'U':
        return _u_chart(var, sample_size, idx)
    else:
        raise ValueError(
            f"알 수 없는 차트 유형: '{chart_type}'. "
            f"사용 가능: 'NP', 'P', 'C', 'U'"
        )


def _np_chart(var: np.ndarray, sample_size: np.ndarray, idx: np.ndarray) -> tuple:
    """NP 관리도 (불량 수) 계산"""
    np_bar = np.sum(var) / len(var)
    p_bar = np.sum(var) / np.sum(sample_size)

    lcl = np_bar - 3 * np.sqrt(np_bar * (1 - p_bar))
    ucl = np_bar + 3 * np.sqrt(np_bar * (1 - p_bar))
    # LCL은 음수가 될 수 없으므로 0으로 클램핑
    lcl = max(0.0, lcl)

    np_chart = pd.DataFrame({
        'point': var,
        'CL': np_bar,
        'LCL': lcl,
        'UCL': ucl,
    }, index=idx)

    return (np_chart,)


def _p_chart(var: np.ndarray, sample_size: np.ndarray, idx: np.ndarray) -> tuple:
    """P 관리도 (불량률) 계산"""
    p_bar = np.sum(var) / np.sum(sample_size)

    lcl = p_bar - 3 * np.sqrt(p_bar * (1 - p_bar) / sample_size)
    ucl = p_bar + 3 * np.sqrt(p_bar * (1 - p_bar) / sample_size)
    # LCL은 음수가 될 수 없으므로 0으로 클램핑
    lcl = np.maximum(0.0, lcl)

    p_chart = pd.DataFrame({
        'point': var / sample_size,
        'CL': p_bar,
        'LCL': lcl,
        'UCL': ucl,
    }, index=idx)

    return (p_chart,)


def _c_chart(var: np.ndarray, idx: np.ndarray) -> tuple:
    """C 관리도 (결점 수) 계산"""
    c_bar = np.mean(var)

    lcl = c_bar - 3 * np.sqrt(c_bar)
    ucl = c_bar + 3 * np.sqrt(c_bar)
    # LCL은 음수가 될 수 없으므로 0으로 클램핑
    lcl = max(0.0, lcl)

    c_chart = pd.DataFrame({
        'point': var,
        'CL': c_bar,
        'LCL': lcl,
        'UCL': ucl,
    }, index=idx)

    return (c_chart,)


def _u_chart(var: np.ndarray, sample_size: np.ndarray, idx: np.ndarray) -> tuple:
    """U 관리도 (단위당 결점 수) 계산"""
    u_bar = np.sum(var) / np.sum(sample_size)

    lcl = u_bar - 3 * np.sqrt(u_bar / sample_size)
    ucl = u_bar + 3 * np.sqrt(u_bar / sample_size)
    # LCL은 음수가 될 수 없으므로 0으로 클램핑
    lcl = np.maximum(0.0, lcl)

    u_chart = pd.DataFrame({
        'point': var / sample_size,
        'CL': u_bar,
        'LCL': lcl,
        'UCL': ucl,
    }, index=idx)

    return (u_chart,)


# ──────────────────────────────────────────────
# 이상점 탐지 (Out-of-Control Detection)
# ──────────────────────────────────────────────

def detect_out_of_control(chart_df: pd.DataFrame) -> list:
    """
    관리 이탈점(이상점)을 탐지합니다.

    관리한계선(UCL/LCL)을 벗어나는 점의 인덱스를 반환합니다.

    Parameters
    ----------
    chart_df : pd.DataFrame
        컬럼: [point, CL, LCL, UCL]

    Returns
    -------
    list
        이상점 인덱스 목록
    """
    ooc_mask = (chart_df['point'] > chart_df['UCL']) | (chart_df['point'] < chart_df['LCL'])
    return list(chart_df.index[ooc_mask])
