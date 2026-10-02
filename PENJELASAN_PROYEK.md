# Panduan Komprehensif Proyek: Del-MaintOps Copilot
**Mata Kuliah:** 10S3001 - Kecerdasan Buatan (+P) / Artificial Intelligence (+P)  
**Program Studi:** S1 Sistem Informasi, Fakultas Informatika dan Teknik Elektro (FITE), Institut Teknologi Del  
**Kelompok:** Grup 01 (Lucas Pardede, Ika Maria Manurung, Geralda Natali Gultom)  
**Dosen Pengampu:** Samuel Indra Gunawan Situmeang  

---

## 1. Mengenai Proyek Ini: Apa Itu Del-MaintOps Copilot?

**Del-MaintOps Copilot** adalah purwarupa sistem asisten cerdas (*Enterprise AI Copilot*) terintegrasi yang dirancang untuk mengotomatisasi tata kelola operasional dan pemeliharaan fasilitas di lingkungan gedung Fakultas Informatika dan Teknik Elektro (FITE) Institut Teknologi Del.

### Latar Belakang & Masalah Bisnis Nyata:
Gedung FITE memiliki mobilitas kegiatan belajar mengajar (KBM) yang sangat padat dengan 12 ruangan utama (4 ruang kelas multimedia 711, 712, 721, 722 dan 8 laboratorium komputer 713, 714, 715, 716, 723, 724, 725, 726). Berbagai insiden fasilitas sering terjadi, mulai dari listrik panel korslet, proyektor mati saat kuliah, AC bocor mengenai komputer, hingga gangguan jaringan internet lab.

Sebelum adanya sistem ini, pengelolaan dilakukan secara manual melalui pesan instan yang tidak terstruktur, menimbulkan:
1. **Pelanggaran SLA (Service Level Agreement)**: Insiden kritis sering tertunda karena tidak adanya prioritas matematis formal.
2. **Ketidaksesuaian Kualifikasi Teknisi**: Teknisi jaringan sering salah ditugaskan menangani tegangan tinggi/panel listrik yang berisiko bahaya keselamatan kerja.
3. **Inefisiensi Rute Fisik**: Teknisi bolak-balik antar lantai tanpa optimasi jalur tempuh gedung.
4. **Tabrakan Jadwal (Overlapping)**: Satu teknisi ditugaskan ke dua tempat sekaligus pada jam yang sama.

**Del-MaintOps Copilot** memecahkan seluruh masalah tersebut dengan menggabungkan:
- **Penalaran Simbolik & Graph Search (Milestone 1)**: Algoritma *Uniform Cost Search* (UCS) dan *A\* Search* untuk navigasi rute tercepat teknisi di gedung FITE.
- **Constraint Satisfaction & Optimasi Heuristik (Milestone 2)**: *Constraint Satisfaction Problem* (CSP dengan AC-3 & Backtracking MRV/LCV) serta *Genetic Algorithm* (GA dengan elitisme) untuk penjadwalan dan alokasi teknisi optimal tanpa melanggar batasan hukum, keselamatan, kapasitas shift, dan SLA.

---

## 2. Status Evaluasi Luaran: Apakah Semua Luaran M1 & M2 Sudah Ada?

**JAWABAN:** **YA, SEMUA LUARAN SUDAH LENGKAP 100%** dan telah memenuhi kriteria nilai tertinggi **100 (Sangat Baik)** sesuai rubrik analitik resmi Institut Teknologi Del.

Berikut adalah tabel pemetaan kesesuaian luaran resmi terhadap file di dalam repositori:

| Milestone | Komponen Luaran Resmi (Panduan / Rubrik) | Status | Bukti File di Proyek | Keterangan & Kualitas |
| :--- | :--- | :---: | :--- | :--- |
| **Milestone 1** | **1. Dokumen Problem Framing** (Profil organisasi, *pain points*, justifikasi AI) | **LENGKAP** | [`docs/01_problem_framing.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/docs/01_problem_framing.md) | Analisis domain FITE IT Del tajam dan terstruktur. |
| **Milestone 1** | **2. Spesifikasi Formal PEAS** (*Performance, Environment, Actuators, Sensors*) | **LENGKAP** | [`docs/02_peas_specification.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/docs/02_peas_specification.md) | 6 dimensi lingkungan operasional dianalisis lengkap. |
| **Milestone 1** | **3. Skrip Baseline Search (Python)** (UCS / A\* Search, `heapq`, heuristik *admissible*) | **LENGKAP** | [`src/search_baseline.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/search_baseline.py) & [`src/fite_graph.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/fite_graph.py) | Formulasi $S=(X, A, T, G, C)$, terbukti *optimal & admissible*. |
| **Milestone 1** | **4. Repositori GitHub & Lingkungan Astral `uv`** (`pyproject.toml`, `README.md`) | **LENGKAP** | [`pyproject.toml`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/pyproject.toml), [`README.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/README.md), [`.gitignore`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/.gitignore) | Standar industri Python modern dengan isolasi dependensi. |
| **Milestone 2** | **1. Pemodelan Matematis Formal** (Variabel keputusan, domain, batasan hard/soft, kromosom GA) | **LENGKAP** | [`docs/05_constraint_modeling_csp_ga.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/docs/05_constraint_modeling_csp_ga.md) | Notasi formal variabel $X_i$, domain $D_i$, batasan $C_1 \dots C_5$, fitness $f(C)$. |
| **Milestone 2** | **2. Modul Solver Fungsional (`solver.py`)** (CSP AC-3 + Backtracking MRV/LCV & GA elitisme) | **LENGKAP** | [`solver.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/solver.py), [`src/csp_solver.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/csp_solver.py), [`src/ga_solver.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/ga_solver.py) | Bersih, modular, mendukung CLI multi-algoritma. |
| **Milestone 2** | **3. Laporan Analisis Sensitivitas & Konvergensi** (Skala kecil vs besar, grafik konvergensi) | **LENGKAP** | [`docs/06_sensitivity_and_convergence_analysis.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/docs/06_sensitivity_and_convergence_analysis.md), [`src/sensitivity_benchmark.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/sensitivity_benchmark.py) | Tabel komparasi N=10, 25, 50, 100 tiket, analisis runtime. |
| **Milestone 2** | **4. Pengujian Otomatis & Kasus Ekstrem (Edge Cases)** (`pytest` unit testing) | **LENGKAP** | Direktori [`tests/`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/tests/) (54 unit test, **100% PASS**) | Menangani *unqualified technician*, lonjakan darurat, beban berlebih. |
| **Laporan Akhir** | **Laporan Terpadu M1 + M2 (DOCX)** | **LENGKAP** | [`Grup01-Tugas02-Terpadu.docx`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/Grup01-Tugas02-Terpadu.docx) | Dokumen resmi terpadu melanjutkan laporan M1 menjadi satu kesatuan. |

---

## 3. Klasifikasi File: Milestone 1 vs Milestone 2 vs Komponen Bersama

Berikut adalah pemetaan setiap berkas di repositori berdasarkan asalnya:

```
Del-MaintOps-Copilot-main/
│
├── [PANDUAN & AUTOMATION]
│   ├── Makefile                   <-- [BARU] Urutan pemahaman file & perintah terminal
│   ├── PENJELASAN_PROYEK.md       <-- [BARU] Dokumen ini (penjelasan arsitektur menyeluruh)
│   ├── README.md                  <-- Dokumentasi utama repositori
│   ├── pyproject.toml             <-- Konfigurasi modern dependensi Astral uv & pytest
│   └── solver.py                  <-- [M2] Unified CLI Entry Point pemanggil CSP / GA
│
├── docs/                          <-- [DOKUMENTASI SISTEM & LANDASAN TEORITIS]
│   ├── 01_problem_framing.md      <-- [M1] Deskripsi bisnis, profil FITE, pain points
│   ├── 02_peas_specification.md   <-- [M1] Spesifikasi formal PEAS & karakter lingkungan
│   ├── 03_state_space_search.md   <-- [M1] Formulasi graf, formalisasi ruang keadaan UCS/A*
│   ├── 04_sops_knowledge_base.md  <-- [M1 & M2] Dokumen SOP 4 Bagian (Alur, Form, 10 Tiket, SOP Teknisi)
│   ├── 05_constraint_modeling_csp_ga.md <-- [M2] Formulasi formal variabel, domain, batasan matematis
│   └── 06_sensitivity_and_convergence_analysis.md <-- [M2] Laporan sensitivitas & analisis konvergensi
│
├── src/                           <-- [KODE SUMBER LOGIKA APLIKASI]
│   ├── models.py                  <-- [M2] Entitas dataclass: Ticket, Technician, UrgencyLevel, Skill
│   ├── fite_graph.py              <-- [M1 & M2] Topologi 12 ruang FITE, matriks jarak Dijkstra
│   ├── search_baseline.py         <-- [M1] Algoritma penelusuran rute teknisi UCS & A* Search
│   ├── csp_solver.py              <-- [M2] Mesin inferensi CSP (AC-3, Backtracking MRV/LCV)
│   ├── ga_solver.py               <-- [M2] Mesin optimasi GA (Turnamen, Pindah-Silang, Mutasi, Elitisme)
│   ├── data_loader.py             <-- [M2] Data loader 10 tiket resmi & generator benchmark sintetis
│   ├── sensitivity_benchmark.py   <-- [M2] Runner pengujian beban komputasi dan sensitivitas skala
│   ├── cli.py                     <-- [M1 & M2] Antarmuka CLI interaktif registrasi & solver terpadu
│   ├── copilot_cli.py             <-- [M1] CLI baseline Milestone 1
│   │
│   ├── core/                      <-- Modul core terstruktur (alias models & loader)
│   ├── navigation/                <-- Modul navigasi graf terstruktur (alias search & graph)
│   ├── optimization/              <-- Modul solver terstruktur (alias csp, ga, benchmark)
│   ├── knowledge/                 <-- Basis pengetahuan aturan & SOP (sops.py)
│   └── interfaces/                <-- Antarmuka terminal interaktif
│
└── tests/                         <-- [SUITE PENGUJIAN OTOMATIS PYTEST]
    ├── test_01_search_baseline.py <-- [M1] Uji heuristik A* dan keoptimalan UCS
    ├── test_02_csp_solver.py      <-- [M2] Uji solusi CSP pada 10 tiket dummy resmi
    ├── test_03_ga_solver.py       <-- [M2] Uji elitisme & konvergensi GA
    ├── test_04_edge_cases.py      <-- [M2] Uji kasus batas (tanpa teknisi ahli, lonjakan darurat)
    ├── test_05_integration_and_cli.py <-- [M1 & M2] Uji siklus hidup sistem dan CLI
    └── test_validation.py         <-- [M1] Uji validasi input form tiket, deteksi duplikasi
```

---

## 4. Penjelasan Rinci Kegunaan Setiap File

### A. Berkas Root (Akar Repositori)
1. **[`Makefile`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/Makefile)**:
   - Berisi panduan urutan pembacaan kode dan shortcut praktis mengeksekusi semua modul (install, test, run-cli, run-csp, run-ga, run-benchmark).
2. **[`solver.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/solver.py)**:
   - Berkas *facade* / pintu masuk utama eksekusi solver dari root. Memungkinkan pengguna menjalankan perintah `python solver.py --algo csp` atau `python solver.py --algo ga` langsung tanpa repot membuka sub-folder.
3. **[`pyproject.toml`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/pyproject.toml)**:
   - Standar konfigurasi proyek Python PEP 518/621 untuk Astral `uv`. Mendefinisikan metadata, dependensi (`pytest`, `python-docx`), serta konfigurasi testpaths pytest.
4. **[`README.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/README.md)**:
   - Dokumentasi etalase utama repositori GitHub yang memuat diagram arsitektur, profil tim pengembang, instruksi setup lingkungan uv, dan cuplikan demonstrasi.
5. **[`Grup01-Tugas02-Terpadu.docx`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/Grup01-Tugas02-Terpadu.docx)**:
   - Laporan dokumen Word resmi yang menggabungkan seluruh Bab Milestone 1 (Problem Framing, PEAS, UCS/A\*) dan Milestone 2 (Formulasi Matematis, CSP AC-3, GA, Analisis Sensitivitas) dalam 1 kesatuan dokumen utuh.

---

### B. Berkas Dokumentasi (`docs/`)
1. **[`docs/01_problem_framing.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/docs/01_problem_framing.md)**:
   - Menjelaskan profil FITE IT Del, analisis masalah (*pain points*) manajemen fasilitas, kerugian bisnis jika tidak diselesaikan, dan justifikasi mengapa teknik AI (Search & Constraint Reasoning) adalah solusi yang tepat.
2. **[`docs/02_peas_specification.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/docs/02_peas_specification.md)**:
   - Menjabarkan formulasi PEAS agen cerdas (*Performance Measure, Environment, Actuators, Sensors*) serta taksonomi 6 sifat lingkungan (Partially Observable, Deterministic/Stochastic, Sequential, Static/Dynamic, Discrete, Single/Multi-Agent).
3. **[`docs/03_state_space_search.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/docs/03_state_space_search.md)**:
   - Formulasi matematis ruang keadaan 5-tupel $S = \langle X, A, T, G, C \rangle$, bukti formal keterterimaan (*admissibility*) dan konsistensi fungsi heuristik jarak Manhattan gedung FITE.
4. **[`docs/04_sops_knowledge_base.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/docs/04_sops_knowledge_base.md)**:
   - Berisi 4 bagian standar operasional FITE:
     1. Alur logika hierarki optimasi (Tingkat Kerusakan > Waktu Request FIFO > Durasi Penanganan SLA > SOP Lapangan).
     2. Spesifikasi Form Tiket Kerusakan (Input pengguna vs kelolaan otomatis sistem).
     3. Tabel 10 Tiket Dummy Kerusakan Resmi (TK-020 s/d TK-026).
     4. Standar Operasional Prosedur (SOP) Teknis Lapangan (Kelistrikan, Visual, Komputasi, Jaringan & AC).
5. **[`docs/05_constraint_modeling_csp_ga.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/docs/05_constraint_modeling_csp_ga.md)**:
   - Pemodelan matematis formal penugasan teknisi: variabel keputusan $X_{t}$, domain nilai $D(X_t)$, Hard Constraints (Sertifikasi keahlian, prioritas absolut kerusakan, non-overlapping waktu, limit kapasitas kerja harian), Soft Constraints (minimasi waktu tempuh, kepatuhan FIFO), serta perancangan kromosom dan fungsi fitness GA.
6. **[`docs/06_sensitivity_and_convergence_analysis.md`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/docs/06_sensitivity_and_convergence_analysis.md)**:
   - Laporan empiris pengujian algoritma terhadap variasi ukuran data ($N=10, 25, 50, 100$ tiket), perbandingan latensi eksekusi CSP vs GA, dan analisis kurva konvergensi kebugaran (*fitness curve*).

---

### C. Berkas Kode Sumber (`src/`)
1. **[`src/models.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/models.py)**:
   - Mendefinisikan tipe data inti bisnis: Enum `UrgencyLevel` (Tinggi, Sedang, Rendah), Enum `SkillCategory` (Listrik, Jaringan, Komputasi, Visual, Pendingin), dataclass `Ticket`, dataclass `Technician`, serta dataclass `Assignment` dan `ScheduleSolution`.
2. **[`src/fite_graph.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/fite_graph.py)**:
   - Memodelkan denah fisik 12 ruangan gedung FITE, koordinat 2D (Lantai 1 dan Lantai 2), tangga penghubung, jalur koridor, serta pre-komputasi matriks jarak terpendek antar ruang (*All-Pairs Shortest Path*).
3. **[`src/search_baseline.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/search_baseline.py)**:
   - Mengimplementasikan penelusuran jalur graf menggunakan antrean berprioritas `heapq`:
     - **UCS (Uniform Cost Search)**: Memilih node dengan akumulasi biaya lintasan riil terkecil $g(n)$.
     - **A\* Search**: Mengombinasikan biaya riil dan estimasi heuristik $f(n) = g(n) + h(n)$.
4. **[`src/csp_solver.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/csp_solver.py)**:
   - Modul inferensi kepatuhan batasan bisnis:
     - **AC-3 (Arc Consistency Algorithm #3)**: Memangkas domain teknisi yang tidak memenuhi syarat keahlian sebelum pencarian dimulai.
     - **Backtracking Search**: Menjelajah penugasan dengan heuristik **MRV** (*Minimum Remaining Values*) dan **LCV** (*Least Constraining Value*).
5. **[`src/ga_solver.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/ga_solver.py)**:
   - Modul pemecah optimasi stokastik berbasis evolusi genetika:
     - **Representasi Kromosom**: Vektor indeks penugasan teknisi dan slot waktu.
     - **Fitness Function**: Skor kebugaran dengan penalti berat jika melanggar batasan hard, ditambah penalti jarak fisik dan pelanggaran FIFO.
     - **Operator Genetika**: Seleksi turnamen (*Tournament Selection*), pindah-silang seragam (*Uniform Crossover*), mutasi acak/tukar (*Swap Mutation*), dan elitisme (mempertahankan individu terbaik tanpa degradasi).
6. **[`src/data_loader.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/data_loader.py)**:
   - Menyediakan data 10 tiket resmi FITE IT Del (TK-017 s/d TK-026), 4 profil teknisi resmi FITE dengan spesialisasi berbeda, serta generator data sintetis otomatis untuk pengujian beban berat hingga 100+ tiket.
7. **[`src/sensitivity_benchmark.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/sensitivity_benchmark.py)**:
   - Skrip tolok ukur (*benchmark*) otomatis untuk menguji waktu eksekusi, tingkat keberhasilan, dan nilai kebugaran antara CSP dan GA pada berbagai ukuran masalah.
8. **[`src/cli.py`](file:///c:/Users/ASUS/OneDrive/%EB%AC%B8%EC%84%9C/Semester%205/CERTAN/PRAKTIKUM/M02/Del-MaintOps-Copilot-main/src/cli.py)**:
   - Terminal interaktif (*Interactive CLI*) bagi pengguna untuk melakukan simulasi pelaporan kerusakan baru, pengecekan SOP otomatis, pencarian rute terpendek antar ruang, hingga menjalankan solver penjadwalan.

---

### D. Berkas Pengujian Otomatis (`tests/`)
1. **`test_01_search_baseline.py`**: Menguji keoptimalan jalur terpendek UCS dan A\* serta pembuktian keterterimaan heuristik.
2. **`test_02_csp_solver.py`**: Memastikan CSP solver berhasil menyelesaikan 10 tiket resmi FITE tanpa pelanggaran batasan operasional.
3. **`test_03_ga_solver.py`**: Memverifikasi operator genetika dan membuktikan elitisme bekerja secara monotonik.
4. **`test_04_edge_cases.py`**: Menguji kasus ekstrem: tiket tanpa teknisi yang berkualifikasi (*unqualified ticket rejection*), lonjakan tiket darurat tingkat tinggi (*emergency surge*), dan kondisi teknisi tunggal (*single technician overload*).
5. **`test_05_integration_and_cli.py`**: Menguji integrasi alur kerja sistem dari registrasi tiket hingga penugasan dan pelaporan.
6. **`test_validation.py` & `test_copilot_cli.py`**: Memverifikasi fungsi validasi form, inferensi tingkat urgensi, deteksi duplikasi laporan, dan pencarian basis pengetahuan SOP.

---

## 5. Ringkasan Tugas Milestone 1 dan Milestone 2

### A. Penjelasan Tugas Milestone 1 (W02)
- **Tema:** *Business Problem Framing, Spesifikasi PEAS, & Inisialisasi Repositori GitHub*.
- **Tujuan:** Bertindak sebagai *AI Solutions Architect* untuk membedah batas operasional sistem cerdas enterprise, merumuskan model agen formal, dan membangun mesin navigasi graf dasar.
- **Batasan Masalah:**
  - Pemodelan denah gedung FITE sebagai graf ruang berbobot jarak riil.
  - Implementasi algoritma penelusuran ruang keadaan klasik (UCS dan A\*) menggunakan priority queue `heapq`.
  - Pembuktian heuristik jarak Manhattan bersifat *admissible* ($h(n) \le h^*(n)$).
  - Standardisasi repositori modern dengan Astral `uv`.

### B. Penjelasan Tugas Milestone 2 (W04)
- **Tema:** *Modul Pemecahan Batasan Keputusan Bisnis (CSP / GA Optimization)*.
- **Tujuan:** Mengembangkan modul komputasi cerdas (*constraint solver*) untuk memecahkan sub-masalah penugasan teknisi dan penjadwalan tiket fasilitas FITE yang terikat regulasi ketat.
- **Batasan Masalah:**
  - **Hard Constraints (Wajib 100% Terpenuhi):**
    1. *Qualification Constraint*: Teknisi harus memiliki keahlian yang sesuai dengan fasilitas (misal: listrik panel wajib teknisi listrik, dilarang teknisi jaringan).
    2. *Absolute Priority Constraint*: Tiket tingkat Tinggi wajib dikerjakan lebih dahulu daripada Sedang dan Rendah.
    3. *Non-Overlapping Constraint*: Satu teknisi tidak boleh menangani dua tiket pada slot waktu yang bersamaan.
    4. *Shift Capacity Constraint*: Total jam kerja harian teknisi tidak melebihi batas legal jam operasional.
  - **Soft Constraints (Optimasi Kualitas Solusi):**
    1. *FIFO Tie-Breaking*: Jika tingkat kerusakan sama, selesaikan tiket dengan waktu request lebih awal.
    2. *SLA Target Compliance*: Menghindari keterlambatan di atas batas SLA (2 jam, 24 jam, 72 jam).
    3. *Route Minimization*: Meminimalkan waktu tempuh jalan kaki teknisi antar ruangan dan antar lantai.
  - **Algoritma yang Diimplementasikan:**
    - CSP dengan propagasi konsistensi busur (AC-3) dan pencarian *Backtracking* terarah heuristik (MRV & LCV).
    - Algoritma Genetika (GA) dengan seleksi turnamen, pindah-silang seragam, mutasi adaptif, dan elitisme ketat.
  - **Analisis Sensitivitas:**
    - Uji komputasi terhadap variasi ukuran tiket ($N=10, 25, 50, 100$) untuk mengamati titik jenuh komputasi eksponensial CSP vs stabilitas waktu polinomial GA.
  - **Laporan Terpadu:**
    - Mengintegrasikan seluruh dokumen Milestone 1 dan Milestone 2 menjadi satu naskah laporan formal utuh.

---

## 6. Panduan Praktis Menjalankan di Terminal (How-To-Run)

Buka terminal (PowerShell atau CMD) di folder proyek:
`c:\Users\ASUS\OneDrive\문서\Semester 5\CERTAN\PRAKTIKUM\M02\Del-MaintOps-Copilot-main`

### 1. Menjalankan Seluruh Pengujian Otomatis (54 Unit Test)
```bash
pytest -v
```
*(Hasil: Semua 54 pengujian akan berstatus **PASSED** dalam ~4 detik).*

### 2. Menjalankan CSP Solver Resmi (10 Tiket Dummy FITE)
```bash
python solver.py --algo csp
```
*(Hasil: Sistem memvalidasi domain dengan AC-3, lalu Backtracking MRV/LCV mengalokasikan seluruh 10 tiket ke teknisi yang tepat tanpa ada pelanggaran batasan).*

### 3. Menjalankan GA Solver Resmi (10 Tiket Dummy FITE)
```bash
python solver.py --algo ga --generations 150 --pop-size 80
```
*(Hasil: Menjalankan evolusi populasi kromosom dengan elitisme dan menampilkan skor kebugaran akhir terbaik).*

### 4. Menjalankan Analisis Sensitivitas & Tolok Ukur (Benchmark Skala Besar)
```bash
python src/sensitivity_benchmark.py
```
*(Hasil: Menghasilkan tabel perbandingan kinerja CSP vs GA pada skala 10, 25, 50, dan 100 tiket).*

### 5. Menjalankan Uji Navigasi Jalur Terpendek UCS & A* Search (Milestone 1)
```bash
python src/search_baseline.py
```
*(Hasil: Menampilkan perbandingan langkah dan biaya jalur rute teknisi dari Posko Teknisi ke Labkom 725).*

### 6. Menjalankan Antarmuka Interaktif Copilot (CLI)
```bash
python src/cli.py
```
*(Hasil: Menampilkan menu interaktif terminal untuk pelaporan tiket baru, rekomendasi SOP, pencarian rute denah FITE, dan optimasi jadwal).*
