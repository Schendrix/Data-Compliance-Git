import pytest
import sqlite3
import os
# Import the functions and constants from the main script
# Note: We now import REPORT_FILE from data_processor
from data_processor import setup_database, insert_sample_data, process_datasets, DB_NAME, TABLE_NAME, REPORT_FILE
from data_processor import generate_report_file # Need this for the new test

# Fixture to ensure the database is cleaned up before and after each test
@pytest.fixture(scope="function")
def clean_db():
    """Sets up and tears down the database file for isolated testing."""
    # Setup: Run the initialization functions from the main script
    setup_database()
    insert_sample_data()
    
    # Ensure any previous report file is removed before setup
    if os.path.exists(REPORT_FILE):
        os.remove(REPORT_FILE)
        
    # Yield control to the test function
    yield 
    
    # Teardown: Clean up the database and report files after the test
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    if os.path.exists(REPORT_FILE):
        os.remove(REPORT_FILE)


def test_database_creation(clean_db):
    """Test that the database file and table are successfully created."""
    assert os.path.exists(DB_NAME), f"Database file '{DB_NAME}' should exist."
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if the 'objects' table exists in the database schema
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}';")
    table_exists = cursor.fetchone() is not None
    conn.close()
    
    assert table_exists, f"Table '{TABLE_NAME}' should exist in the database."

def test_data_insertion_count(clean_db):
    """Test that the correct number of sample objects (5) were inserted."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
    count = cursor.fetchone()[0]
    conn.close()
    
    # The sample data in data_processor.py contains 5 objects
    assert count == 5, f"Expected 5 objects in the database, but found {count}."

def test_analysis_failure_condition(clean_db, capsys):
    """
    Test the failure condition. Sample data (165.0%) exceeds default threshold (150.0%),
    so process_datasets() must return False.
    """
    # The default state of the data/threshold is a failure condition
    result, _ = process_datasets() # Unpack the tuple result
    
    # Check that the function returned False (failure)
    assert result is False, "Analysis should return False when total memory exceeds the threshold."
    
    # Verify the failure message was printed to the console
    captured = capsys.readouterr()
    assert "!!! FAILURE" in captured.out

def test_report_file_generation_and_content(clean_db):
    """Test that the report file is generated and contains the calculated summary."""
    # Run the processing logic
    success, report_data = process_datasets()
    
    # Now, explicitly generate the report file using the test results
    generate_report_file(report_data)
    
    assert os.path.exists(REPORT_FILE), f"Report file '{REPORT_FILE}' must exist after processing."
    
    # Check a key piece of content
    with open(REPORT_FILE, 'r') as f:
        content = f.read()
    
    # This assertion (Total Combined Usage) was fixed previously and is correct.
    expected_usage_line = "- **Total Combined Usage:** `165.00%`"
    
    # FIX: The status line in the report is generated with Markdown bold formatting, 
    # so the assertion must match the exact string, including the surrounding '**'.
    expected_status_line = "**Status:** FAILURE"
    
    assert expected_usage_line in content, "Report content must contain the calculated total usage."
    assert expected_status_line in content, "Report status must reflect the failure condition."