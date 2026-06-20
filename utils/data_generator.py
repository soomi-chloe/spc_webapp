"""
데이터 생성 모듈 (Data Generator)
==================================
SPC 분석을 위한 샘플 데이터를 생성합니다.

- generate_data: 공정능력 분석용 데이터 (LSL/USL 포함)
- generate_value_data: 계량형 관리도용 데이터
- generate_count_data: 계수형 관리도용 데이터
"""

import numpy as np
import pandas as pd


def generate_data(
    var_name: str,
    target: float,
    tolerance: float,
    sg_name: str,
    num_sg: int,
    sg_size: int,
    sg_std: float,
    mean_shift: tuple,
) -> tuple:
    """
    공정능력 분석용 데이터를 생성합니다.

    Parameters
    ----------
    var_name : str
        측정값 컬럼 이름
    target : float
        목표값 (공칭값)
    tolerance : float
        공차 (편측)
    sg_name : str
        부분군 컬럼 이름
    num_sg : int
        부분군 수
    sg_size : int
        부분군 크기 (각 부분군의 샘플 수)
    sg_std : float
        부분군 내 표준편차
    mean_shift : tuple
        평균 이동 범위 (min_shift, max_shift)

    Returns
    -------
    tuple : (df, LSL, USL)
        df: DataFrame with columns [sg_name, var_name]
        LSL: 하한 규격 한계
        USL: 상한 규격 한계
    """
    rows = []
    for i in range(1, num_sg + 1):
        # 각 부분군마다 랜덤 평균 이동 적용
        random_shift = np.random.uniform(mean_shift[0], mean_shift[1])
        samples = np.random.normal(
            loc=target + random_shift,
            scale=sg_std,
            size=sg_size,
        )
        for val in samples:
            rows.append({sg_name: i, var_name: val})

    df = pd.DataFrame(rows)

    # 규격 한계 계산
    LSL = target - tolerance
    USL = target + tolerance

    return df, LSL, USL


def generate_value_data(
    var_name: str,
    target: float,
    sg_name: str,
    num_sg: int,
    sg_size: int,
    sg_std: float,
    mean_shift: float,
    sg_size_variation: int,
) -> pd.DataFrame:
    """
    계량형 관리도용 데이터를 생성합니다.

    Parameters
    ----------
    var_name : str
        측정값 컬럼 이름
    target : float
        목표값 (공칭값)
    sg_name : str
        부분군 컬럼 이름
    num_sg : int
        부분군 수
    sg_size : int
        기본 부분군 크기
    sg_std : float
        부분군 내 표준편차
    mean_shift : float
        평균 이동 범위 (±mean_shift)
    sg_size_variation : int
        부분군 크기 변동 범위

    Returns
    -------
    pd.DataFrame
        columns: [sg_name, var_name]
    """
    rows = []
    for i in range(num_sg):
        # 랜덤 평균 이동
        shift = np.random.uniform(-mean_shift, mean_shift)
        # 부분군 크기 변동 적용
        n_i = sg_size + np.random.randint(-sg_size_variation, sg_size_variation + 1)
        n_i = max(n_i, 1)  # 최소 1개 보장

        samples = np.random.normal(
            loc=target + shift,
            scale=sg_std,
            size=n_i,
        )
        for val in samples:
            rows.append({sg_name: i + 1, var_name: val})

    df = pd.DataFrame(rows)
    return df


def generate_count_data(
    var_name: str,
    sg_name: str,
    num_sg: int,
    sg_size: int,
    p: float,
    sg_size_variation: int,
) -> pd.DataFrame:
    """
    계수형 관리도용 데이터를 생성합니다.

    Parameters
    ----------
    var_name : str
        불량 수(또는 결점 수) 컬럼 이름
    sg_name : str
        부분군 컬럼 이름
    num_sg : int
        부분군 수
    sg_size : int
        기본 표본 크기
    p : float
        불량률 (0~1)
    sg_size_variation : int
        표본 크기 변동 범위

    Returns
    -------
    pd.DataFrame
        columns: [sg_name, 'sample_size', var_name]
        각 부분군당 1행
    """
    rows = []
    for i in range(num_sg):
        # 표본 크기 변동 적용
        sample_size = sg_size + np.random.randint(
            -sg_size_variation, sg_size_variation + 1
        )
        sample_size = max(sample_size, 1)  # 최소 1개 보장

        # 이항분포에서 불량 수 생성
        count = np.random.binomial(n=sample_size, p=p)

        rows.append({
            sg_name: i + 1,
            'sample_size': sample_size,
            var_name: count,
        })

    df = pd.DataFrame(rows)
    return df
