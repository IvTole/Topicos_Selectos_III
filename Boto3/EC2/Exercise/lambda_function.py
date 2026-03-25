import base64
import json
import boto3
import decimal
import uuid

def lambda_handler(event, context):
    item = None
    dynamo_db = boto3.resource('dynamodb')
    table = dynamo_db.Table('ClientOrders')
    decoded_record_data = [base64.b64decode(record['kinesis']['data']) for record in event['Records']]
#decode the incoming stream that is fed up into lambda
    deserialized_data = [json.loads(decoded_record) for decoded_record in decoded_record_data]

    with table.batch_writer() as batch_writer:
        for item in deserialized_data:
            # We've added a try / except block here to deal with invalid input rows more gracefully.
            # Be aware there are stretches of the input data that have no customer ID's at all,
            # keep trying the LogGenerator script to get past that if you run into it.
            try:
                invoice = item['InvoiceNo']
                customer = int(item['Customer'])
                orderDate = item['InvoiceDate']
                quantity = item['Quantity']
                description = item['Description']
                unitPrice = item['UnitPrice']
                country = item['Country'].rstrip()
                stockCode = item['StockCode']
        
                # Construct a unique sort key for this line item
                # We've added a uuid at the end as there is some duplicate invoice/stockcode
                # data in our sample data.
                orderID = invoice + "-" + stockCode + "-" + uuid.uuid4().hex

                batch_writer.put_item(Item = {
                        'CustomerID': decimal.Decimal(customer),
                        'OrderID': orderID,
                        'OrderDate': orderDate,
                        'Quantity': decimal.Decimal(quantity),
                        'UnitPrice': decimal.Decimal(unitPrice),
                        'Description': description,
                        'Country': country
                    }
                )
                print("Wrote item into batch.")
            except:
                print("Error processing invalid input row.")

# def lambda_handler(event, context):
#     dynamo_db = boto3.resource('dynamodb')
#     table = dynamo_db.Table('ClientOrders')
    
#     decoded_records = [base64.b64decode(record['kinesis']['data']) for record in event['Records']]
#     deserialized_data = [json.loads(record) for record in decoded_records]
    
#     success_count = 0
#     error_count = 0
    
#     with table.batch_writer() as batch_writer:
#         for item in deserialized_data:
#             try:
#                 # Validar campos requeridos
#                 if not item.get('Customer') or not item.get('InvoiceNo'):
#                     raise ValueError("Missing required fields")
                
#                 customer = int(float(item['Customer']))
#                 invoice = item['InvoiceNo']
#                 orderDate = item['InvoiceDate']
#                 quantity = int(float(item['Quantity']))
#                 unitPrice = float(item['UnitPrice'])
#                 description = item['Description']
#                 country = item['Country'].rstrip()
#                 stockCode = item['StockCode']
                
#                 orderID = f"{invoice}-{stockCode}-{uuid.uuid4().hex}"
                
#                 batch_writer.put_item(Item={
#                     'CustomerID': decimal.Decimal(customer),
#                     'OrderID': orderID,
#                     'OrderDate': orderDate,
#                     'Quantity': decimal.Decimal(quantity),
#                     'UnitPrice': decimal.Decimal(unitPrice),
#                     'Description': description,
#                     'Country': country
#                 })
#                 success_count += 1
                
#             except (KeyError, ValueError, TypeError) as e:
#                 error_count += 1
#                 print(f"Error processing row: {e}")
#                 print(f"Problematic item: {item}")
    
#     return {
#         'statusCode': 200,
#         'body': json.dumps({
#             'processed': success_count,
#             'errors': error_count,
#             'total': len(deserialized_data)
#         })
#     }
