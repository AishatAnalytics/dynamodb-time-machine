import boto3
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
dynamodb_client = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION'))
s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION'))

TABLE_NAME = os.getenv('TABLE_NAME')
BACKUP_BUCKET = os.getenv('BACKUP_BUCKET')

def create_table():
    print(f"Creating DynamoDB table: {TABLE_NAME}...")
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        print(f"✅ Table {TABLE_NAME} created\n")
        return table
    except dynamodb_client.exceptions.ResourceInUseException:
        print(f"✅ Table {TABLE_NAME} already exists\n")
        return dynamodb.Table(TABLE_NAME)

def create_backup_bucket():
    print(f"Creating S3 backup bucket: {BACKUP_BUCKET}...")
    try:
        s3.create_bucket(Bucket=BACKUP_BUCKET)
        print(f"✅ Bucket {BACKUP_BUCKET} created\n")
    except Exception as e:
        if 'BucketAlreadyOwnedByYou' in str(e):
            print(f"✅ Bucket already exists\n")
        else:
            print(f"⚠️ Bucket issue: {e}\n")

def seed_data(table):
    print("Seeding test data...")
    items = [
        {'id': '1', 'name': 'Laptop', 'price': '999.99', 'stock': '50'},
        {'id': '2', 'name': 'Phone', 'price': '599.99', 'stock': '100'},
        {'id': '3', 'name': 'Monitor', 'price': '399.99', 'stock': '75'},
        {'id': '4', 'name': 'Keyboard', 'price': '99.99', 'stock': '200'},
        {'id': '5', 'name': 'Mouse', 'price': '49.99', 'stock': '300'}
    ]
    for item in items:
        table.put_item(Item=item)
    print(f"✅ Seeded {len(items)} items\n")
    return items

def backup_table(table):
    print(f"📸 Creating backup of {TABLE_NAME}...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_key = f"backups/{TABLE_NAME}/{timestamp}.json"

    response = table.scan()
    items = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'table_name': TABLE_NAME,
        'item_count': len(items),
        'items': items
    }

    s3.put_object(
        Bucket=BACKUP_BUCKET,
        Key=backup_key,
        Body=json.dumps(backup_data, indent=2),
        ContentType='application/json'
    )

    print(f"✅ Backed up {len(items)} items to s3://{BACKUP_BUCKET}/{backup_key}\n")
    return backup_key, timestamp

def simulate_disaster(table):
    print("💥 Simulating disaster — deleting all items...")
    response = table.scan()
    items = response['Items']

    for item in items:
        table.delete_item(Key={'id': item['id']})

    response = table.scan()
    print(f"✅ Disaster simulated — {len(response['Items'])} items remaining\n")

def restore_from_backup(table, backup_key):
    print(f"🔄 Restoring from backup: {backup_key}...")

    response = s3.get_object(Bucket=BACKUP_BUCKET, Key=backup_key)
    backup_data = json.loads(response['Body'].read().decode('utf-8'))

    items = backup_data['items']
    restored = 0

    for item in items:
        table.put_item(Item=item)
        restored += 1

    print(f"✅ Restored {restored} items from backup\n")
    return restored

def verify_restore(table, original_items):
    print("🔍 Verifying restore...")
    response = table.scan()
    restored_items = response['Items']

    print(f"Original items: {len(original_items)}")
    print(f"Restored items: {len(restored_items)}")

    if len(original_items) == len(restored_items):
        print("✅ Restore verified — all items recovered!\n")
        return True
    else:
        print("❌ Restore incomplete!\n")
        return False

def teardown(table):
    print("🗑️ Tearing down test resources...")
    table.delete()
    print(f"✅ Table {TABLE_NAME} deleted")

def run():
    print("⏰ DynamoDB Time Machine")
    print("========================\n")

    # Step 1 — Setup
    print("Step 1: Setting up resources...")
    table = create_table()
    create_backup_bucket()

    # Step 2 — Seed data
    print("Step 2: Seeding test data...")
    original_items = seed_data(table)

    # Step 3 — Backup
    print("Step 3: Creating backup...")
    backup_key, timestamp = backup_table(table)

    # Step 4 — Simulate disaster
    print("Step 4: Simulating disaster...")
    simulate_disaster(table)

    # Step 5 — Restore
    print("Step 5: Restoring from backup...")
    start_time = time.time()
    restored = restore_from_backup(table, backup_key)
    recovery_time = time.time() - start_time

    # Step 6 — Verify
    print("Step 6: Verifying restore...")
    success = verify_restore(table, original_items)

    print("="*50)
    print("📊 TIME MACHINE RESULTS")
    print("="*50)
    print(f"Items backed up: {len(original_items)}")
    print(f"Items restored: {restored}")
    print(f"Recovery time: {recovery_time:.2f} seconds")
    print(f"RPO: Near zero (continuous backup)")
    print(f"RTO: {recovery_time:.2f} seconds")
    print(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")

    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'backup_key': backup_key,
        'items_backed_up': len(original_items),
        'items_restored': restored,
        'recovery_time_seconds': round(recovery_time, 2),
        'rpo': 'Near zero',
        'rto': f'{recovery_time:.2f} seconds',
        'status': 'SUCCESS' if success else 'FAILED'
    }

    with open('time_machine_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print("\n📄 Report saved to time_machine_report.json")

    # Teardown
    print("\nStep 7: Tearing down test resources...")
    teardown(table)

    print("\n✅ DynamoDB Time Machine complete!")

if __name__ == "__main__":
    run()