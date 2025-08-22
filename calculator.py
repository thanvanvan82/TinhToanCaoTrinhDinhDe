# calculator.py
import pandas as pd
import numpy as np

# --- DỮ LIỆU VÀ HẰNG SỐ ---

# Dữ liệu bảng tra cứu Dmax
DMAX_TABLE_DATA = {
    'w (m/s)': [20, 25, 30, 40, 50],
    'Dmax (km)': [1600, 1200, 600, 200, 100]
}
DMAX_DF = pd.DataFrame(DMAX_TABLE_DATA)

# Dữ liệu các tia xạ cho trường hợp vùng nước hẹp
RAY_DATA = [
    {'Tia xạ': -6, 'Góc αi (độ)': -45.0}, {'Tia xạ': -5, 'Góc αi (độ)': -37.5},
    {'Tia xạ': -4, 'Góc αi (độ)': -30.0}, {'Tia xạ': -3, 'Góc αi (độ)': -22.5},
    {'Tia xạ': -2, 'Góc αi (độ)': -15.0}, {'Tia xạ': -1, 'Góc αi (độ)': -7.5},
    {'Tia xạ': 0, 'Góc αi (độ)': 0.0}, {'Tia xạ': 1, 'Góc αi (độ)': 7.5},
    {'Tia xạ': 2, 'Góc αi (độ)': 15.0}, {'Tia xạ': 3, 'Góc αi (độ)': 22.5},
    {'Tia xạ': 4, 'Góc αi (độ)': 30.0}, {'Tia xạ': 5, 'Góc αi (độ)': 37.5},
    {'Tia xạ': 6, 'Góc αi (độ)': 45.0}
]
RAY_DF_BASE = pd.DataFrame(RAY_DATA)
RAY_DF_BASE['cos(αi)'] = np.cos(np.deg2rad(RAY_DF_BASE['Góc αi (độ)']))
RAY_DF_BASE['cos²(αi)'] = RAY_DF_BASE['cos(αi)']**2

# Hằng số vật lý
KINEMATIC_VISCOSITY_V = 1e-5  # ν = 10^-5 m²/s

# --- CÁC HÀM TÍNH TOÁN ---

def interpolate_dmax(speed: float, dmax_df: pd.DataFrame) -> tuple[float | None, str]:
    """Nội suy giá trị Dmax từ tốc độ gió w."""
    if speed is None or speed <= 0:
        return None, "Vui lòng nhập tốc độ gió hợp lệ."

    speeds = dmax_df['w (m/s)'].values
    dmaxs = dmax_df['Dmax (km)'].values

    if speed < speeds[0]:
        return dmaxs[0], "Ngoại suy, lấy theo giá trị biên thấp nhất."
    if speed > speeds[-1]:
        return dmaxs[-1], "Ngoại suy, lấy theo giá trị biên cao nhất."
    
    interpolated_value = np.interp(speed, speeds, dmaxs)
    return float(interpolated_value), "Giá trị nội suy."

def calculate_d_wide(speed: float) -> float | None:
    """Tính toán Đà gió D cho vùng nước rộng."""
    if speed is None or speed <= 0:
        return None
    d_meters = 5e11 * (KINEMATIC_VISCOSITY_V / speed)
    return d_meters / 1000  # Chuyển sang km

def calculate_de(input_df: pd.DataFrame) -> tuple[float, float, float]:
    """Tính toán Đà gió De từ DataFrame đầu vào."""
    df = input_df.copy()
    df['ri × cos²(αi)'] = df['Đà gió ri (km)'] * df['cos²(αi)']
    
    numerator_sum = df['ri × cos²(αi)'].sum()
    denominator_sum = df['cos(αi)'].sum()
    de_result = numerator_sum / denominator_sum if denominator_sum != 0 else 0
    
    return numerator_sum, denominator_sum, de_result
