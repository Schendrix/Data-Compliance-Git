import pytest
import os
import json
import data_processor # Only import the module, not specific functions

# Define the expected usage for the sample data provided in data_processor.py (50 + 75 + 40 = 165.0)
EXPECTED_TOTAL_USAGE = 165.0

# --- Setup and Teardown ---
@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Initialize DB and insert data before each test
    data_processor.setup_database()
    data_processor.insert_sample_data()
    yield  # Run the test
    # Teardown: Clean up the database file after each test
    if os.path.exists(data_processor.DB_NAME):
        os.remove(data_processor.DB_NAME)

# --- Test Cases ---

def test_database_initialization():
    """Test that the database file is created and contains the correct number of records."""
    conn = data_processor.sqlite3.connect(data_processor.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {data_processor.TABLE_NAME};")
    count = cursor.fetchone()[0]
    conn.close()
    
    assert os.path.exists(data_processor.DB_NAME)
    assert count == 5, f"Expected 5 records, but found {count}"


def test_analysis_success_condition():
    """
    Test the scenario where the total memory usage is compliant.
    (Relies on MEMORY_THRESHOLD_PERCENT being > 165.0 in data_processor.py)
    """
    # Run the analysis logic
    result, report_data = data_processor.process_datasets()
    
    # Assert that the analysis succeeded
    assert result is True, "Analysis should return True when total memory is compliant."
    
    # Assert correct usage calculation
    assert report_data['total_usage'] == EXPECTED_TOTAL_USAGE


def test_analysis_failure_condition():
    """
    Test the scenario where the total memory usage is NOT compliant.
    We temporarily set the threshold *within the test* to guarantee a failure condition.
    """
    # Temporarily force the threshold to a value lower than the actual usage (165.0)
    original_threshold = data_processor.MEMORY_THRESHOLD_PERCENT
    data_processor.MEMORY_THRESHOLD_PERCENT = 100.0
    
    # Rerun the analysis logic with the temporary low threshold
    result, report_data = data_processor.process_datasets()
    
    # Assert that the analysis failed
    assert result is False, "Analysis should return False when total memory exceeds the threshold."
    assert report_data['exceeded_by'] == 65.0  # 165.0 - 100.0 = 65.0
    
    # Restore original threshold (as good practice)
    data_processor.MEMORY_THRESHOLD_PERCENT = original_threshold


def test_report_file_generation_and_content():
    """Test that the report file is generated and contains the expected SUCCESS status."""
    
    # Run the analysis logic (it should succeed if threshold is > 165.0)
    result, report_data = data_processor.process_datasets()
    
    # Generate the report based on the successful result
    report_content = data_processor.generate_report_file(report_data)

    # Check that the file was created
    assert os.path.exists(data_processor.REPORT_FILE)
    
    # Check for the expected SUCCESS status line
    expected_status_line = '**Status:** SUCCESS'
    assert expected_status_line in report_content, "Report status must reflect the SUCCESS condition."
    
    # FIX: Assert the presence of the full formatted line, including the list marker (-) and bold (**)
    expected_usage_line = f"- **Total Combined Usage:** `{EXPECTED_TOTAL_USAGE:.2f}%`"
    assert expected_usage_line in report_content
