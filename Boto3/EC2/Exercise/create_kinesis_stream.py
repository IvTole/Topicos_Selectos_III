import boto3

# Configuration
REGION = 'us-east-2'
STREAM_NAME = 'Clientorders'
SHARD_COUNT = 1

def create_kinesis_stream():
    kinesis_client = boto3.client('kinesis', region_name=REGION)
    
    try:
        response = kinesis_client.create_stream(
            StreamName=STREAM_NAME,
            ShardCount=SHARD_COUNT
        )
        print(f'Kinesis Stream {STREAM_NAME} created successfully')
        print('Waiting for stream to become active...')
        
        waiter = kinesis_client.get_waiter('stream_exists')
        waiter.wait(StreamName=STREAM_NAME)
        
        stream_info = kinesis_client.describe_stream(StreamName=STREAM_NAME)
        print(f'Stream ARN: {stream_info["StreamDescription"]["StreamARN"]}')
        print(f'Stream Status: {stream_info["StreamDescription"]["StreamStatus"]}')
        
    except kinesis_client.exceptions.ResourceInUseException:
        print(f'Stream {STREAM_NAME} already exists')
        stream_info = kinesis_client.describe_stream(StreamName=STREAM_NAME)
        print(f'Stream ARN: {stream_info["StreamDescription"]["StreamARN"]}')
        print(f'Stream Status: {stream_info["StreamDescription"]["StreamStatus"]}')
    except Exception as e:
        print(f'Error creating stream: {e}')

if __name__ == '__main__':
    create_kinesis_stream()
