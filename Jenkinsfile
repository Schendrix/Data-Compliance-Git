pipeline {
// Change agent from 'docker' to 'any' to run directly on the executor machine
agent any

// Set environment variables for the script if needed (optional)
environment {
    // Define the path to the virtual environment for easy reference
    VENV_DIR = 'venv'
    PYTHON_BIN = 'venv/bin/python3'
    ANALYTICS_LEVEL = 'CRITICAL'
}

stages {
    stage('Checkout Code') {
        steps {
            echo 'Source code assumed checked out by Jenkins SCM.'
        }
    }

    stage('Setup Environment') {
        steps {
            echo "Creating virtual environment and installing dependencies..."
            // 1. Create the virtual environment using python3
            sh "python3 -m venv ${env.VENV_DIR}"
            
            // 2. Install dependencies using the Python binary inside the venv
            sh "${env.PYTHON_BIN} -m pip install -r requirements.txt"
        }
    }

    stage('Run Unit Tests') {
        steps {
            echo "Running unit tests using pytest from virtual environment..."
            // 3. Execute pytest using the Python binary inside the venv
            sh "${env.PYTHON_BIN} -m pytest"
        }
    }

    stage('Run Data Analysis') {
        steps {
            sh """
            echo "Starting production data analysis script..."
            // 4. Execute the main script using the Python binary inside the venv
            ${env.PYTHON_BIN} data_processor.py
            """
        }
    }

    stage('Reporting') {
        when {
            // Only run this stage if the previous stage (Run Data Analysis) passed
            expression { currentBuild.result == 'SUCCESS' }
        }
        steps {
            echo 'Analysis successful: All dataset memory usage is compliant with the threshold.'
        }
    }
} // End of stages block

post {
    // Define actions that run after the entire pipeline finishes
    always {
        // Archive the generated report file as a build artifact regardless of build status
        archiveArtifacts artifacts: 'analysis_report.md', onlyIfSuccessful: false

        // Clean up the generated database, report file, and the virtual environment directory
        sh 'rm -f object_store.db'
        sh 'rm -f analysis_report.md'
        sh "rm -rf ${env.VENV_DIR}" // Clean up the venv directory
        echo 'Cleanup complete.'
    }
    failure {
        echo 'One or more stages failed (Tests or Data Analysis). The full report is archived as an artifact.'
    }
} // End of post block


}
