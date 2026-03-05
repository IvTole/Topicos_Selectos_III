import boto3
from pprint import pprint

def list_key_pairs():
    ec2_client = boto3.client('ec2')
    
    resp = ec2_client.describe_key_pairs()
    
    pprint(resp['KeyPairs'])

if __name__ == '__main__':
    list_key_pairs()
