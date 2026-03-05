import boto3

# Configuration
BUCKET_NAME = 'ecom-purchaselogs-bucket'
REGION = 'us-east-2'

def create_s3_bucket():
    s3_client = boto3.client('s3', region_name=REGION)
    
    try:
        if REGION == 'us-east-1':
            s3_client.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3_client.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
        print(f'Bucket {BUCKET_NAME} created successfully in {REGION}')
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f'Bucket {BUCKET_NAME} already exists and is owned by you')
    except s3_client.exceptions.BucketAlreadyExists:
        print(f'Bucket {BUCKET_NAME} already exists')
    except Exception as e:
        print(f'Error creating bucket: {e}')
        raise

if __name__ == '__main__':
    create_s3_bucket()
