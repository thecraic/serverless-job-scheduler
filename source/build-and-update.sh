#!/bin/bash

# Builds and updates the dispatcher lambda function

echo "Building the lambda function package..."

rm JobDispatcher.zip
cd job-dispatcher-lambda
zip -r9 ${OLDPWD}/JobDispatcher.zip .
cd ${OLDPWD}

echo "Updating the lambda function..."

aws lambda update-function-code --function-name JobDispatcher --zip-file fileb://JobDispatcher.zip



