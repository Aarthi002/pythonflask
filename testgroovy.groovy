pipeline {
  agent any
  stages {
    stage ('build') {
      steps{
        script{
          sh 'echo "Build Successful"'
          sh 'sudo python3 -m unittest test.py'
        }
      }
    }
    stage ('test: unit-test') {
      steps{
        sh 'echo "hello unittest hari07"'
        sh 'echo "A one line step"'
        sh ''' 
        echo "A multiline step"
        echo "ok"
        ls
        '''
      }
    }
  }
}
