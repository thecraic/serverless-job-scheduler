import time
import sys
import os
import subprocess
import json

if (len(sys.argv)>1):
    print('Running job with ID : ' + sys.argv[1])
    # use this id to fetch job detail from DynamoDB
    if "JOB_DETAIL" in os.environ:
        JOB_DETAIL = os.environ["JOB_DETAIL"]
        print (JOB_DETAIL)
        
        job_config = json.loads(JOB_DETAIL)
        
        download_command="curl " + job_config['job_detail']['sourceUrl'] +" | aws s3 cp - " + job_config['job_detail']['targetLocation'] 
        print (download_command)
        print (os.popen(download_command).read())


    time.sleep(5)
    print('Task ended, took 5 seconds.')
else:
    print('No job ID provided. Nothing to do.')



