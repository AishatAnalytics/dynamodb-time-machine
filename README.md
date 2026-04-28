# DynamoDB Time Machine ⏰

Point-in-time backup and recovery system for DynamoDB using S3.

## The Problem
A developer runs a script that accidentally deletes all records from a production DynamoDB table. No backup. No recovery plan. The data is gone forever.

## What It Does
- Creates a DynamoDB table and seeds it with data
- Backs up all items to S3 with timestamp
- Simulates a disaster by deleting all items
- Restores the table from the S3 backup
- Verifies every item was recovered
- Measures and reports RTO and RPO

## Results
Items backed up: 5
Items restored: 5
Recovery time: 0.28 seconds
RPO: Near zero
RTO: 0.28 seconds
Status: SUCCESS

## Architecture
DynamoDB Table
      ↓ backup
S3 Bucket (timestamped snapshots)
      ↓ restore on disaster
DynamoDB Table (fully recovered)

## Tech Stack
- Python 3
- AWS DynamoDB
- AWS S3
- boto3

## Key Concepts Demonstrated
- RTO and RPO at the data layer
- Point-in-time recovery
- Disaster simulation and testing
- AWS Well-Architected Reliability Pillar

## How To Run
- Clone the repo
- pip install boto3 python-dotenv
- Add your AWS credentials to .env
- Run py time_machine.py

## Part of my 30 cloud projects in 30 days series
Follow along: https://www.linkedin.com/in/aishatolatunji/