"""
Test MongoDB Atlas connection
Run this to verify your MongoDB setup
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def test_connection():
    """Test basic MongoDB connection"""
    print("="*60)
    print("Testing MongoDB Atlas Connection")
    print("="*60)
    print()
    
    try:
        # Get connection string
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            print("ERROR: MONGODB_URI not found in .env")
            print("Please add your connection string to .env file")
            return False
        
        print(" Connecting to MongoDB Atlas...")
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("Connection successful!")
        print()
        
        # Get database
        db_name = os.getenv('MONGODB_DATABASE', 'cashflow')
        db = client[db_name]
        print(f"Using database: {db_name}")
        print()
        
        # Test write operation
        print("Testing write operation...")
        test_collection = db.test_connection
        test_doc = {
            "test": "Hello from CashFlow!",
            "timestamp": datetime.utcnow(),
            "status": "success"
        }
        result = test_collection.insert_one(test_doc)
        print(f"Document inserted with ID: {result.inserted_id}")
        print()
        
        # Test read operation
        print("Testing read operation...")
        retrieved = test_collection.find_one({"_id": result.inserted_id})
        print(f"Retrieved document: {retrieved['test']}")
        print()
        
        # Test update operation
        print("Testing update operation...")
        test_collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"status": "updated"}}
        )
        updated = test_collection.find_one({"_id": result.inserted_id})
        print(f"Updated status: {updated['status']}")
        print()
        
        # Cleanup
        print("Cleaning up test data...")
        test_collection.delete_one({"_id": result.inserted_id})
        print("Test document deleted")
        print()
        
        # Show collections
        print("Available collections:")
        collections = db.list_collection_names()
        if collections:
            for coll in collections:
                count = db[coll].count_documents({})
                print(f"  - {coll}: {count} documents")
        else:
            print("  (No collections yet - will be created automatically)")
        print()
        
        client.close()
        
        print("="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print()
        print("Your MongoDB Atlas setup is working perfectly!")
        print("You can now run: python app.py")
        print()
        
        return True
        
    except ConnectionFailure as e:
        print("Connection failed!")
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check your MONGODB_URI in .env")
        print("2. Verify your password is correct (no special chars)")
        print("3. Check IP whitelist in MongoDB Atlas")
        print("4. Ensure you have internet connection")
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Please check your MongoDB Atlas configuration")
        return False

def test_cashflow_collections():
    """Test CashFlow-specific collections"""
    print("\n" + "="*60)
    print("Testing CashFlow Collections")
    print("="*60)
    print()
    
    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        client = MongoClient(mongodb_uri)
        db_name = os.getenv('MONGODB_DATABASE', 'cashflow')
        db = client[db_name]
        
        # Test users collection
        print("Testing users collection...")
        users = db.users
        test_user = {
            "email": "test@cashflow.ai",
            "phone": "whatsapp:+919876543210",
            "name": "Test User",
            "business_name": "Test Store",
            "created_at": datetime.utcnow()
        }
        
        # Check if user exists
        existing = users.find_one({"email": "test@cashflow.ai"})
        if existing:
            print("Test user already exists")
            user_id = str(existing['_id'])
        else:
            result = users.insert_one(test_user)
            user_id = str(result.inserted_id)
            print(f" Created test user: {user_id}")
        
        # Test transactions collection
        print("\nTesting transactions collection...")
        transactions = db.transactions
        test_txn = {
            "user_id": user_id,
            "type": "sale",
            "item": "Rice",
            "quantity": 10,
            "amount": 800,
            "created_at": datetime.utcnow()
        }
        result = transactions.insert_one(test_txn)
        print(f"  Created test transaction: {result.inserted_id}")
        
        # Test inventory collection
        print("\nTesting inventory collection...")
        inventory = db.inventory
        test_inv = {
            "user_id": user_id,
            "item_name": "Rice",
            "quantity": 50,
            "last_updated": datetime.utcnow()
        }
        result = inventory.insert_one(test_inv)
        print(f"  Created test inventory: {result.inserted_id}")
        
        # Test alerts collection
        print("\n Testing alerts collection...")
        alerts = db.alerts
        test_alert = {
            "user_id": user_id,
            "type": "low_stock",
            "message": "Test alert",
            "read": False,
            "created_at": datetime.utcnow()
        }
        result = alerts.insert_one(test_alert)
        print(f"  Created test alert: {result.inserted_id}")
        
        print("\n" + "="*60)
        print(" All CashFlow collections working!")
        print("="*60)
        
        # Show summary
        print(f"\nDatabase Summary:")
        print(f"  Users: {users.count_documents({})}")
        print(f"  Transactions: {transactions.count_documents({})}")
        print(f"  Inventory: {inventory.count_documents({})}")
        print(f"  Alerts: {alerts.count_documents({})}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("\nCashFlow MongoDB Test Suite\n")
    
    # Test basic connection
    if test_connection():
        # Test CashFlow collections
        test_cashflow_collections()
        
        print("\n" + ""*30)
        print("Your MongoDB Atlas is ready for CashFlow! ")
        print(""*30 + "\n")
    else:
        print("\n Please fix the connection issues before proceeding.\n")
        print("See MONGODB_SETUP.md for detailed instructions.\n")
