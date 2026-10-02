# Pemodelan Matematis Formal: Modul Pemecahan Batasan Keputusan Bisnis (CSP & GA)

**Del-MaintOps Copilot — Fakultas Informatika dan Teknik Elektro (FITE), Institut Teknologi Del**  
*Mata Kuliah: 10S3001 Kecerdasan Buatan (+P) | Tugas 2 (Milestone 2 - W04)*  
*Kelompok 1 (Grup 01): Lucas Pardede (12S24015), Ika Maria Manurung (12S24021), Geralda Natali Gultom (12S24051)*

---

## 1. Domain Masalah Bisnis & Regulasi Operasional

Dalam operasional enterprise dan fasilitas kampus di Fakultas Informatika dan Teknik Elektro (FITE) Institut Teknologi Del, keputusan alokasi penugasan teknisi dan urutan penanganan tiket kerusakan fasilitas menghadapi batasan-batasan ketat:
1. **Regulasi Ketenagakerjaan & Keahlian (SOP Teknis)**: Setiap perbaikan fasilitas membutuhkan kualifikasi spesifik. Sebagai contoh, perbaikan fasilitas kelistrikan (*Mati Listrik / Korsleting Panel*) dilarang keras dikerjakan oleh teknisi jaringan demi keselamatan kerja dan regulasi sarpras.
2. **Kepatuhan Service Level Agreement (SLA)**: Setiap tiket memiliki batas maksimal waktu penyelesaian berdasarkan tingkat keparahan dampak terhadap Kegiatan Belajar Mengajar (KBM):
   - **Tinggi**: Maksimal 2 Jam ($120\text{ menit}$).
   - **Sedang**: Maksimal 24 Jam ($1440\text{ menit}$).
   - **Rendah**: Maksimal 72 Jam ($4320\text{ menit}$).
3. **Keterbatasan Fisik & Navigasi**: Teknisi berpindah antar ruangan (Kelas 711–722 dan Labkom 713–726) pada gedung bertingkat FITE dengan waktu tempuh nyata berdasarkan graf navigasi.
4. **Kapasitas Shift Kerja**: Satu teknisi hanya dapat mengerjakan satu tugas dalam satu waktu (*non-preemptive single machine scheduling*) tanpa tumpang tindih (*no-collision*).

---

## 2. Pemodelan Formal Constraint Satisfaction Problem (CSP)

Secara formal, masalah penugasan dan penjadwalan pemeliharaan fasilitas didefinisikan sebagai tupel CSP:
$$\mathcal{P} = \langle X, D, C \rangle$$

### 2.1. Himpunan Variabel Keputusan ($X$)
Diberikan himpunan tiket kerusakan $T = \{t_1, t_2, \dots, t_N\}$. Untuk setiap tiket $t_i$, didefinisikan variabel keputusan:
$$X_i = (Tech_i, Slot_i)$$
di mana:
- $Tech_i$: Identitas teknisi yang ditugaskan menangani tiket $t_i$.
- $Slot_i \in \{0, 1, 2, \dots, N-1\}$: Nomor urutan penugasan tiket $t_i$ dalam antrean kerja teknisi $Tech_i$.

### 2.2. Domain Nilai ($D$)
Domain untuk setiap variabel $X_i$ dibatasi oleh kualifikasi awal teknisi (*Unary Constraint Filtering*):
$$D(X_i) = \{ (k, s) \mid k \in \mathcal{K}, \text{is\_compatible}(k, t_i) = \text{True}, s \in \{0, 1, \dots, N-1\} \}$$
di mana $\mathcal{K}$ adalah himpunan teknisi yang bertugas:
- $\text{TECH-01}$ (Binsar): $\{\text{Kelistrikan}, \text{Mekanikal/AC}, \text{Umum}\}$
- $\text{TECH-02}$ (Roy): $\{\text{Jaringan/LAN/WiFi}, \text{Komputasi/PC}, \text{Umum}\}$
- $\text{TECH-03}$ (Togu): $\{\text{Audio-Visual/Proyektor/IdeaHub}, \text{Komputasi/PC}, \text{Umum}\}$

### 2.3. Himpunan Batasan (Constraints $C$)

#### A. Batasan Wajib (Hard Constraints — $C_{hard}$)
Solusi jadwal dikatakan **legal/layak (feasible)** jika dan hanya jika seluruh batasan wajib bernilai benar ($\text{True}$):

1. **Batasan Kualifikasi Kompetensi (Skill Matching)**:
   Teknisi yang ditugaskan wajib memiliki spesialisasi keahlian yang dipersyaratkan oleh jenis fasilitas tiket:
   $$\forall i: \quad \text{required\_skill}(t_i) \in \text{skills}(Tech_i)$$
   *Pengecualian khusus SOP*: Fasilitas Mati Listrik secara mutlak mengharuskan kompetensi Kelistrikan ($\text{ELECTRICAL} \in \text{skills}(Tech_i)$).

2. **Ketiadaan Konflik Waktu & Urutan (No Collision / Unique Slot)**:
   Tidak boleh ada dua tiket berbeda yang menempati slot urutan yang sama pada teknisi yang sama:
   $$\forall i \ne j: \quad (Tech_i = Tech_j) \implies (Slot_i \ne Slot_j)$$

3. **Hierarki Prioritas Absolut (Urgency Precedence)**:
   Jika dua tiket dialokasikan ke teknisi yang sama, tiket dengan tingkat keparahan lebih tinggi wajib dikerjakan lebih dahulu:
   $$\forall i, j: \quad (Tech_i = Tech_j \land \text{rank}(t_i) > \text{rank}(t_j)) \implies Slot_i < Slot_j$$
   di mana $\text{rank}(\text{Tinggi}) = 3 > \text{rank}(\text{Sedang}) = 2 > \text{rank}(\text{Rendah}) = 1$.

4. **Kapasitas Shift Kerja Maksimal**:
   Total waktu kerja operasional setiap teknisi dalam satu hari tidak boleh melampaui batas maksimal shift kerja ($480\text{ menit}$ kerja aktif):
   $$\forall k \in \mathcal{K}: \quad \sum_{i: Tech_i = k} \text{duration}(t_i) \le \text{MaxWorkMinutes}_k$$

#### B. Batasan Fleksibel & Penalti Biaya (Soft Constraints — $C_{soft}$)
Digunakan untuk mengoptimalkan kualitas jadwal operasional:

1. **Urutan Kronologis Request (FIFO Tie-Breaker)**:
   Jika dua tiket memiliki tingkat urgensi yang sama pada teknisi yang sama, tiket yang dilaporkan lebih awal diprioritaskan:
   $$\forall i, j: \quad (Tech_i = Tech_j \land \text{urgency}(t_i) = \text{urgency}(t_j) \land \text{req}(t_i) < \text{req}(t_j)) \implies Slot_i < Slot_j$$

2. **Kepatuhan Terhadap Tenggat SLA (SLA Target Lateness Penalty)**:
   Waktu selesai pengerjaan tiket didefinisikan sebagai:
   $$\text{Finish}_i = \text{Start}_i + \text{duration}(t_i)$$
   Keterlambatan terhadap SLA:
   $$\text{Lateness}_i = \max(0, \text{Finish}_i - \text{Deadline}_i)$$
   Formulasi Penalti Keterlambatan:
   $$\text{Penalty}_{SLA} = \sum_{i=1}^N \omega(t_i) \times \text{Lateness}_i, \quad \omega(t_i) = 2 \times \text{rank}(t_i)$$

3. **Minimasi Waktu Tempuh Navigasi FITE (Travel Cost)**:
   $$\text{Cost}_{travel} = \sum_{k \in \mathcal{K}} \sum_{m=0}^{|Q_k|-1} \text{dist}(L_{m}, L_{m+1})$$
   di mana jarak dihitung menggunakan precomputed Dijkstra/A* pada topologi gedung FITE.

---

## 3. Pemodelan Formal Algoritma Genetika (GA)

Sebagai pendekatan optimasi metaheuristik pembanding, masalah dimodelkan ke dalam ruang pencarian evolusioner:

### 3.1. Skema Representasi Kromosom
Individu solusi direpresentasikan sebagai kromosom sepanjang $N$ gen:
$$\mathbf{C} = \langle g_1, g_2, \dots, g_N \rangle$$
Setiap gen $g_i$ merupakan tupel nilai riil dan diskret:
$$g_i = (k_i, w_i)$$
di mana:
- $k_i \in \{0, 1, \dots, |\mathcal{K}|-1\}$: Indeks teknisi yang ditugaskan.
- $w_i \in \mathbb{R}$: Bobot prioritas dinamis yang menentukan urutan eksekusi tiket pada teknisi $k_i$ (tiket dengan $w$ lebih besar dieksekusi lebih dahulu).

### 3.2. Formulasi Penalti dan Fungsi Kebugaran (Fitness Function)
Total biaya individu solusi didefinisikan dengan memasukkan penalti pelanggaran batasan:
$$\text{Cost}(\mathbf{C}) = \text{Penalty}_{SLA} + 0.5 \times \text{Cost}_{travel} + 0.1 \times \text{Makespan} + \text{Penalty}_{hard}$$
di mana penalti batasan wajib diberikan bobot sangat besar jika dilanggar:
$$\text{Penalty}_{hard} = 50000 \times N_{\text{illegal\_skills}} + 10000 \times N_{\text{priority\_inversions}}$$
Fungsi kebugaran (fitness) yang dimaksimalkan:
$$f(\mathbf{C}) = \frac{100\,000}{1.0 + \text{Cost}(\mathbf{C})}$$

### 3.3. Operator Genetika
1. **Seleksi Turnamen ($k$-way Tournament Selection)**: Memilih $k=3$ individu secara acak dan mengambil individu dengan nilai kebugaran tertinggi untuk menjadi induk (*parent*).
2. **Two-Point Crossover**: Memotong dua titik acak pada kromosom induk untuk menghasilkan keturunan yang mempertahankan struktur penugasan kelompok tugas.
3. **Mutasi Terarah**:
   - *Technician Reassignment Mutation* (probabilitas $p_m = 0.20$): Mengubah alokasi teknisi ke pool teknisi lain yang memiliki kualifikasi sah.
   - *Priority Jitter Mutation*: Mengubah bobot $w_i \leftarrow w_i + \mathcal{N}(0, 15)$ untuk menyempurnakan urutan.
4. **Elitisme**: Menyimpan $E=3$ individu terbaik tanpa mutasi ke generasi berikutnya, menjamin kurva konvergensi monoton tidak menurun:
   $$\max f(\mathbf{P}_{t+1}) \ge \max f(\mathbf{P}_t)$$
