"""
Smart Data Analyzer - A comprehensive Streamlit application for data analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from modules.excel_loader import load_file
from modules.pdf_loader import load_pdf_to_df
from modules.report_generator import (
    export_csv,
    export_excel,
    export_json,
    build_export_payloads,
    generate_pdf_report,
)
from modules.data_cleaner import (
    handle_missing_values,
    remove_duplicates,
    get_data_types,
    get_basic_stats,
    get_missing_values_info,
    get_duplicate_rows_count
)
from modules.data_cleaner import generate_report
from modules.eda import (
    get_data_info,
    get_numerical_columns,
    get_categorical_columns,
    get_column_statistics,
    get_correlation_matrix,
    get_value_counts
)
from modules.sql_engine import create_sql_engine
from modules.visualizer import (
    set_visualization_style,
    plot_histogram,
    plot_boxplot,
    plot_scatter,
    plot_correlation_heatmap,
    plot_bar_chart,
    plot_pie_chart,
    plot_line_chart
)
from modules.insights import (
    generate_basic_insights,
    get_column_quality_report,
    get_top_insights,
    get_correlation_insights,
    get_distribution_insights,
    get_statistical_summary
)
from modules.insights import auto_inspect
from modules.history import init_history_db, save_analysis_record, list_history, get_history, delete_history



# Configure Streamlit page
st.set_page_config(
    page_title="Smart Data Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set visualization style
set_visualization_style()

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 0rem 0rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function."""
    
    # Sidebar
    st.sidebar.title("🔧 Smart Data Analyzer")
    st.sidebar.markdown("---")
    
    # Initialize session state
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None
    if 'file_uploaded' not in st.session_state:
        st.session_state.file_uploaded = False
    if 'history_saved' not in st.session_state:
        st.session_state.history_saved = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None


    # Ensure history DB exists
    try:
        init_history_db()
    except Exception:
        # do not block app if DB initialization fails
        pass
    
    # Main title
    st.title("📊 Smart Data Analyzer")
    st.markdown("Upload your data and explore it with powerful analysis tools!")
    
    # Sidebar - File Upload Section
    st.sidebar.header("📁 Data Upload")
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV, Excel, PDF, JSON or TXT",
        type=['csv', 'xlsx', 'xls', 'pdf', 'json', 'txt'],
        help="Support for CSV, Excel, PDF (tables), JSON, and TXT files"
    )
    
    # Load file
    if uploaded_file is not None:
        # Determine file type and load appropriately
        file_type = uploaded_file.type or ""
        try:
            if uploaded_file.name.lower().endswith('.pdf') or 'pdf' in file_type:
                # load tables from PDF
                pdf_df = load_pdf_to_df(uploaded_file)
                if pdf_df is None:
                    st.error("No tables found in PDF file")
                    st.session_state.df = None
                else:
                    st.session_state.df = pdf_df
            elif uploaded_file.name.lower().endswith('.json') or 'json' in file_type:
                st.session_state.df = pd.read_json(uploaded_file)
            elif uploaded_file.name.lower().endswith('.txt') or 'text' in file_type:
                try:
                    st.session_state.df = pd.read_csv(uploaded_file, sep=None, engine='python')
                except Exception:
                    # fallback to single column
                    txt = uploaded_file.getvalue().decode('utf-8')
                    st.session_state.df = pd.DataFrame({'text': txt.splitlines()})
            else:
                st.session_state.df = load_file(uploaded_file)
        except Exception as e:
            st.error(f"Failed to load file: {e}")
            st.session_state.df = None
        st.session_state.original_df = st.session_state.df.copy() if st.session_state.df is not None else None
        st.session_state.file_uploaded = True
        # Persist analysis metadata once per uploaded filename
        try:
            if st.session_state.df is not None and uploaded_file is not None:
                # avoid double-saving the same upload during reruns
                if st.session_state.history_saved != getattr(uploaded_file, 'name', None):
                    report = generate_report(st.session_state.df)
                    rows = int(report.get('rows', 0))
                    cols = int(report.get('columns', 0))
                    score = float(report.get('data_quality_score', 0.0))
                    fname = getattr(uploaded_file, 'name', 'uploaded')
                    ftype = uploaded_file.type or ''
                    try:
                        save_analysis_record(fname, ftype, rows, cols, score)
                        st.session_state.history_saved = fname
                    except Exception:
                        # non-fatal: do not interrupt user flow
                        pass
                # Build backend analysis JSON once per loaded dataset
                if st.session_state.analysis_results is None or st.session_state.history_saved == getattr(uploaded_file, 'name', None):
                    try:
                        st.session_state.analysis_results = auto_inspect(st.session_state.df, persist_sql=True)
                    except Exception:
                        st.session_state.analysis_results = None
        except Exception:
            pass
    
    # Main content - Only show if file is uploaded
    if st.session_state.file_uploaded and st.session_state.df is not None:
        df = st.session_state.df
        
        # Sidebar - Navigation
        st.sidebar.markdown("---")
        st.sidebar.header("📚 Navigation")
        
        page = st.sidebar.radio(
            "Select a section:",
            [
                "📋 Overview",
                "🧹 Data Cleaning",
                "📈 Exploratory Analysis",
                "🔍 Data Quality",
                "📊 Visualizations",
                "💡 Insights",
                "🔎 SQL Query",

                "📜 Analysis History",
                "📤 Export & Reports"
            ]
        )

        
        # PAGE 1: Overview
        if page == "📋 Overview":
            st.header("📋 Data Overview")
            st.markdown("---")
            
            # Get data info
            data_info = get_data_info(df)
            
            # Display key metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📈 Rows", f"{data_info['rows']:,}")
            
            with col2:
                st.metric("📊 Columns", f"{data_info['columns']}")
            
            with col3:
                st.metric("💾 Memory Usage", f"{data_info['memory_usage']:.2f} MB")
            
            with col4:
                st.metric("📋 Shape", f"{data_info['rows']} × {data_info['columns']}")
            
            st.markdown("---")
            
            # Column Information
            st.subheader("📋 Column Information")
            col_info = pd.DataFrame({
                'Column': data_info['column_names'],
                'Data Type': [str(dtype) for dtype in data_info['data_types'].values()]
            })
            st.dataframe(col_info, use_container_width=True)
            
            st.markdown("---")
            
            # First rows preview
            st.subheader("👀 First 10 Rows")
            st.dataframe(df.head(10), use_container_width=True)
            
            st.markdown("---")
            
            # Data Statistics
            st.subheader("📊 Data Statistics")
            st.dataframe(get_basic_stats(df), use_container_width=True)
        
        # PAGE 2: Data Cleaning
        elif page == "🧹 Data Cleaning":
            st.header("🧹 Data Cleaning")
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🛠️ Cleaning Tools")
                
                # Missing values info
                st.write("**Missing Values:**")
                missing_info = get_missing_values_info(df)
                if len(missing_info) > 0:
                    st.dataframe(missing_info, use_container_width=True)
                else:
                    st.success("✅ No missing values found!")
                
                # Duplicate info
                dup_count = get_duplicate_rows_count(df)
                st.write(f"**Duplicate Rows:** {dup_count}")
                
                # Data types
                st.write("**Data Types:**")
                data_types_df = get_data_types(df)
                st.dataframe(data_types_df, use_container_width=True)
            
            with col2:
                st.subheader("⚙️ Actions")
                
                if st.button("🗑️ Remove Duplicates", key="remove_dup"):
                    st.session_state.df = remove_duplicates(st.session_state.df)
                    st.success(f"Duplicates removed! New shape: {st.session_state.df.shape}")
                
                st.write("**Handle Missing Values:**")
                missing_strategy = st.selectbox(
                    "Strategy:",
                    ["drop", "fill"],
                    key="missing_strategy"
                )
                
                if st.button("✨ Apply", key="apply_missing"):
                    st.session_state.df = handle_missing_values(st.session_state.df, missing_strategy)
                    st.success(f"Applied {missing_strategy} strategy! New shape: {st.session_state.df.shape}")
                
                st.write("**Download Cleaned Data:**")
                csv_data = st.session_state.df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_data,
                    file_name="cleaned_data.csv",
                    mime="text/csv"
                )
        
        # PAGE 3: Exploratory Analysis
        elif page == "📈 Exploratory Analysis":
            st.header("📈 Exploratory Data Analysis")
            st.markdown("---")
            
            # Get columns
            numeric_cols = get_numerical_columns(df)
            categorical_cols = get_categorical_columns(df)
            all_cols = list(df.columns)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Column Types Summary")
                summary_data = {
                    'Type': ['Numeric', 'Categorical', 'Total'],
                    'Count': [len(numeric_cols), len(categorical_cols), len(all_cols)]
                }
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
            
            with col2:
                st.subheader("🔢 Numeric Columns")
                if numeric_cols:
                    st.write(", ".join(numeric_cols))
                else:
                    st.info("No numeric columns found")
            
            st.markdown("---")
            
            # Column-wise analysis
            st.subheader("🔍 Column-wise Analysis")
            selected_col = st.selectbox("Select a column:", all_cols)
            
            if selected_col:
                stats = get_column_statistics(df, selected_col)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Statistics:**")
                    for key, value in stats.items():
                        st.write(f"- {key}: {value}")
                
                with col2:
                    st.write("**Value Counts (Top 10):**")
                    vc = get_value_counts(df, selected_col, top=10)
                    st.dataframe(vc, use_container_width=True)
            
            # Correlation analysis
            if len(numeric_cols) > 1:
                st.markdown("---")
                st.subheader("📈 Correlation Matrix")
                corr_matrix = get_correlation_matrix(df)
                st.dataframe(corr_matrix, use_container_width=True)
        
        # PAGE 4: Data Quality
        elif page == "🔍 Data Quality":
            st.header("🔍 Data Quality Report")
            st.markdown("---")
            
            # Quality report
            quality_report = get_column_quality_report(df)
            st.dataframe(quality_report, use_container_width=True)
            
            st.markdown("---")
            
            # Summary stats
            st.subheader("📊 Summary Statistics")
            summary = get_statistical_summary(df)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Rows", summary['rows'])
                st.metric("Numeric Columns", summary['numeric_columns'])
            
            with col2:
                if summary['mean']:
                    st.write("**Mean Values:**")
                    for col, val in summary['mean'].items():
                        st.write(f"- {col}: {val:.2f}")
        
        # PAGE 5: Visualizations
        elif page == "📊 Visualizations":
            st.header("📊 Data Visualizations")
            st.markdown("---")
            
            numeric_cols = get_numerical_columns(df)
            categorical_cols = get_categorical_columns(df)
            all_cols = list(df.columns)
            
            viz_type = st.selectbox(
                "Select visualization type:",
                [
                    "Histogram",
                    "Boxplot",
                    "Scatter Plot",
                    "Correlation Heatmap",
                    "Bar Chart",
                    "Pie Chart",
                    "Line Chart"
                ]
            )
            
            st.markdown("---")
            
            if viz_type == "Histogram":
                if numeric_cols:
                    selected_col = st.selectbox("Select column:", numeric_cols)
                    bins = st.slider("Number of bins:", 10, 100, 30)
                    if st.button("Generate Histogram"):
                        plot_histogram(df, selected_col, bins)
                else:
                    st.warning("No numeric columns available for histogram")
            
            elif viz_type == "Boxplot":
                if numeric_cols:
                    selected_cols = st.multiselect("Select columns:", numeric_cols, default=numeric_cols[:3])
                    if selected_cols and st.button("Generate Boxplot"):
                        plot_boxplot(df, selected_cols)
                else:
                    st.warning("No numeric columns available for boxplot")
            
            elif viz_type == "Scatter Plot":
                if len(numeric_cols) >= 2:
                    col1, col2 = st.columns(2)
                    with col1:
                        x_col = st.selectbox("X-axis:", numeric_cols)
                    with col2:
                        y_col = st.selectbox("Y-axis:", numeric_cols)
                    if st.button("Generate Scatter Plot"):
                        plot_scatter(df, x_col, y_col)
                else:
                    st.warning("Need at least 2 numeric columns for scatter plot")
            
            elif viz_type == "Correlation Heatmap":
                if numeric_cols:
                    if st.button("Generate Correlation Heatmap"):
                        plot_correlation_heatmap(df)
                else:
                    st.warning("No numeric columns available for correlation heatmap")
            
            elif viz_type == "Bar Chart":
                if categorical_cols:
                    selected_col = st.selectbox("Select column:", categorical_cols)
                    top = st.slider("Top N values:", 5, 20, 10)
                    if st.button("Generate Bar Chart"):
                        plot_bar_chart(df, selected_col, top)
                else:
                    st.warning("No categorical columns available for bar chart")
            
            elif viz_type == "Pie Chart":
                if categorical_cols:
                    selected_col = st.selectbox("Select column:", categorical_cols)
                    top = st.slider("Top N values:", 5, 20, 10)
                    if st.button("Generate Pie Chart"):
                        plot_pie_chart(df, selected_col, top)
                else:
                    st.warning("No categorical columns available for pie chart")
            
            elif viz_type == "Line Chart":
                if len(numeric_cols) >= 2:
                    col1, col2 = st.columns(2)
                    with col1:
                        x_col = st.selectbox("X-axis:", numeric_cols)
                    with col2:
                        y_col = st.selectbox("Y-axis:", numeric_cols)
                    if st.button("Generate Line Chart"):
                        plot_line_chart(df, x_col, y_col)
                else:
                    st.warning("Need at least 2 numeric columns for line chart")
        
        # PAGE 6: Insights
        elif page == "💡 Insights":
            st.header("💡 Data Insights")
            st.markdown("---")
            
            # Basic insights
            st.subheader("📌 Basic Insights")
            insights = generate_basic_insights(df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", f"{insights['total_rows']:,}")
            with col2:
                st.metric("Total Columns", insights['total_columns'])
            with col3:
                st.metric("Memory Usage", f"{insights['memory_usage_mb']:.2f} MB")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Duplicate Rows", insights['duplicate_rows'])
            with col2:
                st.metric("Missing Values", insights['total_missing'])
            
            st.markdown("---")
            
            # Top insights
            st.subheader("🔍 Key Insights")
            top_insights = get_top_insights(df)
            for insight in top_insights:
                st.write(f"• {insight}")
            
            st.markdown("---")
            
            # Correlation insights
            st.subheader("🔗 Correlation Insights")
            numeric_cols = get_numerical_columns(df)
            if len(numeric_cols) > 1:
                corr_insights = get_correlation_insights(df)
                for insight in corr_insights:
                    st.write(f"• {insight}")
            else:
                st.info("Not enough numeric columns for correlation analysis")
            
            st.markdown("---")
            
            # Distribution insights
            st.subheader("📊 Distribution Insights")
            dist_insights = get_distribution_insights(df)
            if dist_insights:
                for insight in dist_insights:
                    st.write(f"• {insight}")
            else:
                st.info("No significant distribution patterns detected")
        
        # PAGE 7: SQL Query
        elif page == "🔎 SQL Query":
            st.header("🔎 SQL Query Engine")
            st.markdown("---")
            
            st.info("Execute SQL queries on your data using SQLite")
            
            # Create SQL engine
            sql_engine = create_sql_engine(df, 'data')
            
            st.subheader("📋 Available Columns")
            columns = sql_engine.get_columns()
            st.write(", ".join(columns))
            
            st.markdown("---")
            
            st.subheader("🔍 SQL Query Editor")
            query = st.text_area(
                "Enter your SQL query:",
                value="SELECT * FROM data LIMIT 10",
                height=200,
                help="Use 'data' as the table name"
            )
            
            if st.button("🚀 Execute Query"):
                try:
                    result = sql_engine.execute_query(query)
                    if result is not None:
                        st.success("✅ Query executed successfully!")
                        st.dataframe(result, use_container_width=True)
                        
                        # Download result
                        csv_result = result.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Result",
                            data=csv_result,
                            file_name="query_result.csv",
                            mime="text/csv"
                        )
                    else:
                        st.error("Query execution failed")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            sql_engine.close()


        # PAGE: Analysis History
        elif page == "📜 Analysis History":
            st.header("📜 Analysis History")
            st.markdown("---")

            # List history records
            try:
                records = list_history()
            except Exception as e:
                st.error(f"Failed to read history: {e}")
                records = []

            if not records:
                st.info("No analysis history found")
            else:
                # Column headers
                for rec in records:
                    cols = st.columns([3, 2, 1, 1, 1, 2])
                    with cols[0]:
                        st.write(f"**{rec.get('filename')}**")
                        st.caption(rec.get('upload_time'))
                    with cols[1]:
                        st.write(rec.get('file_type') or "-")
                    with cols[2]:
                        st.write(rec.get('rows_count') or 0)
                    with cols[3]:
                        st.write(rec.get('columns_count') or 0)
                    with cols[4]:
                        st.write(f"{rec.get('data_quality_score')}")
                    with cols[5]:
                        view_key = f"view_{rec.get('id')}"
                        del_key = f"del_{rec.get('id')}"
                        if st.button("View", key=view_key):
                            details = get_history(rec.get('id'))
                            if details:
                                st.json({
                                    'id': details.get('id'),
                                    'filename': details.get('filename'),
                                    'file_type': details.get('file_type'),
                                    'upload_time': details.get('upload_time'),
                                    'rows_count': details.get('rows_count'),
                                    'columns_count': details.get('columns_count'),
                                    'data_quality_score': details.get('data_quality_score'),
                                })
                            else:
                                st.warning("Record not found")
                        if st.button("Delete", key=del_key):
                            try:
                                ok = delete_history(rec.get('id'))
                                if ok:
                                    st.success("Record deleted")
                                    st.experimental_rerun()
                                else:
                                    st.error("Delete failed")
                            except Exception as e:
                                st.error(f"Delete failed: {e}")

        # PAGE: Export & Reports
        elif page == "📤 Export & Reports":
            st.header("📤 Export & Reports")
            st.markdown("---")

            st.write("Export analyzed data in various formats and generate a PDF report.")

            export_col1, export_col2 = st.columns(2)

            with export_col1:
                st.subheader("Export Data")
                csv_bytes = None
                excel_bytes = None
                json_bytes = None
                try:
                    payloads = build_export_payloads(st.session_state.df)
                    csv_bytes = payloads.get("csv")
                    excel_bytes = payloads.get("excel")
                    json_bytes = payloads.get("json")
                except Exception as e:
                    st.error(f"Export generation failed: {e}")

                if csv_bytes is not None:
                    st.download_button("Download CSV", data=csv_bytes, file_name="exported_data.csv", mime="text/csv", key="download_csv")
                if excel_bytes is not None:
                    st.download_button("Download Excel", data=excel_bytes, file_name="exported_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="download_excel")
                if json_bytes is not None:
                    st.download_button("Download JSON", data=json_bytes, file_name="exported_data.json", mime="application/json", key="download_json")

            with export_col2:
                st.subheader("Generate PDF Report")
                st.write("The PDF includes dataset overview, data quality, EDA summary, SQL summary and recommendations.")

                try:
                    analysis_results = auto_inspect(st.session_state.df)
                    # ai_results not implemented; pass None to use analysis recommendations
                    pdf_bytes = generate_pdf_report(analysis_results, ai_results=None, df=st.session_state.df)
                    st.success("PDF report generated")
                    st.download_button(
                        "Download PDF Report",
                        data=pdf_bytes,
                        file_name="report.pdf",
                        mime="application/pdf",
                        key="download_pdf_report",
                    )
                except Exception as e:
                    st.error(f"Failed to generate PDF report: {e}")
    
    else:
        # Show welcome message when no file is uploaded
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ## 👋 Welcome to Smart Data Analyzer!
            
            A powerful and intuitive tool for data exploration and analysis.
            
            ### Features:
            
            - 📊 **Data Overview**: Quick summary of your data
            - 🧹 **Data Cleaning**: Remove duplicates, handle missing values
            - 📈 **Exploratory Analysis**: Understand your data deeply
            - 🔍 **Data Quality**: Comprehensive quality report
            - 📊 **Visualizations**: Create various chart types
            - 💡 **Insights**: Get actionable insights from your data
            - 🔎 **SQL Query**: Execute SQL queries on your data
            
            ### Getting Started:
            
            1. Click "Browse files" in the sidebar
            2. Upload your CSV or Excel file
            3. Explore your data!
            
            ### Supported Formats:

            - CSV (.csv)
            - Excel (.xlsx, .xls)
            - PDF (.pdf)
            - JSON (.json)
            - TXT (.txt)

            ### 📋 Supported Data Types

            - Sales Data
            - Customer Data
            - Inventory Data
            - Financial Data
            - Business Reports

            ### ⚡ System Limits

            - Max File Size: 200 MB
            - Max Rows: 1,000,000
            - Max Columns: 500
            """)
        
        with col2:
            st.image("https://img.icons8.com/fluency/96/null/data-sheet.png", use_column_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>Smart Data Analyzer v1.0 | Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
