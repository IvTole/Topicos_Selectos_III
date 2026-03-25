import boto3
import json
import zipfile
import os
import time

# Configuration
REGION = 'us-east-2'
FUNCTION_NAME = 'KinesisToClientOrders'
ROLE_NAME = 'Lambda-Kinesis-DynamoDB-Role'
STREAM_NAME = 'Clientorders'
TABLE_NAME = 'ClientOrders'

def create_lambda_role():
    iam_client = boto3.client('iam')
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        role_response = iam_client.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Lambda to read from Kinesis and write to DynamoDB'
        )
        role_arn = role_response['Role']['Arn']
        print(f'Role {ROLE_NAME} created: {role_arn}')
        time.sleep(10)  # Wait for role to propagate
    except iam_client.exceptions.EntityAlreadyExistsException:
        role_response = iam_client.get_role(RoleName=ROLE_NAME)
        role_arn = role_response['Role']['Arn']
        print(f'Role {ROLE_NAME} already exists: {role_arn}')
    
    # Policy for Lambda
    lambda_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "kinesis:GetRecords",
                    "kinesis:GetShardIterator",
                    "kinesis:DescribeStream",
                    "kinesis:ListStreams"
                ],
                "Resource": f"arn:aws:kinesis:{REGION}:*:stream/{STREAM_NAME}"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                    "dynamodb:BatchWriteItem"
                ],
                "Resource": f"arn:aws:dynamodb:{REGION}:*:table/{TABLE_NAME}"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            }
        ]
    }
    
    try:
        iam_client.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName='LambdaKinesisDynamoDBPolicy',
            PolicyDocument=json.dumps(lambda_policy)
        )
        print('Lambda policy attached')
    except Exception as e:
        print(f'Error attaching policy: {e}')
    
    return role_arn

def create_lambda_function(role_arn):
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    # Create deployment package
    zip_file = '/tmp/lambda_function.zip'
    with zipfile.ZipFile(zip_file, 'w') as zf:
        zf.write('lambda_function.py', 'lambda_function.py')
    
    with open(zip_file, 'rb') as f:
        zip_content = f.read()
    
    try:
        response = lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.9',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=60,
            MemorySize=256,
            Description='Process Kinesis stream data and write to DynamoDB'
        )
        print(f'Lambda function {FUNCTION_NAME} created')
        print(f'Function ARN: {response["FunctionArn"]}')
        return response['FunctionArn']
    except lambda_client.exceptions.ResourceConflictException:
        print(f'Lambda function {FUNCTION_NAME} already exists')
        response = lambda_client.get_function(FunctionName=FUNCTION_NAME)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f'Error creating Lambda function: {e}')
        return None

def add_kinesis_trigger(function_arn):
    lambda_client = boto3.client('lambda', region_name=REGION)
    kinesis_client = boto3.client('kinesis', region_name=REGION)
    
    # Get stream ARN
    stream_info = kinesis_client.describe_stream(StreamName=STREAM_NAME)
    stream_arn = stream_info['StreamDescription']['StreamARN']
    
    try:
        response = lambda_client.create_event_source_mapping(
            EventSourceArn=stream_arn,
            FunctionName=FUNCTION_NAME,
            StartingPosition='LATEST',
            BatchSize=100,
            MaximumBatchingWindowInSeconds=5
        )
        print(f'Kinesis trigger added to Lambda')
        print(f'Event Source Mapping UUID: {response["UUID"]}')
    except lambda_client.exceptions.ResourceConflictException:
        print('Kinesis trigger already exists')
    except Exception as e:
        print(f'Error adding trigger: {e}')

if __name__ == '__main__':
    print('Creating Lambda role...')
    role_arn = create_lambda_role()
    
    print('\nCreating Lambda function...')
    function_arn = create_lambda_function(role_arn)
    
    if function_arn:
        print('\nAdding Kinesis trigger...')
        add_kinesis_trigger(function_arn)
        
        print('\n✓ Lambda setup completed!')
        print(f'\nFunction: {FUNCTION_NAME}')
        print(f'Trigger: Kinesis Stream "{STREAM_NAME}"')
        print(f'Destination: DynamoDB Table "{TABLE_NAME}"')
