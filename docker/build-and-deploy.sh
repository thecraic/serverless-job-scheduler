#!/bin/bash

# Builds and deploys the docker container to the ECR repo

export set AWS_ACCOUNT_ID=`aws sts get-caller-identity |grep Account |awk '{print $2}'|colrm 15| tr -d '"'`
export set AWS_REGION=`aws configure get region`

echo "Building job-runner docker container..."

docker build -t job-runner .
docker tag job-runner:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/job-runner

echo "Logging into ECR for $AWS_ACCOUNT_ID in region $AWS_REGION"
## Login to the ECR repository - set your own region
$(aws ecr get-login --no-include-email --region $AWS_REGION)

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/job-runner:latest



