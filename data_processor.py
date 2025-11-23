import sqlite3
import json
import sys
import os
import datetime

# --- Configuration ---
DB_NAME = 'object_store.db'
TABLE_NAME = 'objects'
MEMORY_THRESHOLD_PERCENT = 165.0  # The combined memory usage limit (in percent)
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

## Details of Relevant Datasets ({len(data['datasets'])})

| Object Name | Memory % |
| :--- | :--- |
"""
    for name, percent in data['datasets']:
        report_content += f"| {name} | {percent:.2f}% |\n"

    if not data['is_compliant']:
        report_content += "\n## Action Required\n"
        report_content += f"The combined usage exceeds the threshold. Review the listed datasets and consider reducing their memory footprint or increasing the threshold.\n"

    try:
        with open(REPORT_FILE, 'w') as f:
            f.write(report_content)
        # Note: We skip printing success message here to keep console output clean for CI
    except IOError as e:
        print(f"Error writing report file: {e}")

    return report_content


def process_datasets():
    """
    Queries objects, calculates sum of 'memory_percent', compares to threshold,
    and returns a structured report object.
    """
    conn = None
    total_memory_percent = 0.0
    relevant_datasets = []
    is_compliant = False
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        print(f"\n--- Analysis Running ---")
        print(f"Target Type: '{TARGET_METADATA_TYPE}'")
        print(f"Comparison Threshold: {MEMORY_THRESHOLD_PERCENT:.2f}%")
        
        # 1. Select all objects
        cursor.execute(f"SELECT name, metadata FROM {TABLE_NAME};")
        rows = cursor.fetchall()

        # 2. Iterate and process
        for name, metadata_str in rows:
            try:
                metadata = json.loads(metadata_str)
                
                if metadata.get('type') == TARGET_METADATA_TYPE:
                    memory_percent = metadata.get('memory_percent', 0.0)
                    total_memory_percent += memory_percent
                    relevant_datasets.append((name, memory_percent))
                    
            except json.JSONDecodeError:
                print(f"Warning: Failed to decode JSON metadata for object '{name}'. Skipping.")
            except TypeError:
                print(f"Warning: 'memory_percent' is not a valid number for object '{name}'. Skipping.")


        print(f"\nFound {len(relevant_datasets)} objects of type '{TARGET_METADATA_TYPE}':")
        for name, percent in relevant_datasets:
            print(f"- {name}: {percent:.2f}%")

        print(f"\nTotal combined memory percent: {total_memory_percent:.2f}%")
        
        # 3. Compare to threshold
        if total_memory_percent > MEMORY_THRESHOLD_PERCENT:
            exceeded_by = total_memory_percent - MEMORY_THRESHOLD_PERCENT
            print(f"\n!!! FAILURE: The total memory percent ({total_memory_percent:.2f}%) exceeds the threshold ({MEMORY_THRESHOLD_PERCENT:.2f}%) by {exceeded_by:.2f}%.")
            is_compliant = False
        else:
            exceeded_by = 0.0
            print(f"\nSUCCESS: Total memory percent is below the threshold. System is compliant.")
            is_compliant = True

    except sqlite3.Error as e:
        print(f"Database error during processing: {e}")
        exceeded_by = 0.0
        is_compliant = False
    finally:
        if conn:
            conn.close()

    # Prepare data structure for report generation and testing
    report_data = {
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'is_compliant': is_compliant,
        'threshold': MEMORY_THRESHOLD_PERCENT,
        'target_type': TARGET_METADATA_TYPE,
        'total_usage': total_memory_percent,
        'datasets': relevant_datasets,
        'exceeded_by': exceeded_by
    }
    return is_compliant, report_data


def main():
    """Main execution function."""
    setup_database()
    insert_sample_data()
    
    # Run the processing and capture the result and report data
    success, report_data = process_datasets()
    
    # Generate the report file regardless of success or failure
    generate_report_file(report_data)
    
    if not success:
        # Exit with a non-zero status code to fail the CI/CD job
        sys.exit(1)


if __name__ == "__main__":

    main()

