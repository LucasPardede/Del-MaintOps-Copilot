# Dokumen Standar Operasional Prosedur (SOP) & Alur Penanganan Kerusakan Fasilitas FITE IT Del
*(Basis Pengetahuan Operasional Terpadu Milestone 1 & Milestone 2)*

---

## 1. Alur Logika Sistem Penanganan Kerusakan Fasilitas (Workflow)

Sistem penugasan teknisi dan penyelesaian tiket dirancang dengan hierarki optimasi matematis untuk mencegah pelanggaran batasan operasional. Sistem mengurutkan penyelesaian berdasarkan:

1. **Tingkat Kerusakan (Prioritas Absolut / Hard Constraint)**: Sistem mendahulukan tiket berdampak **Tinggi**, lalu **Sedang**, dan terakhir **Rendah**.
2. **Tanggal & Waktu Request (Tie-Breaker / Soft Constraint)**: Jika terdapat tiket dengan tingkat kerusakan yang sama, sistem menerapkan metode antrean kronologis (**FIFO - First In, First Out**).
3. **Durasi Penanganan (SLA Target)**: Batas waktu maksimal eksekusi ditetapkan sebagai formulasi penalti; sistem akan mengeskalasi tiket jika perbaikan melebihi batas ini.
4. **Standar Operasional Prosedur (SOP)**: Panduan teknis eksekusi akhir yang dilakukan oleh teknisi di lapangan berdasarkan tipe fasilitas.

```
[Laporan Pengguna Masuk]
           │
           ▼
[Filter & Validasi Input Ruang & Fasilitas]
           │
           ▼
[1. Urutkan berdasarkan Tingkat Kerusakan: TINGGI > SEDANG > RENDAH (Hard Constraint)]
           │
           ▼
[2. Jika Tingkat Kerusakan Sama: Urutkan Tanggal & Waktu Request (FIFO / Soft Constraint)]
           │
           ▼
[3. Cek Durasi Penanganan SLA & Penugasan Teknisi Sesuai Keahlian (CSP / GA Optimization)]
           │
           ▼
[4. Teknisi Eksekusi Perbaikan Mengikuti SOP Spesifik di Lapangan]
```

---

## 2. Spesifikasi Form Tiket Kerusakan

### A. Input oleh Pengguna (User)
* **Lokasi (Ruangan)**:
  * **Kelas**: 711, 712, 721, 722.
  * **Labkom**: 713, 714, 715, 716, 723, 724, 725, 726.
* **Fasilitas**: Dipilih sesuai ketersediaan ruangan (`PC`, `LAN`, `Proyektor`, `Idea Hub`, `AC`, `Listrik`, `WiFi`, `Colokan`, `Keyboard`, `CCTV`, dll).
* **Deskripsi Masalah**: Keluhan spesifik dari pengguna.

### B. Dikelola Otomatis oleh Sistem
* **ID Tiket**: Nomor urut unik pencatatan (format: `TK-XXX`).
* **Tanggal & Waktu Request**: Timestamp otomatis saat laporan dikirim pengguna (format ISO: `YYYY-MM-DD HH:MM`).
* **Tingkat Kerusakan**: `Tinggi` / `Sedang` / `Rendah` (di-*mapping* otomatis dari jenis fasilitas & dampak urgensi).
* **Durasi Penanganan (SLA)**: 
  * **2 Jam** (Tingkat Tinggi)
  * **24 Jam** (Tingkat Sedang)
  * **72 Jam** (Tingkat Rendah)

---

## 3. Data Dummy Tiket Kerusakan

Data antrean tugas teknisi ini telah diurutkan oleh sistem menggunakan logika prioritas (**Tingkat Kerusakan > Waktu Request**). Data variabel keputusan ini dapat digunakan langsung dalam pengujian algoritma penyelesaian batasan bisnis Anda.

| Urutan | ID Tiket | Tingkat Kerusakan | Tanggal & Waktu Request | Durasi Penanganan | Lokasi | Fasilitas | Deskripsi Masalah |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **TK-020** | **Tinggi** | 2026-10-02 08:00 | Maksimal 2 Jam | Labkom 725 | Mati Listrik | Korsleting di panel server lab, listrik padam. |
| **2** | **TK-017** | **Tinggi** | 2026-10-02 08:30 | Maksimal 2 Jam | Kelas 711 | Proyektor | Mati total saat kelas berlangsung. |
| **3** | **TK-022** | **Tinggi** | 2026-10-02 09:15 | Maksimal 2 Jam | Kelas 712 | Idea Hub | Layar sentuh hang, presentasi terhenti. |
| **4** | **TK-018** | **Sedang** | 2026-10-02 08:15 | Maksimal 24 Jam | Labkom 714 | PC | 3 unit PC di baris C gagal masuk sistem Windows. |
| **5** | **TK-023** | **Sedang** | 2026-10-02 08:45 | Maksimal 24 Jam | Labkom 714 | AC | AC bocor meneteskan air ke meja PC. |
| **6** | **TK-021** | **Sedang** | 2026-10-02 10:00 | Maksimal 24 Jam | Labkom 716 | LAN | Koneksi terputus di 2 meja pojok belakang. |
| **7** | **TK-024** | **Sedang** | 2026-10-02 11:30 | Maksimal 24 Jam | Kelas 721 | WiFi | Sinyal Access Point mati/tidak terdeteksi. |
| **8** | **TK-019** | **Rendah** | 2026-10-02 07:30 | Maksimal 72 Jam | Kelas 722 | Colokan | 2 slot stop kontak belakang kendor. |
| **9** | **TK-025** | **Rendah** | 2026-10-02 09:30 | Maksimal 72 Jam | Labkom 726 | Keyboard | Tombol spasi macet di PC-15. |
| **10** | **TK-026** | **Rendah** | 2026-10-02 11:00 | Maksimal 72 Jam | Labkom 713 | CCTV | Kamera bergeser menghadap plafon. |

---

## 4. Standar Operasional Prosedur (SOP) Eksekusi Fasilitas

### A. Kelistrikan & Keamanan (Tingkat Tinggi & Rendah)
* **Mati Listrik (SLA 2 Jam - Tinggi)**:
  Teknisi sarpras mengevakuasi mahasiswa dari radius bahaya. Turunkan MCB utama, cari titik beban berlebih, dan ganti sekring/kabel utama yang terbakar. Perbaikan ini **tidak boleh** dilakukan oleh teknisi jaringan demi keselamatan kerja.
* **Colokan (SLA 72 Jam - Rendah)**:
  Matikan arus lokal sementara pada baris meja tersebut. Lakukan bongkar pasang modul stop kontak baru, dan wajib uji tegangan dengan multitester sebelum arus dinyalakan kembali.
* **CCTV (SLA 72 Jam - Rendah)**:
  Lakukan kalibrasi fisik posisi lensa, periksa kelayakan konektor BNC/UTP di ujung kamera, dan pastikan rekam jejak aktif pada DVR/NVR di ruang server pusat.

### B. Visual & Presentasi (Tingkat Tinggi)
* **Proyektor (SLA 2 Jam - Tinggi)**:
  Cek indikator lampu (*Lamp/Temp*) pada perangkat. Bersihkan filter debu jika mesin terpantau *overheating*. Jika *hardware* lampu putus, teknisi wajib segera menyediakan dan menyalakan **Proyektor Portabel Cadangan** agar KBM tetap berjalan.
* **Idea Hub (SLA 2 Jam - Tinggi)**:
  Lakukan *hard restart* sistem. Periksa kelayakan modul kabel input HDMI/Type-C. Jika panel layar pecah atau rusak fisik berat, tutup unit dengan pelindung, arahkan dosen menggunakan fasilitas papan tulis, dan eskalasi tiket ke level pengadaan vendor.

### C. Komputasi & Aksesori (Tingkat Sedang & Rendah)
* **PC & CPU (SLA 24 Jam - Sedang)**:
  Lakukan diagnosa *hardware* dengan mendengar bunyi peringatan (*beep code*) motherboard. Jika sistem operasi *corrupt* atau terkena virus, wajib *backup* data partisi sekunder sebelum *install* ulang. Beri label isolasi merah jika PC harus menunggu suku cadang tambahan (RAM/VGA/PSU).
* **Keyboard & Mouse (SLA 72 Jam - Rendah)**:
  Verifikasi apakah masalah berada pada kerusakan fisik periferal (tombol lepas, optik mati) atau pada port USB CPU. Jika rusak fisik, tarik perangkat cadangan layak pakai dari gudang IT dan langsung lakukan penggantian unit (*plug and play*).

### D. Jaringan & Lingkungan (Tingkat Sedang)
* **LAN & WiFi (SLA 24 Jam - Sedang)**:
  Gunakan alat LAN tester untuk memeriksa kabel fisik, potong dan *crimping* ulang konektor RJ45 jika longgar. Untuk WiFi, lakukan *reboot* pada Access Point (AP), periksa konfigurasi IP di *controller* jaringan pusat, dan jadwalkan penggantian jika AP mati akibat lonjakan tegangan listrik.
* **AC (SLA 24 Jam - Sedang)**:
  Jika AC bocor dan menetes ke perangkat elektronik, teknisi wajib mematikan AC seketika dan memindahkan/mengamankan PC di bawahnya. Cek tekanan freon dan jadwalkan prosedur cuci AC jika penyebabnya adalah kotoran penyumbat saluran air.
