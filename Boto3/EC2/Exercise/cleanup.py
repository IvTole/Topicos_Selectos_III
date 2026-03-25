import boto3
import time

# Configuration
REGION = 'us-east-2'
INSTANCE_NAME = 'ecom_instance'
SECURITY_GROUP_NAME = 'security-group-ecom'
STREAM_NAME = 'Clientorders'
DELIVERY_STREAM_NAME = 'Purchaselogs'
BUCKET_NAME = 'ecom-purchaselogs-bucket'
TABLE_NAME = 'ClientOrders'
FUNCTION_NAME = 'KinesisToClientOrders'
LAMBDA_ROLE_NAME = 'Lambda-Kinesis-DynamoDB-Role'
FIREHOSE_ROLE_NAME = 'FirehoseDeliveryRole'
EC2_ROLE_NAME = 'EC2-Kinesis-Role'
INSTANCE_PROFILE_NAME = 'EC2-Kinesis-InstanceProfile'

def delete_ec2_instances():
    print('Deleting EC2 instances...')
    ec2 = boto3.resource('ec2', region_name=REGION)
    ec2_client = boto3.client('ec2', region_name=REGION)
    
    instances = ec2.instances.filter(
        Filters=[{'Name': 'tag:Name', 'Values': [INSTANCE_NAME]},
                 {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'pending', 'stopping']}]
    )
    
    instance_ids = [i.id for i in instances]
    if instance_ids:
        ec2_client.terminate_instances(InstanceIds=instance_ids)
        print(f'Terminating instances: {instance_ids}')
        print('Waiting for instances to terminate...')
        waiter = ec2_client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=instance_ids)
        print('Instances terminated')
    else:
        print('No instances found')

def delete_security_group():
    print('\nDeleting security group...')
    ec2_client = boto3.client('ec2', region_name=REGION)
    
    try:
        groups = ec2_client.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])
        sg_id = groups['SecurityGroups'][0]['GroupId']
        ec2_client.delete_security_group(GroupId=sg_id)
        print(f'Security group {SECURITY_GROUP_NAME} deleted')
    except ec2_client.exceptions.ClientError as e:
        if 'InvalidGroup.NotFound' in str(e):
            print(f'Security group {SECURITY_GROUP_NAME} not found')
        else:
            print(f'Error deleting security group: {e}')

def delete_kinesis_stream():
    print('\nDeleting Kinesis stream...')
    kinesis_client = boto3.client('kinesis', region_name=REGION)
    
    try:
        kinesis_client.delete_stream(
            StreamName=STREAM_NAME,
            EnforceConsumerDeletion=True
        )
        print(f'Kinesis stream {STREAM_NAME} deleted')
    except kinesis_client.exceptions.ResourceNotFoundException:
        print(f'Kinesis stream {STREAM_NAME} not found')
    except Exception as e:
        print(f'Error deleting Kinesis stream: {e}')

def delete_firehose_stream():
    print('\nDeleting Firehose delivery stream...')
    firehose_client = boto3.client('firehose', region_name=REGION)
    
    try:
        firehose_client.delete_delivery_stream(
            DeliveryStreamName=DELIVERY_STREAM_NAME,
            AllowForceDelete=True
        )
        print(f'Delivery stream {DELIVERY_STREAM_NAME} deleted')
    except firehose_client.exceptions.ResourceNotFoundException:
        print(f'Delivery stream {DELIVERY_STREAM_NAME} not found')
    except Exception as e:
        print(f'Error deleting delivery stream: {e}')

def delete_s3_bucket():
    print('\nDeleting S3 bucket...')
    s3 = boto3.resource('s3')
    
    try:
        bucket = s3.Bucket(BUCKET_NAME)
        bucket.objects.all().delete()
        bucket.delete()
        print(f'Bucket {BUCKET_NAME} and all contents deleted')
    except s3.meta.client.exceptions.NoSuchBucket:
        print(f'Bucket {BUCKET_NAME} not found')
    except Exception as e:
        print(f'Error deleting bucket: {e}')

def delete_iam_roles():
    print('\nDeleting IAM roles...')
    iam_client = boto3.client('iam')
    
    # Delete EC2 role
    try:
        iam_client.remove_role_from_instance_profile(
            InstanceProfileName=INSTANCE_PROFILE_NAME,
            RoleName=EC2_ROLE_NAME
        )
        print(f'Role {EC2_ROLE_NAME} removed from instance profile')
    except iam_client.exceptions.NoSuchEntityException:
        pass
    
    try:
        iam_client.delete_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)
        print(f'Instance profile {INSTANCE_PROFILE_NAME} deleted')
    except iam_client.exceptions.NoSuchEntityException:
        print(f'Instance profile {INSTANCE_PROFILE_NAME} not found')
    
    try:
        policies = iam_client.list_role_policies(RoleName=EC2_ROLE_NAME)
        for policy in policies['PolicyNames']:
            iam_client.delete_role_policy(RoleName=EC2_ROLE_NAME, PolicyName=policy)
        iam_client.delete_role(RoleName=EC2_ROLE_NAME)
        print(f'Role {EC2_ROLE_NAME} deleted')
    except iam_client.exceptions.NoSuchEntityException:
        print(f'Role {EC2_ROLE_NAME} not found')
    
    # Delete Lambda role
    try:
        policies = iam_client.list_role_policies(RoleName=LAMBDA_ROLE_NAME)
        for policy in policies['PolicyNames']:
            iam_client.delete_role_policy(RoleName=LAMBDA_ROLE_NAME, PolicyName=policy)
        iam_client.delete_role(RoleName=LAMBDA_ROLE_NAME)
        print(f'Role {LAMBDA_ROLE_NAME} deleted')
    except iam_client.exceptions.NoSuchEntityException:
        print(f'Role {LAMBDA_ROLE_NAME} not found')
    
    # Delete Firehose role
    try:
        policies = iam_client.list_role_policies(RoleName=FIREHOSE_ROLE_NAME)
        for policy in policies['PolicyNames']:
            iam_client.delete_role_policy(RoleName=FIREHOSE_ROLE_NAME, PolicyName=policy)
        iam_client.delete_role(RoleName=FIREHOSE_ROLE_NAME)
        print(f'Role {FIREHOSE_ROLE_NAME} deleted')
    except iam_client.exceptions.NoSuchEntityException:
        print(f'Role {FIREHOSE_ROLE_NAME} not found')

def delete_lambda_function():
    print('\nDeleting Lambda function...')
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    try:
        # Delete event source mappings first
        mappings = lambda_client.list_event_source_mappings(FunctionName=FUNCTION_NAME)
        for mapping in mappings['EventSourceMappings']:
            lambda_client.delete_event_source_mapping(UUID=mapping['UUID'])
            print(f'Event source mapping {mapping["UUID"]} deleted')
    except lambda_client.exceptions.ResourceNotFoundException:
        pass
    
    try:
        lambda_client.delete_function(FunctionName=FUNCTION_NAME)
        print(f'Lambda function {FUNCTION_NAME} deleted')
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f'Lambda function {FUNCTION_NAME} not found')
    except Exception as e:
        print(f'Error deleting Lambda function: {e}')

def delete_dynamodb_table():
    print('\nDeleting DynamoDB table...')
    dynamodb = boto3.client('dynamodb', region_name=REGION)
    
    try:
        dynamodb.delete_table(TableName=TABLE_NAME)
        print(f'DynamoDB table {TABLE_NAME} deleted')
    except dynamodb.exceptions.ResourceNotFoundException:
        print(f'DynamoDB table {TABLE_NAME} not found')
    except Exception as e:
        print(f'Error deleting DynamoDB table: {e}')

if __name__ == '__main__':
    print('Starting cleanup...\n')
    
    delete_ec2_instances()
    time.sleep(5)
    delete_security_group()
    delete_lambda_function()
    delete_kinesis_stream()
    delete_firehose_stream()
    time.sleep(5)
    delete_dynamodb_table()
    delete_s3_bucket()
    delete_iam_roles()
    
    print('\n✓ Cleanup completed!')
