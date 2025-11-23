pipeline {
// Change agent from 'docker' to 'any' to run directly on the executor machine
agent any

// Set environment variables for the script if needed (optional)
environment {
    // A simple variable demonstration, not strictly necessary for this script
    ANALYTICS_LEVEL = 'CRITICAL'
}

stages {
    stage('Checkout Code') {
        steps {
            // FIX: Removed the empty 'script {}' block which caused the Groovy compilation error.
            // When running from SCM, Jenkins automatically checks out the code before the pipeline starts.
            echo 'Source code assumed checked out by Jenkins SCM.'
        }
    }

    stage('Install Dependencies') {
        steps {
            echo 'Installing Python dependencies from requirements.txt...'
            // Using 'python -m pip' is more robust than just 'pip'
            sh 'python -m pip install -r requirements.txt'
        }
    }

    stage('Run Unit Tests') {
        steps {
            echo "Running unit tests using pytest..."
            // Using 'python -m pytest' is more robust than just 'pytest'
            sh 'python -m pytest'
        }
    }

    stage('Run Data Analysis') {
        steps {
            sh """
            echo "Starting production data analysis script..."
            // Run the script. If it exits with status 1 (due to threshold failure), the build will fail.
            python data_processor.py
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
            // You could add steps here to publish reports or artifacts
        }
    }
} // End of stages block

post {
    // Define actions that run after the entire pipeline finishes
    always {
        // Archive the generated report file as a build artifact regardless of build status
        // The file analysis_report.md will be available to download from the Jenkins build page.
        archiveArtifacts artifacts: 'analysis_report.md', onlyIfSuccessful: false

        // Clean up the generated database and report file
        sh 'rm -f object_store.db'
        sh 'rm -f analysis_report.md'
        echo 'Cleanup complete.'
    }
    failure {
        echo 'One or more stages failed (Tests or Data Analysis). The full report is archived as an artifact.'
    }
} // End of post block


}
