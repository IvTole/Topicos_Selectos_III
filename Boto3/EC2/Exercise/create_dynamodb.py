import boto3

# Configuration
REGION = 'us-east-2'
TABLE_NAME = 'ClientOrders'

def create_dynamodb_table():
    dynamodb = boto3.client('dynamodb', region_name=REGION)
    
    try:
        response = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'CustomerID', 'KeyType': 'HASH'},
                {'AttributeName': 'OrderID', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'CustomerID', 'AttributeType': 'N'},
                {'AttributeName': 'OrderID', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f'Creating table {TABLE_NAME}...')
        
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        
        table_info = dynamodb.describe_table(TableName=TABLE_NAME)
        print(f'Table {TABLE_NAME} created successfully')
        print(f'Table ARN: {table_info["Table"]["TableArn"]}')
        print(f'Table Status: {table_info["Table"]["TableStatus"]}')
        
    except dynamodb.exceptions.ResourceInUseException:
        print(f'Table {TABLE_NAME} already exists')
        table_info = dynamodb.describe_table(TableName=TABLE_NAME)
        print(f'Table ARN: {table_info["Table"]["TableArn"]}')
        print(f'Table Status: {table_info["Table"]["TableStatus"]}')
    except Exception as e:
        print(f'Error creating table: {e}')

if __name__ == '__main__':
    create_dynamodb_table()
