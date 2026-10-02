# Spesifikasi PEAS — Del-MaintOps Copilot

## 1. Performance Measure (Ukuran Kinerja)
Agen dinilai berhasil apabila mampu memaksimalkan/meminimalkan hal berikut:
- **Maksimalkan** ketepatan klasifikasi jenis & tingkat urgensi kerusakan yang dilaporkan.
- **Minimalkan** rata-rata waktu tanggap (*response time*) terhadap tiket berprioritas tinggi (target < 2 jam
  untuk kategori kritis, mis. jaringan lab mati saat praktikum).
- **Maksimalkan** jumlah tiket terselesaikan sesuai SLA per SOP yang berlaku.
- **Minimalkan** total jarak/waktu tempuh teknisi dalam menuntaskan rangkaian tiket harian (efisiensi rute).
- **Minimalkan** duplikasi laporan untuk kerusakan yang sama.
- **Maksimalkan** kepuasan pelapor (mahasiswa) melalui transparansi status tiket.

## 2. Environment (Lingkungan)
Lingkungan operasional agen adalah ekosistem digital-fisik gedung FITE: data laporan mahasiswa,
peta lokasi ruang (kelas, lab, Idea Hub, toilet, saung), status ketersediaan teknisi, dan basis pengetahuan
SOP pemeliharaan.

### Klasifikasi 6 Sifat Lingkungan
| Dimensi | Klasifikasi | Justifikasi |
|---|---|---|
| Observability | **Partially Observable** | Agen hanya mengetahui apa yang dilaporkan pengguna/sensor tiket, tidak melihat langsung kondisi fisik ruangan secara real-time. |
| Determinism | **Stochastic** | Waktu penyelesaian, ketersediaan teknisi, dan tingkat kerusakan aktual bisa berbeda dari estimasi awal. |
| Episodic vs Sequential | **Sequential** | Keputusan prioritas tiket saat ini memengaruhi antrian dan rute penanganan berikutnya. |
| Static vs Dynamic | **Dynamic** | Tiket baru dapat masuk kapan saja saat agen sedang memproses antrian yang ada. |
| Discrete vs Continuous | **Discrete** | Lokasi, jenis kerusakan, dan tingkat urgensi direpresentasikan sebagai himpunan nilai diskret berhingga. |
| Single vs Multi-agent | **Multi-agent (kooperatif)** | Sistem berinteraksi dengan banyak pelapor (mahasiswa) dan beberapa teknisi/staf fasilitas secara bersamaan. |

## 3. Actuators (Aktuator)
Tindakan yang dapat dilakukan agen terhadap lingkungannya:
- Mengirim **notifikasi/tiket terstruktur** ke staf/teknisi terkait.
- Menampilkan **jawaban & rekomendasi SOP** kepada mahasiswa pelapor via antarmuka chat.
- Memperbarui **status tiket** (Reported → Verified → Assigned → In Progress → Resolved).
- Menghasilkan **urutan prioritas antrian perbaikan** (output dari modul search).
- Mengeskalasi tiket ke penanggung jawab yang lebih tinggi jika SLA terlampaui.

## 4. Sensors (Sensor)
Sumber masukan yang dipersepsikan agen:
- **Input teks** dari mahasiswa (laporan/pertanyaan via chat).
- **Metadata laporan**: lokasi ruang, jenis fasilitas, waktu lapor, foto (opsional, untuk milestone OCR).
- **Status antrian tiket** yang sedang berjalan (basis data tiket).
- **Basis pengetahuan SOP** yang telah diindeks (dipakai di milestone RAG lanjutan).
- **Ketersediaan teknisi** (jadwal/status aktif-tidaknya staf pemeliharaan).
