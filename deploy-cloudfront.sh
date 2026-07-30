aws cloudformation deploy \
  --region us-east-1 \
  --stack-name little-loop-edge \
  --template-file edge-template.yaml \
  --parameter-overrides \
      LambdaFunctionUrl="$(aws cloudformation describe-stacks --stack-name littleloop-wheel-generator --region ap-southeast-2 --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' --output text)" \
      Username=littleloop \
      Password="$(aws ssm get-parameter --region ap-southeast-2 --name /littleloop/web-password --with-decryption --query Parameter.Value  --output text)" \
      CloudFrontSecret="$(aws ssm get-parameter --region ap-southeast-2 --name /littleloop/cloudfront/shared-secret --with-decryption --query Parameter.Value  --output text)" \
  --capabilities CAPABILITY_IAM
