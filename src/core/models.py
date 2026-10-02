"""
Del-MaintOps Copilot - Core Domain Models & Data Structures
-----------------------------------------------------------
Modul ini mendefinisikan seluruh entitas domain inti sistem secara formal:
- UrgencyLevel & SLA mapping
- SkillCategory & Facility Specifications
- Technician entity & Qualification rules
- Ticket (M1 backward compatibility) & MaintenanceTicket (M2)
- PriorityTicketQueue (heapq dengan dukungan FIFO tie-breaker)
- TaskAssignment & ScheduleSolution
"""

from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class UrgencyLevel(str, Enum):
    """Tingkat urgensi / keparahan kerusakan fasilitas gedung FITE."""
    KRITIS = "kritis"
    TINGGI = "tinggi"
    SEDANG = "sedang"
    RENDAH = "rendah"

    @property
    def priority_rank(self) -> int:
        """Nilai hierarkis untuk prioritas absolut (lebih tinggi = lebih mendesak)."""
        mapping = {
            UrgencyLevel.KRITIS: 4,
            UrgencyLevel.TINGGI: 3,
            UrgencyLevel.SEDANG: 2,
            UrgencyLevel.RENDAH: 1,
        }
        return mapping[self]

    @property
    def heap_weight(self) -> int:
        """Bobot min-heap (skor lebih kecil = keluar lebih dulu di PriorityQueue)."""
        mapping = {
            UrgencyLevel.KRITIS: 0,
            UrgencyLevel.TINGGI: 1,
            UrgencyLevel.SEDANG: 2,
            UrgencyLevel.RENDAH: 3,
        }
        return mapping[self]

    @property
    def default_sla_hours(self) -> int:
        """Target Service Level Agreement (SLA) dalam jam berdasarkan regulasi FITE."""
        mapping = {
            UrgencyLevel.KRITIS: 1,    # 1 Jam (mis. jaringan lab mati saat jam praktikum)
            UrgencyLevel.TINGGI: 2,    # 2 Jam
            UrgencyLevel.SEDANG: 24,   # 24 Jam
            UrgencyLevel.RENDAH: 72,   # 72 Jam
        }
        return mapping[self]

    @classmethod
    def from_str(cls, value: str) -> UrgencyLevel:
        """Parsing string ke UrgencyLevel case-insensitive."""
        val = value.strip().lower()
        for member in cls:
            if member.value == val:
                return member
        raise ValueError(f"Urgensi tidak dikenal: {value!r}")


class SkillCategory(str, Enum):
    """Kategori spesialisasi kompetensi teknisi berdasarkan SOP FITE."""
    ELECTRICAL = "Kelistrikan & Sarpras"
    NETWORK = "Jaringan & Komunikasi"
    AV = "Audio-Visual & Presentasi"
    COMPUTING = "Komputasi & Sistem Labkom"
    HVAC = "Mekanikal & Pendingin (AC)"
    GENERAL = "Pemeliharaan Umum"


# Metadata pemetaan fasilitas ke spesifikasi kompetensi teknis & perkiraan durasi
FACILITY_SPECS: Dict[str, Dict[str, Any]] = {
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
    "Saung": {
        "skill": SkillCategory.GENERAL,
        "default_urgency": UrgencyLevel.RENDAH,
        "est_duration_minutes": 30,
        "description": "Kerusakan kursi atau meja gazebo saung",
    },
    "Toilet": {
        "skill": SkillCategory.GENERAL,
        "default_urgency": UrgencyLevel.RENDAH,
        "est_duration_minutes": 35,
        "description": "Saluran tersumbat atau kran air bocor",
    },
}


@dataclass
class Technician:
    """Entitas teknisi fasilitas FITE IT Del."""
    tech_id: str
    name: str
    skills: Set[SkillCategory]
    base_location: str = "Posko Teknisi"
    shift_start_minute: int = 480   # 08:00 WIB
    shift_end_minute: int = 1020    # 17:00 WIB
    max_work_minutes: int = 480     # 8 jam kerja aktif per hari

    def can_handle(self, required_skill: SkillCategory) -> bool:
        """Memeriksa kelayakan teknisi terhadap keahlian yang dipersyaratkan."""
        return (required_skill in self.skills) or (required_skill == SkillCategory.GENERAL)


@dataclass(order=True)
class Ticket:
    """Representasi satu tiket laporan kerusakan fasilitas (Milestone 1 format)."""
    priority_score: float
    ticket_id: str = field(compare=False)
    location: str = field(compare=False)
    issue_type: str = field(compare=False)
    urgency: str = field(compare=False)  # "kritis" | "tinggi" | "sedang" | "rendah"

    @property
    def issue_description(self) -> str:
        return self.issue_type

    @property
    def facility(self) -> str:
        for k in FACILITY_SPECS:
            if k.lower() in self.issue_type.lower():
                return k
        return "General"

    @property
    def request_time(self) -> datetime:
        return datetime(2026, 10, 2, 8, 0)

    @property
    def sla_hours(self) -> int:
        u = UrgencyLevel.from_str(self.urgency)
        return u.default_sla_hours

    @property
    def estimated_duration_minutes(self) -> int:
        return 30

    @property
    def required_skill(self) -> SkillCategory:
        return SkillCategory.GENERAL

    def is_compatible_technician(self, tech: Technician) -> bool:
        return True


@dataclass
class MaintenanceTicket:
    """Entitas laporan kerusakan fasilitas terpadu (Milestone 2 format)."""
    ticket_id: str
    location: str
    facility: str
    issue_description: str
    request_time: datetime = field(default_factory=datetime.now)
    urgency: UrgencyLevel = UrgencyLevel.SEDANG
    sla_hours: int = 24
    estimated_duration_minutes: int = 30
    required_skill: SkillCategory = SkillCategory.GENERAL

    # Atribut backward-compatibility untuk Milestone 1
    @property
    def issue_type(self) -> str:
        return self.issue_description

    @property
    def priority_score(self) -> float:
        return float(self.urgency.heap_weight)

    def __post_init__(self) -> None:
        if isinstance(self.urgency, str):
            self.urgency = UrgencyLevel.from_str(self.urgency)

        if self.facility in FACILITY_SPECS:
            spec = FACILITY_SPECS[self.facility]
            if self.required_skill == SkillCategory.GENERAL:
                self.required_skill = spec["skill"]
            if self.estimated_duration_minutes == 30:
                self.estimated_duration_minutes = spec["est_duration_minutes"]

        if self.sla_hours == 24 and self.urgency != UrgencyLevel.SEDANG:
            self.sla_hours = self.urgency.default_sla_hours

    @property
    def deadline(self) -> datetime:
        return self.request_time + timedelta(hours=self.sla_hours)

    def is_compatible_technician(self, tech: Technician) -> bool:
        if self.facility == "Mati Listrik":
            return SkillCategory.ELECTRICAL in tech.skills
        return tech.can_handle(self.required_skill)


URGENCY_WEIGHT = {"kritis": 0, "tinggi": 1, "sedang": 2, "rendah": 3}


class PriorityTicketQueue:
    """Antrean prioritas tiket kerusakan menggunakan heapq (min-heap)."""

    def __init__(self) -> None:
        self._heap: List[Tuple[float, int, Ticket]] = []
        self._counter = itertools.count()

    def push(self, ticket_id: str, location: str, issue_type: str, urgency: str) -> None:
        if urgency not in URGENCY_WEIGHT:
            raise ValueError(f"Urgensi tidak dikenal: {urgency!r}")
        score = float(URGENCY_WEIGHT[urgency])
        ticket = Ticket(score, ticket_id, location, issue_type, urgency)
        heapq.heappush(self._heap, (score, next(self._counter), ticket))

    def push_ticket(self, ticket: Any) -> None:
        urg = getattr(ticket, "urgency", "sedang")
        urg_str = urg.value if isinstance(urg, UrgencyLevel) else str(urg).lower()
        score = float(URGENCY_WEIGHT.get(urg_str, 2))
        if isinstance(ticket, Ticket):
            t = ticket
        else:
            t = Ticket(score, ticket.ticket_id, ticket.location, ticket.issue_description, urg_str)
        heapq.heappush(self._heap, (score, next(self._counter), t))

    def pop(self) -> Optional[Ticket]:
        if not self._heap:
            return None
        _, _, ticket = heapq.heappop(self._heap)
        return ticket

    def as_sorted_list(self) -> List[Ticket]:
        return [t for _, _, t in sorted(self._heap)]

    def __len__(self) -> int:
        return len(self._heap)


@dataclass
class TaskAssignment:
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
    assignments: List[TaskAssignment]
    is_valid: bool
    total_makespan_minutes: float
    total_travel_time_minutes: float
    total_lateness_minutes: float
    total_penalty: float
    violations: List[str] = field(default_factory=list)
    technician_workloads: Dict[str, int] = field(default_factory=dict)
    algorithm_name: str = "Unknown Algorithm"
    computation_time_ms: float = 0.0
    explored_states_or_generations: int = 0

    def summary_table(self) -> str:
        lines = [
            f"=== HASIL PENJADWALAN TEKNISI [{self.algorithm_name}] ===",
            f"Status Kelayakan : {'[100% VALID - SEMUA BATASAN TERPENUHI]' if self.is_valid else '[INVALID - ADA PELANGGARAN]'}",
            f"Waktu Komputasi  : {self.computation_time_ms:.2f} ms | Evaluasi: {self.explored_states_or_generations}",
            f"Total Travel     : {self.total_travel_time_minutes:.1f} mnt | Keterlambatan: {self.total_lateness_minutes:.1f} mnt | Total Penalti: {self.total_penalty:.2f}",
            "-" * 105,
            f"{'ID Tiket':<8} | {'Urgensi':<7} | {'Fasilitas':<12} | {'Lokasi':<12} | {'Teknisi':<10} | {'Mulai':<5} | {'Selesai':<5} | {'Travel':<6} | {'SLA':<8}",
            "-" * 105,
        ]
        for a in self.assignments:
            start_str = a.start_time.strftime("%H:%M")
            fin_str = a.finish_time.strftime("%H:%M")
            sla_status = "ON-TIME" if not a.sla_violated else f"+{a.lateness_minutes}m (TELAT)"
            lines.append(
                f"{a.ticket.ticket_id:<8} | {a.ticket.urgency.value.capitalize():<7} | {a.ticket.facility:<12} | "
                f"{a.ticket.location:<12} | {a.technician.name.split()[0]:<10} | {start_str:<5} | {fin_str:<5} | "
                f"{a.travel_time_minutes} mnt{'':<2} | {sla_status:<8}"
            )
        lines.append("-" * 105)
        if self.violations:
            lines.append("DAFTAR PELANGGARAN BATASAN:")
            for v in self.violations:
                lines.append(f"  * {v}")
        return "\n".join(lines)
