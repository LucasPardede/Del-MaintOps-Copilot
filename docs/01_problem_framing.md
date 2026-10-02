# Bab 1 — Pendahuluan & Latar Belakang Masalah Bisnis
## Del-MaintOps Copilot: Generative AI-Driven Facility Recommendation & Decision Support System for FITE IT Del

### 1.1 Profil Organisasi & Konteks Domain
Fakultas Informatika dan Teknik Elektro (FITE) Institut Teknologi Del mengelola puluhan ruang kelas,
laboratorium (Lab RPL, Lab Jaringan, Lab Elektro, dll.), ruang kolaborasi (Idea Hub), serta fasilitas
penunjang umum (toilet, saung, area LAN publik) yang digunakan ratusan mahasiswa setiap hari.
Setiap ruang bergantung pada perangkat pendukung — proyektor/infokus, pendingin ruangan (AC),
jaringan komputer/LAN, dan furnitur — yang rutin mengalami gangguan operasional.

### 1.2 Rumusan Masalah Bisnis (Pain Points)
Proses pelaporan kerusakan fasilitas di FITE saat ini masih bersifat informal dan tidak terpusat:

1. **Pelaporan tidak terstruktur** — mahasiswa melapor melalui grup WhatsApp, chat pribadi ke staf, atau
   lisan langsung, sehingga tidak ada jejak (log) yang bisa ditelusuri.
2. **Tidak ada mekanisme prioritas** — laporan kerusakan kritis (mis. seluruh jaringan lab mati saat jam
   praktikum) dan laporan non-kritis (mis. satu kursi retak di saung) diperlakukan setara, sehingga
   penanganan sering tidak efisien.
3. **Minim basis pengetahuan terpusat** — staf teknisi baru maupun mahasiswa piket tidak punya akses
   cepat ke SOP penanganan standar per jenis kerusakan, sehingga penanganan tidak konsisten.
4. **Tidak terukur SLA (Service Level Agreement)** — tidak ada pencatatan waktu lapor vs waktu selesai,
   sehingga sulit mengevaluasi kinerja tim fasilitas.
5. **Duplikasi laporan** — kerusakan yang sama dilaporkan berulang oleh mahasiswa berbeda karena tidak
   ada visibilitas status laporan yang sudah masuk.

### 1.3 Justifikasi Solusi AI
Masalah di atas adalah kandidat ideal untuk *agentic AI copilot* karena:
- Melibatkan **penalaran berbasis pengetahuan** (SOP fasilitas) yang cocok untuk pendekatan RAG di
  milestone lanjutan.
- Membutuhkan **pengambilan keputusan terukur** (prioritas tiket) yang dapat diformalkan sebagai
  masalah *search* / optimasi ruang keadaan — fokus Milestone 1 ini.
- Volume laporan cukup tinggi dan repetitif sehingga otomasi percakapan (chat interface) memberi nilai
  efisiensi nyata dibanding proses manual.

### 1.4 Batasan Sistem (Scope)
- **Cakupan lokasi**: hanya gedung FITE (kelas, lab, Idea Hub, toilet, saung, koridor ber-LAN).
- **Cakupan fasilitas**: proyektor/infokus, AC, jaringan/LAN, furnitur ruang, sanitasi.
- **Di luar cakupan Milestone 1**: pengadaan barang baru, anggaran/keuangan, fasilitas gedung selain
  FITE, serta modul RAG/LLM/UI penuh (baru masuk di Milestone 3–5).

### 1.5 Tujuan Proyek (Milestone 1)
1. Merumuskan masalah bisnis secara tajam dan terukur (bagian ini).
2. Mendefinisikan spesifikasi PEAS agen cerdas rekomendasi prioritas perbaikan.
3. Menyusun basis pengetahuan awal berupa draf SOP pemeliharaan fasilitas.
4. Memformalkan ruang keadaan (state space) dan mengimplementasikan algoritma pencarian dasar
   (UCS/A*) untuk menentukan urutan penanganan tiket kerusakan yang optimal.
5. Menyiapkan repositori GitHub profesional sebagai fondasi teknis proyek.

### 1.6 Signifikansi Solusi
Dengan Del-MaintOps Copilot, mahasiswa mendapat kanal pelaporan yang jelas, tim fasilitas mendapat
antrian kerja yang sudah terprioritaskan secara objektif, dan institusi mendapat data terstruktur untuk
evaluasi kinerja pemeliharaan aset FITE ke depannya.
