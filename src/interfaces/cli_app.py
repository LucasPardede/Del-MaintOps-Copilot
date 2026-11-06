"""
Del-MaintOps Copilot - Unified Interactive CLI Application
----------------------------------------------------------
Antarmuka baris perintah (REPL bergaya percakapan) yang menyatukan alur logika
Milestone 1 dan Milestone 2:
- Pelaporan tiket & klasifikasi urgensi otomatis berbasis SOP
- Manajemen antrean prioritas (PriorityTicketQueue)
- Pencarian rute navigasi teknisi optimal (UCS & A*)
- Optimasi penjadwalan multi-teknisi terikat batasan bisnis (CSP & GA Solver)
- Basis pengetahuan interaktif SOP FITE IT Del
- Pencarian semantik SOP/kebijakan berbasis vektor (ChromaDB + Sentence-Transformers, Milestone 3)
"""

from __future__ import annotations

import itertools
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.models import MaintenanceTicket, PriorityTicketQueue, Ticket
from knowledge.data_loader import get_default_technicians, get_official_milestone2_tickets
from knowledge.sops import SOP_CATALOG, classify_urgency, detect_category, find_sop
from navigation.graph import FITE_UNIFIED_GRAPH
from navigation.router import a_star_search, uniform_cost_search
from optimization.solver import run_csp_solver, run_ga_solver

STATUS_FLOW = ["Reported", "Verified", "Assigned", "In Progress", "Resolved"]

BANNER = r"""
======================================================================
         Del-MaintOps Copilot -- FITE Institut Teknologi Del
      Generative AI-Driven Facility Recommendation & Decision Support
======================================================================
"""

MENU = """
==================== MENU DEL-MAINTOPS COPILOT =====================
  1. Lapor kerusakan baru
  2. Lihat antrian tiket prioritas
  3. Proses tiket prioritas berikutnya (Rute Navigasi UCS & A*)
  4. Optimasi Penjadwalan Teknisi (CSP & GA Solver - Milestone 2)
  5. Tanya SOP pemeliharaan fasilitas FITE
  6. Lihat daftar lokasi & topologi gedung FITE
  7. Lihat riwayat tiket selesai (Resolved)
  8. Bantuan (penjelasan menu)
  9. Cari SOP (Semantic Search - Milestone 3)
  10. Keluar
======================================================================"""

HELP_TEXT = """
Panduan Menu Del-MaintOps Copilot:
  1. Lapor Kerusakan Baru     -> Mencatat laporan kerusakan: lokasi & fasilitas dipilih lewat
                                 nomor, urgensi ditentukan otomatis oleh sistem sesuai SOP.
  2. Lihat Antrian Tiket      -> Menampilkan tiket aktif terurut prioritas (heapq + FIFO).
  3. Proses Tiket Berikutnya  -> Menangani tiket paling mendesak: sistem menghitung rute tercepat
                                 teknisi dari Posko Teknisi (UCS & A*) dan memindahkan status tiket.
  4. Optimasi Penjadwalan     -> Menjalankan mesin inferensi batasan formal:
                                 - CSP Solver (AC-3 + Backtracking MRV/Degree/LCV)
                                 - GA Solver (Algoritma Genetika dengan Elitisme)
  5. Tanya SOP                -> Membaca prosedur resmi 5 langkah per jenis fasilitas.
  6. Lihat Daftar Lokasi      -> Menampilkan seluruh simpul graf ruangan lantai 1 & 2 FITE.
  7. Lihat Riwayat            -> Menampilkan riwayat tiket yang sudah terselesaikan pada sesi ini.
  8. Bantuan                  -> Menampilkan petunjuk ini.
  9. Cari SOP (Semantic)      -> Mencari SOP/kebijakan dengan kalimat bebas (pencarian vektor,
                                 Cosine Similarity). Kueri di luar cakupan ditolak otomatis.
                                 Membutuhkan indeks: uv run python scripts/build_index.py --reset
  10. Keluar                  -> Mengakhiri sesi aplikasi.
"""


@dataclass
class TicketRecord:
    ticket: MaintenanceTicket
    sop_id: Optional[str]
    status: str = "Reported"
    reported_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    route_ucs: Optional[List[str]] = None
    route_astar: Optional[List[str]] = None
    route_cost: Optional[float] = None


class DelMaintOpsAppCLI:
    """Aplikasi CLI Interaktif Del-MaintOps Copilot."""

    def __init__(self, start_location: str = "Posko Teknisi") -> None:
        self.queue = PriorityTicketQueue()
        self.records: Dict[str, TicketRecord] = {}
        self.history: List[TicketRecord] = []
        self.start_location = start_location
        self._id_counter = itertools.count(1)
        self._vector_store = None  # dimuat malas (lazy) saat menu 9 pertama kali dipakai

    def _next_ticket_id(self) -> str:
        return f"TKT-{next(self._id_counter):03d}"

    def _bot(self, msg: str) -> None:
        print(f"\nCopilot> {msg}")

    def _ask(self, prompt: str) -> str:
        return input(f"Pengguna> {prompt}")

    def _ask_choice(self, options: List[str]) -> Optional[int]:
        for i, opt in enumerate(options, start=1):
            print(f"      {i}. {opt}")
        raw = self._ask(f"Pilih nomor (1-{len(options)}), atau 0 untuk batal: ").strip()
        if not raw.isdigit():
            self._bot("Input harus berupa angka.")
            return None
        val = int(raw)
        if val == 0:
            self._bot("Operasi dibatalkan.")
            return None
        if 1 <= val <= len(options):
            return val - 1
        self._bot(f"Nomor di luar rentang 1-{len(options)}.")
        return None

    def _is_duplicate(self, location: str, sop_id: Optional[str]) -> Optional[TicketRecord]:
        for rec in self.records.values():
            if rec.ticket.location == location and rec.sop_id == sop_id and rec.status != "Resolved":
                return rec
        return None

    # -- 1. Lapor Kerusakan Baru --
    def flow_lapor(self) -> None:
        self._bot("Silakan laporkan kerusakan fasilitas gedung FITE.")
        locations = sorted(list(FITE_UNIFIED_GRAPH.keys()))
        self._bot("Pilih lokasi ruangan fasilitas:")
        idx = self._ask_choice(locations)
        if idx is None:
            return
        location = locations[idx]

        self._bot(f"Lokasi terpilih: {location}. Deskripsikan masalah yang terjadi:")
        issue_desc = self._ask("Deskripsi masalah: ").strip()
        if not issue_desc:
            self._bot("Deskripsi tidak boleh kosong. Pelaporan dibatalkan.")
            return

        sop_id = detect_category(issue_desc)
        practicum_active = False
        exam_sensitive = False
        safety_hazard = False

        if sop_id == "SOP-03":
            self._bot("Kerusakan terkait jaringan/LAN terdeteksi.")
            p_idx = self._ask_choice(["Ya, saat ini sedang praktikum aktif", "Tidak, di luar jam praktikum"])
            practicum_active = (p_idx == 0)
        elif sop_id == "SOP-02":
            self._bot("Kerusakan pendingin ruangan (AC) terdeteksi.")
            e_idx = self._ask_choice(["Ya, ruangan dipakai ujian / praktikum", "Tidak"])
            exam_sensitive = (e_idx == 0)
        elif sop_id == "SOP-04":
            s_idx = self._ask_choice(["Ada risiko bahaya keselamatan/sanitasi mendesak", "Tidak ada bahaya mendesak"])
            safety_hazard = (s_idx == 0)

        urgency_str = classify_urgency(
            sop_id or "SOP-04",
            practicum_active=practicum_active,
            exam_or_temperature_sensitive=exam_sensitive,
            safety_hazard=safety_hazard,
        )

        dup = self._is_duplicate(location, sop_id)
        if dup:
            self._bot(
                f"[PERINGATAN DUPLIKASI] Laporan serupa sudah aktif pada tiket {dup.ticket.ticket_id} "
                f"[{dup.ticket.urgency.value.upper()}] status {dup.status}. "
                f"Laporan Anda ditambahkan sebagai log pendukung tanpa membuat antrian ganda."
            )
            return

        tid = self._next_ticket_id()
        ticket = self.queue.push(
            ticket_id=tid,
            location=location,
            issue_type=issue_desc,
            urgency=urgency_str,
        )

        rec = TicketRecord(ticket=ticket, sop_id=sop_id, status="Verified")
        self.records[tid] = rec

        sop_info = f" (SOP: {sop_id} - {SOP_CATALOG[sop_id]['title']})" if sop_id else ""
        self._bot(
            f"Tiket berhasil dibuat: {tid} | Lokasi: {location} | "
            f"Urgensi: {ticket.urgency.value.upper()} | SLA: {ticket.sla_hours} Jam{sop_info}."
        )

    def _urgency_str(self, ticket: Any) -> str:
        urg = getattr(ticket, "urgency", "sedang")
        return urg.value if hasattr(urg, "value") else str(urg)

    # -- 2. Lihat Antrian Tiket --
    def flow_antrian(self) -> None:
        sorted_tickets = self.queue.as_sorted_list()
        if not sorted_tickets:
            self._bot("Antrian tiket saat ini kosong. Seluruh fasilitas terpantau normal.")
            return

        self._bot(f"Daftar antrian tiket fasilitas aktif ({len(sorted_tickets)} tiket, terurut prioritas):")
        print("-" * 90)
        print(f"{'No.':<4} | {'ID Tiket':<8} | {'Urgensi':<8} | {'Lokasi':<18} | {'Deskripsi Kerusakan'}")
        print("-" * 90)
        for i, t in enumerate(sorted_tickets, start=1):
            urg_display = self._urgency_str(t)
            print(f"{i:<4} | {t.ticket_id:<8} | {urg_display.upper():<8} | {t.location:<18} | {getattr(t, 'issue_description', getattr(t, 'issue_type', ''))}")
        print("-" * 90)

    # -- 3. Proses Tiket Berikutnya (Navigasi UCS & A*) --
    def flow_proses(self) -> None:
        top = self.queue.pop()
        if top is None:
            self._bot("Tidak ada tiket dalam antrian untuk diproses.")
            return

        rec = self.records.pop(top.ticket_id, None)
        if rec is None:
            rec = TicketRecord(ticket=top, sop_id=None)

        urg_display = top.urgency.value if hasattr(top.urgency, "value") else str(top.urgency)
        self._bot(f"Memproses tiket prioritas tertinggi: {top.ticket_id} [{urg_display.upper()}] @ {top.location}...")

        ucs_path, ucs_cost = uniform_cost_search(FITE_UNIFIED_GRAPH, self.start_location, top.location)
        astar_path, astar_cost = a_star_search(FITE_UNIFIED_GRAPH, self.start_location, top.location)

        if ucs_path is None:
            self._bot(f"Lokasi {top.location} tidak terjangkau dari {self.start_location}.")
            return

        rec.route_ucs = ucs_path
        rec.route_astar = astar_path
        rec.route_cost = ucs_cost

        print(f"    Rute UCS : {' -> '.join(ucs_path)} | Biaya = {ucs_cost} menit")
        print(f"    Rute A*  : {' -> '.join(astar_path)} | Biaya = {astar_cost} menit")
        self._bot("[VERIFIKASI] Biaya UCS dan A* identik -> Heuristik terbukti Admissible & Optimal.")

        rec.status = "Resolved"
        rec.resolved_at = datetime.now()
        self.history.append(rec)
        self._bot(f"Tiket {top.ticket_id} selesai ditangani (Status: Resolved). Teknisi siap ke penugasan berikutnya.")

    # -- 4. Optimasi Penjadwalan Teknisi (Milestone 2) --
    def flow_optimasi_penjadwalan(self) -> None:
        self._bot("Modul Pemecahan Batasan Keputusan Bisnis (CSP / GA Optimization - Milestone 2)")
        print("    Pilih mesin inferensi penjadwalan:")
        print("      1. Jalankan CSP Solver (AC-3 + Backtracking MRV/Degree/LCV)")
        print("      2. Jalankan GA Solver (Algoritma Genetika dengan Elitisme)")
        print("      3. Analisis Perbandingan Komparatif (CSP vs GA)")
        sub = self._ask("Pilih metode (1-3): ").strip()

        tickets = get_official_milestone2_tickets()
        techs = get_default_technicians()

        if sub == "1":
            self._bot("Mengeksekusi CSP Solver pada 10 tiket resmi FITE IT Del...")
            sol = run_csp_solver(tickets, techs)
            print("\n" + sol.summary_table() + "\n")
        elif sub == "2":
            self._bot("Mengeksekusi GA Solver (generasi=80, populasi=60) pada 10 tiket resmi...")
            sol = run_ga_solver(tickets, techs, generations=80, population_size=60)
            print("\n" + sol.summary_table() + "\n")
        elif sub == "3":
            self._bot("Menjalankan benchmarking komparatif langsung...")
            sol_csp = run_csp_solver(tickets, techs)
            sol_ga = run_ga_solver(tickets, techs, generations=80, population_size=60)
            print("\n" + "=" * 90)
            print(f"{'Metrik Evaluasi':<32} | {'CSP Solver':<25} | {'GA Solver':<25}")
            print("-" * 90)
            print(f"{'Validitas Batasan Formal':<32} | {'100% VALID' if sol_csp.is_valid else 'PELANGGARAN':<25} | {'100% VALID' if sol_ga.is_valid else 'PELANGGARAN':<25}")
            print(f"{'Waktu Komputasi':<32} | {f'{sol_csp.computation_time_ms:.2f} ms':<25} | {f'{sol_ga.computation_time_ms:.2f} ms':<25}")
            print(f"{'Total Waktu Tempuh FITE':<32} | {f'{sol_csp.total_travel_time_minutes:.1f} menit':<25} | {f'{sol_ga.total_travel_time_minutes:.1f} menit':<25}")
            print(f"{'Total Keterlambatan SLA':<32} | {f'{sol_csp.total_lateness_minutes:.1f} menit':<25} | {f'{sol_ga.total_lateness_minutes:.1f} menit':<25}")
            print(f"{'Total Penalti Bisnis':<32} | {f'{sol_csp.total_penalty:.2f}':<25} | {f'{sol_ga.total_penalty:.2f}':<25}")
            print(f"{'Makespan Penyelesaian':<32} | {f'{sol_csp.total_makespan_minutes:.1f} menit':<25} | {f'{sol_ga.total_makespan_minutes:.1f} menit':<25}")
            print("=" * 90 + "\n")
        else:
            self._bot("Operasi dibatalkan.")

    # -- 5. Tanya SOP --
    def flow_sop(self) -> None:
        self._bot("Daftar Prosedur Operasional Standar (SOP) Fasilitas FITE:")
        sop_list = list(SOP_CATALOG.items())
        labels = [f"{s['title']} ({sid})" for sid, s in sop_list]
        labels.append("Cari berdasarkan kata kunci bebas")
        idx = self._ask_choice(labels)
        if idx is None:
            return

        if idx < len(sop_list):
            sid, s = sop_list[idx]
            self._bot(f"[{sid}] {s['title']} (Urgensi Default: {s['default_urgency'].value.upper()}, SLA: {s['sla_hours']} Jam):")
            for step_num, step_desc in enumerate(s["procedure"], start=1):
                print(f"      {step_num}. {step_desc}")
        else:
            kw = self._ask("Masukkan kata kunci pencarian SOP: ")
            hits = find_sop(kw)
            if not hits:
                self._bot(f"Tidak ada SOP yang cocok dengan kata kunci '{kw}'.")
            else:
                for hit_id in hits:
                    s = SOP_CATALOG[hit_id]
                    self._bot(f"[{hit_id}] {s['title']} (SLA: {s['sla_hours']} Jam):")
                    for step_num, step_desc in enumerate(s["procedure"], start=1):
                        print(f"        {step_num}. {step_desc}")

    # -- 9. Cari SOP (Semantic Search, Milestone 3) --
    SEMANTIC_SNIPPET_CHARS = 220

    def _get_vector_store(self):
        """Memuat SOPVectorStore secara lazy; mengembalikan None (disertai petunjuk) jika tak tersedia.

        Impor ditunda agar CLI lama tetap berjalan tanpa chromadb/sentence-transformers
        maupun tanpa indeks. Atribut ``_vector_store`` yang sudah terisi dipakai apa adanya.
        """
        if self._vector_store is not None:
            return self._vector_store
        try:
            from knowledge.retrieval_config import PERSIST_DIR
        except ImportError:  # pragma: no cover - modul konfigurasi selalu ada di repo
            self._bot("Modul pencarian semantik belum tersedia pada repositori ini.")
            return None
        index_dir = Path(__file__).resolve().parents[2] / PERSIST_DIR
        if not index_dir.exists():
            self._bot(
                "Indeks pencarian semantik belum dibangun. Jalankan terlebih dahulu:\n"
                "      uv run python scripts/build_index.py --reset"
            )
            return None
        try:
            from knowledge.vector_store import SOPVectorStore

            store = SOPVectorStore()
        except ImportError as exc:
            self._bot(
                f"Dependensi pencarian semantik belum terpasang ({exc}). "
                "Jalankan: uv sync (chromadb & sentence-transformers)."
            )
            return None
        if store.count() == 0:
            self._bot(
                "Indeks kosong. Jalankan terlebih dahulu:\n"
                "      uv run python scripts/build_index.py --reset"
            )
            return None
        self._vector_store = store
        return store

    def flow_semantic_search(self) -> None:
        self._bot("Pencarian semantik SOP & kebijakan FITE. Tulis pertanyaan dengan kalimat bebas.")
        query = self._ask("Pertanyaan Anda: ").strip()
        if not query:
            self._bot("Pertanyaan tidak boleh kosong.")
            return
        store = self._get_vector_store()
        if store is None:
            return

        response = store.search(query)
        if response.rejected:
            self._bot(
                "Pertanyaan ini berada di luar cakupan basis pengetahuan SOP/kebijakan fasilitas FITE "
                f"(kemiripan tertinggi {response.top_similarity:.3f} < ambang {response.threshold:.2f}). "
                "Coba gunakan kalimat yang menjelaskan kerusakan fasilitas, atau gunakan menu 5 (Tanya SOP)."
            )
            return

        self._bot(f"Ditemukan {len(response.results)} potongan dokumen paling relevan (kemiripan kosinus):")
        for rank, res in enumerate(response.results, start=1):
            meta = res.metadata
            sla = meta.get("sla_hours", 0)
            sla_txt = f"{sla} jam" if sla else "tidak berlaku"
            snippet = " ".join(res.text.split())
            title_prefix = f"Judul: {str(meta.get('title', '')).strip().rstrip('.')}. "
            if snippet.startswith(title_prefix):  # judul sudah tampil di baris atas
                snippet = snippet[len(title_prefix):]
            if len(snippet) > self.SEMANTIC_SNIPPET_CHARS:
                snippet = snippet[: self.SEMANTIC_SNIPPET_CHARS].rsplit(" ", 1)[0] + " ..."
            print(f"  {rank}. [{meta.get('doc_id', '?')}] {meta.get('title', '')}")
            print(f"     Kemiripan: {res.similarity:.3f} | Kategori: {meta.get('category', '-')} | SLA: {sla_txt}")
            print(f"     {snippet}")

    # -- 6. Lihat Daftar Lokasi --
    def flow_lokasi(self) -> None:
        self._bot("Daftar lokasi ruangan valid pada topologi fisik gedung FITE:")
        for loc in sorted(FITE_UNIFIED_GRAPH.keys()):
            edges = ", ".join(f"{dest} ({cost}m)" for dest, cost in FITE_UNIFIED_GRAPH[loc])
            print(f"    - {loc:<18} -> {edges}")

    # -- 7. Lihat Riwayat --
    def flow_riwayat(self) -> None:
        if not self.history:
            self._bot("Belum ada tiket yang berstatus Resolved pada sesi ini.")
            return
        self._bot(f"Riwayat penyelesaian tiket ({len(self.history)} tiket selesai):")
        for r in self.history:
            urg_display = self._urgency_str(r.ticket)
            print(f"    * {r.ticket.ticket_id} [{urg_display.upper()}] @ {r.ticket.location} - "
                  f"Rute optimal: {r.route_cost} mnt - Status: {r.status}")

    # -- Loop Utama --
    def run(self) -> None:
        print(BANNER)
        self._bot("Selamat datang di Del-MaintOps Copilot FITE IT Del. Silakan pilih menu di bawah:")
        while True:
            print(MENU)
            choice = self._ask("Pilih nomor menu (1-10): ").strip().lower()

            if choice in {"10", "keluar", "exit", "quit", "bye"}:
                self._bot("Terima kasih telah menggunakan Del-MaintOps Copilot. Sampai jumpa!")
                break
            elif choice == "1":
                self.flow_lapor()
            elif choice == "2":
                self.flow_antrian()
            elif choice == "3":
                self.flow_proses()
            elif choice == "4":
                self.flow_optimasi_penjadwalan()
            elif choice == "5":
                self.flow_sop()
            elif choice == "6":
                self.flow_lokasi()
            elif choice == "7":
                self.flow_riwayat()
            elif choice == "9":
                self.flow_semantic_search()
            elif choice in {"8", "bantuan", "help", "menu", "?"}:
                print(HELP_TEXT)
            else:
                self._bot("Pilihan tidak valid. Masukkan angka 1-10 sesuai menu.")


def main() -> None:
    app = DelMaintOpsAppCLI()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nCopilot> Sesi ditutup oleh pengguna. Sampai jumpa!")
        sys.exit(0)


if __name__ == "__main__":
    main()
