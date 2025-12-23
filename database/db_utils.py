"""
Database utility functions for PostgreSQL connection and data fetching.
"""

import psycopg2
from psycopg2 import pool
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection pool
connection_pool = None


def init_connection_pool():
    """Initialize the database connection pool."""
    global connection_pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1,  # Minimum connections
            10,  # Maximum connections
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        return True, "Connection pool created successfully"
    except Exception as e:
        return False, f"Error creating connection pool: {str(e)}"


def get_connection():
    """Get a connection from the pool."""
    global connection_pool
    if connection_pool is None:
        success, message = init_connection_pool()
        if not success:
            raise Exception(message)
    return connection_pool.getconn()


def release_connection(conn):
    """Return a connection to the pool."""
    global connection_pool
    if connection_pool:
        connection_pool.putconn(conn)


def close_all_connections():
    """Close all connections in the pool."""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()


def test_connection():
    """Test the database connection."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        release_connection(conn)
        return True, f"Connected successfully! PostgreSQL version: {version[0]}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def execute_query(query, params=None):
    """
    Execute a SQL query and return results as a pandas DataFrame.
    
    Args:
        query (str): SQL query to execute
        params (tuple, optional): Parameters for the query
        
    Returns:
        pd.DataFrame: Query results as a DataFrame
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        # Fetch column names
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        return df
    except Exception as e:
        raise Exception(f"Query execution failed: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)


def get_table_list():
    """Get a list of all tables in the database."""
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """
    try:
        df = execute_query(query)
        return df['table_name'].tolist()
    except Exception as e:
        raise Exception(f"Failed to fetch table list: {str(e)}")


def get_table_data(table_name, limit=100):
    """
    Fetch data from a specific table.
    
    Args:
        table_name (str): Name of the table
        limit (int): Maximum number of rows to fetch
        
    Returns:
        pd.DataFrame: Table data
    """
    # Note: Using parameterized queries for table names is not straightforward
    # We'll validate the table name exists first
    tables = get_table_list()
    if table_name not in tables:
        raise Exception(f"Table '{table_name}' not found in database")
    
    query = f"SELECT * FROM {table_name} LIMIT {limit};"
    return execute_query(query)


def get_table_info(table_name):
    """
    Get column information for a specific table.
    
    Args:
        table_name (str): Name of the table
        
    Returns:
        pd.DataFrame: Column information
    """
    query = """
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
    """
    return execute_query(query, (table_name,))


def get_fund_datagroup_matrix():
    """
    Get a matrix showing which datagroups exist for each fund.
    Returns a pivot table with funds as rows and datagroups as columns.
    
    Returns:
        pd.DataFrame: Pivot table with funds and datagroups showing IDs
    """
    query = """
        SELECT 
            f.id as fund_id,
            f.fund_name,
            dgm.datagroup_display_name,
            dgm.id,
            dgm.sequence
        FROM lm_datagroup_metadata_master dgm
        INNER JOIN lm_funds f ON dgm.fund_id = f.id
        ORDER BY f.fund_name, dgm.sequence;
    """
    
    try:
        df = execute_query(query)
        
        if df.empty:
            return pd.DataFrame()
        
        # Create a pivot table with funds as rows and datagroups as columns
        # Show the ID where datagroup exists for that fund
        pivot_df = df.pivot_table(
            index=['fund_id', 'fund_name'],
            columns='datagroup_display_name',
            values='id',
            aggfunc='first',  # Take the first ID if multiple exist
            fill_value=''
        )
        
        return pivot_df
    
    except Exception as e:
        raise Exception(f"Failed to fetch fund-datagroup matrix: {str(e)}")


def get_fund_datagroup_details():
    """
    Get detailed information about fund-datagroup relationships.
    
    Returns:
        pd.DataFrame: Detailed datagroup information for each fund
    """
    query = """
        SELECT 
            f.fund_name,
            dgm.datagroup_display_name,
            dgm.datagroup_lookup,
            dgm.sequence,
            dgm.data_format,
            dgm.description,
            dgm.is_hidden
        FROM lm_datagroup_metadata_master dgm
        INNER JOIN lm_funds f ON dgm.fund_id = f.id
        WHERE dgm.is_deleted = FALSE AND f.is_deleted = FALSE
        ORDER BY f.fund_name, dgm.sequence;
    """
    return execute_query(query)


def get_fund_datagroup_key_matrix():
    """
    Get a matrix showing which datagroups have key metadata for each fund.
    Returns a pivot table with funds as rows and datagroups as columns.
    Based on lm_key_metadata_master table.
    
    Returns:
        pd.DataFrame: Pivot table with funds and datagroups showing key count
    """
    query = """
        SELECT 
            f.id as fund_id,
            f.fund_name,
            dgm.datagroup_display_name,
            COUNT(km.id) as key_count
        FROM lm_key_metadata_master km
        INNER JOIN lm_funds f ON km.fund_id = f.id
        INNER JOIN lm_datagroup_metadata_master dgm ON km.datagroup_id = dgm.id
        GROUP BY f.id, f.fund_name, dgm.datagroup_display_name
        ORDER BY f.fund_name, dgm.datagroup_display_name;
    """
    
    try:
        df = execute_query(query)
        
        if df.empty:
            return pd.DataFrame()
        
        # Create a pivot table with funds as rows and datagroups as columns
        # Show the count of keys for each fund-datagroup combination
        pivot_df = df.pivot_table(
            index=['fund_id', 'fund_name'],
            columns='datagroup_display_name',
            values='key_count',
            aggfunc='sum',
            fill_value=''
        )
        
        return pivot_df
    
    except Exception as e:
        raise Exception(f"Failed to fetch fund-datagroup key matrix: {str(e)}")


def get_key_metadata_details(fund_name, datagroup_name):
    """
    Get detailed key metadata for a specific fund and datagroup.
    
    Args:
        fund_name (str): Name of the fund
        datagroup_name (str): Display name of the datagroup
        
    Returns:
        pd.DataFrame: Detailed key metadata information
    """
    query = """
        SELECT 
            km.id,
            km.key_display_name,
            km.key_lookup,
            km.formula,
            km.is_raw,
            km.is_calculated,
            km.sequence,
            km.calculation_level,
            km.data_type,
            km.unit,
            km.description,
            km.is_current
        FROM lm_key_metadata_master km
        INNER JOIN lm_funds f ON km.fund_id = f.id
        INNER JOIN lm_datagroup_metadata_master dgm ON km.datagroup_id = dgm.id
        WHERE f.fund_name = %s AND dgm.datagroup_display_name = %s
        ORDER BY km.sequence;
    """
    
    try:
        df = execute_query(query, (fund_name, datagroup_name))
        return df
    except Exception as e:
        raise Exception(f"Failed to fetch key metadata details: {str(e)}")


def get_missing_descriptions_stats():
    """
    Get statistics about missing descriptions, totals, and formula status.
    
    Returns:
        dict: Counts of missing descriptions, totals, raw/calc status, and formula gaps
    """
    datagroup_query = """
        SELECT 
            COUNT(*) as total_count,
            COUNT(*) FILTER (WHERE description IS NULL OR TRIM(description) = '') as missing_count
        FROM lm_datagroup_metadata_master;
    """
    
    key_query = """
        SELECT 
            COUNT(*) as total_count,
            COUNT(*) FILTER (WHERE description IS NULL OR TRIM(description) = '') as missing_count,
            COUNT(*) FILTER (WHERE is_raw = TRUE) as raw_count,
            COUNT(*) FILTER (WHERE is_calculated = TRUE) as calculated_count,
            COUNT(*) FILTER (WHERE is_calculated = TRUE AND (formula IS NULL)) as missing_formula_count
        FROM lm_key_metadata_master;
    """
    
    stats = {
        'datagroup_total': 0,
        'datagroup_missing': 0,
        'key_total': 0,
        'key_missing': 0,
        'key_raw': 0,
        'key_calculated': 0,
        'key_missing_formula': 0
    }
    
    try:
        dg_df = execute_query(datagroup_query)
        if not dg_df.empty:
            stats['datagroup_total'] = int(dg_df['total_count'].iloc[0])
            stats['datagroup_missing'] = int(dg_df['missing_count'].iloc[0])
            
        km_df = execute_query(key_query)
        if not km_df.empty:
            stats['key_total'] = int(km_df['total_count'].iloc[0])
            stats['key_missing'] = int(km_df['missing_count'].iloc[0])
            stats['key_raw'] = int(km_df['raw_count'].iloc[0])
            stats['key_calculated'] = int(km_df['calculated_count'].iloc[0])
            stats['key_missing_formula'] = int(km_df['missing_formula_count'].iloc[0])
            
        return stats
    except Exception as e:
        print(f"Error fetching missing description stats: {e}")
        return stats

