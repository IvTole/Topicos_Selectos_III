import boto3
import time

# Configuration
REGION = 'us-east-2'
INSTANCE_NAME = 'ecom_instance'
SECURITY_GROUP_NAME = 'security-group-ecom'
DELIVERY_STREAM_NAME = 'Purchaselogs'
BUCKET_NAME = 'ecom-purchaselogs-bucket'
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
    
    # Delete Firehose role
    try:
        policies = iam_client.list_role_policies(RoleName=FIREHOSE_ROLE_NAME)
        for policy in policies['PolicyNames']:
            iam_client.delete_role_policy(RoleName=FIREHOSE_ROLE_NAME, PolicyName=policy)
        iam_client.delete_role(RoleName=FIREHOSE_ROLE_NAME)
        print(f'Role {FIREHOSE_ROLE_NAME} deleted')
    except iam_client.exceptions.NoSuchEntityException:
        print(f'Role {FIREHOSE_ROLE_NAME} not found')

if __name__ == '__main__':
    print('Starting cleanup...\n')
    
    delete_ec2_instances()
    time.sleep(5)
    delete_security_group()
    delete_firehose_stream()
    time.sleep(5)
    delete_s3_bucket()
    delete_iam_roles()
    
    print('\n✓ Cleanup completed!')
