# app.py
import streamlit as st
import pandas as pd

# Import toàn bộ logic từ file calculator.py
from calculator import (
    DMAX_DF,
    RAY_DF_BASE,
    interpolate_dmax,
    calculate_d_wide,
    calculate_de
)

# --- Cấu hình trang ---
st.set_page_config(
    page_title="Công cụ tính toán Đà gió Toàn diện",
    page_icon="💨",
    layout="wide"
)

# --- GIAO DIỆN NGƯỜI DÙNG (UI) ---

st.title("💨 CÔNG CỤ TÍNH TOÁN ĐÀ GIÓ TOÀN DIỆN")
st.markdown("Chuyển thể từ ứng dụng HTML/JS sang Python với Streamlit để tính toán, nội suy và kiểm tra điều kiện Đà gió.")
st.divider()

# --- Thông tin chung ---
with st.container(border=True):
    st.subheader("📋 THÔNG TIN CHUNG")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Dự án:", placeholder="Nhập tên dự án")
        st.text_input("Hạng mục:", placeholder="Nhập hạng mục")
    with col2:
        st.text_input("Vị trí tính toán:", placeholder="Nhập vị trí tính toán")
        st.number_input("Hướng gió chính (độ):", min_value=0.0, max_value=360.0, step=1.0, value=0.0)
st.divider()


# --- BƯỚC 2: Nhập liệu và tính toán De hoặc D ---
st.header("BƯỚC 2: NHẬP DỮ LIỆU VÀ TÍNH TOÁN")
d_final = None

if calculation_case == "Vùng nước hẹp (Tính De)":
    st.info("Nhập giá trị Đà gió `ri` (đơn vị: km) cho từng tia xạ vào bảng dưới đây.")
    
    input_df = RAY_DF_BASE.copy()
    input_df.insert(3, 'Đà gió ri (km)', 0.0)
    
    edited_df = st.data_editor(
        input_df,
        column_config={
            "Đà gió ri (km)": st.column_config.NumberColumn(format="%.3f km"),
            "Tia xạ": st.column_config.NumberColumn(disabled=True),
            "Góc αi (độ)": st.column_config.NumberColumn(disabled=True),
            "cos(αi)": st.column_config.NumberColumn(disabled=True),
            "cos²(αi)": st.column_config.NumberColumn(disabled=True),
        },
        hide_index=True,
        key="de_editor"
    )

    # GỌI HÀM TÍNH TOÁN TỪ calculator.py
    numerator_sum, denominator_sum, de_result = calculate_de(edited_df)
    d_final = de_result

    st.subheader("🎯 KẾT QUẢ TÍNH TOÁN (De)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng tử số (Σ ri×cos²αi)", f"{numerator_sum:.3f} km")
    col2.metric("Tổng mẫu số (Σ cosαi)", f"{denominator_sum:.3f}")
    col3.metric("ĐÀ GIÓ TƯƠNG ĐƯƠNG (De)", f"{de_result:.3f} km")
else:
    st.info("Đà gió trung bình (D) sẽ được tự động tính ở **BƯỚC 3** sau khi bạn nhập Tốc độ gió (w).")
st.divider()


# --- BƯỚC 3: Xác định Dmax ---
st.header("BƯỚC 3: XÁC ĐỊNH ĐÀ GIÓ LỚN NHẤT CHO PHÉP (Dmax)")
col1, col2 = st.columns([1, 2])
with col1:
    wind_speed = st.number_input(
        "Nhập Tốc độ gió tính toán (w, m/s):",
        min_value=0.1, value=None, step=0.5,
        format="%.2f m/s", placeholder="Ví dụ: 27.5"
    )
    # GỌI HÀM TÍNH TOÁN TỪ calculator.py
    dmax_result, dmax_note = interpolate_dmax(wind_speed, DMAX_DF)
    
    if dmax_result is not None:
        st.metric("Dmax nội suy", f"{dmax_result:.3f} km", delta=dmax_note, delta_color="off")
with col2:
    st.markdown("**Bảng E.3 - Giá trị tra cứu (Tham khảo)**")
    st.dataframe(DMAX_DF, hide_index=True, use_container_width=True)

if calculation_case == "Vùng nước rộng (Tính D)":
    # GỌI HÀM TÍNH TOÁN TỪ calculator.py
    d_wide_result = calculate_d_wide(wind_speed)
    d_final = d_wide_result
    st.subheader("🎯 KẾT QUẢ TÍNH TOÁN (D)")
    if d_wide_result is not None:
        st.metric("Đà gió trung bình tính toán (D)", f"{d_wide_result:.3f} km")
    else:
        st.warning("Nhập tốc độ gió ở trên để tính D.")
st.divider()


# --- BƯỚC 4: Kiểm tra và Kết luận (Giữ nguyên) ---
st.header("BƯỚC 4: KIỂM TRA & KẾT LUẬN")
# ... (Phần này không thay đổi vì nó chỉ hiển thị kết quả đã tính toán) ...
# (Copy phần "BƯỚC 4" từ phiên bản trước vào đây)
d_type_label = "De" if calculation_case == "Vùng nước hẹp (Tính De)" else "D"
with st.container(border=True):
    st.markdown(f"""
    - **Đà gió tính toán ({d_type_label}):** `{"-" if d_final is None else f"{d_final:.3f}"} km`
    - **Đà gió lớn nhất cho phép (Dmax):** `{"-" if dmax_result is None else f"{dmax_result:.3f}"} km`
    - **Điều kiện kiểm tra:** `{d_type_label} ≤ Dmax`
    """)
    if wind_speed is None or d_final is None:
        st.warning("Vui lòng nhập đủ dữ liệu (Đà gió ri hoặc Tốc độ gió w) để có kết luận.")
    elif d_final <= dmax_result:
        st.success(f"**KẾT LUẬN: PHÙ HỢP** ({d_final:.3f} km ≤ {dmax_result:.3f} km)")
    else:
        st.error(f"**KẾT LUẬN: KHÔNG PHÙ HỢP** ({d_final:.3f} km > {dmax_result:.3f} km)")

