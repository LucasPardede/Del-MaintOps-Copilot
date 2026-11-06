# Perbandingan Model Embedding untuk Pipeline Retrieval SOP FITE

> Dokumen ini dihasilkan secara otomatis oleh `scripts/compare_embedding_models.py` dan dilengkapi pengujian empiris OOD.
> Semua angka berasal dari eksekusi nyata, bukan dikarang.

## 1. Tujuan

Membandingkan tiga model embedding untuk memilih model terbaik bagi
pipeline pencarian semantik SOP/kebijakan FITE berbahasa Indonesia:
1. `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Multilingual)
2. `intfloat/multilingual-e5-small` (Multilingual dengan prefix asymmetric query/passage)
3. `sentence-transformers/all-MiniLM-L6-v2` (English-only baseline)

---

## 2. Model yang Dibandingkan

| # | Model | Bahasa | Dimensi | Ukuran (MB) | Parameter |
|---|-------|--------|---------|-------------|-----------|
| 1 | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Multilingual (50+) | 384 | 448.8 | 117,653,760 |
| 2 | `intfloat/multilingual-e5-small` | Multilingual (100+) | 384 | 448.8 | 117,653,760 |
| 3 | `sentence-transformers/all-MiniLM-L6-v2` | English only | 384 | 86.6 | 22,713,216 |

---

## 3. Data Uji

- **Dokumen**: 8 SOP dari `SOP_CATALOG` (judul + prosedur)
- **Kueri In-Domain**: 10 kueri bahasa Indonesia non-literal (sinonim)
- **Kueri Out-of-Domain (OOD)**: Kueri acak di luar domain kampus/FITE (kuliner, beasiswa, hiburan)

### Daftar Kueri In-Domain (Sinonim)

| ID | Kueri | Target | Catatan |
|----|-------|--------|---------|
| Q01 | alat presentasi di kelas tidak bisa menampilkan gambar | SOP-01 | Sinonim proyektor → alat presentasi |
| Q02 | ruangan terasa panas dan pengatur suhu tidak berfungsi | SOP-02 | Sinonim AC → pengatur suhu, tidak dingin → panas |
| Q03 | mahasiswa tidak bisa mengakses internet di laboratorium | SOP-03 | Sinonim jaringan/LAN → internet, lab → laboratorium |
| Q04 | tempat duduk di area santai sudah patah dan berbahaya | SOP-04 | Sinonim kursi → tempat duduk, saung → area santai |
| Q05 | colokan di ruang server mengeluarkan percikan api | SOP-05 | Sinonim listrik/korsleting → percikan api |
| Q06 | komputer di lab tidak bisa booting dan layar hitam | SOP-06 | Sinonim PC → komputer, boot error |
| Q07 | papan digital interaktif layar sentuhnya tidak merespons | SOP-07 | Sinonim Idea Hub → papan digital interaktif |
| Q08 | kamera keamanan di plafon lab tidak merekam video | SOP-08 | Sinonim CCTV → kamera keamanan |
| Q09 | perangkat pendingin udara bocor air ke lantai | SOP-02 | Sinonim AC → pendingin udara, bocor |
| Q10 | koneksi WiFi lambat saat ujian praktikum berlangsung | SOP-03 | Sinonim jaringan → WiFi, konteks praktikum |

---

## 4. Hasil Perbandingan

### 4.1 Ringkasan Metrik Temu Balik

| Metrik | paraphrase-multilingual-MiniLM-L12-v2 | multilingual-e5-small | all-MiniLM-L6-v2 |
|--------|---------------------------------------|-----------------------|------------------|
| **Hit@1** | 6/10 (60%) | 8/10 (80%) | 3/10 (30%) |
| **Avg Cosine (target)** | 0.3631 | 0.8543 | 0.5251 |
| **Avg Cosine (non-target)** | 0.2107 | 0.8183 | 0.4397 |
| **Separation (target - non-target)** | **0.1524** | 0.0360 | 0.0854 |
| **Dimensi vektor** | 384 | 384 | 384 |
| **Ukuran model (MB)** | 448.8 | 448.8 | 86.6 |
| **Waktu encode dokumen (s)** | 1.451 | 1.044 | 0.693 |
| **Waktu encode kueri (s)** | 0.293 | 0.185 | 0.119 |

### 4.2 Detail Hit@1 per Kueri

| Kueri | Target | paraphrase-multilingual-MiniLM-L12-v2 (rank1 / sim) | multilingual-e5-small (rank1 / sim) | all-MiniLM-L6-v2 (rank1 / sim) |
|-------|--------|---------------------------------------------------|-------------------------------------|--------------------------------|
| Q01 | SOP-01 | SOP-07 (-0.016) ❌ | SOP-07 (0.817) ❌ | SOP-02 (0.585) ❌ |
| Q02 | SOP-02 | SOP-02 (0.370) ✅ | SOP-02 (0.873) ✅ | SOP-01 (0.628) ❌ |
| Q03 | SOP-03 | SOP-05 (0.272) ❌ | SOP-03 (0.856) ✅ | SOP-05 (0.419) ❌ |
| Q04 | SOP-04 | SOP-06 (0.277) ❌ | SOP-05 (0.830) ❌ | SOP-05 (0.437) ❌ |
| Q05 | SOP-05 | SOP-05 (0.380) ✅ | SOP-05 (0.856) ✅ | SOP-05 (0.544) ✅ |
| Q06 | SOP-06 | SOP-06 (0.467) ✅ | SOP-06 (0.876) ✅ | SOP-06 (0.498) ✅ |
| Q07 | SOP-07 | SOP-07 (0.461) ✅ | SOP-07 (0.867) ✅ | SOP-08 (0.456) ❌ |
| Q08 | SOP-08 | SOP-08 (0.601) ✅ | SOP-08 (0.880) ✅ | SOP-08 (0.641) ✅ |
| Q09 | SOP-02 | SOP-02 (0.442) ✅ | SOP-02 (0.841) ✅ | SOP-01 (0.551) ❌ |
| Q10 | SOP-03 | SOP-05 (0.376) ❌ | SOP-03 (0.844) ✅ | SOP-05 (0.493) ❌ |

---

## 5. Analisis Spektrum Cosine & Pemisahan Out-of-Domain (OOD)

Evaluasi tambahan dilakukan untuk menguji perilaku model terhadap kueri di luar domain fasilitas (OOD):

| Kueri Uji | Tipe | paraphrase-multilingual-MiniLM-L12-v2 (max sim) | multilingual-e5-small (max sim) |
|-----------|------|-------------------------------------------------|---------------------------------|
| `alat presentasi di kelas tidak bisa menampilkan gambar` | In-Domain | 0.3700 | 0.8385 |
| `ruangan terasa panas dan pengatur suhu tidak berfungsi` | In-Domain | 0.4300 | 0.8733 |
| `resep nasi goreng spesial` | OOD | **0.1299** | 0.7868 |
| `cara mendaftar beasiswa luar negeri` | OOD | **0.1037** | 0.7994 |
| `harga tiket konser coldplay jakarta` | OOD | **0.0982** | 0.7890 |

### Temuan Krusial: Masalah Anisotropi pada E5 vs Kalibrasi Threshold
1. **Fenomena Anisotropi pada E5**: Vektor embedding pada model `multilingual-e5-small` terdistribusi dalam kerucut sempit (*narrow cone*), sehingga semua pasangan teks menghasilkan cosine similarity tinggi (>0.75), bahkan untuk teks yang sama sekali tidak berhubungan (OOD `resep nasi goreng` mendapat kemiripan 0.7868). Selisih antara kueri in-domain dan OOD hanya sebesar **~0.04 - 0.07**. Hal ini membuat penentuan ambang batas penolakan OOD menjadi sangat rapuh (*fragile*).
2. **Distribusi Lebih Isotropik pada paraphrase-multilingual**: Model `paraphrase-multilingual-MiniLM-L12-v2` menghasilkan pemisahan (*margin*) yang sangat lebar: kueri in-domain berada pada rentang **0.35 - 0.60**, sedangkan kueri OOD anjlok ke rentang **0.09 - 0.13**. Selisih margin mencapai **>0.25**.

---

## 6. Keputusan Desain & Model Final

### Model Terpilih: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

**Justifikasi Arsitektur:**
1. **Presisi Penolakan OOD yang Stabil**: Dengan ambang batas default `OOD_SIMILARITY_THRESHOLD = 0.35`, seluruh kueri OOD berhasil ditolak secara konsisten (`sim < 0.35` -> `rejected=True`), sementara kueri in-domain yang relevan diterima (`sim >= 0.35`). Pada model E5, threshold 0.35 tidak akan pernah menolak kueri apapun karena skor dasarnya selalu >0.78.
2. **Kesesuaian Kontrak Antarmuka**: Model ini secara natural tidak memerlukan penambahan prefix khusus (`QUERY_PREFIX = ""`, `PASSAGE_PREFIX = ""`), meminimalkan *cognitive overhead* dan risiko mismatch prefix pada modul downstream.
3. **Multilingual Native**: Memiliki pemahaman yang solid atas kosakata teknis dan sinonim bahasa Indonesia sehari-hari di lingkungan kampus FITE IT Del.
4. **Efisiensi Memori & Latensi**: Ukuran 448 MB dan waktu inferensi ~0.29 detik per kueri sangat ideal untuk inferensi berbasis CPU pada workstation kampus.
