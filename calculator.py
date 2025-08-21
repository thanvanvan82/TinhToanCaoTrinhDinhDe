# calculator.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import warnings

# === 1. CẤU HÌNH BAN ĐẦU ===
GRAVITY = 9.81
KINEMATIC_VISCOSITY = 1E-5
K_CONSTANT = 5E11

# === 2. DỮ LIỆU VÀ BẢNG TRA CỨU (Chỉ giữ lại của Đê Sông) ===
ri_data_list = [
    850.0, 1100.5, 1420.0, 1750.8, 1980.0, 2150.3, 2200.0,
    2180.5, 1950.0, 1680.7, 1400.0, 1050.2, 800.0
]
list_de_song = [
    {"tuyến đê sông": "Tuyến A", "cấp đê sông": "IV", "loại địa hình": "MẶT NƯỚC", "Htk": 4.5, "d": 5.0, "aw": 10, "chiều dài của các tia xạ (m)": ri_data_list, "b (đê sông, m)": 0.2, "s": 0.1},
    {"tuyến đê sông": "Tuyến B", "cấp đê sông": "IV", "loại địa hình": "MẶT NƯỚC", "Htk": 4.2, "d": 5.0, "aw": 10, "chiều dài của các tia xạ (m)": ri_data_list, "b (đê sông, m)": 0.2, "s": 0.1},
    {"tuyến đê sông": "Tuyến C", "cấp đê sông": "IV", "loại địa hình": "MẶT NƯỚC", "Htk": 4.3, "d": 5.0, "aw": 10, "chiều dài của các tia xạ (m)": ri_data_list, "b (đê sông, m)": 0.2, "s": 0.1},
    {"tuyến đê sông": "Tuyến D", "cấp đê sông": "III", "loại địa hình": "A", "Htk": 4.1, "d": 5.0, "aw": 10, "chiều dài của các tia xạ (m)": ri_data_list, "b (đê sông, m)": 0.2, "s": 0.1}
]
HE_SO_AN_TOAN_SONG = {"Đặc biệt": 0.80, "I": 0.60, "II": 0.50, "III": 0.40, "IV": 0.30, "V": 0.20}
VAN_TOC_GIO_THIET_KE = {
    ("I", "II"): {"van_toc_tieu_chuan": 36.0, "van_toc_dac_biet": 40.0},
    ("III", "IV", "V"): {"van_toc_tieu_chuan": 33.0}
}
TAN_SUAT_BAO = {
    ("I", "II"): {"tieu_chuan": 2.0, "dac_biet": 1.0},
    ("III", "IV", "V"): {"tieu_chuan": 4.0}
}
DATA_KW = {"Vw": [20, 30, 40, 50], "Kw_1e6": [2.1, 3.0, 3.9, 4.8]}
DATA_KL = pd.DataFrame({
    'Vận tốc gió Vl, m/s': [10, 15, 20, 25, 30, 35, 40],
    'A': [1.10, 1.10, 1.09, 1.09, 1.09, 1.09, 1.08],
    'B': [1.30, 1.28, 1.26, 1.25, 1.24, 1.22, 1.21],
    'C': [1.47, 1.44, 1.42, 1.39, 1.38, 1.36, 1.34]
}).set_index('Vận tốc gió Vl, m/s')
DATA_LU = pd.DataFrame({'Vl': [20, 25, 30, 40, 50], 'Lu_km': [1600, 1200, 600, 200, 100]})

# === 3. UTILITY FUNCTIONS ===
# (Giữ nguyên các hàm: validate_positive, interpolate_safe, get_wind_parameters)
def validate_positive(value: float, name: str) -> bool:
    if value is None or value <= 0:
        warnings.warn(f"Cảnh báo: {name} = {value} không hợp lệ (phải > 0)")
        return False
    return True

def interpolate_safe(x: float, xp: List[float], fp: List[float], name: str = "giá trị") -> float:
    try:
        if not (min(xp) <= x <= max(xp)):
            warnings.warn(f"Cảnh báo: {name} = {x:.2f} nằm ngoài phạm vi nội suy [{min(xp)}, {max(xp)}]")
        return float(np.interp(x, xp, fp))
    except Exception as e:
        warnings.warn(f"Lỗi nội suy cho {name}: {e}")
        return np.nan

def get_wind_parameters(cap_de_song: str, co_luan_chung: bool = False) -> Tuple[float, float, str]:
    cap_upper = cap_de_song.upper()
    if cap_upper in ["I", "II"]:
        if co_luan_chung:
            Vl = VAN_TOC_GIO_THIET_KE[("I", "II")]["van_toc_dac_biet"]
        else:
            Vl = VAN_TOC_GIO_THIET_KE[("I", "II")]["van_toc_tieu_chuan"]
    elif cap_upper in ["III", "IV", "V"]:
        Vl = VAN_TOC_GIO_THIET_KE[("III", "IV", "V")]["van_toc_tieu_chuan"]
    else:
        return np.nan, np.nan, "Cấp công trình không hợp lệ"
    return Vl, 0, "" # Bỏ p_bao và giải thích vì không dùng đến

# === 4. TÍNH TOÁN ĐÊ SÔNG - OPTIMIZED ===
# (Giữ nguyên toàn bộ class RiverDykeCalculator)
class RiverDykeCalculator:
    # ... (Copy y hệt class RiverDykeCalculator từ code gốc của bạn vào đây) ...
    def __init__(self, data_kw: Dict, data_kl: pd.DataFrame, data_lu: pd.DataFrame, he_so_an_toan: Dict):
        self.data_kw = data_kw
        self.data_kl = data_kl
        self.data_lu = data_lu
        self.he_so_an_toan = he_so_an_toan

    def calc_kfl(self, Vl: float) -> Optional[float]:
        if not validate_positive(Vl, "Vận tốc gió Vl"): return np.nan
        return min(0.675 + 4.5 / Vl, 1.0)

    def calc_kl(self, Vl: float, loai_dia_hinh: str) -> Optional[float]:
        if not validate_positive(Vl, "Vận tốc gió Vl"): return np.nan
        dia_hinh_normalized = str(loai_dia_hinh).strip().upper()
        SPECIAL_TERRAINS = {'MẶT NƯỚC', 'CÁT BẰNG PHẲNG', 'CÁT PHẲNG', 'BÃI CÁT', 'CỒN CÁT', 'TUYẾT PHỦ'}
        if dia_hinh_normalized in SPECIAL_TERRAINS: return 1.0
        if dia_hinh_normalized in self.data_kl.columns:
            return interpolate_safe(Vl, self.data_kl.index.values, self.data_kl[dia_hinh_normalized].values, f"kl với địa hình {dia_hinh_normalized}")
        warnings.warn(f"Loại địa hình '{loai_dia_hinh}' không được hỗ trợ"); return np.nan

    def calc_Vw(self, kfl: float, kl: float, Vl: float) -> Optional[float]:
        if any(val is None or val <=0 for val in [kfl, kl, Vl]): return np.nan
        return kfl * kl * Vl

    def calc_delta_H_iterative(self, Vw: float, L: float, d: float, aw: float,
                              max_iterations: int = 100, tolerance: float = 1e-6) -> Tuple[Optional[float], Optional[float]]:
        if not all(validate_positive(val, name) for val, name in [(Vw, "Vw"), (L, "L"), (d, "d")]): return np.nan, np.nan
        kw = interpolate_safe(Vw, self.data_kw["Vw"], [k * 1e-6 for k in self.data_kw["Kw_1e6"]], "Kw")
        if np.isnan(kw): return np.nan, np.nan
        aw_rad = np.deg2rad(aw)
        constant_part = kw * (Vw**2 * L) * np.cos(aw_rad) / GRAVITY
        delta_H = 0.0
        for i in range(max_iterations):
            denominator = d + 0.5 * delta_H
            if abs(denominator) < 1e-10:
                warnings.warn("Lỗi: Mẫu số gần bằng 0 trong phép tính delta_H"); return np.nan, np.nan
            delta_H_new = constant_part / denominator
            if abs(delta_H_new - delta_H) < tolerance: return delta_H_new, kw
            delta_H = delta_H_new
        warnings.warn(f"Cảnh báo: Đạt số lần lặp tối đa ({max_iterations})"); return delta_H, kw

    def calculate(self, params: Dict) -> Dict:
        cap_de_song = params.get('cấp đê sông')
        loai_dia_hinh = params.get('loại địa hình')
        Htk, d, aw = params.get('Htk'), params.get('d'), params.get('aw')
        b_song = params.get('b (đê sông, m)', 0.2)
        s = params.get('s', 0.1)

        # Giả sử L được tính hoặc cho trước, ở đây lấy từ chiều dài tia xạ
        # Đây là một điểm cần làm rõ trong logic gốc, ta tạm tính De (đà sóng hiệu quả)
        ri = params.get('chiều dài của các tia xạ (m)', [])
        GOC_ALPHA = np.arange(-45, 46, 7.5)
        COS_ALPHA = np.cos(np.deg2rad(GOC_ALPHA))
        if isinstance(ri, list) and len(ri) == 13:
            ri_values = np.array(ri)
            De = np.dot(ri_values, COS_ALPHA) / np.sum(COS_ALPHA)
        else:
            De = 2200 # Giá trị mặc định nếu đầu vào không đúng
            warnings.warn(f"Dữ liệu tia xạ không hợp lệ, sử dụng giá trị mặc định L={De}m")
        L = De

        Vl, _, _ = get_wind_parameters(cap_de_song)
        kfl = self.calc_kfl(Vl)
        kl = self.calc_kl(Vl, loai_dia_hinh)
        Vw = self.calc_Vw(kfl, kl, Vl)
        delta_H, _ = self.calc_delta_H_iterative(Vw, L, d, aw)

        a_song = self.he_so_an_toan.get(cap_de_song, np.nan)
        Zds = Htk + delta_H + a_song + b_song + s if not any(np.isnan([Htk, delta_H, a_song, b_song, s])) else np.nan

        return {
            'L (m)': L,
            'Vl (m/s)': Vl, 'kfl': kfl, 'kl': kl, 'Vw (m/s)': Vw, 'ΔH (m)': delta_H,
            'a (đê sông, m)': a_song, 'Zđs (m)': Zds
        }


# === 5. MAIN CALCULATION WORKFLOW (Rút gọn) ===
def main_workflow_song(df_input_song: pd.DataFrame):
    calc_song = RiverDykeCalculator(
        data_kw=DATA_KW, data_kl=DATA_KL, data_lu=DATA_LU,
        he_so_an_toan=HE_SO_AN_TOAN_SONG
    )
    df_ket_qua_song = pd.DataFrame()
    if not df_input_song.empty:
        results_song_series = df_input_song.apply(lambda row: calc_song.calculate(row.to_dict()), axis=1)
        df_ket_qua_song = pd.concat([df_input_song, pd.json_normalize(results_song_series)], axis=1)
    return df_ket_qua_song
