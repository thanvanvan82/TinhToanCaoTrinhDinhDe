# app.py
import streamlit as st
import pandas as pd
import io

# Import logic tính toán đã được rút gọn
from calculator import main_workflow_song, list_de_song, ri_data_list

# --- Cấu hình trang ---
st.set_page_config(
    page_title="Tính toán Cao trình Đê Sông",
    page_icon="🌊",
    layout="wide"
)

# --- Hàm tiện ích cho UI (đã tối ưu) ---
@st.cache_data
def to_csv(df):
    """Chuyển DataFrame thành file CSV trong bộ nhớ."""
    return df.to_csv(index=False).encode('utf-8')

# --- Giao diện chính ---
st.title("🌊 Hệ thống Tính toán Cao trình Đê Sông")
st.markdown("Ứng dụng web cho phép nhập thông số, tính toán và trực quan hóa cao trình đỉnh đê sông.")
st.divider()

st.header("1. Nhập dữ liệu đầu vào")
st.markdown("Chỉnh sửa trực tiếp dữ liệu trong bảng dưới đây hoặc thêm/xóa hàng. Cột `chiều dài của các tia xạ (m)` sẽ luôn được sử dụng dữ liệu mặc định.")

# Khởi tạo DataFrame từ dữ liệu mặc định
df_input_song_default = pd.DataFrame(list_de_song)
# Chuyển list thành string để hiển thị, vì data_editor không hỗ trợ list
df_input_song_default['chiều dài của các tia xạ (m)'] = str(ri_data_list)

# Sử dụng st.data_editor để tạo bảng có thể chỉnh sửa
edited_df_song = st.data_editor(
    df_input_song_default,
    num_rows="dynamic",
    key="editor_song"
)

# --- Nút tính toán và hiển thị kết quả ---
st.header("2. Thực hiện tính toán")
if st.button("🚀 Bắt đầu tính toán", type="primary", use_container_width=True):
    if edited_df_song.empty:
        st.warning("Vui lòng nhập ít nhất một hàng dữ liệu để tính toán.")
    else:
        with st.spinner("Đang thực hiện các phép tính..."):
            
            # Gán lại giá trị list tia xạ chuẩn cho mọi hàng trước khi tính
            # Vì người dùng không thể nhập list một cách dễ dàng qua UI
            df_for_calculation = edited_df_song.copy()
            df_for_calculation['chiều dài của các tia xạ (m)'] = [ri_data_list] * len(df_for_calculation)

            # Chạy workflow chính (phiên bản rút gọn)
            df_ket_qua_song = main_workflow_song(df_for_calculation)

            st.success("✅ Tính toán hoàn tất!")
            st.divider()

            st.header("3. Kết quả tính toán")
            
            # Hiển thị bảng kết quả
            st.subheader("Bảng kết quả chi tiết")
            st.dataframe(df_ket_qua_song)

            # Hiển thị biểu đồ (dùng hàm có sẵn của Streamlit)
            st.subheader("Biểu đồ so sánh cao trình đỉnh đê")
            
            # Chuẩn bị dữ liệu cho biểu đồ
            df_chart = df_ket_qua_song.set_index('tuyến đê sông')[['Zđs (m)']]
            st.bar_chart(df_chart)

            # Nút tải xuống file CSV
            csv_data = to_csv(df_ket_qua_song)
            st.download_button(
                label="📥 Tải xuống kết quả (CSV)",
                data=csv_data,
                file_name="ket_qua_tinh_toan_de_song.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # Lưu kết quả vào session state để không bị mất khi re-run
            st.session_state.result = df_ket_qua_song
