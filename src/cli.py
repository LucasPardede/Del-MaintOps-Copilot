"""
Del-MaintOps Copilot - CLI Interaktif (Milestone 1 tambahan)
-----------------------------------------------------------------
Antarmuka baris perintah agar mahasiswa FITE benar-benar bisa "mengobrol"
dengan agen: melapor kerusakan, menanyakan SOP, dan meminta rekomendasi
rute penanganan teknisi -- semua di atas komponen yang sudah dibangun di
`search_baseline.py` (PriorityTicketQueue, UCS, A*).

Catatan lingkup (scope): Ini BUKAN chatbot berbasis LLM/RAG (itu baru masuk
di Milestone 3-4). Modul tanya-jawab SOP di sini adalah pencocokan kata
kunci sederhana atas basis pengetahuan `docs/sops_fite.md`, sekadar
placeholder agar interaksi terasa nyata di Milestone 1. Fungsi inti (non
I/O) dipisah dari loop interaktif supaya tetap bisa diuji lewat pytest.

Jalankan:
    uv run python src/cli.py
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from search_baseline import (  # noqa: E402
    FITE_GRAPH,
    PriorityTicketQueue,
    Ticket,
    a_star_search,
    uniform_cost_search,
)

POSKO = "Posko Teknisi"

# ---------------------------------------------------------------------------
# 1. Basis pengetahuan SOP (ringkasan docs/sops_fite.md) untuk Q&A sederhana
# ---------------------------------------------------------------------------

SOP_KB: List[Dict[str, object]] = [
    {
        "id": "SOP-01",
        "judul": "Proyektor/Infokus Rusak",
        "kata_kunci": ["proyektor", "infokus", "projector", "layar", "hdmi"],
        "urgensi_default": "tinggi",
        "sla": "2 jam sejak laporan diverifikasi",
        "ringkasan": (
            "Laporkan kode ruang + gejala (tidak menyala/buram/tidak ada sinyal HDMI). "
            "Tiket diteruskan ke teknisi AV dengan prioritas tinggi; jika perlu ganti "
            "lampu/unit, dieskalasi ke staf sarana."
        ),
    },
    {
        "id": "SOP-02",
        "judul": "AC Tidak Dingin / Bermasalah",
        "kata_kunci": ["ac", "pendingin", "dingin", "bocor", "bising"],
        "urgensi_default": "sedang",
        "sla": "4 jam kerja (naik jadi tinggi jika ruang dipakai ujian/praktikum sensitif suhu)",
        "ringkasan": (
            "Cantumkan kode ruang + gejala (tidak dingin/bocor air/bising). Tiket "
            "diteruskan ke teknisi mekanikal/elektrikal untuk cek freon/filter/kompresor."
        ),
    },
    {
        "id": "SOP-03",
        "judul": "Gangguan Jaringan Komputer / LAN Lab",
        "kata_kunci": ["jaringan", "lan", "internet", "wifi", "koneksi", "ip"],
        "urgensi_default": "sedang",
        "sla": "1 jam jika kritis (saat jam praktikum), 4 jam di luar itu",
        "ringkasan": (
            "Cantumkan lab/ruang, jumlah komputer terdampak, dan jenis gangguan. Tiket "
            "kritis (saat jam praktikum aktif) langsung dieskalasi ke admin jaringan "
            "tanpa antrian normal."
        ),
    },
    {
        "id": "SOP-04",
        "judul": "Fasilitas Umum (Idea Hub, Toilet, Saung, Furnitur)",
        "kata_kunci": ["toilet", "saung", "kursi", "meja", "furnitur", "idea hub", "sanitasi"],
        "urgensi_default": "rendah",
        "sla": "1 hari kerja (4 jam khusus isu keselamatan/sanitasi mendesak)",
        "ringkasan": (
            "Cantumkan lokasi spesifik + deskripsi kerusakan. Tiket diteruskan ke staf "
            "kebersihan/sarana umum; naik prioritas jika ada isu keselamatan/sanitasi."
        ),
    },
]


def find_relevant_sop(query: str) -> Optional[Dict[str, object]]:
    """Cocokkan pertanyaan/deskripsi bebas mahasiswa ke entri SOP via kata kunci.

    Mengembalikan entri SOP dengan jumlah kata kunci cocok terbanyak, atau
    None jika tidak ada kecocokan sama sekali (di luar cakupan sistem).
    """
    q = query.lower()
    best_entry: Optional[Dict[str, object]] = None
    best_score = 0
    for entry in SOP_KB:
        score = sum(1 for kw in entry["kata_kunci"] if kw in q)
        if score > best_score:
            best_score = score
            best_entry = entry
    return best_entry


# ---------------------------------------------------------------------------
# 2. Inferensi urgensi otomatis (aturan dari SOP + konteks jam praktikum)
# ---------------------------------------------------------------------------

def infer_default_urgency(issue_type: str, during_practicum: bool = False) -> str:
    """Tebak urgensi default berdasarkan SOP yang cocok dengan jenis kerusakan.

    Kasus khusus SOP-03 (jaringan): jadi "kritis" jika dilaporkan saat jam
    praktikum aktif, sesuai docs/sops_fite.md.
    """
    entry = find_relevant_sop(issue_type)
    if entry is None:
        return "rendah"  # default konservatif untuk kasus di luar 4 SOP dikenal
    if entry["id"] == "SOP-03" and during_practicum:
        return "kritis"
    return str(entry["urgensi_default"])


# ---------------------------------------------------------------------------
# 3. Deteksi duplikasi laporan (pain point #5 di problem_framing.md)
# ---------------------------------------------------------------------------

def is_duplicate(existing_tickets: List[Ticket], location: str, issue_type: str) -> Optional[Ticket]:
    """Cari tiket aktif dengan lokasi sama & jenis kerusakan yang mirip."""
    issue_lower = issue_type.lower().strip()
    for t in existing_tickets:
        if t.location == location and t.issue_type.lower().strip() == issue_lower:
            return t
    return None


def generate_ticket_id(counter: "itertools.count") -> str:
    return f"TKT-{next(counter):03d}"


# ---------------------------------------------------------------------------
# 4. Sesi interaktif (I/O) -- state disimpan selama proses CLI berjalan
# ---------------------------------------------------------------------------

class CopilotSession:
    def __init__(self) -> None:
        self.queue = PriorityTicketQueue()
        self.active_tickets: List[Ticket] = []
        self.dispatch_log: List[Tuple[Ticket, List[str], int]] = []
        self._id_counter = itertools.count(1)

    # -- helper tampilan lokasi valid -------------------------------------
    def print_known_locations(self) -> None:
        print("Lokasi yang dikenali sistem (graf gedung FITE):")
        for loc in FITE_GRAPH:
            if loc != POSKO:
                print(f"  - {loc}")

    # -- 1) lapor kerusakan -------------------------------------------------
    def report_ticket(self) -> None:
        print("\n--- Lapor Kerusakan Fasilitas ---")
        self.print_known_locations()
        location = input("Lokasi ruangan/fasilitas: ").strip()
        if location not in FITE_GRAPH or location == POSKO:
            print(
                "[!] Lokasi belum terdaftar di peta gedung, tiket tetap dicatat "
                "tapi rekomendasi rute belum bisa dihitung untuk lokasi ini."
            )

        issue_type = input("Deskripsikan kerusakan (mis. 'infokus tidak menyala'): ").strip()
        if not issue_type:
            print("[!] Deskripsi tidak boleh kosong, laporan dibatalkan.")
            return

        dup = is_duplicate(self.active_tickets, location, issue_type)
        if dup is not None:
            print(
                f"[i] Laporan serupa sudah tercatat sebagai {dup.ticket_id} "
                f"({dup.urgency}) -- kemungkinan duplikat. Laporan tetap boleh "
                "dilanjutkan bila kondisinya berbeda."
            )
            lanjut = input("Lanjutkan tetap catat laporan baru? (y/n): ").strip().lower()
            if lanjut != "y":
                print("Laporan dibatalkan.")
                return

        during_practicum = False
        matched = find_relevant_sop(issue_type)
        if matched is not None and matched["id"] == "SOP-03":
            during_practicum = input(
                "Apakah ini terjadi saat jam praktikum aktif? (y/n): "
            ).strip().lower() == "y"

        suggested = infer_default_urgency(issue_type, during_practicum)
        print(f"[i] SOP relevan: {matched['judul'] if matched else 'tidak ditemukan (di luar 4 SOP dikenal)'}")
        print(f"[i] Urgensi yang disarankan sistem: {suggested.upper()}")

        override = input(
            f"Tekan Enter untuk menerima '{suggested}', atau ketik urgensi lain "
            "(kritis/tinggi/sedang/rendah): "
        ).strip().lower()
        urgency = override if override else suggested

        ticket_id = generate_ticket_id(self._id_counter)
        try:
            self.queue.push(ticket_id, location, issue_type, urgency)
        except ValueError as exc:
            print(f"[!] {exc} -- laporan dibatalkan.")
            return

        ticket = Ticket(0, ticket_id, location, issue_type, urgency)
        self.active_tickets.append(ticket)
        print(f"[OK] Tiket {ticket_id} tercatat dengan urgensi '{urgency}'.")
        if matched is not None:
            print(f"     SLA target: {matched['sla']}")

    # -- 2) lihat antrian -----------------------------------------------
    def show_queue(self) -> None:
        print("\n--- Antrian Tiket (urutan prioritas) ---")
        sorted_tickets = self.queue.as_sorted_list()
        if not sorted_tickets:
            print("Belum ada tiket aktif.")
            return
        for i, t in enumerate(sorted_tickets, start=1):
            print(f"  {i}. [{t.urgency.upper():6}] {t.ticket_id} - {t.location}: {t.issue_type}")

    # -- 3) rekomendasi rute ---------------------------------------------
    def dispatch_next(self) -> None:
        print("\n--- Rekomendasi Rute Teknisi (UCS & A*) ---")
        if len(self.queue) == 0:
            print("Tidak ada tiket di antrian.")
            return

        next_ticket = self.queue.pop()
        self.active_tickets = [t for t in self.active_tickets if t.ticket_id != next_ticket.ticket_id]
        print(f"Tiket berikutnya yang ditangani: {next_ticket.ticket_id} @ {next_ticket.location}")

        if next_ticket.location not in FITE_GRAPH:
            print("[!] Lokasi tidak ada di graf gedung, rute tidak dapat dihitung.")
            self.dispatch_log.append((next_ticket, [], -1))
            return

        ucs_path, ucs_cost = uniform_cost_search(FITE_GRAPH, POSKO, next_ticket.location)
        astar_path, astar_cost = a_star_search(FITE_GRAPH, POSKO, next_ticket.location)

        if ucs_path is None:
            print("[!] Lokasi tidak terjangkau dari Posko Teknisi di graf saat ini.")
            self.dispatch_log.append((next_ticket, [], -1))
            return

        print(f"  UCS  : {' -> '.join(ucs_path)}  | total = {ucs_cost} menit")
        print(f"  A*   : {' -> '.join(astar_path)}  | total = {astar_cost} menit")
        self.dispatch_log.append((next_ticket, ucs_path, ucs_cost))

    # -- 4) tanya SOP ------------------------------------------------------
    def ask_sop(self) -> None:
        print("\n--- Tanya SOP Penanganan ---")
        query = input("Tulis pertanyaan/kondisi (mis. 'AC bocor di lab'): ").strip()
        entry = find_relevant_sop(query)
        if entry is None:
            print(
                "Maaf, pertanyaan ini di luar cakupan basis pengetahuan SOP saat ini "
                "(hanya proyektor, AC, jaringan/LAN, dan fasilitas umum)."
            )
            return
        print(f"[{entry['id']}] {entry['judul']}")
        print(f"  Urgensi default : {entry['urgensi_default']}")
        print(f"  SLA target      : {entry['sla']}")
        print(f"  Ringkasan       : {entry['ringkasan']}")

    # -- 5) riwayat sesi -----------------------------------------------------
    def show_dispatch_log(self) -> None:
        print("\n--- Riwayat Penanganan Sesi Ini ---")
        if not self.dispatch_log:
            print("Belum ada tiket yang dikirim ke teknisi pada sesi ini.")
            return
        for ticket, path, cost in self.dispatch_log:
            route = " -> ".join(path) if path else "(rute tidak tersedia)"
            biaya = f"{cost} menit" if cost >= 0 else "-"
            print(f"  {ticket.ticket_id} [{ticket.urgency}] {ticket.location}: {route} ({biaya})")


MENU = """
=== Del-MaintOps Copilot | CLI Interaktif ===
1. Lapor kerusakan fasilitas baru
2. Lihat antrian tiket (urutan prioritas)
3. Minta rekomendasi rute teknisi ke tiket berikutnya (UCS & A*)
4. Tanya SOP penanganan
5. Lihat riwayat penanganan sesi ini
6. Keluar
"""


def run() -> None:
    print("Halo! Saya Del-MaintOps Copilot, asisten pelaporan fasilitas FITE IT Del.")
    print("Ketik nomor menu untuk berinteraksi. Ketik '6' kapan saja untuk keluar.\n")

    session = CopilotSession()
    while True:
        print(MENU)
        choice = input("Pilihan Anda: ").strip()

        if choice == "1":
            session.report_ticket()
        elif choice == "2":
            session.show_queue()
        elif choice == "3":
            session.dispatch_next()
        elif choice == "4":
            session.ask_sop()
        elif choice == "5":
            session.show_dispatch_log()
        elif choice == "6":
            print("\nTerima kasih sudah menggunakan Del-MaintOps Copilot. Sampai jumpa!")
            break
        else:
            print("[!] Pilihan tidak dikenal, coba lagi.")


if __name__ == "__main__":
    try:
        run()
    except (KeyboardInterrupt, EOFError):
        print("\n\nSesi dihentikan. Sampai jumpa!")
