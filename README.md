The Lambda is exposed using a Lambda Function URL protected with AWS IAM authentication.

## Architecture


Client
|
| IAM authenticated request
|
Lambda Function URL
|
|
Lambda
|
+--> AWS Parameter Store
| |
| +--> Humanitix API Key
| +--> Wheel of Names API Key
|
+--> Humanitix API
|
+--> Wheel of Names API

## Project Layout

├── template.yaml
├── requirements.txt
└─+ src
  ├── lambda_function.py
  ├── config.py
  ├── secrets.py
  ├── models.py
  ├── util.py
  ├── humanitix.py
  ├── wheel.py
  └── wheel_logo.py


## AWS Parameters

Create the following SecureString parameters:

/littleloop/humanitix/api-key
/littleloop/wheel/api-key
/littleloop/cloudfront/shared-secret
/littleloop/web-password


## Lambda Permissions
The Lambda execution role requires:

ssm:GetParameter
kms:Decrypt


permissions.

## Deployment

Install SAM CLI:

https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

Build:

```bash
sam build

Deploy:

Cloudfront: 

./deploy-cloudfront.sh  (in us-east-1)
You then need the distribution id from the cloudfront distribution that makes to pass to the sam deploy
Also remember to go and set the cloudfront distribution to the free plan and enable a custom domain name

You can put this in whatever region you want.
sam deploy --guided

During deployment provide:

EventId
DistributionId


## Calling the Lambda

The lambda configures itself to be only callable via the cloudfront distribution, so test in the console if you need to
