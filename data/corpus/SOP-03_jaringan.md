---
doc_id: SOP-03
title: Gangguan Jaringan Komputer / LAN Laboratorium
doc_type: sop
category: jaringan
default_urgency: sedang
sla_hours: 24
---
## Tujuan
Dokumen ini menetapkan prosedur penanganan gangguan jaringan komputer, LAN, dan WiFi di laboratorium serta ruang kelas FITE IT Del. Jaringan menjadi tulang punggung kegiatan praktikum, sehingga gangguan harus segera didiagnosis.

## Ruang Lingkup
SOP ini berlaku untuk koneksi terputus, internet lambat atau mati, kabel LAN bermasalah, port switch error, dan Access Point (AP) WiFi yang mati atau tidak terdeteksi. Urgensi bawaan adalah Sedang dengan SLA 24 jam. Contoh kasus pada data tiket adalah koneksi terputus di dua meja pojok belakang Labkom 716 dan sinyal AP yang tidak terdeteksi di Kelas 721. Penanganan dilakukan oleh admin jaringan, yaitu teknisi jaringan Roy.

## Aturan Eskalasi Saat Praktikum
Jika gangguan jaringan terjadi saat praktikum berlangsung, tiket dinaikkan ke prioritas Kritis dan langsung dieskalasi ke admin jaringan tanpa antrean normal. Kenaikan prioritas ini berlaku untuk seluruh Labkom yang sedang dipakai praktikum.

## Prosedur
1. Laporan mencantumkan lab atau ruang, jumlah komputer terdampak, dan jenis gangguan.
2. Sistem mengecek status switch dan access point terkait jika ada monitoring jaringan.
3. Tiket kritis langsung dieskalasi ke admin jaringan tanpa antrean normal.
4. Admin jaringan melakukan diagnosis, yaitu restart perangkat, cek kabel, dan cek konfigurasi. Kabel fisik diperiksa dengan LAN tester, dan konektor RJ45 yang longgar dipotong lalu di-crimping ulang.
5. Untuk WiFi, AP di-reboot dan konfigurasi IP diperiksa pada controller jaringan pusat. Penggantian dijadwalkan jika AP mati akibat lonjakan tegangan listrik.
6. Status tiket diperbarui menjadi Resolved setelah konektivitas terverifikasi normal.

## Batas Kewenangan
Teknisi jaringan tidak boleh mengerjakan pekerjaan kelistrikan. Lonjakan tegangan listrik yang merusak Access Point dikoordinasikan dengan teknisi kelistrikan.

## Dokumen Terkait
Kenaikan prioritas saat praktikum dijelaskan lebih lanjut pada Kebijakan Penggunaan Lab saat Praktikum dan Ujian. Batas waktu dan eskalasi tiket mengikuti Kebijakan SLA, Prioritas, dan Eskalasi Tiket.
