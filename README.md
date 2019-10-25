# Serverless Job Scheduler

The Serverless Job Scheduler is a prototype ad-hoc job scheduler that shows how Amazon Cloudwatch, Lambda, Fargate and SNS can be used to implement a cost-effective scalable, event driven job scheduler. 

Sometimes jobs take longer than 15 minutes to run (Lambda max execution time). In these cases it makes sense to run the job as an ECS (Elastic Container Service) fargate task.

This example is easy to deploy and uses AWS CloudFormation to automatically provision and configure the necessary AWS services.


![architecture diagram](/images/architecture.png)


Job configurations, including cron schedule, current status and job execution parameters are stored in a DynamoDB table.

A CloudWatch rule running every minute triggers a Lambda function (JobDispatcher) which checks the job configurations for any jobs that have exceeded their "next fire time" and are "READY" to run. 

The JobDispatcher then asychronously invokes another (JobRunner) Lambda function for each overdue job. It then calculates the "next fire time" for the job based on it's cron schedule and updates the job status in DynamoDB to "RUNNING" - preventing double jobbing.

The JobRunner function  performs a check (polls) to see if there is work to do, and then creates a fargate task passing the job execution details to the docker container as an environment variable. 

When the fargate task is completed, the Amazon ECS (Elastic Container Service) system automatically generates an SNS (Simple Notification Service) event. A CloudWatch rule detects these events and triggers a (JobMonitor) Lambda function which returns the status of the job to "READY"  - in preparation for the next scheduled fire time.

Jobs configuration records are managed by adding or updating them into the DynamoDB table.

## Advantages
* Practically infinite number of job configurations are possible. CloudWatch default event bus is limited to 300 initially.
* No requirement to maintain servers for cron tasks.
* Flexiblity to specify different task defintions or docker containers in job configurations (not demonstrated here).
* DynamoDB can be conveniently used by an application to manage job configurations, or see what is currently running.

## Limitations
* This example is a prototype, provide as-is without guarantee and not meant to be used in production without modification for fault tolerance and exception handling.
* Fargate launch type has an initial quota of 50 concurrent executions - this limit may be raised by requesting a limit increase.
* JobRunner polling is a basic "file exists" check for this prototype. 
* JobDisptacher is called every minute by CloudWatch. If you need this to run more than once per minute. [See here](https://aws.amazon.com/blogs/architecture/a-serverless-solution-for-invoking-aws-lambda-at-a-sub-minute-frequency/)


## Recommendations
* [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) should be used to store any credentials used by tasks or polling functions.
* Fargate containers have 10Gb ephemeral storage  - considering chunking or streaming larger files into S3


## Getting Started
Clone the repository

```
git clone https://github.com/thecraic/serverless-job-scheduler.git
```

Create a bucket we can use to read/store job data.

```
aws s3 mb s3://<YOUR_BUCKET_NAME>
export BUCKET_NAME=<YOUR_BUCKET_NAME>
```

Create the CloudFormation stack. This will create all of the resources in the default account and region for your AWS CLI profile

```
cd serverless-job-scheduler
aws cloudformation create-stack \
    --stack-name serverless-job-scheduler \
    --capabilities CAPABILITY_IAM  \
    --template-body file://$PWD/serverless-job-scheduler.yml \
    --parameters ParameterKey=AllowedBucket,ParameterValue=$BUCKET_NAME

```
Monitor the stack creation until complete in the AWS Console under CloudFormation. 


Build and deploy the docker container task runner to the ECR Repository
```
cd docker
chmod +x build-and-deploy.sh
./build-and-deploy.sh
```

Build and update the JobDispatcher Lambda function package.
```
cd ../source
chmod +x build-and-update.sh
./build-and-update.sh
```

You should now have everything running and the CloudWatch rule will be in place calling the dispatcher function every minute. This can be checked in
[CloudWatch Rules](https://console.aws.amazon.com/cloudwatch/home?#rules:)

Monitor the dispatcher function in CloudWatch Logs Streams for /aws/lambda/JobDispatcher
**Make sure you choose same region as configured in your AWS CLI default profile.**

Here you will see there are no job configurations found.

![no work log](/images/JobDispatcherLog_no_work.png)


***

## Add a scheduled job configuration
This is done by adding a record with the following structure to the DynamoDB table job_configuration. **REPLACE targetLocation with the name of your S3 bucket.**

```
aws dynamodb put-item \
    --table-name job_configuration \
    --item '
{
  "jobId": {
    "S": "2aaf0cda-f267-11e9-81b4-2a2ae2dbcce4"
  },
  "job_name": {
    "S": "Example Transfer Job"
  },
  "job_description": {
    "S": "Downloads whitepaper to S3 every 5 minutes."
  },
  "job_detail": {
    "M": {
      "sourceUrl": {
        "S": "https://d1.awsstatic.com/whitepapers/aws-overview.pdf"
      },
      "targetLocation": {
        "S": "s3://serverless-job-scheduler-target/aws-overview.pdf"
      }
    }
  },
  "job_status": {
    "S": "READY"
  },
  "last_run_status": {
    "S": "OK"
  },
  "next_fire_time": {
    "N": "1571842128"
  },
  "schedule_expression": {
    "S": "*/5 * * * *"
  }
}'

```
Notes:
* jobId should be a unique identifier for the job
* schedule_expression must be a valid cron expression
* next_fire_time should be a unix timestamp (UTC) - in the past to start the schedule immediately.

When this item is created the fargate task will be run every 5 minutes. The docker container will receive an environment variable JOB_DETAIL containing the instructions for the task.

In this case the instruction is to download the source file and place it into the target S3 bucket.

***

## Monitoring Jobs

When the Job Dispatcher detects that this job has missed the "next fire time" , it calls the Job Runner Lambda, updates the job status to "RUNNING" and sets the next fire time for this job. Details are logged in CloudWatch Log Group: /aws/lambda/JobDispatcher

![work log](/images/JobDispatcherLog_1_job.png)

The output logs from each ECS fargate task are available in CloudWatch logs under the LogGroup:
/ecs/job-schedulerTaskDefinition

![fargate task log](/images/ECS_fargate_runner_log.png)

In this case we can see that the file was downloads and piped directly into the target S3 location.

***



This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied.