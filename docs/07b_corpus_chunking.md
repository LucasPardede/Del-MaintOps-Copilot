# 07b — Korpus, Prapemrosesan & Chunking (Milestone 3)

> **Pemilik dokumen**: Ika Maria Manurung (12S24021) — Data Modeler & Knowledge Engineer
> **Rubrik**: Korpus & Prapemrosesan (bobot 25%)
> **Kode terkait**: `data/corpus/`, `src/knowledge/chunker.py`, `src/knowledge/sops.py`

---

## 1. Pemilihan dan Representativitas Korpus

Korpus terdiri atas **15 dokumen** Markdown UTF-8 di `data/corpus/` (indeks lengkap dan jumlah kata ada di `data/corpus/README.md`). Dokumen dibagi menjadi dua kelompok yang sengaja dibuat saling berkaitan agar kueri ambigu yang realistis dapat diuji.

| Kelompok | Dokumen | Isi |
|---|---|---|
| SOP fasilitas (`doc_type: sop`) | SOP-01 s.d. SOP-08 | Proyektor, AC, Jaringan/LAN, Fasilitas Umum, Kelistrikan & Panel Server, Komputer Lab & Periferal, Idea Hub, CCTV |
| Kebijakan/panduan (`kebijakan`, `panduan`) | KB-09 s.d. KB-15 | SLA & eskalasi, K3 kelistrikan, pelaporan tiket & ruang valid, penggunaan lab saat praktikum/ujian, perangkat cadangan & gudang IT, kualifikasi teknisi, siklus status tiket & laporan duplikat |

Representativitas didasarkan pada cakupan domain, bukan jumlah dokumen:

- **Seluruh jenis fasilitas** pada `FACILITY_SPECS` (listrik, proyektor, Idea Hub, PC, AC, LAN, WiFi, colokan, keyboard, CCTV, saung, toilet) memiliki dokumen prosedur.
- **Ketiga tingkat urgensi baku** (Tinggi 2 jam, Sedang 24 jam, Rendah 72 jam) dan tingkat Kritis muncul pada dokumen.
- **Tumpang tindih antar-dokumen yang disengaja**, misalnya jaringan saat praktikum (SOP-03 dan KB-12), AC di ruang ujian (SOP-02 dan KB-12), proyektor cadangan (SOP-01 dan KB-13), serta larangan teknisi jaringan mengerjakan listrik (SOP-05, KB-10, KB-14). Ini menghasilkan kueri ambigu yang jawabannya terletak pada lebih dari satu dokumen.
- Total **4020 kata** (dihitung dengan kode, lihat README korpus); tiap dokumen 254–288 kata.

**Batasan yang perlu diakui**: korpus berskala kecil (15 dokumen, 46 chunk pada parameter bawaan) dan SOP-01..08 serta KB-09..15 disusun tim dari dokumen proyek, bukan dari regulasi institusi yang sesungguhnya. Hasil benchmark karenanya mengukur kualitas pipeline pada domain proyek ini, bukan kesiapan produksi.

## 2. Perbaikan Konsistensi Data

Sebelum dikonversi menjadi korpus, `src/knowledge/sops.py` dibandingkan dengan `docs/04_sops_knowledge_base.md` (acuan otoritatif: tabel SLA Tinggi 2 jam, Sedang 24 jam, Rendah 72 jam), `docs/05_constraint_modeling_csp_ga.md`, dan `src/core/models.py`.

### 2.1 Yang diubah (hanya string `sla` pada `sops.py`; nilai `sla_hours` tidak berubah)

| SOP | Sebelum | Sesudah | Alasan |
|---|---|---|---|
| SOP-02 | `"4 jam kerja"` (`sla_hours` 24) | `"24 jam"` | Bertentangan dengan `sla_hours` 24 dan SLA Sedang 24 jam. |
| SOP-03 | `"1 jam (kritis saat praktikum) / 4 jam (di luar jam praktikum)"` (`sla_hours` 24) | `"24 jam (dinaikkan ke prioritas kritis dan dieskalasi langsung ke admin jaringan saat praktikum)"` | Angka 1 jam dan 4 jam bertentangan dengan SLA Sedang 24 jam. Kenaikan ke Kritis kini berupa aturan eskalasi (narasi) tanpa angka. |
| SOP-04 | `"1-3 hari kerja"` (`sla_hours` 72) | `"72 jam"` | Temuan tambahan: "hari kerja" dapat melampaui 72 jam bila melewati akhir pekan, sehingga tidak setara dengan SLA Rendah 72 jam. |

Dampak pada test: `pytest -v` menghasilkan **54 passed** sebelum dan sesudah perubahan. Tidak ada test yang bergantung pada string lama; satu-satunya pemakai `sop["sla"]` adalah tampilan CLI (`src/cli.py`).

### 2.2 Inkonsistensi yang ditemukan tetapi tidak diubah (menunggu keputusan)

| Temuan | Rincian | Perlakuan di korpus |
|---|---|---|
| SOP-05 vs docs/04 | Kata kunci SOP-05 memuat "colokan", tetapi docs/04 dan `FACILITY_SPECS` menetapkan Colokan = Rendah/72 jam, sedangkan `sops.py` menetapkan SOP-05 = Tinggi/2 jam. | Front matter SOP-05 mengikuti `sops.py` (tinggi, 2). Isi dokumen memisahkan: mati listrik/korsleting = Tinggi, colokan kendor = Rendah 72 jam. |
| SOP-06 vs docs/04 | SOP-06 (24 jam, Sedang) memuat keyboard/mouse, tetapi docs/04 menetapkan Keyboard & Mouse = Rendah/72 jam. | Front matter mengikuti `sops.py`; isi dokumen menyebut periferal ringan sebagai Rendah 72 jam. |
| CCTV | docs/04 menempatkan CCTV pada bagian "Kelistrikan & Keamanan", sedangkan `data_loader.py` dan `FACILITY_SPECS` mensyaratkan keahlian Jaringan. | Korpus mengikuti kode (ditangani teknisi jaringan, Roy). |
| SLA Kritis | `models.py` menetapkan Kritis = 1 jam, sedangkan docs/02 menyebut target "< 2 jam" untuk kategori kritis. | Korpus hanya menulis bahwa target Kritis lebih ketat daripada 2 jam, tanpa angka tunggal. |

## 3. Prapemrosesan (Cleaning)

Dilakukan pada dua tingkat. Pertama, pemeriksaan file korpus dengan skrip: UTF-8 murni (tanpa BOM), tanpa CR, tab, atau spasi di ujung baris, tanpa baris kosong ganda, bentuk Unicode NFC, tanpa karakter non-ASCII, dan istilah seragam ("Labkom 725", "SLA", "MCB", "Access Point (AP)"). Hasil pemeriksaan: tidak ada pelanggaran.

Kedua, fungsi `clean_text()` di `chunker.py` yang dipanggil setiap `chunk_document()`:

1. Normalisasi Unicode ke NFC.
2. Newline seragam (`\r\n` dan `\r` menjadi `\n`); tab dan spasi tak-pecah menjadi spasi; karakter lebar-nol dibuang.
3. Spasi berlebih dalam baris dipadatkan; spasi di ujung baris dibuang; tiga baris kosong atau lebih dipadatkan menjadi satu.
4. Penanda markdown (`##`, `-`, `1.`) dibuang saat segmentasi blok, sehingga embedding tidak terpengaruh simbol.

Loader juga menolak file dengan karakter mojibake dan melaporkan front matter rusak dengan pesan yang menyebut nama file dan baris/kolom bermasalah.

## 4. Skema Metadata dan Alasannya untuk Hybrid Search

Setiap chunk membawa metadata (semua bertipe `str`/`int`, sesuai batasan ChromaDB):

| Field | Tipe | Fungsi pada hybrid search |
|---|---|---|
| `doc_id` | str | Menelusuri dokumen sumber dan mengevaluasi hit pada benchmark (`expected_doc_ids`). |
| `title` | str | Tampilan hasil dan prefiks konteks chunk. |
| `doc_type` | str | Filter `sop` / `kebijakan` / `panduan`, misalnya hanya aturan kebijakan. |
| `category` | str | Filter per kategori fasilitas (`listrik`, `jaringan`, dst.) saat jenis fasilitas sudah diketahui dari form tiket. |
| `default_urgency` | str | Filter dan konteks urgensi untuk RAG; `-` untuk dokumen kebijakan. |
| `sla_hours` | int | Filter numerik dan konteks SLA; `0` bila tidak berlaku. |
| `source_file` | str | Keterlacakan ke file sumber. |
| `chunk_index` | int | Urutan chunk, untuk merangkai ulang konteks yang berdekatan. |

Karena form tiket sudah mengetahui fasilitas, kategori dan urgensi dapat dipakai sebagai filter eksak sehingga pencarian semantik bekerja pada ruang kandidat yang lebih sempit.

## 5. Algoritma Chunking (Word-Aware Recursive + Overlap)

`chunk_document()` memotong dari satuan terbesar ke terkecil:

1. **Blok**: teks dipecah menjadi heading, paragraf, dan item daftar. Teks heading dijadikan prefiks ("Prosedur: ...") pada blok berikutnya sehingga heading tidak pernah menjadi ujung chunk dan chunk tetap tahu bagiannya.
2. **Kalimat**: blok yang tidak muat dalam satu chunk dipecah per kalimat.
3. **Kata**: hanya kalimat yang melebihi ukuran chunk yang dipecah per kata, dengan potongan berukuran seimbang. Pada korpus ini tidak ada kalimat sepanjang itu (kalimat terpanjang 32 kata), sehingga langkah ini tidak pernah aktif pada parameter bawaan.

Blok atau kalimat dikemas secara greedy hingga mendekati `chunk_size_words`. **Overlap**: ekor chunk sebelumnya dibawa ke awal chunk berikutnya, maksimal `overlap_words` kata, dibulatkan ke batas kalimat. Bila kalimat terakhir lebih panjang dari batas overlap, diambil ekor kata yang dimajukan ke batas klausa (setelah koma/titik koma) bila ada. Overlap dipangkas otomatis bila membuat chunk melebihi ukuran.

**Penanganan singkatan**: pemisah kalimat tidak memotong setelah `mis.`, `dsb.`, `dll.`, `dst.`, `Lt.`, `No.`, `sdh.` dan singkatan serupa, maupun setelah inisial satu huruf dan titik yang diikuti huruf kecil. Contoh dari korpus: "(mis. Saung 2, Toilet Pria Lt. 1)" tetap utuh dalam satu kalimat. Konsekuensinya konservatif: bila singkatan berada di akhir kalimat sebenarnya dan diikuti huruf besar, dua kalimat tergabung (tidak pernah terpotong salah).

**Properti**: ukuran dihitung dalam kata (whitespace) dan mencakup overlap; prefiks `Judul: <title>.` tidak dihitung; keluaran deterministik; parameter divalidasi (`chunk_size_words > 0`, `0 <= overlap < chunk_size_words`).

### Hasil pada parameter bawaan (120 kata, overlap 20, `prepend_title=True`)

Dari `python src/knowledge/chunker.py`:

| Metrik | Nilai |
|---|---|
| Dokumen / chunk | 15 / 46 (3 chunk per dokumen, SOP-06 empat) |
| Kata per chunk (isi tanpa prefiks) | min 28, rata-rata 95,8, maks 119 |
| Chunk kosong / metadata bertipe tidak valid / melebihi ukuran | 0 / 0 / 0 |
| Chunk yang berakhir bukan di batas kalimat | 0 |
| Overlap terukur antar-chunk berurutan | rata-rata 12,5 kata; 0 dari 31 pasangan tanpa overlap; tidak ada yang melebihi 20 kata |
| Chunk (indeks > 0) yang overlapnya tidak berawal di awal kalimat | 2 dari 31 |

Statistik korpus yang relevan: 278 kalimat, rata-rata 14,5 kata (median 14, p90 22, maks 32); 164 blok, rata-rata 24,5 kata (maks 97).

**Catatan kualitas (keterbatasan yang diketahui)**: karena blok dijaga utuh, chunk dapat lebih kecil bila blok berikutnya tidak muat; contohnya SOP-06-c000 hanya 28 kata. Lima dari 46 chunk berisi kurang dari 60 kata. Pada ukuran chunk 20 kata (uji kasus ekstrem), 36 chunk berakhir di tengah kalimat karena banyak kalimat lebih panjang dari 20 kata; hal ini wajar dan menegaskan bahwa ukuran chunk perlu di atas panjang kalimat tipikal.

## 6. Justifikasi Parameter Chunking

> **STATUS: BAGIAN ANGKA MENUNGGU EKSPERIMEN GERALDA.** Pada saat penulisan, `docs/chunking_experiment_results.md` belum tersedia. Angka perbandingan Hit@k, cosine target, dan pengaruh `prepend_title` akan diisi dari file tersebut setelah ada; tidak ada angka eksperimen yang ditulis di sini.

### 6.1 Argumen teoretis

- **Chunk terlalu besar**: satu vektor harus meringkas banyak topik sehingga makna kabur (vektor mendekati rata-rata topik), skor cosine ke kueri spesifik turun, dan konteks yang dikirim ke LLM pada RAG memuat noise.
- **Chunk terlalu kecil**: satu langkah prosedur atau satu kondisi eskalasi terpisah dari konteks (misalnya prasyarat atau pengecualian), sehingga makna terputus dan banyak chunk menjadi mirip satu sama lain.
- **Overlap**: informasi di batas chunk (misalnya akhir satu langkah dan awal langkah berikutnya) muncul di dua chunk sehingga tidak hilang. Overlap terlalu besar menggandakan teks dan jumlah vektor tanpa informasi baru; di sini overlap dibatasi sekitar 1–2 kalimat.
- **Batas wajar kapasitas model**: model sentence-transformer memiliki panjang urutan maksimum; teks di luar batas dipotong diam-diam sebelum di-embed. **Risiko yang perlu diverifikasi Lucas/Geralda**: panjang maksimum `paraphrase-multilingual-MiniLM-L12-v2` yang tercatat pada model card adalah 128 token sub-kata, dan 120 kata bahasa Indonesia ditambah prefiks judul kemungkinan melampaui itu. Hal ini belum saya ukur (model tidak diunduh di lingkungan ini) dan harus dicek dengan `model.max_seq_length` serta jumlah token chunk nyata. Bila terbukti, ukuran 120 kata bukan pilihan yang aman dan eksperimen ukuran yang lebih kecil (misalnya 60–80 kata) menjadi sangat relevan.
- **Struktur korpus**: kalimat rata-rata 14,5 kata dan blok rata-rata 24,5 kata, jadi 120 kata setara 5–8 kalimat atau 3–5 blok; overlap 20 kata setara 1–2 kalimat.

### 6.2 Kerangka isian setelah eksperimen Geralda

| Konfigurasi (size/overlap/title) | Jumlah chunk | Hit@1 | Hit@3 | Rata-rata cosine target | Catatan |
|---|---|---|---|---|---|
| *diisi dari `docs/chunking_experiment_results.md`* | | | | | |

Keputusan akhir parameter, beserta alasan berbasis angka, ditulis di sini setelah tabel terisi.

## 7. Reproduksi

```bash
python src/knowledge/chunker.py                      # statistik + cek mandiri (parameter bawaan)
python src/knowledge/chunker.py --chunk-size 60 --overlap 10 --no-title
python -m pytest -q                                  # 54 test lama tetap lulus
```


---

## 8. Addendum Revisi: Status Data Proyek, Eksperimen, dan Batas Token

Bagian ini melengkapi catatan sebelumnya tanpa mengubah dokumen korpus atau perilaku `chunker.py`.

### 8.1 Status dan asal data: asumsi untuk simulasi proyek

SOP-01 sampai SOP-08 dan KB-09 sampai KB-15 merupakan **data asumsi/sintetis yang disusun kelompok untuk kebutuhan proyek perkuliahan**. Data tersebut bukan regulasi resmi, SOP operasional yang telah disahkan, atau representasi kebijakan aktual Institut Teknologi Del. Pemilihan bentuk SOP dan kebijakan dilakukan agar sistem dapat mendemonstrasikan alur pencarian pengetahuan pada domain pemeliharaan fasilitas.

Dengan demikian, klaim representativitas pada laporan dibatasi pada **cakupan skenario domain proyek**, bukan validitas institusional. Untuk penggunaan nyata, isi dokumen harus ditinjau dan disahkan oleh pemilik proses/institusi terkait. Batasan ini merupakan keputusan ruang lingkup simulasi akademik, bukan kekurangan pengumpulan regulasi resmi.

### 8.2 Rencana eksperimen yang dapat direproduksi

Eksperimen tidak lagi bergantung pada tabel isian manual. Skrip `scripts/experiment_chunking.py` menjalankan kombinasi:

| Chunk size (kata) | Overlap (kata) | Tujuan |
|---:|---:|---|
| 60 | 10 | Potongan kecil, konteks lokal |
| 80 | 15 | Potongan menengah-kecil |
| 100 | 15 | Kandidat kompromi |
| 120 | 20 | Parameter awal |
| 150 | 30 | Potongan lebih besar |

Setiap kombinasi diuji dengan `prepend_title=True` dan `False`, sehingga pengaruh prefiks judul dapat dibandingkan pada korpus dan kueri yang sama. Kumpulan kueri mencakup kueri relevan, sinonim, kontekstual, ambigu, dan dua kueri out-of-domain.

Metrik yang dilaporkan:

- **Hit@1**: proporsi kueri domain yang dokumen targetnya berada di peringkat pertama.
- **Hit@3**: proporsi kueri domain yang setidaknya satu dokumen targetnya berada pada tiga hasil teratas.
- **MRR**: rata-rata kebalikan peringkat pertama dokumen target.
- **Mean best target cosine**: rata-rata skor cosine tertinggi dari dokumen target untuk setiap kueri domain.
- **Token limit**: jumlah chunk yang panjang tokennya melampaui `model.max_seq_length`.
- **OOD top-1 score**: skor hasil tertinggi untuk kueri di luar domain; skor ini dilaporkan untuk dianalisis, bukan langsung dianggap sebagai ambang penolakan.

Hasil aktual disimpan ke `reports/chunking_experiment_results.json` dan `reports/chunking_experiment_summary.csv`. Angka hasil tidak dicantumkan di dokumen ini sebelum skrip dijalankan pada lingkungan yang memiliki model embedding. Dengan demikian, tidak ada hasil eksperimen yang direkayasa.

### 8.3 Verifikasi batas token model embedding

Jumlah kata bukan ukuran yang setara dengan jumlah token sub-kata. Karena itu, ukuran 120 kata tidak boleh dinyatakan aman hanya berdasarkan jumlah kata.

Skrip eksperimen menggunakan tokenizer milik model yang benar-benar dipakai, menghitung token setiap chunk **termasuk prefiks judul dan special tokens**, lalu membandingkannya dengan `model.max_seq_length`. Kolom `chunks_over_model_limit` menunjukkan jumlah chunk yang berisiko dipotong saat embedding. Parameter yang dipilih untuk integrasi harus mengutamakan tidak adanya pemotongan (atau memiliki margin aman), kemudian dibandingkan kembali berdasarkan Hit@k, MRR, dan cosine target.

Model bawaan skrip adalah `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, tetapi dapat disamakan dengan model yang dipilih anggota tim melalui argumen `--model`. Jika model embedding tim berbeda, eksperimen wajib dijalankan ulang dengan model tersebut; batas token model tidak boleh diasumsikan sama.

### 8.4 Kontrak integrasi dengan anggota tim embedding dan vector store

Keluaran `load_and_chunk_corpus()` tetap berupa daftar objek dengan tiga bagian:

- `id`: ID stabil per chunk, misalnya `SOP-01-c000`.
- `text`: teks chunk yang akan dikirim ke model embedding.
- `metadata`: metadata dokumen ditambah `source_file` dan `chunk_index`.

Anggota tim embedding/ChromaDB dapat mengonsumsi `id`, `text`, dan `metadata` tersebut secara langsung. `id` digunakan sebagai ID record ChromaDB; `text` sebagai document; dan `metadata` sebagai metadata record. Jangan membuat ulang chunk secara terpisah pada pipeline embedding karena hal itu dapat membuat ID, teks, dan hasil eksperimen tidak konsisten. Jika parameter chunking berubah, jalankan ulang ingestion/indexing agar isi vector store sama dengan konfigurasi yang dievaluasi.

### 8.5 Cara menjalankan eksperimen

Dari root repository, pasang dependensi bila belum tersedia:

```bash
uv add sentence-transformers
```

Lalu jalankan:

```bash
uv run python scripts/experiment_chunking.py
```

Jika tim memakai model lain:

```bash
uv run python scripts/experiment_chunking.py --model NAMA_MODEL_TIM
```

Skrip mengunduh/memuat model sesuai mekanisme Sentence-Transformers, sehingga eksekusi pertama memerlukan akses model yang tersedia di lingkungan. Setelah selesai, lampirkan kedua berkas hasil dari direktori `reports/` pada laporan atau repositori.

### 8.6 Aturan keputusan parameter akhir

Parameter 120/20 **belum ditetapkan sebagai hasil terbaik**. Parameter akhir baru dapat dipilih setelah hasil eksperimen nyata tersedia. Gunakan urutan keputusan berikut:

1. Singkirkan konfigurasi yang menyebabkan chunk melampaui batas token model (atau terlalu dekat dengan batas sehingga tidak memiliki ruang untuk instruksi/prefiks tambahan pada tahap berikutnya).
2. Dari konfigurasi yang aman, bandingkan Hit@1, Hit@3, MRR, dan mean best target cosine.
3. Periksa pengaruh `prepend_title` dengan membandingkan pasangan konfigurasi yang sama.
4. Tinjau hasil kueri ambigu dan OOD secara manual. Skor cosine OOD saja tidak cukup untuk menetapkan ambang penolakan.
5. Catat konfigurasi terpilih, alasan, dan trade-off berdasarkan berkas hasil eksperimen yang benar-benar dihasilkan.
