"""
Del-MaintOps Copilot - Data Loader & Benchmark Scenario Generator
----------------------------------------------------------------
Milestone 2 (W04): Penyedia Data Dummy Resmi dan Generator Kasus Uji.

Modul ini menyediakan:
1. 10 Tiket Dummy Resmi dari Dokumen Milestone 2 (TK-017 s/d TK-026).
2. Data Teknisi FITE IT Del dengan kualifikasi spesialisasi sesuai SOP.
3. Generator Dataset Sintetis untuk Pengujian Analisis Sensitivitas (Skala Kecil, Sedang, Besar).
4. Edge Case Generator untuk kasus ekstrem (Over-constrained, Surge Kritis, Single Tech).
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Tuple

from models import (
    FACILITY_SPECS,
    MaintenanceTicket,
    SkillCategory,
    Technician,
    UrgencyLevel,
)


def get_default_technicians() -> List[Technician]:
    """Mengembalikan daftar 3 teknisi standar FITE IT Del dengan pembagian spesialisasi."""
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
    """Mengembalikan 10 tiket dummy resmi sesuai tabel Dokumen Spesifikasi Milestone 2."""
    raw_data = [
        # Urutan 1
        ("TK-020", "Labkom 725", "Mati Listrik", "Korsleting di panel server lab, listrik padam.",
         datetime(2026, 10, 2, 8, 0), UrgencyLevel.TINGGI, 2, 45, SkillCategory.ELECTRICAL),
        # Urutan 2
        ("TK-017", "Kelas 711", "Proyektor", "Mati total saat kelas berlangsung.",
         datetime(2026, 10, 2, 8, 30), UrgencyLevel.TINGGI, 2, 35, SkillCategory.AV),
        # Urutan 3
        ("TK-022", "Kelas 712", "Idea Hub", "Layar sentuh hang, presentasi terhenti.",
         datetime(2026, 10, 2, 9, 15), UrgencyLevel.TINGGI, 2, 40, SkillCategory.AV),
        # Urutan 4
        ("TK-018", "Labkom 714", "PC", "3 unit PC di baris C gagal masuk sistem Windows.",
         datetime(2026, 10, 2, 8, 15), UrgencyLevel.SEDANG, 24, 50, SkillCategory.COMPUTING),
        # Urutan 5
        ("TK-023", "Labkom 714", "AC", "AC bocor meneteskan air ke meja PC.",
         datetime(2026, 10, 2, 8, 45), UrgencyLevel.SEDANG, 24, 45, SkillCategory.HVAC),
        # Urutan 6
        ("TK-021", "Labkom 716", "LAN", "Koneksi terputus di 2 meja pojok belakang.",
         datetime(2026, 10, 2, 10, 0), UrgencyLevel.SEDANG, 24, 30, SkillCategory.NETWORK),
        # Urutan 7
        ("TK-024", "Kelas 721", "WiFi", "Sinyal Access Point mati/tidak terdeteksi.",
         datetime(2026, 10, 2, 11, 30), UrgencyLevel.SEDANG, 24, 25, SkillCategory.NETWORK),
        # Urutan 8
        ("TK-019", "Kelas 722", "Colokan", "2 slot stop kontak belakang kendor.",
         datetime(2026, 10, 2, 7, 30), UrgencyLevel.RENDAH, 72, 20, SkillCategory.ELECTRICAL),
        # Urutan 9
        ("TK-025", "Labkom 726", "Keyboard", "Tombol spasi macet di PC-15.",
         datetime(2026, 10, 2, 9, 30), UrgencyLevel.RENDAH, 72, 15, SkillCategory.COMPUTING),
        # Urutan 10
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
    """Menghasilkan dataset tiket sintetis untuk analisis skalabilitas (skala besar)."""
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
        urgency: UrgencyLevel = spec["default_urgency"]  # type: ignore

        # Variasi waktu pelaporan tersebar sepanjang hari kerja
        minute_offset = random.randint(0, 360)
        req_time = base_date + timedelta(minutes=minute_offset)

        tid = f"SYN-{i+1:03d}"
        desc = f"Gangguan pada {facility} di {loc} - otomatis disimulasikan."

        tickets.append(
            MaintenanceTicket(
                ticket_id=tid,
                location=loc,
                facility=facility,
                issue_description=desc,
                request_time=req_time,
                urgency=urgency,
                sla_hours=urgency.default_sla_hours,
                estimated_duration_minutes=spec["est_duration_minutes"],  # type: ignore
                required_skill=spec["skill"],  # type: ignore
            )
        )

    # Urutkan berdasarkan prioritas bisnis (Urgensi > Request Time)
    tickets.sort(key=lambda t: (-t.urgency.priority_rank, t.request_time))
    return tickets


def get_edge_case_scenarios() -> Dict[str, Tuple[List[MaintenanceTicket], List[Technician]]]:
    """Menghasilkan skenario-skenario kasus ekstrem (edge cases) untuk pengujian ketahanan solver."""
    base_date = datetime(2026, 10, 2, 8, 0)
    default_techs = get_default_technicians()

    # Skenario 1: Over-Constrained (Ketiadaan Teknisi yang Berkompeten)
    # Terdapat kerusakan Mati Listrik, namun satu-satunya teknisi yang ada HANYA teknisi Jaringan murni.
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

    # Skenario 2: Lonjakan Tiket Darurat Sekaligus (Emergency Surge)
    # 6 tiket kategori TINGGI (SLA 2 jam) datang pada menit yang hampir bersamaan
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
    # Hanya 1 teknisi serba bisa yang harus menangani seluruh 10 tiket resmi
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
