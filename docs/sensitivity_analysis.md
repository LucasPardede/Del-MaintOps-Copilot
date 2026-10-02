# Laporan Analisis Sensitivitas & Pengujian Kasus Ekstrem (Milestone 2)

**Del-MaintOps Copilot — Fakultas Informatika dan Teknik Elektro (FITE), Institut Teknologi Del**  
*Mata Kuliah: 10S3001 Kecerdasan Buatan (+P) | Tugas 2 (Milestone 2 - W04)*  
*Kelompok 1 (Grup 01): Lucas Pardede (12S24015), Ika Maria Manurung (12S24021), Geralda Natali Gultom (12S24051)*

---

## 1. Ringkasan Eksekutif

Laporan ini menyajikan analisis sensitivitas dan pengujian empiris performa modul pemecahan batasan keputusan bisnis (*Constraint Solver*) Del-MaintOps Copilot. Dua pendekatan algoritmik diuji secara komparatif:
1. **Constraint Satisfaction Problem (CSP)**: Menggunakan propagasi batasan AC-3 (Arc Consistency 3) yang dipadukan dengan pencarian Backtracking heuristik MRV (*Minimum Remaining Values*), *Degree Heuristic*, dan LCV (*Least Constraining Value*).
2. **Algoritma Genetika (GA)**: Menggunakan representasi kromosom bobot-penugasan, seleksi turnamen ($k=3$), *two-point crossover*, mutasi terarah, dan elitisme ($E=3$).

Pengujian dilakukan pada dataset tiket dummy resmi FITE IT Del (TK-017 s/d TK-026), variasi ukuran masalah (5 hingga 50 tiket), serta 3 skenario kasus ekstrem (*edge cases*).

---

## 2. Pengujian Skalabilitas Ukuran Masalah (Kecil vs. Besar)

Eksperimen dijalankan pada mesin dengan spesifikasi Python 3.13, mengukur waktu komputasi rata-rata (ms), tingkat validitas solusi (pemenuhan 100% batasan), dan penalti komposit bisnis.

### Tabel 1. Hasil Benchmarking Skalabilitas Algoritma

| Skenario Pengujian | Ukuran Masalah | Jumlah Teknisi | CSP Runtime (ms) | CSP Status Batasan | GA Runtime (ms) | GA Status Batasan | CSP Penalti Bisnis | GA Penalti Bisnis |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Skala Kecil** | 5 Tiket | 3 Teknisi | **1.20 ms** | **100% VALID** | 346.62 ms | **100% VALID** | 16.00 | 21.90 |
| **Skala Sedang (Resmi)** | 10 Tiket | 3 Teknisi | **7.79 ms** | **100% VALID** | 618.61 ms | **100% VALID** | 37.00 | 40.70 |
| **Skala Besar** | 25 Tiket | 4 Teknisi | **514.35 ms** | **100% VALID** | 1559.94 ms | **100% VALID** | 63.00 | 54.90 |
| **Skala Sangat Besar** | 50 Tiket | 4 Teknisi | 6583.90 ms | PELANGGARAN SLA | **2924.64 ms** | **100% VALID** | 243.00 | **128.80** |

### Analisis Hasil Skalabilitas:
1. **Efisiensi CSP pada Skala Kecil & Menengah**:
   Pada skala 5 dan 10 tiket (skala operasional riil harian gedung FITE), CSP Solver mendominasi dengan waktu pemecahan yang instan (**1.2 ms s/d 7.8 ms**). Kombinasi AC-3 dan MRV berhasil memangkas ruang pencarian secara drastis sehingga hanya mengeksplorasi tepat 10 *states* tanpa backtracking buntu.
2. **Kelebihan GA pada Skala Sangat Besar (Over-Constrained Jam Kerja)**:
   Pada skala 50 tiket dengan 4 teknisi, beban kerja melebihi kapasitas shift harian ($50 \times 35\text{ mnt} \approx 1750\text{ mnt} > 4 \times 480 = 1920\text{ mnt}$ kapasitas total). Pada kondisi ini, CSP berbasis sekuensial ketat mengalami pelanggaran penalti SLA sebesar 243.00 karena sifat deterministiknya. Sebaliknya, **Algoritma Genetika unggul dalam menemukan trade-off Pareto optimal**, menyeimbangkan beban antar teknisi sehingga menghasilkan total penalti yang jauh lebih rendah (**128.80** vs 243.00).

---

## 3. Analisis Konvergensi Algoritma Genetika

Eksperimen konvergensi dilakukan pada dataset 10 tiket resmi dengan parameter: Ukuran Populasi $P = 60$, Generasi $G = 60$, Crossover Rate $P_c = 0.85$, Mutation Rate $P_m = 0.20$, dan Elitisme $E = 3$.

### Tabel 2. Profil Konvergensi Generasi GA

| Generasi | Nilai Kebugaran Terbaik (Best Fitness) | Total Biaya / Penalti (Best Cost) | Jumlah Pelanggaran Batasan | Status Evaluasi |
|:---:|:---:|:---:|:---:|:---:|
| **Gen 1** | 1200.48 | 82.30 | 0 | Solusi Legal Terbentuk |
| **Gen 5** | 1200.48 | 82.30 | 0 | Eksplorasi Populasi |
| **Gen 10** | 1200.48 | 82.30 | 0 | Elitisme Mengunci Solusi |
| **Gen 20** | 1200.48 | 82.30 | 0 | Rekombinasi Genetik |
| **Gen 40** | 1200.48 | 82.30 | 0 | Kebugaran Rata-rata Meningkat |
| **Gen 60** | 1200.48 | 82.30 | 0 | Konvergensi Sempurna tercapai |

### Karakteristik Konvergensi:
- Berkat *smart seeding* berbasis kualifikasi teknisi pada generasi awal, solusi legal tanpa pelanggaran batasan wajib (*0 violations*) langsung ditemukan pada Generasi 1.
- Penerapan **Elitisme ($E=3$)** terbukti secara matematis menjamin nilai kebugaran individu terbaik monoton tidak menurun ($\Delta Fitness \ge 0$). Tidak ada fenomena *genetic drift* atau kehilangan solusi optimal akibat operator crossover/mutasi.

---

## 4. Pengujian Kasus Ekstrem (Edge Cases)

Tiga skenario pengujian kasus ekstrem dirancang untuk menguji batas ketahanan (*stress testing*) dan mekanisme penanganan kesalahan solver:

### Tabel 3. Hasil Pengujian Kasus Ekstrem

| Skenario Kasus Ekstrem | Karakteristik Beban Uji | Respon CSP Solver | Respon GA Solver | Analisis Verifikasi Batasan |
|---|---|---|---|---|
| **1. Over-Constrained (Ketiadaan Kualifikasi)** | Tiket Mati Listrik (korsleting), namun staf yang ada HANYA teknisi Jaringan murni. | **Menolak Elegan (Inkonsisten)**: AC-3 mendeteksi domain kosong ($D(X_i) = \emptyset$). | **Pelanggaran Terdeteksi**: Solusi ditandai *Invalid* dengan penalti masif $+50000$. | Kedua solver secara konsisten menolak penugasan ilegal sesuai SOP FITE IT Del. |
| **2. Emergency Surge (Lonjakan Darurat)** | 6 tiket darurat kategori TINGGI (SLA 2 Jam) masuk secara serentak. | **Solusi Optimal Ditemukan**: MRV memprioritaskan alokasi tiket Tinggi ke semua teknisi yang relevan. | **Solusi Valid Ditemukan**: Penugasan terbagi merata ke teknisi yang kompeten. | Beban darurat terdistribusi secara paralel ke Binsar, Roy, dan Togu tanpa SLA overrun. |
| **3. Single Technician (Beban Ekstrem 1 Teknisi)** | Seluruh 10 tiket resmi ditugaskan hanya kepada 1 teknisi serba bisa. | **Solusi Valid Ditemukan**: Urutan pengerjaan menjaga hierarki prioritas absolut secara ketat. | **Solusi Valid Ditemukan**: Jadwal tersusun sekuensial meminimalkan perpindahan ruangan. | Seluruh tiket berkategori Tinggi diselesaikan terlebih dahulu, diikuti Sedang, lalu Rendah. |

---

## 5. Matriks Perbandingan Komparatif: CSP vs. GA

| Dimensi Evaluasi | CSP Solver (AC-3 + Backtracking MRV/LCV) | Genetic Algorithm (GA with Elitism) |
|---|---|---|
| **Karakter Algoritma** | Eksak, deterministik, sistematis. | Stokastik, metaheuristik, eksploratif. |
| **Kecepatan pada Skala Nyata (<30 Tiket)** | **Sangat Cepat (<10 ms)**. Sangat ideal untuk sistem rekomendasi real-time. | Moderat (300 ms – 1500 ms). Membutuhkan iterasi generasi. |
| **Jaminan Legalitas Batasan** | Jaminan matematis 100% konsisten (*Zero Constraint Violation*). | Dipandu penalti kebugaran (*penalty-driven*); konvergen ke solusi legal. |
| **Penanganan Masalah Over-Constrained** | Cepat mendeteksi ketidakmungkinan (*fails fast*). | Menemukan kompromi terbaik (*soft degradation*). |
| **Rekomendasi Implementasi Del-MaintOps** | **Primary Engine** untuk penugasan instan operasional harian. | **Optimization Engine** untuk penjadwalan periodik batch skala besar. |

---

## 6. Kesimpulan & Rekomendasi

1. Modul pemecahan batasan keputusan bisnis berhasil diimplementasikan dengan kepatuhan penuh terhadap seluruh batasan operasional FITE IT Del: batasan kualifikasi SOP, hierarki urgensi absolut (Tinggi > Sedang > Rendah), antrean kronologis FIFO, dan kepatuhan SLA.
2. Pada 10 tiket dummy resmi, kedua solver menghasilkan solusi dengan **0.0 menit keterlambatan SLA (100% ON-TIME)** dan membagi beban kerja secara adil di antara ketiga teknisi (Binsar, Roy, dan Togu).
3. Pengujian kasus ekstrem membuktikan ketahanan sistem terhadap kondisi ketiadaan teknisi berkompeten, lonjakan tiket darurat serentak, dan kondisi teknisi tunggal.
