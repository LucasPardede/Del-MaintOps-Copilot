# Korpus Basis Pengetahuan FITE IT Del (Milestone 3)

Direktori ini berisi 15 dokumen Markdown (UTF-8) yang menjadi korpus pencarian semantik
Del-MaintOps Copilot. Setiap file diawali front matter sederhana (`doc_id`, `title`, `doc_type`,
`category`, `default_urgency`, `sla_hours`) yang dibaca oleh `src/knowledge/chunker.py`.
Nama file mengikuti pola `<doc_id>_<slug>.md`.

## Indeks Dokumen

| doc_id | Judul | doc_type | Kategori | Urgensi bawaan | SLA (jam) | Jumlah kata | Jumlah chunk |
|---|---|---|---|---|---|---|---|
| KB-09 | Kebijakan SLA, Prioritas & Eskalasi Tiket | kebijakan | sla | - | 0 | 288 | 3 |
| KB-10 | Keselamatan Kerja (K3) Kelistrikan & Lab | kebijakan | k3 | - | 0 | 267 | 3 |
| KB-11 | Panduan Pelaporan Tiket & Daftar Ruang Valid | panduan | pelaporan | - | 0 | 273 | 3 |
| KB-12 | Kebijakan Penggunaan Lab saat Praktikum & Ujian | kebijakan | praktikum | - | 0 | 254 | 3 |
| KB-13 | Prosedur Perangkat Cadangan & Gudang IT | panduan | inventaris | - | 0 | 270 | 3 |
| KB-14 | Kualifikasi & Pembagian Tugas Teknisi | kebijakan | teknisi | - | 0 | 257 | 3 |
| KB-15 | Siklus Status Tiket & Penanganan Laporan Duplikat | panduan | status_tiket | - | 0 | 262 | 3 |
| SOP-01 | Penanganan Proyektor/Infokus Rusak | sop | proyektor | tinggi | 2 | 284 | 3 |
| SOP-02 | Penanganan AC Tidak Dingin / Bermasalah | sop | ac | sedang | 24 | 287 | 3 |
| SOP-03 | Gangguan Jaringan Komputer / LAN Laboratorium | sop | jaringan | sedang | 24 | 276 | 3 |
| SOP-04 | Kerusakan Fasilitas Penunjang Umum | sop | umum | rendah | 72 | 254 | 3 |
| SOP-05 | Kelistrikan & Panel Server FITE | sop | listrik | tinggi | 2 | 276 | 3 |
| SOP-06 | Komputer Laboratorium & Periferal | sop | pc | sedang | 24 | 261 | 4 |
| SOP-07 | Idea Hub & Layar Presentasi Interaktif | sop | ideahub | tinggi | 2 | 256 | 3 |
| SOP-08 | Kamera Pengawas (CCTV) Laboratorium | sop | cctv | rendah | 72 | 255 | 3 |
| | **Total (15 dokumen)** | | | | | **4020** | **46** |

Catatan metode: "Jumlah kata" dihitung pada badan dokumen setelah cleaning (tanpa front matter dan
tanpa penanda markdown `#`, `-`, `1.`) dengan pemisah whitespace. "Jumlah chunk" adalah hasil
`load_and_chunk_corpus()` dengan parameter bawaan (120 kata, overlap 20 kata, `prepend_title=True`).
Angka dihasilkan dari kode, bukan ditulis manual. Urgensi `-` dan SLA `0` berarti tidak berlaku untuk
dokumen kebijakan/panduan.

## Asal Isi Dokumen (Catatan Jujur)

- **SOP-01 sampai SOP-08** dikonversi dari `SOP_CATALOG` (`src/knowledge/sops.py`) dan bagian SOP lapangan
  pada `docs/04_sops_knowledge_base.md`. Bagian "Tujuan", "Ruang Lingkup", "Eskalasi", "Dokumen Terkait", dan
  "Catatan Lapangan" disusun tim sebagai kerangka penjelas; isinya hanya merangkum fakta yang sudah ada di
  dokumen proyek (kategori, urgensi, SLA, kasus pada 10 tiket dummy, pembagian teknisi).
- **KB-09 sampai KB-15** adalah dokumen baru yang **disusun tim** berdasarkan dokumen proyek
  (`docs/01`, `docs/02`, `docs/04`, `docs/05`, `src/core/models.py`, `src/knowledge/data_loader.py`).
  Dokumen ini bukan salinan regulasi resmi institusi. Penyajian aturan (mis. penggabungan laporan duplikat
  pada KB-15 dan sub-kasus kenaikan prioritas pada KB-12) merupakan perumusan tim atas fakta proyek yang ada.
- Kenaikan prioritas Kritis pada jaringan saat praktikum ditulis sebagai aturan eskalasi tanpa angka SLA
  tersendiri; tabel SLA baku yang dipakai adalah Tinggi 2 jam, Sedang 24 jam, Rendah 72 jam.


## Penegasan Ruang Lingkup Data

Seluruh SOP dan KB pada korpus ini adalah **data asumsi/simulasi yang dibuat kelompok untuk tugas proyek perkuliahan**, bukan regulasi resmi atau SOP institusi yang telah disahkan. Data disusun agar skenario pemeliharaan fasilitas pada proyek dapat diuji secara konsisten. Oleh karena itu, korpus hanya merepresentasikan cakupan skenario proyek akademik. Penggunaan operasional nyata memerlukan validasi dan persetujuan pemilik proses terkait.
