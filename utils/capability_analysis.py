"""
공정능력 분석 모듈 (Process Capability Analysis)
===================================================
공정능력 지수(Cp, Cpk, Pp, Ppk)와 정규성 검정을 수행합니다.

- normality_test: Shapiro-Wilk 정규성 검정
- process_capability: 공정능력 지수 계산
- judge_capability: 공정능력 판정
"""

import numpy as np
import pandas as pd
from scipy import stats

from utils.unbiased_constants import calc_unbiased_const


def normality_test(data: pd.DataFrame) -> tuple:
    """
    Shapiro-Wilk 정규성 검정을 수행합니다.

    Parameters
    ----------
    data : pd.DataFrame
        2개 컬럼: [부분군 이름, 측정값]

    Returns
    -------
    tuple : (is_normal, stat, p_value)
        is_normal: bool - 정규분포 여부 (p > 0.05)
        stat: float - 검정 통계량
        p_value: float - p-값
    """
    import warnings
    # 두 번째 컬럼이 측정값
    var_col = data.columns[1]
    values = data[var_col].dropna().values

    # Shapiro-Wilk는 N <= 5000 권장. 대용량 데이터에서는 첫 5000개로 검정
    if len(values) > 5000:
        # 무작위 샘플링 (재현 가능하도록 seed 고정)
        rng = np.random.default_rng(42)
        values = rng.choice(values, size=5000, replace=False)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stat, p_value = stats.shapiro(values)
    is_normal = p_value > 0.05

    return is_normal, stat, p_value


def process_capability(
    data: pd.DataFrame,
    LSL: float,
    USL: float,
) -> dict:
    """
    공정능력 지수를 계산합니다.

    Parameters
    ----------
    data : pd.DataFrame
        2개 컬럼: [부분군 이름, 측정값]
    LSL : float
        하한 규격 한계 (Lower Specification Limit)
    USL : float
        상한 규격 한계 (Upper Specification Limit)

    Returns
    -------
    dict
        Cp, Cpk, Pp, Ppk, x_bar, sigma_within, sigma_overall,
        mean_sg (부분군 평균 Series), sigma_sg (부분군 표준편차 Series)
    """
    sg_col = data.columns[0]  # 부분군 컬럼
    var_col = data.columns[1]  # 측정값 컬럼

    # 부분군별 그룹화
    grouped = data.groupby(sg_col)[var_col]

    # 부분군 평균 및 표준편차 (ddof=1)
    mean_sg = grouped.mean()
    sigma_sg = grouped.std(ddof=1)

    # 각 부분군 크기
    n_values = grouped.count()

    # 전체 평균
    x_bar = data[var_col].mean()

    # ─── 전체 표준편차 (Overall) ───
    # sigma_hat: 전체 데이터의 표준편차 (ddof=1)
    sigma_hat = data[var_col].std(ddof=1)
    # sigma_overall: sigma_hat / c4(n) — n은 전체 데이터 수
    n_total = len(data)
    if n_total >= 2:
        c4_overall = calc_unbiased_const('c4', n_total)
        sigma_overall = sigma_hat / c4_overall
    else:
        sigma_overall = sigma_hat

    # ─── 군내 표준편차 (Within) ───
    # 부분군 크기가 모두 1이면 (I-MR 케이스): MR 기반으로 추정
    valid_sigma_sg = sigma_sg.dropna()
    if len(valid_sigma_sg) == 0 or (n_values <= 1).all():
        # I-MR 케이스: 인접 측정값의 이동범위로 군내변동 추정
        values = data[var_col].values
        mr_values = np.abs(np.diff(values))  # MR with window=2
        mr_bar = np.mean(mr_values) if len(mr_values) > 0 else np.nan
        # d2(2) = 1.128
        d2_val = calc_unbiased_const('d2', 2)
        sigma_within = mr_bar / d2_val if not np.isnan(mr_bar) else sigma_overall
    else:
        # 풀링된 표준편차 (pooled std) 방식
        sigma_p = np.sqrt(np.sum(valid_sigma_sg ** 2) / len(valid_sigma_sg))

        # 자유도 d = 전체 데이터 수 - 부분군 수 + 1
        d = max(2, len(data) - len(valid_sigma_sg) + 1)
        c4_within = calc_unbiased_const('c4', d)
        sigma_within = sigma_p / c4_within

    # ─── 공정능력 지수 계산 ───
    # Cp: 잠재 공정능력 (군내 변동 기준)
    Cp = (USL - LSL) / (6 * sigma_within)

    # Cpk: 실제 공정능력 (군내 변동 + 치우침 고려)
    Cpu = (USL - x_bar) / (3 * sigma_within)
    Cpl = (x_bar - LSL) / (3 * sigma_within)
    Cpk = min(Cpu, Cpl)

    # Pp: 잠재 공정성능 (전체 변동 기준)
    Pp = (USL - LSL) / (6 * sigma_overall)

    # Ppk: 실제 공정성능 (전체 변동 + 치우침 고려)
    Ppu = (USL - x_bar) / (3 * sigma_overall)
    Ppl = (x_bar - LSL) / (3 * sigma_overall)
    Ppk = min(Ppu, Ppl)

    return {
        'Cp': Cp,
        'Cpk': Cpk,
        'Pp': Pp,
        'Ppk': Ppk,
        'x_bar': x_bar,
        'sigma_within': sigma_within,
        'sigma_overall': sigma_overall,
        'mean_sg': mean_sg,
        'sigma_sg': sigma_sg,
    }


def judge_capability(value: float) -> tuple:
    """
    공정능력 지수를 판정합니다.

    Parameters
    ----------
    value : float
        공정능력 지수 (Cp, Cpk, Pp, Ppk 등)

    Returns
    -------
    tuple : (judgment_text, color)
        judgment_text: str - 판정 결과 ('충분', '보통', '부족')
        color: str - 표시 색상 ('green', 'orange', 'red')
    """
    if value >= 1.33:
        return ('충분', 'green')
    elif value >= 1.0:
        return ('보통', 'orange')
    else:
        return ('부족', 'red')
