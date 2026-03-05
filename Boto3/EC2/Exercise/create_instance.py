import boto3

# Configuration
REGION = 'us-east-2'
AMI_ID = 'ami-03e666df3cd425262'
INSTANCE_TYPE = 't3.micro'
KEY_NAME = 'ecom_key'
SECURITY_GROUP_NAME = 'security-group-ecom'
INSTANCE_NAME = 'ecom_instance'
VOLUME_SIZE = 8
IAM_INSTANCE_PROFILE = 'EC2-Kinesis-InstanceProfile'

# Initialize EC2 resource
ec2 = boto3.resource('ec2', region_name=REGION)

# Create a security group if it doesn't exist
def create_security_group():
    ec2_client = boto3.client('ec2', region_name=REGION)
    
    # Get default VPC
    vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    
    try:
        response = ec2_client.create_security_group(
            GroupName=SECURITY_GROUP_NAME,
            Description='Security group for Free Tier EC2',
            VpcId=vpc_id
        )
        sg_id = response['GroupId']
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 5000,
                    'ToPort': 5000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                }
            ]
        )
        
        print(f'Security group {SECURITY_GROUP_NAME} created with ID: {sg_id}')
        return sg_id
    except ec2_client.exceptions.ClientError as e:
        if 'InvalidGroup.Duplicate' in str(e):
            print(f'Security group {SECURITY_GROUP_NAME} already exists.')
            groups = ec2_client.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])
            return groups['SecurityGroups'][0]['GroupId']
        else:
            raise

# Launch EC2 instance
def launch_instance():
    sg_id = create_security_group()

    with open('user_data.sh', 'r') as f:
        user_data_script = f.read()

    instance = ec2.create_instances(
        ImageId=AMI_ID,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SecurityGroupIds=[sg_id],
        IamInstanceProfile={'Name': IAM_INSTANCE_PROFILE},
        MinCount=1,
        MaxCount=1,
        UserData=user_data_script,
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeSize': VOLUME_SIZE,
                    'VolumeType': 'gp3',
                    'DeleteOnTermination': True
                }
            }
        ],
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': INSTANCE_NAME}]
        }]
    )[0]

    print("Launching instance, please wait...")
    instance.wait_until_running()
    instance.reload()
    print(f'Instance launched with ID: {instance.id}')
    print(f'Public DNS: {instance.public_dns_name}')
    print(f'Public IP: {instance.public_ip_address}')

if __name__ == "__main__":
    launch_instance()
