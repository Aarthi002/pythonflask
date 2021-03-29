pipeline {
    agent any
	environment {
		PROJECT_ID = 'tasko-task'
                CLUSTER_NAME = 'k8s-cluster'
                LOCATION = 'us-central1-c'
                CREDENTIALS_ID = 'tasko-task'		
	}
	
    stages {
    stage ('Code Pull') {
      steps{
        script{
          sh 'echo "Pull Successful"'
        }
      }
    }
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
	    
	    
	    
	    stage('Build Docker Image') {
		    steps {
			    sh 'whoami'
			    script {
				    myimage = docker.build("katara123/devops:${env.BUILD_ID}")
			    }
		    }
	    }
	    
	    stage("Push Docker Image") {
		    steps {
			    script {
				    echo "Push Docker Image"
				    withCredentials([string(credentialsId: 'dockerhub', variable: 'dockerhub')]) {
            				sh "docker login -u katara123 -p ${dockerhub}"
				    }
				        myimage.push("${env.BUILD_ID}")
				    
			    }
		    }
	    }
	    
	    stage('Deploy to K8s') {
		    steps{
			    echo "Deployment started ..."
			    sh 'ls -ltr'
			    sh 'pwd'
			    /*sh "sed -i 's/tagversion/${env.BUILD_ID}/g' serviceLB.yaml"*/
				sh "sed -i 's/tagversion/${env.BUILD_ID}/g' deployment.yaml"
			   /* echo "Start deployment of serviceLB.yaml"*/
			    /*step([$class: 'KubernetesEngineBuilder', projectId: env.PROJECT_ID, clusterName: env.CLUSTER_NAME, location: env.LOCATION, manifestPattern: 'serviceLB.yaml', credentialsId: env.CREDENTIALS_ID, verifyDeployments: true])*/
				echo "Start deployment of deployment.yaml"
				step([$class: 'KubernetesEngineBuilder', projectId: env.PROJECT_ID, clusterName: env.CLUSTER_NAME, location: env.LOCATION, manifestPattern: 'deployment.yaml', credentialsId: env.CREDENTIALS_ID, verifyDeployments: true])
			    echo "Deployment Finished ..."
		    }
	    }
    }
}
