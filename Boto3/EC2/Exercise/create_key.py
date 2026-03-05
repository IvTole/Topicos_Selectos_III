import boto3
from pprint import pprint

def create_key_pair(key_name, key_type, region='us-east-2', store=False):
    ec2_client = boto3.client('ec2', region_name=region)

    try:
        resp = ec2_client.create_key_pair(
            KeyName = key_name,
            KeyType= key_type
        )
    except ec2_client.exceptions.ClientError as e:
        if 'InvalidKeyPair.Duplicate' in str(e):
            print(f'Key pair {key_name} already exists. Deleting and recreating...')
            ec2_client.delete_key_pair(KeyName=key_name)
            resp = ec2_client.create_key_pair(
                KeyName = key_name,
                KeyType= key_type
            )
        else:
            raise

    #pprint(resp['KeyMaterial'])

    #store the pem file
    if store:
        file = open(key_name+'.pem', 'w')
        file.write(resp['KeyMaterial'])
        file.close()

if __name__ == '__main__':
    key_name = 'ecom_key'
    key_type = 'rsa'
    region = 'us-east-2'

    create_key_pair(key_name=key_name, key_type=key_type, region=region, store=True)