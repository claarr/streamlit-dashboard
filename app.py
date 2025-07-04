import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
from textwrap import wrap


# URL Google Sheet yang dipublikasikan sebagai CSV
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSbaeltz8dJKOJ5zUt4FqggdFZPPqfFiJAiIVnS8zdLhbAPQjK1LGQWoqAO0WAYlaiOG2EeUfB32EMI/pub?output=csv"
df = pd.read_csv(sheet_url)

st.title("📊 Data Indikator Air Minum Layak & Sanitasi Layak")

# Layout horizontal: 4 kolom (2 untuk filter, 2 untuk tombol)
col1, col2, col3, col4 = st.columns([3, 3, 1, 1])

# Filter Provinsi
with col1:
    provinsi_list = ["Semua"] + sorted(df["Provinsi"].dropna().unique().tolist())
    provinsi = st.selectbox("Pilih Provinsi", provinsi_list)

# Filter Cluster
with col2:
    cluster_list = ["Semua"] + sorted(df["Cluster"].dropna().unique().tolist())
    cluster = st.selectbox("Pilih Cluster", cluster_list)

# Filter berdasarkan input
filtered_df = df.copy()
if provinsi != "Semua":
    filtered_df = filtered_df[filtered_df["Provinsi"] == provinsi]
if cluster != "Semua":
    filtered_df = filtered_df[filtered_df["Cluster"] == int(cluster)]

# Download CSV
with col3:
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    st.download_button("📥 CSV", data=csv_buffer.getvalue(), file_name="data_terfilter.csv", mime="text/csv")

# Download PDF
def create_pdf(df):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=10)

    max_cols_per_page = 10  # karena Provinsi + 9 = 10 kolom
    max_col_width = 50
    min_col_width = 20
    page_width = 270

    # Pastikan kolom 'Provinsi' ada
    if 'Provinsi' not in df.columns:
        raise ValueError("Kolom 'Provinsi' tidak ditemukan di dataframe.")

    # Kolom selain Provinsi
    other_cols = [col for col in df.columns if col != 'Provinsi']

    for start in range(0, len(other_cols), max_cols_per_page):
        end = min(start + max_cols_per_page, len(other_cols))
        current_cols = ['Provinsi'] + other_cols[start:end]  # tambahkan 'Provinsi' setiap halaman
        df_slice = df[current_cols]

        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Laporan Data Terfilter", ln=True, align="C")

        # Hitung lebar kolom
        pdf.set_font("Arial", size=6)
        col_widths = []
        for col in df_slice.columns:
            max_len = max(df_slice[col].astype(str).map(len).max(), len(str(col)))
            width = pdf.get_string_width("W" * max_len) + 4
            width = min(max_col_width, max(min_col_width, width))
            col_widths.append(width)

        total_width = sum(col_widths)
        scale = page_width / total_width if total_width > page_width else 1
        col_widths = [w * scale for w in col_widths]

        # Header
        pdf.set_font("Arial", 'B', 7)
        y_start = pdf.get_y()
        x_start = pdf.get_x()

        # Bungkus dan simpan header
        wrapped_headers = []
        row_height = 4
        max_lines = 0
        for col in df_slice.columns:
            wrapped = wrap(str(col), width=20)
            max_lines = max(max_lines, len(wrapped))
            wrapped_headers.append(wrapped)

        # Tulis header yang sejajar
        for i, wrapped in enumerate(wrapped_headers):
            x = x_start + sum(col_widths[:i])
            y = y_start
            pdf.set_xy(x, y)
            for line in wrapped:
                pdf.cell(col_widths[i], row_height, line, border=0, align='C')
                y += row_height
            pdf.rect(x, y_start, col_widths[i], row_height * max_lines)

        pdf.set_y(y_start + row_height * max_lines)

        # Isi baris
        pdf.set_font("Arial", '', 6)
        for _, row in df_slice.iterrows():
            for i, item in enumerate(row):
                pdf.cell(col_widths[i], 6, str(item), border=1)
            pdf.ln()

    pdf_output = pdf.output(dest='S').encode('latin-1')
    return io.BytesIO(pdf_output)


with col4:
    pdf_buffer = create_pdf(filtered_df)
    st.download_button(
        label="📄 PDF",
        data=pdf_buffer,
        file_name="data_terfilter.pdf",
        mime="application/pdf"
    )

# Tampilkan tabel
st.dataframe(filtered_df, use_container_width=True)
