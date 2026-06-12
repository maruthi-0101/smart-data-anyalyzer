"""
Module for loading and reading Excel and CSV files.
"""

import pandas as pd
import streamlit as st
from typing import Optional


def load_csv(file) -> Optional[pd.DataFrame]:
    """
    Load CSV file and return as DataFrame.
    
    Args:
        file: Uploaded CSV file
        
    Returns:
        DataFrame or None if loading fails
    """
    try:
        df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"Error loading CSV file: {str(e)}")
        return None


def load_excel(file) -> Optional[pd.DataFrame]:
    """
    Load Excel file and return as DataFrame.
    
    Args:
        file: Uploaded Excel file
        
    Returns:
        DataFrame or None if loading fails
    """
    try:
        df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"Error loading Excel file: {str(e)}")
        return None


def load_file(file) -> Optional[pd.DataFrame]:
    """
    Load file based on extension (CSV or Excel).
    
    Args:
        file: Uploaded file
        
    Returns:
        DataFrame or None if loading fails
    """
    if file is None:
        return None
        
    file_extension = file.name.split('.')[-1].lower()
    
    if file_extension == 'csv':
        return load_csv(file)
    elif file_extension in ['xlsx', 'xls']:
        return load_excel(file)
    else:
        st.error(f"Unsupported file format: {file_extension}")
        return None
