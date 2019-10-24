import json
import time
import boto3
import os
import datetime
from boto3.dynamodb.conditions import Key, Attr
import croniter

lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
            
def lambda_handler(event, context):

    JOB_RUNNER_LAMBDA = os.environ["JOB_RUNNER_LAMBDA"]
    
    current_ts = int(time.time())
    print ("Current timestamp: " + str(current_ts))
    
    # lookup dynamoDB to get jobs on this schedule
    table = dynamodb.Table('job_configuration')
    response = table.scan(
    FilterExpression=Attr('next_fire_time').lt(current_ts) & Attr('job_status').eq("READY")
    )
    jobs = response['Items']
    print ("Found " + str(len(jobs)) + " jobs to run on this schecule.")

    for job in jobs:
        print (job)
        
        # make sure the cron expression is valid or it would break the scheduler
        if not croniter.croniter.is_valid(job['schedule_expression']):
            print ("Skipping job " + job['jobId'] + " with invalid schedule expression: " + job['schedule_expression'])
        else:
            job_params={"jobId":job['jobId'] , "job_detail": job['job_detail']}
            response = lambda_client.invoke(
                FunctionName=JOB_RUNNER_LAMBDA,
                InvocationType='Event',
                Payload=json.dumps(job_params)
            )
            print(response)
            
            # update the job status in dynamodb so it won't run twice and set next fire time
            now = datetime.datetime.now()
            cron = croniter.croniter(job['schedule_expression'], now)
            next_fire = cron.get_next(datetime.datetime)
            print ("Next fire time:")
            print (next_fire)
        
            next_fire_ts = int(datetime.datetime.strptime(str(next_fire), '%Y-%m-%d %H:%M:%S').strftime("%s"))
            response = table.update_item(
                Key={
                    'jobId': job['jobId']
                },
                UpdateExpression="set job_status = :js, next_fire_time=:nft",
                ExpressionAttributeValues={
                    ':js': "RUNNING",
                    ':nft': next_fire_ts
                },
            ReturnValues="UPDATED_NEW"
            )
            print(response)
    
    
    return 
