"""
Module for data visualization operations.
"""

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional


def set_visualization_style():
    """Set default visualization style."""
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)


def plot_histogram(df: pd.DataFrame, column: str, bins: int = 30):
    """
    Plot histogram for a column.
    
    Args:
        df: Input DataFrame
        column: Column name
        bins: Number of bins
    """
    try:
        fig, ax = plt.subplots()
        ax.hist(df[column], bins=bins, edgecolor='black', alpha=0.7)
        ax.set_title(f'Histogram of {column}')
        ax.set_xlabel(column)
        ax.set_ylabel('Frequency')
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error plotting histogram: {str(e)}")


def plot_boxplot(df: pd.DataFrame, columns: list):
    """
    Plot boxplot for numeric columns.
    
    Args:
        df: Input DataFrame
        columns: List of column names
    """
    try:
        fig, ax = plt.subplots()
        df[columns].boxplot(ax=ax)
        ax.set_title('Boxplot of Selected Columns')
        plt.xticks(rotation=45)
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error plotting boxplot: {str(e)}")


def plot_scatter(df: pd.DataFrame, x_col: str, y_col: str):
    """
    Plot scatter plot.
    
    Args:
        df: Input DataFrame
        x_col: X-axis column
        y_col: Y-axis column
    """
    try:
        fig, ax = plt.subplots()
        ax.scatter(df[x_col], df[y_col], alpha=0.6)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(f'{x_col} vs {y_col}')
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error plotting scatter plot: {str(e)}")


def plot_correlation_heatmap(df: pd.DataFrame):
    """
    Plot correlation heatmap.
    
    Args:
        df: Input DataFrame
    """
    try:
        numeric_df = df.select_dtypes(include=[np.number])
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', center=0, ax=ax)
        ax.set_title('Correlation Heatmap')
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error plotting correlation heatmap: {str(e)}")


def plot_bar_chart(df: pd.DataFrame, column: str, top: int = 10):
    """
    Plot bar chart for categorical column.
    
    Args:
        df: Input DataFrame
        column: Column name
        top: Number of top values to display
    """
    try:
        fig, ax = plt.subplots()
        df[column].value_counts().head(top).plot(kind='bar', ax=ax, color='skyblue', edgecolor='black')
        ax.set_title(f'Top {top} Values in {column}')
        ax.set_xlabel(column)
        ax.set_ylabel('Count')
        plt.xticks(rotation=45)
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error plotting bar chart: {str(e)}")


def plot_pie_chart(df: pd.DataFrame, column: str, top: int = 10):
    """
    Plot pie chart for categorical column.
    
    Args:
        df: Input DataFrame
        column: Column name
        top: Number of top values to display
    """
    try:
        fig, ax = plt.subplots()
        df[column].value_counts().head(top).plot(kind='pie', ax=ax, autopct='%1.1f%%')
        ax.set_ylabel('')
        ax.set_title(f'Distribution of {column}')
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error plotting pie chart: {str(e)}")


def plot_line_chart(df: pd.DataFrame, x_col: str, y_col: str):
    """
    Plot line chart.
    
    Args:
        df: Input DataFrame
        x_col: X-axis column
        y_col: Y-axis column
    """
    try:
        fig, ax = plt.subplots()
        ax.plot(df[x_col], df[y_col], marker='o', linewidth=2)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(f'{x_col} vs {y_col}')
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error plotting line chart: {str(e)}")
