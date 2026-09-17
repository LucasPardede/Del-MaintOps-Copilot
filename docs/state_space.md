# Formulasi Ruang Keadaan (State Space) — Modul Rekomendasi Prioritas Perbaikan

Masalah dimodelkan sebagai **routing teknisi berbobot prioritas**: seorang teknisi berangkat dari Posko
menuju serangkaian lokasi bertiket di gedung FITE, dan sistem harus merekomendasikan urutan/rute yang
meminimalkan total biaya (waktu tempuh + penalti keterlambatan SLA) menggunakan **Uniform Cost
Search (UCS)** dan **A\* Search**.

## Komponen Formal (X, A, T, G, C)

**1. State Space (X)** — Himpunan status $s = (lokasi\_saat\_ini, TiketSelesai)$, di mana:
- $lokasi\_saat\_ini \in L$, $L$ = himpunan simpul graf (Posko Teknisi, Ruang Kelas 301–305, Lab RPL,
  Lab Jaringan, Idea Hub, Toilet Lt.1, Saung, dst.)
- $TiketSelesai \subseteq T$, $T$ = himpunan tiket kerusakan aktif yang perlu ditangani.

**2. Initial State**: $s_0 = (\text{Posko Teknisi}, \emptyset)$ — teknisi mulai dari posko, belum ada tiket selesai.

**3. Actions (A)**: $Move(l')$ — berpindah dari lokasi saat ini ke lokasi bertetangga $l'$ pada graf konektivitas
gedung FITE (koridor/jalur antar ruang).

**4. Transition Model (T)**:
$$Result((l, TiketSelesai), Move(l')) = (l', TiketSelesai \cup \{t \mid t \in T, lokasi(t) = l'\})$$
Berpindah ke lokasi $l'$ akan otomatis menandai tiket di lokasi tersebut sebagai selesai ditangani.

**5. Goal Test (G)**: $TiketSelesai \supseteq T_{prioritas}$ — seluruh tiket berprioritas tinggi (kritis & tinggi)
telah tertangani.

**6. Path Cost (C)**: $C(path) = \sum (\text{waktu\_tempuh}_{i,j}) + \sum (\text{penalti\_SLA}_t)$
- $\text{waktu\_tempuh}_{i,j}$: bobot edge graf (menit tempuh antar lokasi).
- $\text{penalti\_SLA}_t$: penalti tambahan jika tiket $t$ ditangani melewati batas SLA sesuai kategori
  urgensinya (lihat `docs/sops_fite.md`).

## Heuristik untuk A* — $h(s)$
$$h(s) = \min_{t \in T_{prioritas} \setminus TiketSelesai} \text{jarak\_estimasi}(lokasi\_saat\_ini, lokasi(t))$$
Estimasi jarak diambil dari batas bawah waktu tempuh minimum antar dua simpul pada graf (tidak pernah
melebihi jarak riil), sehingga **admissible** — tidak pernah overestimate biaya sisa menuju goal — dan
konsisten karena mengikuti pertidaksamaan segitiga pada graf berbobot non-negatif.

## Contoh Ruang Lokasi (Graf)
```
Posko Teknisi -- (3) -- Lab RPL
Posko Teknisi -- (5) -- Idea Hub
Lab RPL       -- (2) -- Lab Jaringan
Idea Hub      -- (4) -- Ruang Kelas 301
Lab Jaringan  -- (3) -- Ruang Kelas 301
Ruang Kelas 301 -- (2) -- Saung
Idea Hub      -- (6) -- Toilet Lt.1
```
Bobot edge merepresentasikan estimasi waktu tempuh (menit). Implementasi lengkap dan uji coba ada di
`src/search_baseline.py`.
