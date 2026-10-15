# ROX Wiki & DPS Simulator Studio

Comprehensive Game Database, Wiki, and Full-Parity DPS Simulator for **Ragnarok X: Next Generation (ROX)**.

## Overview

- **Zero-Fallback Arang Game Logic Engine**: 100% fidelity calculation logic mapped from master spreadsheets.
- **Divinity Inscription Studio**: 8 parts, Levels 0-7, 53 Substats pool with multi-selection and real-time auto-pinning.
- **Pet Sanctuary Studio**: Simplified stat template entry for Normal (6 stats) and SP pets (8 stats).
- **Dual-Page Equipment Studio**: 2-page equipment switchboard, 3 independent enchantment lines per slot (Lv. 1-15, all major cities), card sockets, refine and shadow memory.
- **High-Performance Architecture**: Zero external UI framework bloat, Swiss design system, sub-millisecond calculation pipeline.

## Getting Started

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) or `pip`

### Installation

```bash
# Clone the repository
git clone git@github.com-vhp201003:vhp201003/rox-tools.git
cd rox-tools

# Install dependencies
uv sync
```

### Running the Simulator

```bash
# Launch FastAPI web application on port 8001
python run.py
# Or directly via uvicorn
python -m uvicorn rox_wiki.server:app --host 127.0.0.1 --port 8001 --app-dir src --loop asyncio
```

Visit `http://127.0.0.1:8001/` to access the Simulator & Wiki UI.

### Testing

```bash
python -m pytest tests/test_arang_parity.py -v
```

## Project Structure

```
rox-tool/
├── assets/         # UI assets, screenshots & templates
├── docs/           # Architecture, design & research documents
├── scripts/        # Asset extractors, database compilers & migration tools
├── src/            # Application source code
│   └── rox_wiki/   # FastAPI application, engine & Swiss UI
├── tests/          # Parity test suites & calculation verifications
├── pyproject.toml  # Project configuration & dependencies
└── run.py          # Entry point script
```
