import boto3
import json

# Configuration
REGION = 'us-east-2'
DELIVERY_STREAM_NAME = 'Purchaselogs'
BUCKET_NAME = 'ecom-purchaselogs-bucket'
IAM_ROLE_NAME = 'FirehoseDeliveryRole'

def create_firehose_role():
    iam_client = boto3.client('iam')
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "firehose.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        role_response = iam_client.create_role(
            RoleName=IAM_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Firehose to write to S3'
        )
        role_arn = role_response['Role']['Arn']
        print(f'Role {IAM_ROLE_NAME} created: {role_arn}')
    except iam_client.exceptions.EntityAlreadyExistsException:
        role_response = iam_client.get_role(RoleName=IAM_ROLE_NAME)
        role_arn = role_response['Role']['Arn']
        print(f'Role {IAM_ROLE_NAME} already exists: {role_arn}')
    
    # Attach policy for S3 access
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{BUCKET_NAME}",
                    f"arn:aws:s3:::{BUCKET_NAME}/*"
                ]
            }
        ]
    }
    
    try:
        iam_client.put_role_policy(
            RoleName=IAM_ROLE_NAME,
            PolicyName='FirehoseS3Policy',
            PolicyDocument=json.dumps(policy_document)
        )
        print('Policy attached to role')
    except Exception as e:
        print(f'Error attaching policy: {e}')
    
    return role_arn

def create_firehose_delivery_stream(role_arn):
    firehose_client = boto3.client('firehose', region_name=REGION)
    
    try:
        response = firehose_client.create_delivery_stream(
            DeliveryStreamName=DELIVERY_STREAM_NAME,
            DeliveryStreamType='DirectPut',
            S3DestinationConfiguration={
                'RoleARN': role_arn,
                'BucketARN': f'arn:aws:s3:::{BUCKET_NAME}',
                'Prefix': 'logs/',
                'BufferingHints': {
                    'SizeInMBs': 5,
                    'IntervalInSeconds': 300
                },
                'CompressionFormat': 'UNCOMPRESSED'
            }
        )
        print(f'Delivery stream {DELIVERY_STREAM_NAME} created successfully')
        print(f'Stream ARN: {response["DeliveryStreamARN"]}')
    except firehose_client.exceptions.ResourceInUseException:
        print(f'Delivery stream {DELIVERY_STREAM_NAME} already exists')
    except Exception as e:
        print(f'Error creating delivery stream: {e}')
        raise

if __name__ == '__main__':
    print('Creating IAM role for Firehose...')
    role_arn = create_firehose_role()
    
    print('\nWaiting for role to propagate...')
    import time
    time.sleep(10)
    
    print('\nCreating Firehose delivery stream...')
    create_firehose_delivery_stream(role_arn)
