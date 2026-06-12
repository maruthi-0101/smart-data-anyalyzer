# 📊 Smart Data Analyzer

A comprehensive Streamlit application for data exploration, analysis, and visualization.

## Features

### 📋 Overview
- Display dataset dimensions (rows, columns)
- Show column names and data types
- Preview first 10 rows
- Display statistical summary

### 🧹 Data Cleaning
- Remove duplicate rows
- Handle missing values (drop or fill strategy)
- View data quality metrics
- Download cleaned data

### 📈 Exploratory Data Analysis
- Analyze numeric and categorical columns
- Calculate column statistics
- View correlation matrix
- Get value counts for columns

### 🔍 Data Quality
- Comprehensive quality report
- Missing value analysis
- Data type information
- Summary statistics

### 📊 Visualizations
- **Histogram**: Distribution of numeric data
- **Boxplot**: Outlier detection and distribution
- **Scatter Plot**: Relationships between variables
- **Correlation Heatmap**: Visual correlation matrix
- **Bar Chart**: Categorical value counts
- **Pie Chart**: Categorical proportions
- **Line Chart**: Trend analysis

### 💡 Insights
- Basic data metrics
- Data quality insights
- Correlation analysis
- Distribution patterns
- Statistical summary

### 🔎 SQL Query Engine
- Execute SQL queries on your data
- Use intuitive SQL interface
- Download query results

## Installation

1. Clone or download this project

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Project Structure

```
smart-data-analyzer/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Project dependencies
├── README.md             # This file
└── modules/
    ├── __init__.py       # Package initialization
    ├── excel_loader.py   # File loading functionality
    ├── data_cleaner.py   # Data cleaning operations
    ├── eda.py            # Exploratory data analysis
    ├── sql_engine.py     # SQL query engine
    ├── visualizer.py     # Data visualization functions
    └── insights.py       # Insight generation functions
```

## Modules Description

### `excel_loader.py`
Handles loading CSV and Excel files (.xlsx, .xls) into pandas DataFrames.

### `data_cleaner.py`
Provides data cleaning functionality:
- Handle missing values
- Remove duplicates
- Get data type information
- Calculate basic statistics
- Analyze missing values

### `eda.py`
Exploratory Data Analysis functions:
- Get comprehensive data info
- Identify numeric/categorical columns
- Calculate column statistics
- Compute correlation matrix
- Get value counts

### `sql_engine.py`
SQL query interface for DataFrames:
- Create in-memory SQLite database
- Execute SQL queries
- Filter data using SQL
- Get summary statistics

### `visualizer.py`
Visualization functions using matplotlib and seaborn:
- Histogram, boxplot, scatter plot
- Correlation heatmap
- Bar chart, pie chart, line chart

### `insights.py`
Generate actionable insights:
- Basic insights (rows, columns, duplicates)
- Column quality report
- Top insights with emoji indicators
- Correlation insights
- Distribution insights
- Statistical summary

## Supported File Formats

- **CSV** (.csv)
- **Excel** (.xlsx, .xls)

## Requirements

- Python 3.7+
- pandas
- numpy
- streamlit
- matplotlib
- seaborn
- openpyxl (for Excel support)

## Getting Started

1. Launch the application with `streamlit run app.py`
2. Upload your CSV or Excel file using the file uploader in the sidebar
3. Navigate through different sections using the sidebar menu
4. Explore, analyze, and visualize your data!

## Tips

- Use **Overview** section to quickly understand your data
- Use **Data Cleaning** to prepare your data for analysis
- Use **Visualizations** to explore relationships and patterns
- Use **Insights** to get automatic analysis recommendations
- Use **SQL Query** for advanced filtering and aggregation

## Features in Detail

### Data Upload
- Click "Browse files" in the sidebar
- Select your CSV or Excel file
- Data is automatically loaded and displayed

### Real-time Analysis
- All analysis is performed in real-time
- Interactive visualizations
- Session-based data management

### Data Transformation
- Clean data in-place
- Preview before and after cleaning
- Download cleaned datasets

### Advanced Queries
- Write custom SQL queries
- Execute against your data
- Export query results

## Troubleshooting

**File upload not working?**
- Ensure file is in supported format (CSV, XLSX, XLS)
- Check file is not corrupted
- Try with a smaller file

**Visualizations not appearing?**
- Ensure column is of correct data type
- Check for sufficient data
- Try different visualization types

**SQL query errors?**
- Verify table name is "data"
- Check column names are correct
- Ensure SQL syntax is valid

## Future Enhancements

- Advanced statistical tests
- Machine learning predictions
- Custom report generation
- Data export to multiple formats
- Collaborative analysis features

## License

This project is open source and available for personal and educational use.

## Support

For issues or suggestions, please check the application's error messages or review your data format.

---

**Built with ❤️ using Streamlit**
