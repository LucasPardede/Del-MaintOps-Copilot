"""
Del-MaintOps Copilot - Data Models & Domain Entities
---------------------------------------------------
Milestone 2 (W04): Modul Pemecahan Batasan Keputusan Bisnis (CSP / GA Optimization).

Modul ini mendefinisikan entitas bisnis formal untuk penjadwalan dan alokasi
tugas penanganan fasilitas di FITE IT Del:
- UrgencyLevel & SLA mapping
- SkillCategory & FacilityType
- Ticket & Technician representation
- Assignment & ScheduleSolution
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class UrgencyLevel(str, Enum):
    """Tingkat urgensi / keparahan kerusakan fasilitas."""
    TINGGI = "Tinggi"
    SEDANG = "Sedang"
    RENDAH = "Rendah"

    @property
    def priority_rank(self) -> int:
        """Nilai hierarkis untuk prioritas absolut (lebih tinggi = lebih prioritas)."""
        mapping = {
            UrgencyLevel.TINGGI: 3,
            UrgencyLevel.SEDANG: 2,
            UrgencyLevel.RENDAH: 1,
        }
        return mapping[self]

    @property
    def default_sla_hours(self) -> int:
        """Target Service Level Agreement (SLA) dalam jam berdasarkan regulasi FITE."""
        mapping = {
            UrgencyLevel.TINGGI: 2,    # 2 Jam
            UrgencyLevel.SEDANG: 24,   # 24 Jam
            UrgencyLevel.RENDAH: 72,   # 72 Jam
        }
        return mapping[self]


class SkillCategory(str, Enum):
    """Kategori spesialisasi kompetensi teknisi berdasarkan SOP FITE."""
    ELECTRICAL = "Kelistrikan & Sarpras"
    NETWORK = "Jaringan & Komunikasi"
    AV = "Audio-Visual & Presentasi"
    COMPUTING = "Komputasi & Sistem Labkom"
    HVAC = "Mekanikal & Pendingin (AC)"
    GENERAL = "Pemeliharaan Umum"


# Metadata fasilitas: pemetaan ke SkillCategory, perkiraan durasi kerja dasar (menit), dan urgensi default
FACILITY_SPECS: Dict[str, Dict[str, object]] = {
    "Mati Listrik": {
        "skill": SkillCategory.ELECTRICAL,
        "default_urgency": UrgencyLevel.TINGGI,
        "est_duration_minutes": 45,
        "description": "Korsleting, beban lebih panel server, MCB trip",
    },
    "Proyektor": {
        "skill": SkillCategory.AV,
        "default_urgency": UrgencyLevel.TINGGI,
        "est_duration_minutes": 35,
        "description": "Lampu mati, over-heating, no HDMI signal",
    },
    "Idea Hub": {
        "skill": SkillCategory.AV,
        "default_urgency": UrgencyLevel.TINGGI,
        "est_duration_minutes": 40,
        "description": "Touchscreen hang, port presentasi bermasalah",
    },
    "PC": {
        "skill": SkillCategory.COMPUTING,
        "default_urgency": UrgencyLevel.SEDANG,
        "est_duration_minutes": 50,
        "description": "OS corrupt, hardware beep error, backup & restore",
    },
    "AC": {
        "skill": SkillCategory.HVAC,
        "default_urgency": UrgencyLevel.SEDANG,
        "est_duration_minutes": 45,
        "description": "Bocor air di atas perangkat, freon kurang, drain tersumbat",
    },
    "LAN": {
        "skill": SkillCategory.NETWORK,
        "default_urgency": UrgencyLevel.SEDANG,
        "est_duration_minutes": 30,
        "description": "Kabel putus, crimping ulang RJ-45, port switch error",
    },
    "WiFi": {
        "skill": SkillCategory.NETWORK,
        "default_urgency": UrgencyLevel.SEDANG,
        "est_duration_minutes": 25,
        "description": "Access Point hang/mati, controller IP issue",
    },
    "Colokan": {
        "skill": SkillCategory.ELECTRICAL,
        "default_urgency": UrgencyLevel.RENDAH,
        "est_duration_minutes": 20,
        "description": "Stop kontak kendor, penggantian modul saklar",
    },
    "Keyboard": {
        "skill": SkillCategory.COMPUTING,
        "default_urgency": UrgencyLevel.RENDAH,
        "est_duration_minutes": 15,
        "description": "Tombol macet, switch rusak, penggantian unit dari gudang",
    },
    "CCTV": {
        "skill": SkillCategory.NETWORK,
        "default_urgency": UrgencyLevel.RENDAH,
        "est_duration_minutes": 30,
        "description": "Kalibrasi sudut lensa, konektor BNC/UTP DVR",
    },
}


@dataclass
class Technician:
    """Entitas teknisi fasilitas FITE IT Del."""
    tech_id: str
    name: str
    skills: Set[SkillCategory]
    base_location: str = "Posko Teknisi"
    shift_start_minute: int = 480   # 08:00 WIB (menit sejak 00:00)
    shift_end_minute: int = 1020    # 17:00 WIB (menit sejak 00:00, 9 jam inklusif istirahat)
    max_work_minutes: int = 480     # 8 jam kerja aktif maksimal per hari

    def can_handle(self, required_skill: SkillCategory) -> bool:
        """Memeriksa apakah teknisi memiliki kualifikasi untuk menangani masalah."""
        return (required_skill in self.skills) or (required_skill == SkillCategory.GENERAL)


@dataclass
class MaintenanceTicket:
    """Entitas tiket laporan kerusakan fasilitas."""
    ticket_id: str
    location: str
    facility: str
    issue_description: str
    request_time: datetime
    urgency: UrgencyLevel
    sla_hours: int = 2
    estimated_duration_minutes: int = 30
    required_skill: SkillCategory = SkillCategory.GENERAL

    def __post_init__(self) -> None:
        # Isi otomatis metadata fasilitas jika belum diset secara spesifik
        if self.facility in FACILITY_SPECS:
            spec = FACILITY_SPECS[self.facility]
            if self.required_skill == SkillCategory.GENERAL:
                self.required_skill = spec["skill"]  # type: ignore
            if self.sla_hours == 2 and self.urgency != UrgencyLevel.TINGGI:
                self.sla_hours = self.urgency.default_sla_hours
            if self.estimated_duration_minutes == 30:
                self.estimated_duration_minutes = spec["est_duration_minutes"]  # type: ignore

    @property
    def deadline(self) -> datetime:
        """Tenggat waktu penyelesaian sesuai SLA resmi."""
        return self.request_time + timedelta(hours=self.sla_hours)

    def is_compatible_technician(self, tech: Technician) -> bool:
        """Pemeriksaan kelayakan teknisi terhadap batasan kualifikasi SOP."""
        # SOP Khusus: "Perbaikan Mati Listrik TIDAK BOLEH dilakukan oleh teknisi jaringan, harus teknisi sarpras/listrik"
        if self.facility == "Mati Listrik":
            return SkillCategory.ELECTRICAL in tech.skills
        return tech.can_handle(self.required_skill)


@dataclass
class TaskAssignment:
    """Hasil alokasi tugas spesifik kepada teknisi pada jadwal tertentu."""
    ticket: MaintenanceTicket
    technician: Technician
    start_time: datetime
    finish_time: datetime
    travel_time_minutes: int
    wait_time_minutes: int
    sla_violated: bool
    lateness_minutes: int = 0
    penalty: float = 0.0


@dataclass
class ScheduleSolution:
    """Solusi jadwal operasional lengkap untuk sekumpulan tiket."""
    assignments: List[TaskAssignment]
    is_valid: bool
    total_makespan_minutes: float
    total_travel_time_minutes: float
    total_lateness_minutes: float
    total_penalty: float
    violations: List[str] = field(default_factory=list)
    technician_workloads: Dict[str, int] = field(default_factory=dict)
    algorithm_name: str = "Unknown"
    computation_time_ms: float = 0.0
    explored_states_or_generations: int = 0

    def summary_table(self) -> str:
        """Menghasilkan representasi tabel teks yang rapi dari penugasan."""
        lines = [
            f"=== JADWAL PENUGASAN TEKNISI ({self.algorithm_name}) ===",
            f"Status Validasi : {'[VALID - SEMUA BATASAN TERPENUHI]' if self.is_valid else '[INVALID - TERDAPAT PELANGGARAN]'}",
            f"Waktu Komputasi : {self.computation_time_ms:.2f} ms | Evaluasi: {self.explored_states_or_generations}",
            f"Total Travel   : {self.total_travel_time_minutes:.1f} mnt | Total Keterlambatan: {self.total_lateness_minutes:.1f} mnt | Penalti: {self.total_penalty:.2f}",
            "-" * 105,
            f"{'ID Tiket':<8} | {'Urgensi':<7} | {'Fasilitas':<12} | {'Lokasi':<12} | {'Teknisi':<10} | {'Mulai':<5} | {'Selesai':<5} | {'Travel':<6} | {'SLA':<8}",
            "-" * 105,
        ]
        for a in self.assignments:
            start_str = a.start_time.strftime("%H:%M")
            fin_str = a.finish_time.strftime("%H:%M")
            sla_status = "ON-TIME" if not a.sla_violated else f"+{a.lateness_minutes}m (TELAT)"
            lines.append(
                f"{a.ticket.ticket_id:<8} | {a.ticket.urgency.value:<7} | {a.ticket.facility:<12} | "
                f"{a.ticket.location:<12} | {a.technician.name:<10} | {start_str:<5} | {fin_str:<5} | "
                f"{a.travel_time_minutes} mnt{'':<2} | {sla_status:<8}"
            )
        lines.append("-" * 105)
        if self.violations:
            lines.append("PELANGGARAN BATASAN:")
            for v in self.violations:
                lines.append(f"  - [WARNING] {v}")
        return "\n".join(lines)
