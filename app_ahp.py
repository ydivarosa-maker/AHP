import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="SPK AHP - Pemilihan Mobil Terbaik",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# FUNGSI PERHITUNGAN AHP & VALIDASI KONSISTENSI
# -------------------------------------------------------------
# Nilai Random Index (RI) standar Thomas L. Saaty
RI_DICT = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}

def hitung_ahp(matriks, label):
    """
    Menghitung normalisasi matriks, bobot prioritas (eigenvector),
    lambda max, Consistency Index (CI), dan Consistency Ratio (CR).
    """
    n = len(matriks)
    
    # 1. Normalisasi Matriks (dibagi jumlah kolom)
    sum_kolom = np.sum(matriks, axis=0)
    matriks_norm = matriks / sum_kolom
    
    # 2. Priority Vector (Rata-rata tiap baris matriks normalisasi)
    bobot = np.mean(matriks_norm, axis=1)
    
    # 3. Uji Konsistensi
    kali_matriks = np.dot(matriks, bobot)
    rasio_konsistensi_vektor = kali_matriks / bobot
    lambda_max = np.mean(rasio_konsistensi_vektor)
    
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = RI_DICT.get(n, 1.12)
    cr = ci / ri if ri > 0 else 0.0
    
    df_matriks = pd.DataFrame(matriks, index=label, columns=label)
    df_norm = pd.DataFrame(matriks_norm, index=label, columns=label)
    df_bobot = pd.DataFrame({'Elemen': label, 'Bobot Prioritas': bobot}).set_index('Elemen')
    
    return {
        'matriks': df_matriks,
        'normalisasi': df_norm,
        'bobot': bobot,
        'df_bobot': df_bobot,
        'lambda_max': lambda_max,
        'ci': ci,
        'cr': cr,
        'konsisten': cr <= 0.1
    }

# -------------------------------------------------------------
# DEFINISI ELEMEN AWAL
# -------------------------------------------------------------
KRITERIA = ['Style', 'Keandalan', 'Konsumsi BBM']
ALTERNATIF = ['Avanza', 'Xenia', 'Ertiga', 'Grand Livina']

# -------------------------------------------------------------
# SIDEBAR / NAVIGASI
# -------------------------------------------------------------
st.sidebar.title("📌 Menu Navigasi")
menu = st.sidebar.radio(
    "Pilih Halaman:",
    ["Hierarki & Penjelasan", "Matriks Kriteria", "Matriks Alternatif", "Hasil Rekomendasi & Ranking"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Mata Kuliah:** Sistem Pendukung Keputusan (SPK)\n\n"
    "**Metode:** Analytic Hierarchy Process (AHP)\n\n"
    "**Tujuan:** Rekomendasi Pemilihan Mobil Terbaik"
)

# -------------------------------------------------------------
# SESSION STATE UNTUK NILAI DEFAULT MATRIKS
# -------------------------------------------------------------
# Matriks Kriteria Default
# Keandalan:Style = 2 -> Style:Keandalan = 1/2
# Konsumsi:Style = 1/3 -> Style:Konsumsi = 3
# Konsumsi:Keandalan = 1/4 -> Keandalan:Konsumsi = 4
if 'val_k_sk' not in st.session_state:
    st.session_state.val_k_sk = 0.5   # Style vs Keandalan
if 'val_k_sb' not in st.session_state:
    st.session_state.val_k_sb = 3.0   # Style vs Konsumsi BBM
if 'val_k_kb' not in st.session_state:
    st.session_state.val_k_kb = 4.0   # Keandalan vs Konsumsi BBM

# Matriks Alternatif - Kriteria Style Default
if 'style_pairs' not in st.session_state:
    st.session_state.style_pairs = {
        ('Avanza', 'Xenia'): 2.0,        # Xenia:Avanza = 1/2 -> Avanza:Xenia = 2
        ('Avanza', 'Ertiga'): 1/3,       # Ertiga:Avanza = 3 -> Avanza:Ertiga = 1/3
        ('Avanza', 'Grand Livina'): 1/4, # Grand Livina:Avanza = 4 -> Avanza:GL = 1/4
        ('Xenia', 'Ertiga'): 1/2,        # Ertiga:Xenia = 2 -> Xenia:Ertiga = 1/2
        ('Xenia', 'Grand Livina'): 1/5,  # Grand Livina:Xenia = 5 -> Xenia:GL = 1/5
        ('Ertiga', 'Grand Livina'): 2.0  # Grand Livina:Ertiga = 1/2 -> Ertiga:GL = 2
    }

# Matriks Alternatif - Kriteria Keandalan Default
if 'keandalan_pairs' not in st.session_state:
    st.session_state.keandalan_pairs = {
        ('Avanza', 'Xenia'): 2.0,        # Xenia:Avanza = 1/2 -> Avanza:Xenia = 2
        ('Avanza', 'Ertiga'): 1/4,       # Ertiga:Avanza = 4 -> Avanza:Ertiga = 1/4
        ('Avanza', 'Grand Livina'): 1/3, # Grand Livina:Avanza = 3 -> Avanza:GL = 1/3
        ('Xenia', 'Ertiga'): 1/5,        # Ertiga:Xenia = 5 -> Xenia:Ertiga = 1/5
        ('Xenia', 'Grand Livina'): 1/4,  # Grand Livina:Xenia = 4 -> Xenia:GL = 1/4
        ('Ertiga', 'Grand Livina'): 3.0  # Grand Livina:Ertiga = 1/3 -> Ertiga:GL = 3
    }

# Matriks Alternatif - Kriteria Konsumsi BBM Default
if 'bbm_pairs' not in st.session_state:
    st.session_state.bbm_pairs = {
        ('Avanza', 'Xenia'): 2.0,        # Xenia:Avanza = 1/2 -> Avanza:Xenia = 2
        ('Avanza', 'Ertiga'): 1/2,       # Ertiga:Avanza = 2 -> Avanza:Ertiga = 1/2
        ('Avanza', 'Grand Livina'): 4.0, # Grand Livina:Avanza = 1/4 -> Avanza:GL = 4
        ('Xenia', 'Ertiga'): 1/1.5,      # Ertiga:Xenia = 1.5 -> Xenia:Ertiga = 1/1.5
        ('Xenia', 'Grand Livina'): 3.0,  # Grand Livina:Xenia = 1/3 -> Xenia:GL = 3
        ('Ertiga', 'Grand Livina'): 4.0  # Grand Livina:Ertiga = 1/4 -> Ertiga:GL = 4
    }

# -------------------------------------------------------------
# BUILD MATRIKS KOMPARASI BERPASANGAN
# -------------------------------------------------------------
# 1. Matriks Kriteria
m_kriteria = np.ones((3, 3))
m_kriteria[0, 1] = st.session_state.val_k_sk
m_kriteria[1, 0] = 1.0 / st.session_state.val_k_sk
m_kriteria[0, 2] = st.session_state.val_k_sb
m_kriteria[2, 0] = 1.0 / st.session_state.val_k_sb
m_kriteria[1, 2] = st.session_state.val_k_kb
m_kriteria[2, 1] = 1.0 / st.session_state.val_k_kb
res_kriteria = hitung_ahp(m_kriteria, KRITERIA)

# 2. Matriks Alternatif per Kriteria
def buat_matriks_alt(pairs_dict):
    m = np.ones((4, 4))
    idx = {alt: i for i, alt in enumerate(ALTERNATIF)}
    for (a1, a2), val in pairs_dict.items():
        i, j = idx[a1], idx[a2]
        m[i, j] = val
        m[j, i] = 1.0 / val
    return m

res_alt_style = hitung_ahp(buat_matriks_alt(st.session_state.style_pairs), ALTERNATIF)
res_alt_keandalan = hitung_ahp(buat_matriks_alt(st.session_state.keandalan_pairs), ALTERNATIF)
res_alt_bbm = hitung_ahp(buat_matriks_alt(st.session_state.bbm_pairs), ALTERNATIF)

# 3. Skor Sintesis Akhir Global
matriks_bobot_alternatif = np.column_stack((
    res_alt_style['bobot'],
    res_alt_keandalan['bobot'],
    res_alt_bbm['bobot']
))
skor_akhir = np.dot(matriks_bobot_alternatif, res_kriteria['bobot'])

df_rekap = pd.DataFrame({
    'Alternatif': ALTERNATIF,
    'Bobot Style': res_alt_style['bobot'],
    'Bobot Keandalan': res_alt_keandalan['bobot'],
    'Bobot Konsumsi BBM': res_alt_bbm['bobot'],
    'Skor Akhir': skor_akhir
}).sort_values(by='Skor Akhir', ascending=False).reset_index(drop=True)

df_rekap['Ranking'] = df_rekap.index + 1

# -------------------------------------------------------------
# HALAMAN 1: HIERARKI & PENJELASAN
# -------------------------------------------------------------
if menu == "Hierarki & Penjelasan":
    st.header("🎯 Struktur Hierarki Keputusan (AHP)")
    st.write(
        "Metode **Analytic Hierarchy Process (AHP)** menguraikan masalah keputusan yang kompleks "
        "menjadi suatu hierarki yang terdiri atas tujuan (*goal*), kriteria, dan alternatif."
    )
    
    col_tujuan, col_kriteria, col_alternatif = st.columns(3)
    
    with col_tujuan:
        st.subheader("1. Tujuan (Goal)")
        st.success("🎯 **Membeli / Memilih Mobil Terbaik**")
        st.caption("Fokus akhir dari penentuan prioritas keputusan.")

    with col_kriteria:
        st.subheader("2. Kriteria Evaluasi")
        for k in KRITERIA:
            st.info(f"🔹 **{k}**")
        st.caption("3 parameter pertimbangan utama.")

    with col_alternatif:
        st.subheader("3. Alternatif Pilihan")
        for a in ALTERNATIF:
            st.warning(f"🚗 **{a}**")
        st.caption("4 pilihan mobil yang dibandingkan.")

    st.markdown("---")
    st.subheader("Skala Perbandingan Saaty (1 - 9)")
    skala_df = pd.DataFrame({
        "Intensitas Kepentingan": [1, 3, 5, 7, 9, "2, 4, 6, 8", "Resiprokal (1/x)"],
        "Definisi": [
            "Sama pentingnya (Equal Importance)",
            "Cukup penting (Moderate Importance)",
            "Lebih penting (Strong Importance)",
            "Sangat penting (Very Strong / Demonstrated)",
            "Mutlak lebih penting (Extreme Importance)",
            "Nilai-nilai antara dua preferensi yang berdekatan",
            "Jika elemen i bernilai x dibanding j, maka j bernilai 1/x dibanding i"
        ]
    })
    st.table(skala_df)

# -------------------------------------------------------------
# HALAMAN 2: MATRIKS KRITERIA
# -------------------------------------------------------------
elif menu == "Matriks Kriteria":
    st.header("⚖️ Evaluasi Perbandingan Berpasangan Antar Kriteria")
    st.write("Sesuaikan perbandingan berpasangan antar kriteria di bawah ini:")

    with st.expander("🛠️ Formulir Penyesuaian Nilai Perbandingan Kriteria", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            val_sk = st.number_input("Style dibanding Keandalan:", value=float(st.session_state.val_k_sk), min_value=0.01, max_value=9.0, step=0.1, format="%.4f")
        with c2:
            val_sb = st.number_input("Style dibanding Konsumsi BBM:", value=float(st.session_state.val_k_sb), min_value=0.01, max_value=9.0, step=0.1, format="%.4f")
        with c3:
            val_kb = st.number_input("Keandalan dibanding Konsumsi BBM:", value=float(st.session_state.val_k_kb), min_value=0.01, max_value=9.0, step=0.1, format="%.4f")
        
        # Simpan state bila ada perubahan
        st.session_state.val_k_sk = val_sk
        st.session_state.val_k_sb = val_sb
        st.session_state.val_k_kb = val_kb

    st.markdown("---")
    col_left, col_right = st.columns([1.2, 1])
    
    with col_left:
        st.subheader("Matriks Perbandingan Berpasangan")
        st.dataframe(res_kriteria['matriks'].style.format("{:.4f}"), use_container_width=True)
        
        st.subheader("Matriks Ternormalisasi")
        st.dataframe(res_kriteria['normalisasi'].style.format("{:.4f}"), use_container_width=True)

    with col_right:
        st.subheader("Bobot Prioritas Kriteria")
        st.dataframe(res_kriteria['df_bobot'].style.format("{:.4f}"), use_container_width=True)
        
        st.subheader("Hasil Uji Konsistensi")
        st.write(f"**λ Max (Lambda Max):** `{res_kriteria['lambda_max']:.4f}`")
        st.write(f"**Consistency Index (CI):** `{res_kriteria['ci']:.4f}`")
        st.write(f"**Random Index (RI, n=3):** `0.58`")
        st.write(f"**Consistency Ratio (CR):** `{res_kriteria['cr']:.4f}`")
        
        if res_kriteria['konsisten']:
            st.success("✅ **CR <= 0.10: Matriks Kriteria KONSISTEN**")
        else:
            st.error("⚠️ **CR > 0.10: Matriks Kriteria TIDAK KONSISTEN (Perlu Ditinjau)**")

# -------------------------------------------------------------
# HALAMAN 3: MATRIKS ALTERNATIF
# -------------------------------------------------------------
elif menu == "Matriks Alternatif":
    st.header("🚘 Evaluasi Alternatif Mobil Berdasarkan Setiap Kriteria")
    
    tab_style, tab_keandalan, tab_bbm = st.tabs(["Kriteria Style", "Kriteria Keandalan", "Kriteria Konsumsi BBM"])
    
    def render_tab_alternatif(res, nama_kriteria):
        st.markdown(f"### Matriks Perbandingan Alternatif pada Kriteria: **{nama_kriteria}**")
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.write("**Matriks Perbandingan Berpasangan:**")
            st.dataframe(res['matriks'].style.format("{:.4f}"), use_container_width=True)
            st.write("**Matriks Ternormalisasi:**")
            st.dataframe(res['normalisasi'].style.format("{:.4f}"), use_container_width=True)
        with c2:
            st.write("**Bobot Prioritas Alternatif:**")
            st.dataframe(res['df_bobot'].style.format("{:.4f}"), use_container_width=True)
            
            st.write("**Uji Konsistensi (n=4, RI=0.90):**")
            st.write(f"- λ Max: `{res['lambda_max']:.4f}`")
            st.write(f"- CI: `{res['ci']:.4f}`")
            st.write(f"- CR: `{res['cr']:.4f}`")
            
            if res['konsisten']:
                st.success(f"✅ CR ({res['cr']:.4f}) <= 0.10: Konsisten")
            else:
                st.warning(f"⚠️ CR ({res['cr']:.4f}) > 0.10: Tidak Konsisten")

    with tab_style:
        render_tab_alternatif(res_alt_style, "Style")
        
    with tab_keandalan:
        render_tab_alternatif(res_alt_keandalan, "Keandalan")
        
    with tab_bbm:
        render_tab_alternatif(res_alt_bbm, "Konsumsi BBM")

# -------------------------------------------------------------
# HALAMAN 4: REKOMENDASI & RANKING
# -------------------------------------------------------------
elif menu == "Hasil Rekomendasi & Ranking":
    st.header("🏆 Rekomendasi Akhir & Peringkat Mobil")
    
    # Mobil Terbaik
    juara = df_rekap.iloc[0]
    st.success(
        f"### 🥇 Mobil Terbaik yang Direkomendasikan: **{juara['Alternatif']}**\n"
        f"Dengan perolehan skor preferensi global tertinggi sebesar **{juara['Skor Akhir']:.4f}** (atau {juara['Skor Akhir']*100:.2f}%)."
    )
    
    col1, col2 = st.columns([1.1, 1.3])
    
    with col1:
        st.subheader("📋 Tabel Rekapitulasi & Ranking")
        st.dataframe(
            df_rekap[['Ranking', 'Alternatif', 'Bobot Style', 'Bobot Keandalan', 'Bobot Konsumsi BBM', 'Skor Akhir']]
            .style.format({
                'Bobot Style': '{:.4f}',
                'Bobot Keandalan': '{:.4f}',
                'Bobot Konsumsi BBM': '{:.4f}',
                'Skor Akhir': '{:.4f}'
            }),
            use_container_width=True,
            hide_index=True
        )
        
    with col2:
        st.subheader("📊 Visualisasi Perbandingan Skor Akhir")
        fig = px.bar(
            df_rekap,
            x='Alternatif',
            y='Skor Akhir',
            color='Alternatif',
            text='Skor Akhir',
            title='Skor Akhir Preferensi Global AHP',
            labels={'Skor Akhir': 'Skor Preferensi', 'Alternatif': 'Mobil'},
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_traces(texttemplate='%{text:.4f}', textposition='outside')
        fig.update_layout(yaxis_range=[0, max(df_rekap['Skor Akhir']) * 1.25], showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Breakdown Kontribusi Kriteria terhadap Setiap Mobil")
    # Dataframe kontribusi bobot (bobot alternatif dikali bobot kriteria masing-masing)
    df_kontribusi = pd.DataFrame({
        'Alternatif': ALTERNATIF,
        'Style': res_alt_style['bobot'] * res_kriteria['bobot'][0],
        'Keandalan': res_alt_keandalan['bobot'] * res_kriteria['bobot'][1],
        'Konsumsi BBM': res_alt_bbm['bobot'] * res_kriteria['bobot'][2],
    })
    
    fig_stack = px.bar(
        df_kontribusi,
        x='Alternatif',
        y=['Style', 'Keandalan', 'Konsumsi BBM'],
        title='Dekomposisi Kontribusi Skor per Kriteria (Stacked Bar)',
        labels={'value': 'Kontribusi Skor', 'variable': 'Kriteria'},
        barmode='stack'
    )
    st.plotly_chart(fig_stack, use_container_width=True)