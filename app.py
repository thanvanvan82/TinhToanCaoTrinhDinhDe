# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# Import logic tính toán từ file calculator.py
from calculator import main_workflow, ri_data_list, list_de_song, list_de_bien

# --- Cấu hình trang ---
st.set_page_config(
    page_title="Hệ thống tính toán cao trình đỉnh đê",
    page_icon="🌊",
    layout="wide"
)

# --- Hàm tiện ích cho UI ---
def plot_de_song(df):
    """Vẽ và hiển thị biểu đồ cho đê sông."""
    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(kind='bar', x='tuyến đê sông', y='Zđs (m)', rot=0, ax=ax)
    ax.set_title("So sánh Cao trình Đỉnh đê giữa các Tuyến sông", fontsize=14)
    ax.set_xlabel("Tên Tuyến đê")
    ax.set_ylabel("Cao trình Zđs (m)")
    ax.bar_label(ax.containers[0], fmt='%.2f')
    plt.tight_layout()
    return fig

def plot_de_bien(df):
    """Vẽ và hiển thị biểu đồ cho đê biển."""
    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(kind='bar', x='tuyến đê biển', y=['Zđb (m)', 'Zđb_tràn (m)'], rot=0, ax=ax)
    ax.set_title("So sánh Cao trình Đỉnh đê Biển", fontsize=14)
    ax.set_xlabel("Tên Tuyến đê")
    ax.set_ylabel("Cao trình (m)")
    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f', label_type='edge', padding=2)
    ax.legend(["Không tràn (Rslp)", "Cho phép tràn (Rcp)"])
    plt.tight_layout()
    return fig

def to_excel(df_song, df_bien):
    """Chuyển đổi các DataFrame thành file Excel trong bộ nhớ."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if not df_song.empty:
            df_song.to_excel(writer, sheet_name='ChiTiet_DeSong', index=False)
        if not df_bien.empty:
            df_bien.to_excel(writer, sheet_name='ChiTiet_DeBien', index=False)
    processed_data = output.getvalue()
    return processed_data

# --- Giao diện chính ---
st.title("🌊 Hệ thống Tính toán Cao trình Đê")
st.markdown("Ứng dụng web cho phép nhập thông số, tính toán và trực quan hóa cao trình đỉnh đê sông và đê biển.")

# Tạo các tab cho Đê sông và Đê biển
tab1, tab2 = st.tabs(["📊 Tính toán Đê Sông", "📈 Tính toán Đê Biển"])

# --- Tab Đê Sông ---
with tab1:
    st.header("Nhập dữ liệu cho Đê Sông")
    st.markdown("Chỉnh sửa trực tiếp dữ liệu trong bảng dưới đây hoặc thêm/xóa hàng.")
    
    # Khởi tạo DataFrame từ dữ liệu mặc định
    df_input_song_default = pd.DataFrame(list_de_song)
    # Streamlit không thể hiển thị list trong ô, nên ta chuyển nó thành string
    df_input_song_default['chiều dài của các tia xạ (m)'] = df_input_song_default['chiều dài của các tia xạ (m)'].astype(str)

    # Sử dụng st.data_editor để tạo bảng có thể chỉnh sửa
    edited_df_song = st.data_editor(
        df_input_song_default,
        num_rows="dynamic",
        key="editor_song"
    )

# --- Tab Đê Biển ---
with tab2:
    st.header("Nhập dữ liệu cho Đê Biển")
    st.markdown("Chỉnh sửa trực tiếp dữ liệu trong bảng dưới đây hoặc thêm/xóa hàng.")
    
    # Khởi tạo DataFrame từ dữ liệu mặc định
    df_input_bien_default = pd.DataFrame(list_de_bien)
    
    # Sử dụng st.data_editor
    edited_df_bien = st.data_editor(
        df_input_bien_default,
        num_rows="dynamic",
        key="editor_bien"
    )

# --- Nút tính toán và hiển thị kết quả ---
if st.button("🚀 Bắt đầu tính toán", type="primary", use_container_width=True):
    with st.spinner("Đang thực hiện các phép tính phức tạp... Vui lòng chờ..."):
        
        # Xử lý lại dữ liệu đầu vào từ bảng editor
        # Chuyển cột tia xạ từ string về lại list of floats
        try:
            # Dùng list mặc định vì việc nhập list qua UI rất phức tạp
            # Trong một ứng dụng thực tế, có thể cần một giao diện nhập riêng cho 'ri'
            for i, row in edited_df_song.iterrows():
                 edited_df_song.at[i, 'chiều dài của các tia xạ (m)'] = ri_data_list

        except Exception as e:
            st.error(f"Lỗi xử lý dữ liệu đầu vào cho đê sông: {e}")
            st.stop()
        
        # Chạy workflow chính
        df_ket_qua_song, df_ket_qua_bien = main_workflow(edited_df_song, edited_df_bien)

        st.success("✅ Tính toán hoàn tất!")

        # Tạo file Excel trong bộ nhớ để chuẩn bị cho việc tải xuống
        excel_data = to_excel(df_ket_qua_song, df_ket_qua_bien)
        st.download_button(
            label="📥 Tải xuống toàn bộ kết quả (Excel)",
            data=excel_data,
            file_name="ket_qua_tinh_toan_cao_trinh_de.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.divider()

        # Hiển thị kết quả Đê Sông
        if not df_ket_qua_song.empty:
            st.header("Kết quả Đê Sông")
            st.dataframe(df_ket_qua_song)
            try:
                fig_song = plot_de_song(df_ket_qua_song)
                st.pyplot(fig_song)
            except Exception as e:
                st.warning(f"Không thể vẽ biểu đồ cho đê sông: {e}")

        # Hiển thị kết quả Đê Biển
        if not df_ket_qua_bien.empty:
            st.header("Kết quả Đê Biển")
            st.dataframe(df_ket_qua_bien)
            try:
                fig_bien = plot_de_bien(df_ket_qua_bien)
                st.pyplot(fig_bien)
            except Exception as e:
                st.warning(f"Không thể vẽ biểu đồ cho đê biển: {e}")