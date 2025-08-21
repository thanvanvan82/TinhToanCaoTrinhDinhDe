# calculator.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import warnings

# === 1. CẤU HÌNH BAN ĐẦU ===
# Thiết lập hằng số vật lý
GRAVITY = 9.81  # m/s²
KINEMATIC_VISCOSITY = 1E-5  # m²/s
K_CONSTANT = 5E11  # Hằng số trong công thức tính đà sóng

# === 2. BẢNG TRA CỨU ===
# ... (giữ lại HE_SO_AN_TOAN_SONG, HE_SO_AN_TOAN_BIEN, DATA_KW, ...)

# --- BẢNG TRA CỨU TCVN (Hằng số) ---
HE_SO_AN_TOAN_SONG = {"Đặc biệt": 0.80, "I": 0.60, "II": 0.50, "III": 0.40, "IV": 0.30, "V": 0.20}
HE_SO_AN_TOAN_BIEN = {"I": 0.6, "II": 0.5, "III": 0.4, "IV": 0.3, "V": 0.2}
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
GAMMA_F_LOOKUP = {
    "Bê tông nhựa asphalt, bê tông, cấu kiện bê tông nhẵn, cỏ, cát - asphalt": 1.00,
    "Cấu kiện bê tông liên kết ngang, cấu kiện có cỏ mọc": 0.95,
    "Các cấu kiện đặc biệt: basalt, basalton, hydroblock, haringman, fixstone, mảng armorflex": 0.90,
    "Cấu kiện kè cao thấp chiếm 25 phần trăm diện tích với chênh cao lớn hơn 10 cm": 0.90,
    "Lessinische và vilvoordse, cấu kiện có độ nhám nhỏ": 0.85,
    "Mấu giảm sóng loại nhỏ chiếm 4 phần trăm bề mặt kè": 0.85,
    "Đá lát khan, đá xây chít vữa theo họa tiết": 0.85,
    "Kè đá đổ thâm nhập nhựa": 0.80,
    "Mấu giảm sóng loại nhỏ chiếm 1/9 bề mặt kè": 0.80,
    "Kè đá đổ một lớp": 0.70,
    "Kè đá đổ hai lớp": 0.55
}
CONFIG_DE_BIEN = {}

# === 3. UTILITY FUNCTIONS ===
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
            p_bao = TAN_SUAT_BAO[("I", "II")]["dac_biet"]
            giai_thich = "Cấp I/II có luận chứng đặc biệt (p=1%)"
        else:
            Vl = VAN_TOC_GIO_THIET_KE[("I", "II")]["van_toc_tieu_chuan"]
            p_bao = TAN_SUAT_BAO[("I", "II")]["tieu_chuan"]
            giai_thich = "Cấp I/II tiêu chuẩn (p=2%)"
    elif cap_upper in ["III", "IV", "V"]:
        Vl = VAN_TOC_GIO_THIET_KE[("III", "IV", "V")]["van_toc_tieu_chuan"]
        p_bao = TAN_SUAT_BAO[("III", "IV", "V")]["tieu_chuan"]
        giai_thich = "Cấp III/IV/V (p=4%)"
    else:
        return np.nan, np.nan, "Cấp công trình không hợp lệ"
    return Vl, p_bao, giai_thich

# === 4. TÍNH TOÁN ĐÊ SÔNG - OPTIMIZED ===
class RiverDykeCalculator:
    def __init__(self, data_kw: Dict, data_kl: pd.DataFrame, data_lu: pd.DataFrame, he_so_an_toan: Dict):
        self.data_kw = data_kw
        self.data_kl = data_kl
        self.data_lu = data_lu
        self.he_so_an_toan = he_so_an_toan

    # --- Tính toán đà sóng ---
    def calc_da_song_hep(chieu_dai_cac_tia_ri: Union[List[float], Dict[float, float]]) -> float:
        """  
        Args:
            chieu_dai_cac_tia_ri: Chiều dài của các tia xạ (m).
                - List: 13 phần tử từ -45° đến +46° (bước 7.5°)
                - Dict: Keys là góc (độ), values là chiều dài tia (m)   
        
        Returns:
            float: Giá trị De
        """
        GOC_ALPHA = np.arange(-45, 46, 7.5)
        COS_ALPHA = np.cos(np.deg2rad(GOC_ALPHA))
        
        if isinstance(chieu_dai_cac_tia_ri, list):
            if len(chieu_dai_cac_tia_ri) != 13:
                raise ValueError("List phải có 13 phần tử")
            ri_values = np.array(chieu_dai_cac_tia_ri)
        else:  # dict
            ri_values = np.array([chieu_dai_cac_tia_ri.get(a, 0) for a in GOC_ALPHA])
        De = np.dot(ri_values, COS_ALPHA) / np.sum(COS_ALPHA)
        return De
    
    def calc_da_song_rong(Vl,Vw,lu_lookup):
        """
        Tính toán đà sóng trung bình L và đà sóng giới hạn Lu.

        Args:
            Vw (float): Vận tốc gió tính toán (m/s).
            lu_lookup (pd.DataFrame): DataFrame chứa dữ liệu tra cứu Lu.

        Returns:
            tuple: (giá trị L (m), giá trị Lu (m)) hoặc (None, None) nếu lỗi.
        """
        Kvis = 5E11

        V_nhot = 1E-5

        if Vw <= 0:
            return None, None
            
        # a. Tính đà sóng trung bình L theo công thức (116)
        Ltt = Kvis * V_nhot / Vw
        
        # b. Tính đà sóng giới hạn Lu bằng cách gọi hàm nội suy
        Lu = calc_Lu(Vl, lu_lookup)

        L = min(Ltt, Lu)

        return L
        
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
        # <<< THAY ĐỔI: Sử dụng tên key mới để lấy dữ liệu
        cap_de_song = params.get('cấp đê sông')
        loai_dia_hinh = params.get('loại địa hình')
        Htk, L, d, aw = params.get('Htk'), params.get('L'), params.get('d'), params.get('aw')
        b_song = params.get('b (đê sông, m)', 0.2)
        s = params.get('s', 0.1)

        Vl, _, _ = get_wind_parameters(cap_de_song)
        kfl = self.calc_kfl(Vl)
        kl = self.calc_kl(Vl, loai_dia_hinh)
        Vw = self.calc_Vw(kfl, kl, Vl)
        delta_H, _ = self.calc_delta_H_iterative(Vw, L, d, aw)

        a_song = self.he_so_an_toan.get(cap_de_song, np.nan)
        Zds = Htk + delta_H + a_song + b_song + s if not any(np.isnan([Htk, delta_H, a_song, b_song, s])) else np.nan

        # <<< THAY ĐỔI: Trả về dictionary với tên key mới
        return {
            'Vl (m/s)': Vl, 
            'kfl (m/s)': kfl, 
            'kl (m/s)': kl, 
            'Vw (m/s)': Vw, 
            'ΔH (m)': delta_H, 
            'a (đê sông, m)': a_song, 
            'Zđs (m)': Zds
        }

# === 5. TÍNH TOÁN ĐÊ BIỂN - OPTIMIZED ===
class SeaDykeCalculator:
    def __init__(self, he_so_an_toan: Dict, gamma_f_lookup: Dict, config: Dict):
        self.he_so_an_toan = he_so_an_toan
        self.gamma_f_lookup = gamma_f_lookup
        self.config = config

    def calc_wave_parameters(self, Hsp: float, Tp: float, alpha: float) -> Tuple[float, float]:
        Tm_1_0_p = Tp / alpha
        s0 = 2 * np.pi * Hsp / (GRAVITY * Tm_1_0_p**2)
        return Tm_1_0_p, s0

    def calc_tan_alpha(self, m: float) -> Optional[float]:
        return 1 / m if m > 0 else np.nan

    def calc_wave_breaking_index(self, tan_alpha: float, s0: float) -> float:
        return tan_alpha / np.sqrt(s0) if s0 > 0 else 0

    def calc_gamma_beta(self, beta: float) -> float:
        return 1 - 0.0022 * min(abs(beta), 80)

    def calc_gamma_beta_tran(self, beta: float) -> float:
        return 1 - 0.0033 * min(abs(beta), 80)

    def calc_gamma_b(self, B: float, Lb: float) -> Tuple[float, str]:
        if B is None or B <= 0 or Lb is None or Lb <= 0:
            return 1.0, "Không có cơ đê"
        gamma_b_raw = 1 - (B / Lb)
        return max(0.6, min(1.0, gamma_b_raw)), "Có cơ đê"
    
    def calc_gamma_v(self, alpha_w: float) -> Optional[float]:
        if alpha_w == 90: return 0.65
        if alpha_w == 45: return 1.00
        if 45 < alpha_w < 90: return 1.35 - 0.0078 * alpha_w
        return np.nan

    def calc_gamma_f_corrected(self, gamma_f_base: float, Rcp: float, Hsp: float) -> float:
        if Hsp <= 0: return gamma_f_base, np.nan 
        ratio_Rcp_Hsp = Rcp / Hsp
        if gamma_f_base < 0.90:
            if ratio_Rcp_Hsp >= 0.5: return gamma_f_base - 0.05, ratio_Rcp_Hsp
            else: return gamma_f_base, ratio_Rcp_Hsp
        if ratio_Rcp_Hsp > 1.0: return gamma_f_base - 0.3, ratio_Rcp_Hsp
        if ratio_Rcp_Hsp <= 0.5: return gamma_f_base, ratio_Rcp_Hsp
        return gamma_f_base - 0.6 * (ratio_Rcp_Hsp - 0.5), ratio_Rcp_Hsp

    def calc_Rslp(self, Hsp: float, xi_p: float, gamma_beta: float, gamma_b: float, gamma_f: float) -> Tuple[float, str]:
        condition = gamma_b * xi_p
        if 0.5 < condition < 1.8:
            Rslp = 1.75 * gamma_beta * gamma_b * gamma_f * xi_p * Hsp
            status_song_vo = "Sóng vỡ"
        elif 1.8 <= condition < 10.0:
            Rslp = gamma_beta * gamma_f * gamma_b * (4.3 - 1.6 / np.sqrt(xi_p)) * Hsp
            status_song_vo = "Sóng chưa vỡ"
        else:
            Rslp = np.nan
        return Rslp, status_song_vo

    def calc_overflow_rate(self, Rcp: float, Hsp: float, Tp: float, tan_alpha: float, s0: float, gamma_f_star: float, gamma_b: float, gamma_beta: float, gamma_v: float, xi_o: float):
        if not all(validate_positive(v, n) for v, n in [ (Rcp, "Rcp"), (Hsp, "Hsp"), (Tp, "Tp"), (tan_alpha, "tan_alpha")]): return np.nan   
        try:
            if xi_o > 7.0:
                q_norm = 0.21 * np.exp(-Rcp / (gamma_f_star * gamma_beta * Hsp * (0.33 + 0.022 * xi_o)))
                status_song_tran = "Sóng vỡ"
            elif gamma_b * xi_o <= 2.0:
                q_norm = (0.067 / np.sqrt(tan_alpha)) * gamma_b * xi_o * np.exp(-4.3 * Rcp / (Hsp * xi_o * gamma_b * gamma_f_star * gamma_beta * gamma_v))
                status_song_tran = "Sóng tràn"
            else:
                q_norm = 0.2 * np.exp(-2.3 * Rcp / (Hsp * gamma_f_star * gamma_beta))
                status_song_tran = "Sóng tràn tính theo công thức tất định"
            return q_norm * np.sqrt(GRAVITY * Hsp**3) * 1000, status_song_tran
        except Exception as e:
            warnings.warn(f"Lỗi trong calc_overflow_rate: {e}")
            return np.nan, "Lỗi tính toán"

    def solve_Rcp_iterative(self, q_target: float, Hsp: float, Tp: float, tan_alpha: float, s0: float, gamma_b: float, gamma_f_star: float, gamma_beta: float, gamma_v: float, xi_o: float) -> Tuple[float, float]:
        Rcp = 0.5 * Hsp
        tolerance = (5 / 100) * q_target
        for i in range(100):            
            q_calc, status_song_tran = self.calc_overflow_rate(Rcp, Hsp, Tp, tan_alpha, s0,gamma_f_star, gamma_b, gamma_beta, gamma_v, xi_o)
            if q_calc is None or np.isnan(q_calc): return np.nan, np.nan, "Lỗi trong vòng lặp"
            if abs(q_calc - q_target) <= tolerance: return Rcp, q_calc, status_song_tran
            adj_factor = 0.1 if i < 5 else 0.05
            Rcp *= (1 + adj_factor) if q_calc > q_target else (1 - adj_factor)
            Rcp = max(0.1 * Hsp, min(5.0 * Hsp, Rcp))
        
        warnings.warn(f"Hàm solve_Rcp_iterative không hội tụ sau 100 vòng lặp.")
        # Trả về kết quả cuối cùng sau vòng lặp nếu không hội tụ
        
        return Rcp, q_calc, status_song_tran

    def calculate(self, params: Dict) -> Dict:
        # <<< THAY ĐỔI: Sử dụng tên key mới để lấy dữ liệu
        cap_de_bien = params.get('cấp đê biển')
        Hsp, Tp, alpha = params.get('Hsp'), params.get('Tp'), params.get('alpha')
        m, B, Lb, beta, alpha_w = params.get('m'), params.get('B'), params.get('Lb'), params.get('beta'), params.get('alpha_w')
        Ztkp, b_bien = params.get('Ztkp'), params.get('b (đê biển, m)')
        q_muc_tieu = params.get('[q] (l/s.m)')
        vat_lieu = params.get('vật liệu')

        if not vat_lieu:
            warnings.warn(f"Tuyến đê {params.get('tuyến đê biển')} thiếu thông tin 'vật liệu'.")
            
        Tm_1_0_p, s0 = self.calc_wave_parameters(Hsp, Tp, alpha)
        tan_alpha = self.calc_tan_alpha(m=m)
        xi_p = self.calc_wave_breaking_index(tan_alpha, s0)
        gamma_b, status_berm = self.calc_gamma_b(B, Lb)
        gamma_f = self.gamma_f_lookup.get(vat_lieu, 1.0)
        gamma_beta = self.calc_gamma_beta(beta)
        gamma_beta_tran = self.calc_gamma_beta_tran(beta)
        xi_o = tan_alpha / np.sqrt(s0)
        gamma_v = self.calc_gamma_v(alpha_w)
        gamma_f_star, ratio_Rcp_Hsp = self.calc_gamma_f_corrected(gamma_f, 1.9, Hsp)

        Rslp, status_song_vo = self.calc_Rslp(Hsp, xi_p, gamma_beta, gamma_b, gamma_f)
        Rcp, q_calc, status_song_tran = self.solve_Rcp_iterative(q_muc_tieu, Hsp, Tp, tan_alpha, s0, gamma_b, gamma_f_star, gamma_beta_tran, gamma_v, xi_o)
        
        a_bien = self.he_so_an_toan.get(cap_de_bien, np.nan)
        Zdb = Ztkp + Rslp + a_bien + b_bien if not np.isnan(Rslp) else np.nan
        Zdb_tran = Ztkp + Rcp + a_bien + b_bien if not np.isnan(Rcp) else np.nan
        
        # <<< THAY ĐỔI: Trả về dictionary với tên key mới
        return {
            # Trung gian cho cả 2 trường hợp
            'a (đê biển, m)': a_bien,
            'Cơ đê': status_berm,
            'Tm-1,0p (s)': Tm_1_0_p,
            's0': s0,
            'tan(α)': tan_alpha,
            'γ_b': gamma_b,             
            
            # Trung gian & Kết quả cho trường hợp Sóng leo (Không tràn)
            'γ_f (vật liệu)': gamma_f, 
            'ξ_p (leo)': xi_p,
            'γ_β (leo)': gamma_beta,
            'Tình trạng sóng vỡ (leo)': status_song_vo,
            'Rslp (m)': Rslp,
            'Zđb (m)': Zdb,

            # Trung gian & Kết quả cho trường hợp Sóng tràn
            '[q] (l/s.m)': q_muc_tieu,
            'ξ_o (tràn)': xi_o,
            'γ_β (tràn)': gamma_beta_tran,
            'γ_v': gamma_v,
            'Tỷ lệ Rcp và Hsp': ratio_Rcp_Hsp,
            'γ_f* (hiệu chỉnh)': gamma_f_star,
            'Rcp (m)': Rcp,
            'Tình trạng sóng tràn': status_song_tran,
            'q_calc (l/s.m)': q_calc,
            'Zđb_tràn (m)': Zdb_tran,
        }

# === 6. MAIN CALCULATION WORKFLOW ===
def main_workflow(df_input_song: pd.DataFrame, df_input_bien: pd.DataFrame):
    # --- KHỞI TẠO CALCULATORS ---
    calc_song = RiverDykeCalculator(
        data_kw=DATA_KW, data_kl=DATA_KL, data_lu=DATA_LU,
        he_so_an_toan=HE_SO_AN_TOAN_SONG
    )
    calc_bien = SeaDykeCalculator(
        he_so_an_toan=HE_SO_AN_TOAN_BIEN,
        gamma_f_lookup=GAMMA_F_LOOKUP,
        config={} # CONFIG_DE_BIEN không được dùng nên để trống
    )

    # --- TÍNH TOÁN ĐÊ SÔNG ---
    df_ket_qua_song = pd.DataFrame()
    if not df_input_song.empty:
        results_song_series = df_input_song.apply(lambda row: calc_song.calculate(row.to_dict()), axis=1)
        df_ket_qua_song = pd.concat([df_input_song, pd.json_normalize(results_song_series)], axis=1)

    # --- TÍNH TOÁN ĐÊ BIỂN ---
    df_ket_qua_bien = pd.DataFrame()
    if not df_input_bien.empty:
        results_bien_series = df_input_bien.apply(lambda row: calc_bien.calculate(row.to_dict()), axis=1)
        df_ket_qua_bien = pd.concat([df_input_bien, pd.json_normalize(results_bien_series)], axis=1)

    return df_ket_qua_song, df_ket_qua_bien