import boto3
import json

# Configuration
ROLE_NAME = 'EC2-Kinesis-Role'
INSTANCE_PROFILE_NAME = 'EC2-Kinesis-InstanceProfile'

def create_ec2_role():
    iam_client = boto3.client('iam')
    
    # Trust policy para EC2
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    # Crear rol
    try:
        role_response = iam_client.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for EC2 to access Kinesis Firehose'
        )
        role_arn = role_response['Role']['Arn']
        print(f'Role {ROLE_NAME} created: {role_arn}')
    except iam_client.exceptions.EntityAlreadyExistsException:
        role_response = iam_client.get_role(RoleName=ROLE_NAME)
        role_arn = role_response['Role']['Arn']
        print(f'Role {ROLE_NAME} already exists: {role_arn}')
    
    # Policy para Kinesis Firehose
    firehose_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "firehose:PutRecord",
                    "firehose:PutRecordBatch",
                    "firehose:DescribeDeliveryStream"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cloudwatch:PutMetricData"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        iam_client.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName='KinesisFirehosePolicy',
            PolicyDocument=json.dumps(firehose_policy)
        )
        print('Kinesis Firehose policy attached')
    except Exception as e:
        print(f'Error attaching policy: {e}')
    
    # Crear Instance Profile
    try:
        iam_client.create_instance_profile(
            InstanceProfileName=INSTANCE_PROFILE_NAME
        )
        print(f'Instance profile {INSTANCE_PROFILE_NAME} created')
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f'Instance profile {INSTANCE_PROFILE_NAME} already exists')
    
    # Asociar rol con Instance Profile
    try:
        iam_client.add_role_to_instance_profile(
            InstanceProfileName=INSTANCE_PROFILE_NAME,
            RoleName=ROLE_NAME
        )
        print(f'Role {ROLE_NAME} added to instance profile')
    except iam_client.exceptions.LimitExceededException:
        print('Role already associated with instance profile')
    
    return INSTANCE_PROFILE_NAME

if __name__ == '__main__':
    instance_profile = create_ec2_role()
    print(f'\nInstance profile name to use in EC2: {instance_profile}')
