import streamlit as st
import pandas as pd
import numpy as np

# --- Cấu hình trang ---
st.set_page_config(
    page_title="Công cụ tính toán đà gió",
    page_icon="💨",
    layout="wide"
)

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
RAY_DF = pd.DataFrame(RAY_DATA)
RAY_DF['cos(αi)'] = np.cos(np.deg2rad(RAY_DF['Góc αi (độ)']))
RAY_DF['cos²(αi)'] = RAY_DF['cos(αi)']**2

# Hằng số vật lý
KINEMATIC_VISCOSITY_V = 1e-5  # ν = 10^-5 m²/s

# --- CÁC HÀM TÍNH TOÁN ---

@st.cache_data
def interpolate_dmax(speed: float | None, dmax_df: pd.DataFrame) -> tuple[float | None, str]:
    if speed is None or not isinstance(speed, (int, float)) or speed <= 0:
        return None, "Vui lòng nhập tốc độ gió hợp lệ."
    speeds = dmax_df['w (m/s)'].values
    dmaxs = dmax_df['Dmax (km)'].values
    if speed < speeds[0]:
        return dmaxs[0], "Ngoại suy, lấy theo giá trị biên thấp nhất."
    if speed > speeds[-1]:
        return dmaxs[-1], "Ngoại suy, lấy theo giá trị biên cao nhất."
    interpolated_value = np.interp(speed, speeds, dmaxs)
    return float(interpolated_value), "Giá trị nội suy."

def calculate_d_wide(speed: float | None) -> float | None:
    if speed is None or not isinstance(speed, (int, float)) or speed <= 0:
        return None
    d_meters = 5e11 * (KINEMATIC_VISCOSITY_V / speed)
    return d_meters / 1000

# --- GIAO DIỆN NGƯỜI DÙNG (UI) ---

st.title("💨 CÔNG CỤ TÍNH TOÁN ĐÀ GIÓ TOÀN DIỆN")
st.markdown("Chuyển thể từ ứng dụng HTML/JS sang Python với Streamlit để tính toán, nội suy và kiểm tra điều kiện Đà gió.")
st.divider()

# --- Thông tin chung ---
with st.container(border=True):
    st.subheader("📋 THÔNG TIN CHUNG")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Dự án:", placeholder="Nhập tên dự án", key="project_name")
        st.text_input("Hạng mục:", placeholder="Nhập hạng mục", key="item_name")
    with col2:
        st.text_input("Vị trí tính toán:", placeholder="Nhập vị trí tính toán", key="location")
        st.number_input("Hướng gió chính (độ):", min_value=0.0, max_value=360.0, step=1.0, value=0.0, key="wind_direction")
st.divider()

# --- BƯỚC 1: Lựa chọn trường hợp tính toán ---
st.header("BƯỚC 1: LỰA CHỌN TRƯỜNG HỢP TÍNH TOÁN")
calculation_case = st.radio(
    "Chọn phương pháp tính Đà gió:",
    ["Vùng nước hẹp (Tính De)", "Vùng nước rộng (Tính D)"],
    horizontal=True,
    label_visibility="collapsed"
)
st.divider()

# --- BƯỚC 2: Xác định Dmax ---
st.header("BƯỚC 2: XÁC ĐỊNH ĐÀ GIÓ LỚN NHẤT CHO PHÉP (Dmax)")
col1, col2 = st.columns([1, 2])
with col1:
    wind_speed = st.number_input(
        "Nhập Tốc độ gió tính toán (w, m/s):",
        min_value=0.1,
        value=None,
        step=0.5,
        format="%.2f",
        placeholder="Ví dụ: 27.5"
    )
    dmax_result, dmax_note = interpolate_dmax(wind_speed, DMAX_DF)
    
    if dmax_result is not None:
        st.metric("Dmax nội suy", f"{dmax_result:.3f} km", delta=dmax_note, delta_color="off")

with col2:
    st.markdown("**Bảng E.3 - Giá trị tra cứu (Tham khảo TCVN 9901:2023)**")
    st.dataframe(DMAX_DF, hide_index=True, use_container_width=True)
st.divider()


# --- BƯỚC 3: Nhập liệu và tính toán De hoặc D ---
st.header("BƯỚC 3: NHẬP DỮ LIỆU VÀ TÍNH TOÁN")
d_final = None

if calculation_case == "Vùng nước hẹp (Tính De)":
    st.info("Nhập giá trị Đà gió `ri` (đơn vị: km) cho từng tia xạ vào bảng dưới đây.")
    input_df = RAY_DF.copy()
    input_df.insert(3, 'Đà gió ri (km)', 0.0)
    
    edited_df = st.data_editor(
        input_df,
        column_config={
            "Đà gió ri (km)": st.column_config.NumberColumn(
                "Đà gió ri (km)",
                help="Nhập đà gió theo tia xạ (đơn vị km)",
                min_value=0.0,
                format="%.3f"
            ),
            "Tia xạ": st.column_config.NumberColumn(disabled=True),
            "Góc αi (độ)": st.column_config.NumberColumn(disabled=True),
            "cos(αi)": st.column_config.NumberColumn(disabled=True),
            "cos²(αi)": st.column_config.NumberColumn(disabled=True),
        },
        hide_index=True, key="de_editor"
    )
    edited_df['ri × cos²(αi)'] = edited_df['Đà gió ri (km)'] * edited_df['cos²(αi)']
    
    numerator_sum = edited_df['ri × cos²(αi)'].sum()
    denominator_sum = edited_df['cos(αi)'].sum()
    de_result = numerator_sum / denominator_sum if denominator_sum != 0 else 0
    d_final = de_result

    st.subheader("🎯 KẾT QUẢ TÍNH TOÁN (De)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng tử số (Σ ri×cos²αi)", f"{numerator_sum:.3f} km")
    c2.metric("Tổng mẫu số (Σ cosαi)", f"{denominator_sum:.3f}")
    c3.metric("ĐÀ GIÓ TƯƠNG ĐƯƠNG (De)", f"{de_result:.3f} km")

else: # Vùng nước rộng
    st.info("Đà gió trung bình (D) được tự động tính dựa trên Tốc độ gió (w) bạn đã nhập ở **BƯỚC 3**. Công thức sử dụng: **D = 5 x 10¹¹ x (ν / w)**.")
    d_wide_result = calculate_d_wide(wind_speed)
    d_final = d_wide_result

    st.subheader("🎯 KẾT QUẢ TÍNH TOÁN (D)")
    if d_wide_result is not None:
        st.metric("Đà gió trung bình tính toán (D)", f"{d_wide_result:.3f} km")
    else:
        st.warning("Nhập tốc độ gió ở trên để tính D.")
st.divider()


# --- BƯỚC 4: Kiểm tra và Kết luận ---
st.header("BƯỚC 4: KIỂM TRA & KẾT LUẬN")

d_type_label = "De" if calculation_case == "Vùng nước hẹp (Tính De)" else "D"

with st.container(border=True):
    d_final_str = f"{d_final:.3f}" if d_final is not None else "-"
    dmax_result_str = f"{dmax_result:.3f}" if dmax_result is not None else "-"

    st.markdown(f"""
    - **Đà gió tính toán ({d_type_label}):** `{d_final_str} km`
    - **Đà gió lớn nhất cho phép (Dmax):** `{dmax_result_str} km`
    - **Điều kiện kiểm tra:** `{d_type_label} ≤ Dmax`
    """)

    if d_final is not None and dmax_result is not None:
        if d_final <= dmax_result:
            st.success(f"**KẾT LUẬN: PHÙ HỢP** ({d_final:.3f} km ≤ {dmax_result:.3f} km)")
        else:
            st.error(f"**KẾT LUẬN: KHÔNG PHÙ HỢP** ({d_final:.3f} km > {dmax_result:.3f} km)")
    else:
        st.warning("Vui lòng nhập đủ dữ liệu (Đà gió ri và/hoặc Tốc độ gió w) để có kết luận.")



