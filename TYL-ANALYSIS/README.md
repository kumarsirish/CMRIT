# TYL Analysis Dashboard

A Streamlit-based web application for analysing **Tie Your Laces (TYL)** assessment data at CMRIT for AI & ML students. The tool helps identify students who are at risk (scored below passing marks in one or more TYL subjects) and supports faculty in planning remedial interventions.

---

## Features

- **TYL Analysis Dashboard** – Upload an Excel file with TYL scores, configure passing marks and the number of failing subjects threshold, and instantly see:
  - Students who scored below the passing mark in the selected skill areas (Ax, Sx, etc.)
  - A colour-coded table (failing scores highlighted in red)
  - Per-column count of values below passing marks
  - CSV download for each sheet/skill combination
- **Teacher Load Dashboard** – Placeholder dashboard for teacher workload analysis *(work in progress)*.
- Built-in **TYL Eligibility** and **TYL Marks Reference** tables for quick reference.

---

## Project Structure

```
TYL-ANALYSIS/
├── src/
│   ├── streamlit_app.py          # App entry point – page routing
│   ├── tyl_dashboard.py          # TYL Analysis Dashboard UI & logic
│   ├── teacher_load_dashboard.py # Teacher Load Dashboard (WIP)
│   └── tyl_analysis.py           # Core data-processing utilities
├── tests/
│   ├── conftest.py               # Pytest fixtures
│   └── test_tyl_dashboard.py     # Unit tests
├── requirements.txt
├── Makefile
└── README.md
```

---

## Prerequisites

- Python 3.9+
- A virtual environment (recommended)

---

## Installation

```bash
# Clone / navigate to the project
cd TYL-ANALYSIS

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# or using Make:
make build
```

---

## Running the App

```bash
streamlit run src/streamlit_app.py
# or using Make:
make run
```

The app will open at `http://localhost:8501` in your browser.

---

## Running Tests

```bash
pytest tests/test_tyl_dashboard.py
# or using Make:
make test
```

---

## Make Targets

| Target  | Description                                      |
|---------|--------------------------------------------------|
| `build` | Install all dependencies from `requirements.txt` |
| `test`  | Run the test suite with pytest                   |
| `run`   | Launch the Streamlit app                         |
| `clean` | Remove cache files and test artefacts            |
| `all`   | `clean` → `build` → `test`                       |

---

## Usage

1. Launch the app (`make run`).
2. Open the **TYL Analysis Dashboard**.
3. Review the **TYL Eligibility** and **TYL Marks Reference** tables.
4. Upload the TYL scores Excel file (`.xlsx`).
5. Set **Passing marks** and the **number of subjects** below which a student is flagged.
6. Enter the sheet names (comma-separated, e.g. `UG-AIML,UG-CSAIML`).
7. Click **Run Analysis** to view results.
8. Download filtered results as CSV per sheet and skill.

---

## Dependencies

| Package    | Purpose                        |
|------------|--------------------------------|
| `streamlit`| Web UI framework               |
| `pandas`   | Data manipulation              |
| `openpyxl` | Reading `.xlsx` files          |
| `pytest`   | Testing framework              |

---

## TYL Skills Analysed

| Skill | Assessments Covered      | Default Pass Mark |
|-------|--------------------------|-------------------|
| Ax    | A1, A2, A3               | Configurable      |
| Sx    | S1, S2, S3               | Configurable      |

Additional skills can be added by extending the `Skill` dataclass in [src/tyl_analysis.py](src/tyl_analysis.py).
