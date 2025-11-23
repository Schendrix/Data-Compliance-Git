pipeline {
// Change agent from 'docker' to 'any' to run directly on the executor machine
agent any

// Set environment variables for the script if needed (optional)
environment {
    // CI/CD Configuration
    VENV_DIR = 'venv'
    PYTHON_BIN = 'venv/bin/python3'
    ANALYTICS_LEVEL = 'CRITICAL'
    
    // BLUE/GREEN CONFIGURATION
    BLUE_ENV = 'blue_env_stable'
    GREEN_ENV = 'green_env_new'

    // NEW: Create a versioned filename using the Jenkins BUILD_NUMBER
    VERSIONED_FILENAME = "data_processor_v${env.BUILD_NUMBER}.py"
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
            sh "python3 -m venv ${env.VENV_DIR}"
            sh "${env.PYTHON_BIN} -m pip install -r requirements.txt"
        }
    }

    stage('Run Unit Tests') {
        steps {
            echo "Running unit tests using pytest from virtual environment..."
            sh "${env.PYTHON_BIN} -m pytest"
        }
    }

    stage('Run Data Analysis') {
        steps {
            sh """
            echo "Starting production data analysis script..."
            ${env.PYTHON_BIN} data_processor.py
            """
        }
    }

    // --- CD STAGE: Simulated Blue/Green Deployment ---
    stage('Blue/Green Deployment') {
        steps {
            echo 'Compliance check PASSED. Building Green Environment.'

            // 5. Build the new "Green" Environment and deploy the new code
            sh "mkdir -p ${env.GREEN_ENV}"
            sh "cp data_processor.py ${env.GREEN_ENV}/${env.VERSIONED_FILENAME}"
            echo "DEPLOYMENT: New version ${env.BUILD_NUMBER} deployed to GREEN environment: ${env.GREEN_ENV}"

            // 6. Simulate Green Environment Tests (Placeholder for smoke tests, etc.)
            echo 'TESTING: Running smoke tests against the Green Environment...'
            sh 'echo "Green environment tests passed successfully."'

            // 7. Traffic Switch (The Cutover) - Simulating switching a symbolic link
            sh "ln -sf ${env.GREEN_ENV} current_live_service"
            echo "CUTOVER: Traffic switched to new Green environment (${env.GREEN_ENV}). Old Blue is now standby."

            // 8. Verification Step - List the contents of the live service link target
            echo 'VERIFICATION: Listing files in the LIVE service link target...'
            sh "ls -l current_live_service/"
        }
    }
    // --- END CD STAGE ---

} // End of stages block

post {
    // Define actions that run after the entire pipeline finishes
    always {
        // Archive the generated report file as a build artifact regardless of build status
        archiveArtifacts artifacts: 'analysis_report.md', onlyIfSuccessful: false

        // Clean up the generated database, report file, virtual environment, and simulated production folder
        sh 'rm -f object_store.db'
        sh 'rm -f analysis_report.md'
        sh "rm -rf ${env.VENV_DIR}" // Clean up the venv directory
        
        // Clean up Blue/Green directories and the live link
        sh "rm -rf ${env.BLUE_ENV}"
        sh "rm -rf ${env.GREEN_ENV}"
        sh "rm -f current_live_service"

        echo 'Cleanup complete.'
    }
    failure {
        echo 'One or more stages failed (Tests or Data Analysis). The full report is archived as an artifact.'
    }

} // End of post block


} // FINAL CLOSING BRACE FOR THE PIPELINE BLOCK
