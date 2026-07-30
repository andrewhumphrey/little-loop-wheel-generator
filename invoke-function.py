#!/usr/bin/env python3 

import boto3
import requests

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


url = "https://t62vf6qglk72tehnftqwssvup40oespc.lambda-url.ap-southeast-2.on.aws/"

session = boto3.Session()
credentials = session.get_credentials()

request = AWSRequest(
    method="GET",
    url=url,
)

SigV4Auth(
    credentials,
    "lambda",
    session.region_name,
).add_auth(request)

response = requests.get(
    url,
    headers=dict(request.headers),
)

print(response.json())
