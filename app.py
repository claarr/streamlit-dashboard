import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import textwrap


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
def create_pdf_simple(df):
    pdf = FPDF(orientation='L', unit='mm', format='A4')

    pdf.set_font("Arial", size=6)
    page_width = 270  # Lebar halaman A4 landscape
    max_col_width = 100
    min_col_width = 20

    # Hitung lebar kolom
    col_widths = []
    for col in df.columns:
        if col == 'Provinsi':
            max_data_width = df[col].astype(str).map(lambda val: pdf.get_string_width(val)).max()
            width = max(max_data_width, min_col_width) + 6
        else:
            header_width = pdf.get_string_width(str(col))
            data_width = df[col].astype(str).map(lambda val: pdf.get_string_width(val)).max()
            width = max(header_width, data_width, min_col_width) + 6
        width = min(width, max_col_width)
        col_widths.append(width)

    provinsi_idx = df.columns.get_loc('Provinsi')

    # Fungsi untuk membagi kolom ke dalam grup, selalu sertakan Provinsi di setiap grup
    def split_columns(col_widths, max_width, fixed_idx):
        splits = []
        current = [fixed_idx]  # selalu mulai dengan Provinsi
        total = col_widths[fixed_idx]
        for i, w in enumerate(col_widths):
            if i == fixed_idx:
                continue
            if total + w > max_width:
                splits.append(current)
                current = [fixed_idx, i]
                total = col_widths[fixed_idx] + w
            else:
                current.append(i)
                total += w
        if current:
            splits.append(current)
        return splits

    col_indices_groups = split_columns(col_widths, page_width, provinsi_idx)

    for group in col_indices_groups:
        pdf.add_page()

        # Judul
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Data Indikator Air Minum Layak & Sanitasi Layak", ln=True, align="C")
        pdf.ln(5)

        group_col_widths = [col_widths[i] for i in group]
        row_height = 4
        wrap_widths = [int(width // 2.5) for width in group_col_widths]

        # Header
        pdf.set_font("Arial", 'B', 7)
        wrapped_headers = []
        max_lines = 0
        for i, col_idx in enumerate(group):
            lines = textwrap.wrap(str(df.columns[col_idx]), width=wrap_widths[i])
            wrapped_headers.append(lines)
            max_lines = max(max_lines, len(lines))

        y_start = pdf.get_y()
        x_start = pdf.get_x()

        for line_num in range(max_lines):
            for i, lines in enumerate(wrapped_headers):
                num_lines = len(lines)
                padding_top = (max_lines - num_lines) // 2
                if line_num < padding_top or line_num >= padding_top + num_lines:
                    text = ""
                else:
                    text = lines[line_num - padding_top]
                pdf.cell(group_col_widths[i], row_height, text, border=0, align='C')
            pdf.ln()

        # Border header
        pdf.set_y(y_start)
        for i, width in enumerate(group_col_widths):
            x = x_start + sum(group_col_widths[:i])
            pdf.rect(x, y_start, width, row_height * max_lines)

        pdf.set_y(y_start + row_height * max_lines)

        # Isi data
        pdf.set_font("Arial", '', 6)
        for _, row in df.iterrows():
            for i in group:
                text = str(row[i])[:50]
                pdf.cell(col_widths[i], 6, text, border=1, align='C')
            pdf.ln()

    pdf_output = pdf.output(dest='S').encode('latin-1')
    return io.BytesIO(pdf_output)


with col4:
    pdf_buffer = create_pdf_simple(filtered_df)
    st.download_button(
        label="📄 PDF",
        data=pdf_buffer,
        file_name="data_terfilter.pdf",
        mime="application/pdf"
    )


# Tampilkan tabel
st.dataframe(filtered_df, use_container_width=True)