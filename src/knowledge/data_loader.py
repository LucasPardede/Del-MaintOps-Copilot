"""
Del-MaintOps Copilot - Data Loader & Benchmark Scenario Provider
----------------------------------------------------------------
Modul penyedia data:
1. 10 Tiket Dummy Resmi dari Dokumen Spesifikasi Milestone 2 (TK-017 s/d TK-026).
2. Pool Teknisi FITE IT Del dengan pembagian spesialisasi kualifikasi SOP.
3. Generator Dataset Sintetis untuk Skalabilitas (5, 10, 25, 50 tiket).
4. Edge Case Generator untuk Stress Testing Solver (Over-constrained, Surge, Single Tech).
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from core.models import (
    FACILITY_SPECS,
    MaintenanceTicket,
    SkillCategory,
    Technician,
    UrgencyLevel,
)


def get_default_technicians() -> List[Technician]:
    """Mengembalikan daftar 3 teknisi standar FITE IT Del dengan pembagian kompetensi SOP."""
    return [
        Technician(
            tech_id="TECH-01",
            name="Binsar (Sarpras & Kelistrikan)",
            skills={SkillCategory.ELECTRICAL, SkillCategory.HVAC, SkillCategory.GENERAL},
            base_location="Posko Teknisi",
            shift_start_minute=480,  # 08:00
            shift_end_minute=1020,   # 17:00
            max_work_minutes=480,
        ),
        Technician(
            tech_id="TECH-02",
            name="Roy (Jaringan & Labkom)",
            skills={SkillCategory.NETWORK, SkillCategory.COMPUTING, SkillCategory.GENERAL},
            base_location="Posko Teknisi",
            shift_start_minute=480,  # 08:00
            shift_end_minute=1020,   # 17:00
            max_work_minutes=480,
        ),
        Technician(
            tech_id="TECH-03",
            name="Togu (Audio-Visual & Hardware)",
            skills={SkillCategory.AV, SkillCategory.COMPUTING, SkillCategory.GENERAL},
            base_location="Posko Teknisi",
            shift_start_minute=480,  # 08:00
            shift_end_minute=1020,   # 17:00
            max_work_minutes=480,
        ),
    ]


def get_official_milestone2_tickets() -> List[MaintenanceTicket]:
    """Mengembalikan 10 tiket dummy resmi sesuai tabel spesifikasi Milestone 2."""
    raw_data = [
        ("TK-020", "Labkom 725", "Mati Listrik", "Korsleting di panel server lab, listrik padam.",
         datetime(2026, 10, 2, 8, 0), UrgencyLevel.TINGGI, 2, 45, SkillCategory.ELECTRICAL),
        ("TK-017", "Kelas 711", "Proyektor", "Mati total saat kelas berlangsung.",
         datetime(2026, 10, 2, 8, 30), UrgencyLevel.TINGGI, 2, 35, SkillCategory.AV),
        ("TK-022", "Kelas 712", "Idea Hub", "Layar sentuh hang, presentasi terhenti.",
         datetime(2026, 10, 2, 9, 15), UrgencyLevel.TINGGI, 2, 40, SkillCategory.AV),
        ("TK-018", "Labkom 714", "PC", "3 unit PC di baris C gagal masuk sistem Windows.",
         datetime(2026, 10, 2, 8, 15), UrgencyLevel.SEDANG, 24, 50, SkillCategory.COMPUTING),
        ("TK-023", "Labkom 714", "AC", "AC bocor meneteskan air ke meja PC.",
         datetime(2026, 10, 2, 8, 45), UrgencyLevel.SEDANG, 24, 45, SkillCategory.HVAC),
        ("TK-021", "Labkom 716", "LAN", "Koneksi terputus di 2 meja pojok belakang.",
         datetime(2026, 10, 2, 10, 0), UrgencyLevel.SEDANG, 24, 30, SkillCategory.NETWORK),
        ("TK-024", "Kelas 721", "WiFi", "Sinyal Access Point mati/tidak terdeteksi.",
         datetime(2026, 10, 2, 11, 30), UrgencyLevel.SEDANG, 24, 25, SkillCategory.NETWORK),
        ("TK-019", "Kelas 722", "Colokan", "2 slot stop kontak belakang kendor.",
         datetime(2026, 10, 2, 7, 30), UrgencyLevel.RENDAH, 72, 20, SkillCategory.ELECTRICAL),
        ("TK-025", "Labkom 726", "Keyboard", "Tombol spasi macet di PC-15.",
         datetime(2026, 10, 2, 9, 30), UrgencyLevel.RENDAH, 72, 15, SkillCategory.COMPUTING),
        ("TK-026", "Labkom 713", "CCTV", "Kamera bergeser menghadap plafon.",
         datetime(2026, 10, 2, 11, 0), UrgencyLevel.RENDAH, 72, 30, SkillCategory.NETWORK),
    ]

    tickets: List[MaintenanceTicket] = []
    for tid, loc, fac, desc, req_time, urg, sla, dur, skill in raw_data:
        tickets.append(
            MaintenanceTicket(
                ticket_id=tid,
                location=loc,
                facility=fac,
                issue_description=desc,
                request_time=req_time,
                urgency=urg,
                sla_hours=sla,
                estimated_duration_minutes=dur,
                required_skill=skill,
            )
        )
    return tickets


def generate_synthetic_tickets(
    count: int,
    base_date: datetime = datetime(2026, 10, 2, 8, 0),
    seed: int = 42,
) -> List[MaintenanceTicket]:
    """Menghasilkan dataset tiket sintetis untuk benchmarking skalabilitas (25, 50, 100 tiket)."""
    random.seed(seed)
    locations = [
        "Kelas 711", "Kelas 712", "Kelas 721", "Kelas 722",
        "Labkom 713", "Labkom 714", "Labkom 715", "Labkom 716",
        "Labkom 723", "Labkom 724", "Labkom 725", "Labkom 726",
    ]
    facilities = list(FACILITY_SPECS.keys())

    tickets: List[MaintenanceTicket] = []
    for i in range(count):
        facility = random.choice(facilities)
        spec = FACILITY_SPECS[facility]
        loc = random.choice(locations)
        urgency: UrgencyLevel = spec["default_urgency"]

        minute_offset = random.randint(0, 360)
        req_time = base_date + timedelta(minutes=minute_offset)
        tid = f"SYN-{i+1:03d}"
        desc = f"Gangguan fasilitas {facility} di {loc} (Simulasi Skalabilitas)."

        tickets.append(
            MaintenanceTicket(
                ticket_id=tid,
                location=loc,
                facility=facility,
                issue_description=desc,
                request_time=req_time,
                urgency=urgency,
                sla_hours=urgency.default_sla_hours,
                estimated_duration_minutes=spec["est_duration_minutes"],
                required_skill=spec["skill"],
            )
        )

    # Urutkan berdasarkan hierarki bisnis: Urgensi > Waktu Request
    tickets.sort(key=lambda t: (-t.urgency.priority_rank, t.request_time))
    return tickets


def get_edge_case_scenarios() -> Dict[str, Tuple[List[MaintenanceTicket], List[Technician]]]:
    """Menghasilkan skenario kasus ekstrem (edge cases) untuk stress testing."""
    base_date = datetime(2026, 10, 2, 8, 0)
    default_techs = get_default_technicians()

    # Skenario 1: Over-Constrained (Ketiadaan Kualifikasi Spesialisasi)
    unqualified_tech = [
        Technician(
            tech_id="TECH-NET-ONLY",
            name="Network Specialist Only",
            skills={SkillCategory.NETWORK},
            base_location="Posko Teknisi",
        )
    ]
    ticket_electrical = [
        MaintenanceTicket(
            ticket_id="EDGE-01",
            location="Labkom 725",
            facility="Mati Listrik",
            issue_description="Korsleting panel utama.",
            request_time=base_date,
            urgency=UrgencyLevel.TINGGI,
            sla_hours=2,
            estimated_duration_minutes=45,
            required_skill=SkillCategory.ELECTRICAL,
        )
    ]

    # Skenario 2: Emergency Surge (Lonjakan Darurat Serentak)
    surge_tickets = [
        MaintenanceTicket(
            ticket_id=f"SURGE-{i+1:02d}",
            location=f"Labkom 7{20+i}",
            facility="Mati Listrik" if i % 2 == 0 else "Proyektor",
            issue_description=f"Kerusakan darurat ruang 7{20+i}",
            request_time=base_date + timedelta(minutes=i * 5),
            urgency=UrgencyLevel.TINGGI,
            sla_hours=2,
            estimated_duration_minutes=40,
            required_skill=SkillCategory.ELECTRICAL if i % 2 == 0 else SkillCategory.AV,
        )
        for i in range(6)
    ]

    # Skenario 3: Single Technician Under Heavy Load
    super_tech = [
        Technician(
            tech_id="TECH-SOLO",
            name="Solo Hero Technician",
            skills={
                SkillCategory.ELECTRICAL,
                SkillCategory.NETWORK,
                SkillCategory.AV,
                SkillCategory.COMPUTING,
                SkillCategory.HVAC,
                SkillCategory.GENERAL,
            },
            base_location="Posko Teknisi",
            max_work_minutes=600,
        )
    ]

    return {
        "over_constrained_no_skill": (ticket_electrical, unqualified_tech),
        "emergency_surge": (surge_tickets, default_techs),
        "single_technician": (get_official_milestone2_tickets(), super_tech),
    }
