import sqlite3
import json
import sys
import os
import datetime

# --- Configuration ---
DB_NAME = 'object_store.db'
TABLE_NAME = 'objects'
MEMORY_THRESHOLD_PERCENT = 150.0  # The combined memory usage limit (in percent)
TARGET_METADATA_TYPE = 'dataset'
REPORT_FILE = 'analysis_report.md'
# --- End Configuration ---


def setup_database():
    """Initializes the SQLite database and creates the objects table. Deletes existing DB for a clean run."""
    conn = None
    try:
        # Check if DB file exists and delete it for a clean run
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
            print(f"Removed existing database file: {DB_NAME}")

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        print(f"Creating table '{TABLE_NAME}'...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                metadata TEXT,        -- Stores JSON string
                description TEXT,
                connections TEXT      -- Stores JSON string of connection IDs
            );
        """)
        conn.commit()
        print("Database setup complete.")

    except sqlite3.Error as e:
        print(f"Database error during setup: {e}")
    finally:
        if conn:
            conn.close()


def insert_sample_data():
    """Inserts sample object data, including various metadata types."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Data to be inserted. metadata and connections are stored as JSON strings.
        data = [
            # Dataset A: Contributes 50%
            ('obj-001', 'User_Activity_Log', 
             {'type': 'dataset', 'memory_percent': 50.0, 'owner': 'team_a'},
             'Logs user activity for auditing.', ['conn-01']),
            
            # Dataset B: Contributes 75%
            ('obj-002', 'Product_Catalog', 
             {'type': 'dataset', 'memory_percent': 75.0, 'owner': 'team_b'},
             'Current product inventory list.', ['conn-02', 'conn-03']),
             
            # Tool object: Ignored in calculation
            ('obj-003', 'ETL_Script_V2', 
             {'type': 'tool', 'version': '2.1', 'dependencies': 3},
             'Script for transforming user data.', ['conn-04']),
             
            # Dataset C: Contributes 40% (Total dataset memory will be 50 + 75 + 40 = 165.0)
            ('obj-004', 'Sales_Metrics_EU', 
             {'type': 'dataset', 'memory_percent': 40.0, 'owner': 'team_a'},
             'European sales performance metrics.', []),

            # Configuration object: Ignored in calculation
            ('obj-005', 'App_Config_Dev', 
             {'type': 'config', 'status': 'draft'},
             'Development environment settings.', ['conn-05']),
        ]

        print("Inserting sample data...")
        for obj_id, name, metadata_dict, description, connections_list in data:
            # Convert Python dictionary/list to JSON string for storage
            metadata_str = json.dumps(metadata_dict)
            connections_str = json.dumps(connections_list)

            cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (id, name, metadata, description, connections) 
                VALUES (?, ?, ?, ?, ?);
            """, (obj_id, name, metadata_str, description, connections_str))

        conn.commit()
        print(f"Successfully inserted {len(data)} objects.")

    except sqlite3.Error as e:
        print(f"Database error during data insertion: {e}")
    finally:
        if conn:
            conn.close()


def generate_report_file(data):
    """Generates a detailed markdown report of the analysis results."""
    
    report_content = f"""# Dataset Memory Analysis Report

**Generated On:** {data['timestamp']}
**Status:** {'FAILURE' if not data['is_compliant'] else 'SUCCESS'}

## Configuration
- Target Metadata Type: `{data['target_type']}`
- Compliance Threshold: `{data['threshold']:.2f}%`

## Results Summary
- **Total Combined Usage:** `{data['total_usage']:.2f}%`
- **Is Compliant:** {'Yes' if data['is_compliant'] else 'No'}
- **Exceeded By:** `{data['exceeded_by']:.2f}%`

## Details of Relevant Datasets
