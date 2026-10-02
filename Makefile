# ==============================================================================
# Makefile - Del-MaintOps Copilot (FITE IT Del)
# Mata Kuliah: 10S3001 Kecerdasan Buatan (+P) | Proyek Terpadu (Milestone 1 & 2)
# ==============================================================================
#
# PANDUAN URUTAN MEMAHAMI STRUKTUR FILE PROYEK:
# ------------------------------------------------------------------------------
# 1. Pahami Domain Masalah Bisnis & SOP Operasional:
#    - docs/01_problem_framing.md    : Profil operasional FITE, pain points, justifikasi AI.
#    - docs/02_peas_specification.md : Spesifikasi agen (Performance, Environment, Actuators, Sensors).
#    - docs/04_sops_knowledge_base.md: 4 Bagian SOP (Alur logika, Form tiket, 10 Dummy tiket, SOP teknisi).
#
# 2. Pahami Fondasi Milestone 1 (Navigation & Search):
#    - src/fite_graph.py             : Topologi graf 12 ruangan gedung FITE (lantai 1 & lantai 2).
#    - src/search_baseline.py        : Implementasi algoritma UCS & A* Search (admissible Manhattan heuristic).
#
# 3. Pahami Fondasi Milestone 2 (Constraint Modeling & Solver Optimization):
#    - docs/05_constraint_modeling_csp_ga.md: Formulasi matematis formal CSP & GA.
#    - src/models.py                 : Entitas domain (Ticket, Technician, UrgencyLevel, SkillCategory).
#    - src/data_loader.py            : Loader 10 tiket resmi & generator skenario benchmark skala besar.
#    - src/csp_solver.py             : Mesin inferensi CSP (propagasi AC-3, backtracking MRV/LCV, domain pruning).
#    - src/ga_solver.py              : Solver optimasi GA (representasi kromosom, turnamen, elitisme, crossover).
#    - solver.py                     : Unified runner / facade CLI untuk CSP dan GA.
#    - src/sensitivity_benchmark.py  : Skrip pengujian sensitivitas (skala kecil s/d 100 tiket, analisis konvergensi).
#
# 4. Pahami Antarmuka & Eksekusi Interaktif:
#    - src/cli.py / src/copilot_cli.py : Antarmuka teks interaktif untuk registrasi tiket, navigasi rute, & solver.
#
# 5. Pahami Verifikasi Mutu & Validasi Kasus Ekstrem:
#    - tests/                        : 54 unit test otomatis (100% PASS) mencakup seluruh edge cases.
#
# ==============================================================================
# PERINTAH EKSEKUSI TERMINAL (CLI COMMANDS)
# ==============================================================================

.PHONY: help install test test-v run-cli run-csp run-ga run-benchmark run-search clean report

# Menampilkan bantuan perintah yang tersedia
help:
	@echo ==============================================================================
	@echo  DEL-MAINTOPS COPILOT - AUTOMATION & EXECUTION MENU
	@echo ==============================================================================
	@echo  make install       - Install dependensi proyek menggunakan pip / uv
	@echo  make test          - Jalankan seluruh 54 unit test otomatis (pytest)
	@echo  make test-v        - Jalankan pytest dengan output verbose
	@echo  make run-cli       - Jalankan Copilot CLI Interaktif (Simulasi Tiket & Navigasi)
	@echo  make run-csp       - Jalankan CSP Solver (AC-3 + Backtracking) pada 10 tiket resmi
	@echo  make run-ga        - Jalankan GA Solver (Genetic Algorithm) pada 10 tiket resmi
	@echo  make run-benchmark - Jalankan Analisis Sensitivitas (10, 25, 50, 100 tiket)
	@echo  make run-search    - Jalankan uji penelusuran rute terpendek UCS & A* Search
	@echo  make clean         - Bersihkan cache Python (__pycache__, .pytest_cache)
	@echo ==============================================================================

# Install dependensi
install:
	python -m pip install --upgrade pip
	pip install pytest python-docx

# Menjalankan seluruh pengujian otomatis
test:
	pytest

# Menjalankan pengujian otomatis mode verbose
test-v:
	pytest -v

# Menjalankan CLI Interaktif Copilot
run-cli:
	python src/cli.py

# Menjalankan CSP Solver resmi Milestone 2
run-csp:
	python solver.py --algo csp

# Menjalankan GA Solver resmi Milestone 2
run-ga:
	python solver.py --algo ga

# Menjalankan benchmark analisis sensitivitas dan waktu konvergensi
run-benchmark:
	python src/sensitivity_benchmark.py

# Menjalankan baseline penelusuran graf rute teknisi (Milestone 1)
run-search:
	python src/search_baseline.py

# Membersihkan file sampah cache
clean:
	python -c "import shutil, os, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + ['.pytest_cache']]"
