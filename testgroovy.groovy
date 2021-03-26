pipeline {
  agent any
  environment {
    //once you sign up for Docker hub, use that user_id here
    registry = "katara123/devops"
    //- update your credentials ID after creating credentials for connecting to Docker Hub
    registryCredential = 'katara123'
    dockerImage = ''
  }
  stages {
    stage ('Code Pull') {
      steps{
        script{
          sh 'echo "Pull Successful"'
        }
      }
    }
    
    /*stage('PyLint: Code Analysis') {
      steps {
        script {
          sh 'pylint sample.py | tee pylint.log'
          recordIssues(
            tool: pyLint(pattern: 'pylint.log'),
            failTotalHigh: 10,
          )
        }
      }
    }*/
    
    stage ('test: Unit-Test') {
      steps{
        sh 'sudo python3 -m unittest test.py -v'
        sh 'echo "Unittest Success"'
        sh 'pwd'
      }
    }
    
    stage ('test: Jmeter-test') {
      steps{
        sh 'sudo /home/davidbala592/jmeter/apache-jmeter-5.4.1/bin/jmeter -n -t /home/davidbala592/jmeter/apache-jmeter-5.4.1/bin/google-demo.jmx -l /home/davidbala592/jmeter/apache-jmeter-5.4.1/bin/google-demo-result.jtl'
        sh 'echo "Perfomance Test Success"'
        perfReport '/home/davidbala592/jmeter/apache-jmeter-5.4.1/bin/google-demo-result.jtl'
      }
    }
    
    stage('SonarQube analysis') {
      environment {
        scannerHome = tool 'scanner'
      }
      steps {
        withSonarQubeEnv('SonarQube') {
          
          sh '''
          sudo ${scannerHome}/bin/sonar-scanner \
          -D sonar.login=admin \
          -D sonar.password=gcp \
          -D sonar.projectKey=quizapp \
          -D sonar.projectName=quizapp \
          -D sonar.projectVersion=1.0 \
          -D sonar.sources=/var/lib/jenkins/workspace/test_pipeline/app.py \
          -D sonar.language=py \
          -D sonar.sourceEncoding=UTF-8 \
          -D sonar.python.xunit.reportPath=nosetests.xml \
          -D sonar.python.coverage.reportPath=coverage.xml
          '''
        }
      }
    }
    
    stage('Building image') {
      steps{
        script {
          dockerImage = docker.build registry
        }
      }
    }
    stage('Upload Image - DockerHub') {
      steps{
        script {
          docker.withRegistry( '', registryCredential ) {
            dockerImage.push()  
          }
        }
      }
    }
    // Stopping Docker containers for cleaner Docker run
    stage('Clean Container') {
      steps {
        sh 'docker ps -f name=mypythonappContainer -q | xargs --no-run-if-empty docker container stop'
        sh 'docker container ls -a -fname=mypythonappContainer -q | xargs -r docker container rm'
      }
    }
    // Running Docker container, make sure port 80 mapped from flask server port 5000 is opened in
    stage('Docker Run') {
      steps{
        script {
          dockerImage.run("-p 0.0.0.0:80:5000/tcp --rm --name mypythonappContainer")
        }
      }
    }
  }
}
