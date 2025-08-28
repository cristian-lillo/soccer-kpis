# Soccer KPIs

A comprehensive analysis framework for football Key Performance Indicators (KPIs) developed as a thesis project for the Master of Science in Computer Science at the University of Chile.

## Overview

This research project focuses on developing and validating advanced methodologies for football analytics, specifically targeting the creation, analysis, and interpretation of Key Performance Indicators in professional football. The project leverages multiple data sources and state-of-the-art analytical techniques to provide insights into player and team performance.

## Key Features

- **Multi-source Data Integration**: Support for various football data providers including StatsBomb, Wyscout, and regional datasets
- **Standardized Data Processing**: Utilizes [kloppy](https://github.com/PySport/kloppy) for unified data handling across different formats
- **Advanced Analytics**: Implementation of modern football analytics methodologies including VAEP, PlayerRank, and custom KPI frameworks
- **Comprehensive Validation**: Cross-validation using multiple datasets from different leagues and competitions

## Project Structure

```
soccer-kpis/
├── data/                   # Data from various providers (see data/README.md)
├── models/                 # Implementations of football analytics methodologies
│   ├── ea-sports-ppi/          # EA Sports Player Performance Index
│   ├── playerank/              # PlayerRank methodology implementation
│   └── vaep/                   # VAEP and SPADL implementations
├── notebooks/              # Jupyter notebooks for data analysis and exploration
├── scripts/                # Utility scripts for data processing and configuration
├── requirements.txt        # Project dependencies
└── README.md               # This file
```

## Installation

### Prerequisites

This project requires **Python 3.12** to ensure compatibility with all analytical libraries. Some dependencies are not yet compatible with Python 3.13.

**Download Python 3.12.10**: [Official Python Release](https://www.python.org/downloads/release/python-31210/)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/cristian-lillo/soccer-kpis.git
cd soccer-kpis
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Data Sources

This project integrates data from multiple providers to ensure comprehensive analysis. See [`data/README.md`](data/README.md) for detailed information about:

- **StatsBomb Open Data**: Extensive event data with tactical annotations
- **Wyscout Academic Dataset**: European leagues and international tournaments
- **Chilean Primera División**: Regional competition data for validation
- Additional reference datasets for methodology comparison

## Methodologies

The project implements and compares several established football analytics frameworks:

### VAEP (Valuing Actions by Estimating Probabilities)
Implementation of the Decroos et al. methodology for action valuation in football.

### PlayerRank
Implementation of the Pappalardo et al. player ranking system based on network analysis.

### Custom KPI Framework
Development of novel Key Performance Indicators tailored for specific analytical needs.

## Research Objectives

1. **Methodological Validation**: Compare and validate existing football analytics methodologies
2. **Regional Analysis**: Analyze performance patterns in different football contexts
3. **KPI Development**: Create and validate new Key Performance Indicators
4. **Framework Integration**: Develop a unified framework for football performance analysis

## Contributing

This is a thesis project, but contributions and discussions are welcome. Please feel free to open issues or submit pull requests.

## License

This project is developed for academic purposes as part of a Master's thesis at the University of Chile.

## Author

**Cristian Lillo Ciero**
Master of Science in Computer Science
University of Chile

## Acknowledgments

- University of Chile, Department of Computer Science
- [PySport](https://github.com/PySport) community for the kloppy library
- Data providers: StatsBomb, Wyscout, and others for making football data accessible for research
