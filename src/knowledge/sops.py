"""
Del-MaintOps Copilot - Standard Operating Procedures (SOP) Knowledge Base
-------------------------------------------------------------------------
Modul basis pengetahuan SOP fasilitas FITE IT Del terpadu (M1 & M2).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from core.models import UrgencyLevel

# Basis pengetahuan SOP 4 entri dasar untuk Milestone 1
SOP_KB: Dict[str, Dict[str, Any]] = {
    "SOP-01": {
        "title": "Penanganan Proyektor/Infokus Rusak",
        "category": "proyektor",
        "keywords": ["proyektor", "infokus", "projector", "layar", "hdmi", "tayang"],
        "default_urgency": "tinggi",
        "sla": "2 jam sejak laporan diverifikasi",
        "sla_hours": 2,
        "procedure": [
            "Laporkan kode ruang + gejala (tidak menyala / gambar buram / tidak ada sinyal HDMI).",
            "Sistem memverifikasi status via checklist otomatis (cek kabel, cek sumber listrik).",
            "Jika belum teratasi, tiket diteruskan ke teknisi AV dengan prioritas tinggi.",
            "Teknisi mengecek unit; eskalasi ke staf sarana jika perlu penggantian lampu/unit.",
            "Status tiket diperbarui menjadi Resolved setelah uji tayang berhasil.",
        ],
    },
    "SOP-02": {
        "title": "Penanganan AC Tidak Dingin / Bermasalah",
        "category": "ac",
        "keywords": ["ac", "pendingin", "dingin", "bocor", "kompresor", "freon"],
        "default_urgency": "sedang",
        "sla": "4 jam kerja",
        "sla_hours": 24,
        "procedure": [
            "Laporan mencantumkan kode ruang dan gejala (tidak dingin, bocor air, bising).",
            "Sistem mengecek riwayat servis unit AC (histori berulang ditandai untuk audit unit).",
            "Tiket diteruskan ke teknisi mekanikal/elektrikal.",
            "Teknisi memeriksa freon/filter/kompresor sesuai gejala.",
            "Tiket ditutup setelah suhu ruangan dikonfirmasi normal oleh pelapor/petugas piket.",
        ],
    },
    "SOP-03": {
        "title": "Gangguan Jaringan Komputer / LAN Laboratorium",
        "category": "jaringan",
        "keywords": ["jaringan", "lan", "internet", "koneksi", "wifi", "ip", "switch"],
        "default_urgency": "sedang",
        "sla": "1 jam (kritis saat praktikum) / 4 jam (di luar jam praktikum)",
        "sla_hours": 24,
        "procedure": [
            "Laporan mencantumkan lab/ruang, jumlah komputer terdampak, dan jenis gangguan.",
            "Sistem mengecek status switch/access point terkait (jika ada monitoring jaringan).",
            "Tiket kritis langsung dieskalasi ke admin jaringan tanpa antrian normal.",
            "Admin jaringan melakukan diagnosis (restart perangkat, cek kabel, cek konfigurasi).",
            "Status tiket diperbarui menjadi Resolved setelah konektivitas terverifikasi normal.",
        ],
    },
    "SOP-04": {
        "title": "Kerusakan Fasilitas Penunjang Umum",
        "category": "umum",
        "keywords": ["toilet", "saung", "kursi", "meja", "pintu", "wastafel"],
        "default_urgency": "rendah",
        "sla": "1-3 hari kerja",
        "sla_hours": 72,
        "procedure": [
            "Laporan mencantumkan lokasi spesifik (mis. Saung 2, Toilet Pria Lt. 1).",
            "Sistem mengelompokkan laporan sejenis untuk efisiensi rute penanganan teknisi sarana.",
            "Tiket diproses sesuai jadwal pemeliharaan harian tim sarana.",
            "Staf sarana melakukan perbaikan fisik atau penggantian inventaris rusak.",
            "Tiket ditutup dan diverifikasi pada inspeksi fasilitas mingguan berikutnya.",
        ],
    },
}

# Katalog SOP Diperluas (Milestone 2)
SOP_CATALOG: Dict[str, Dict[str, Any]] = dict(SOP_KB)
SOP_CATALOG.update({
    "SOP-05": {
        "title": "Kelistrikan & Panel Server FITE",
        "category": "listrik",
        "keywords": ["listrik", "mati listrik", "korsleting", "mcb", "colokan", "stop kontak", "tegangan"],
        "default_urgency": "tinggi",
        "sla": "2 jam",
        "sla_hours": 2,
        "procedure": [
            "Evakuasi segera mahasiswa dari area korsleting atau bahaya kebakaran.",
            "Turunkan MCB utama. Perbaikan ini WAJIB dilakukan oleh teknisi listrik bersertifikat.",
            "Dilarang keras dikerjakan oleh teknisi jaringan demi keselamatan kerja.",
            "Ganti sekring/kabel yang terbakar dan lakukan uji tegangan dengan multitester.",
            "Tiket ditutup setelah pasokan daya stabil dan aman.",
        ],
    },
    "SOP-06": {
        "title": "Komputer Laboratorium & Periferal",
        "category": "pc",
        "keywords": ["pc", "komputer", "windows", "boot", "keyboard", "mouse", "cpu", "ram"],
        "default_urgency": "sedang",
        "sla": "24 jam",
        "sla_hours": 24,
        "procedure": [
            "Diagnosa gejala kerusakan melalui beep code motherboard atau layar error OS.",
            "Jika sistem corrupt atau terkena malware, backup data penting lalu restore OS.",
            "Untuk keyboard/mouse rusak fisik, lakukan plug-and-play unit cadangan dari gudang.",
            "Pasang label isolasi merah jika menunggu penggantian modul RAM/PSU.",
            "Tiket ditutup setelah PC lolos benchmark diagnostik.",
        ],
    },
    "SOP-07": {
        "title": "Idea Hub & Layar Presentasi Interaktif",
        "category": "ideahub",
        "keywords": ["idea hub", "ideahub", "touchscreen", "layar sentuh", "interactive board"],
        "default_urgency": "tinggi",
        "sla": "2 jam",
        "sla_hours": 2,
        "procedure": [
            "Lakukan hard restart unit Idea Hub dan cek kabel HDMI/Type-C.",
            "Jika panel sentuh retak berat, arahkan dosen menggunakan papan tulis manual sementara.",
            "Eskalasikan ke vendor resmi bila terjadi kerusakan hardware internal.",
            "Tiket ditutup setelah fungsi kalibrasi sentuh normal.",
        ],
    },
    "SOP-08": {
        "title": "Kamera Pengawas (CCTV) Laboratorium",
        "category": "cctv",
        "keywords": ["cctv", "kamera", "dvr", "nvr", "plafon", "rekaman"],
        "default_urgency": "rendah",
        "sla": "72 jam",
        "sla_hours": 72,
        "procedure": [
            "Periksa konektor BNC/UTP di belakang unit kamera.",
            "Lakukan kalibrasi sudut pandang lensa agar mencakup area lab secara optimal.",
            "Pastikan feed video terdeteksi aktif pada server NVR pusat.",
            "Tiket ditutup setelah rekaman video tersimpan normal.",
        ],
    },
})


def detect_category(text: str) -> Optional[str]:
    """Mendeteksi ID SOP yang relevan berdasarkan kata kunci pada batas kata."""
    text_lower = text.lower()
    for sop_id, sop in SOP_CATALOG.items():
        for kw in sop["keywords"]:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text_lower):
                return sop_id
    return None


def classify_urgency(
    sop_id: str,
    practicum_active: bool = False,
    during_practicum: bool = False,
    exam_or_practicum_room: bool = False,
    exam_or_temperature_sensitive: bool = False,
    safety_or_sanitation: bool = False,
    safety_hazard: bool = False,
    **kwargs,
) -> str:
    """Menentukan tingkat urgensi akhir berdasarkan aturan kenaikan SOP FITE."""
    is_practicum = practicum_active or during_practicum
    is_exam_temp = exam_or_practicum_room or exam_or_temperature_sensitive
    is_safety = safety_or_sanitation or safety_hazard

    if sop_id == "SOP-01":
        return "tinggi"
    elif sop_id == "SOP-02":
        return "tinggi" if is_exam_temp else "sedang"
    elif sop_id == "SOP-03":
        return "kritis" if is_practicum else "sedang"
    elif sop_id == "SOP-04":
        return "tinggi" if is_safety else "rendah"
    elif sop_id == "SOP-05":
        return "tinggi"
    elif sop_id in SOP_CATALOG:
        return SOP_CATALOG[sop_id]["default_urgency"]
    return "rendah"


def find_sop(keyword: str) -> List[str]:
    """Mencari ID SOP yang judul atau kata kuncinya memuat keyword."""
    kw = keyword.lower().strip()
    if not kw:
        return []
    hits = []
    # Cari di SOP_KB terlebih dahulu (M1), lalu katalog lengkap
    for sop_id, sop in SOP_CATALOG.items():
        haystack = (sop["title"] + " " + " ".join(sop["keywords"])).lower()
        if kw in haystack:
            hits.append(sop_id)
    return hits
