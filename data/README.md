# Data

## Source

The following providers are all supported by the [kloppy repository](https://github.com/PySport/kloppy), which provides a standardized interface for working with different football data formats, facilitating centralized data processing and analysis.

## Providers

### StatsBomb
- **Source**: [StatsBomb Open Data](https://github.com/statsbomb/open-data)
- **Type**: Event data with detailed tactical information
- **Content**: Extensive collection of matches from multiple high-profile competitions including FIFA World Cup, UEFA European Championships, Premier League, and various domestic leagues
- **Usage**: ✅ Will be used - Comprehensive open dataset with rich tactical context

### Wyscout
- **Source**: [Soccer match event dataset](https://figshare.com/collections/Soccer_match_event_dataset/4415000/2)
- **Type**: Event data from academic research
- **Content**: Comprehensive dataset including matches from the 2017/2018 season across major European leagues (Serie A, Premier League, Bundesliga, La Liga, Ligue 1), plus international tournaments (Euro 2016 and World Cup 2018)
- **Usage**: ✅ Will be used - Academic dataset used in PlayerRank paper

### Chile
- **Source**: Private Wyscout data
- **Type**: Event data from Chilean football
- **Content**: Comprehensive coverage of Chilean Primera División matches spanning multiple seasons (2022-2024), providing detailed event data from South American football
- **Usage**: ✅ Will be used - Enables analysis of regional football patterns and KPI validation in different competitive contexts

### Metrica Sports
- **Source**: [Metrica Sports sample data](https://github.com/metrica-sports/sample-data)
- **Type**: Tracking and event data
- **Content**: High-quality sample matches featuring detailed player positioning data and ball tracking information
- **Usage**: 🔍 Reference - Provides examples of professional-grade tracking data for methodology comparison

### SkillCorner
- **Source**: [SkillCorner Open Data](https://github.com/SkillCorner/opendata)
- **Type**: Tracking data
- **Content**: Sample matches with comprehensive player and ball tracking, including advanced metrics and positioning analytics
- **Usage**: 🔍 Reference - Demonstrates state-of-the-art tracking data capabilities

### Sportec Solutions
- **Source**: [DFL (German Football League) data](https://doi.org/10.6084/m9.figshare.28196177)
- **Type**: Official match data in XML format
- **Content**: Professional Bundesliga match information and events in standardized XML format, representing official league data structure
- **Usage**: 🔍 Reference - Example of official league data formatting and structure

## Primary Datasets

The selected datasets for this thesis research are strategically chosen to provide comprehensive coverage and analytical depth:

1. **StatsBomb Open Data** - Delivers extensive event data with rich tactical annotations across multiple high-profile competitions, providing an ideal foundation for comprehensive KPI analysis and validation across different competitive levels.

2. **Chile (Wyscout)** - Contributes local competition data from Chilean Primera División, enabling the analysis of regional football patterns and validation of KPI methodologies in South American football contexts, adding geographical diversity to the research.

3. **Wyscout** - Functions as the primary academic reference dataset, particularly valuable for PlayerRank methodology validation and comparison with established research frameworks in football analytics.

These datasets collectively provide an optimal research foundation through:
- **Comprehensive Volume**: Hundreds of professional matches spanning different competitions and geographical regions
- **Data Quality**: Professional-grade event annotations with detailed tactical and contextual information
- **Competitive Diversity**: Multiple leagues, playing styles, and competitive levels from European and South American football
- **Research Accessibility**: Open-source and academically available datasets ensuring reproducibility and transparency