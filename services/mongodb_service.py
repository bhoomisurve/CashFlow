from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from datetime import datetime, timedelta
from config import Config
import asyncio
from bson.objectid import ObjectId

class MongoDBService:
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = MongoClient(
            Config.MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        self.db = self.client[Config.MONGODB_DATABASE]
        
        # Collections
        self.users = self.db.users
        self.transactions = self.db.transactions
        self.inventory = self.db.inventory
        self.alerts = self.db.alerts
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Users indexes
            self.users.create_index([("email", 1)], unique=True, sparse=True)
            self.users.create_index([("phone", 1)], unique=True, sparse=True)
            
            # Transactions indexes
            self.transactions.create_index([("user_id", 1), ("created_at", -1)])
            self.transactions.create_index([("type", 1)])
            
            # Inventory indexes
            self.inventory.create_index([("user_id", 1), ("item_name", 1)], unique=True)
            
            # Alerts indexes
            self.alerts.create_index([("user_id", 1), ("read", 1)])
            self.alerts.create_index([("created_at", -1)])
            
        except Exception as e:
            print(f"Index creation error: {e}")
    
    async def create_transaction(self, user_id, entities, raw_text):
        """Create a new transaction record"""
        transaction_data = {
            'user_id': user_id,
            'type': entities.get('type', 'unknown'),
            'item': entities.get('item'),
            'quantity': entities.get('quantity', 0),
            'amount': entities.get('amount', 0),
            'unit': entities.get('unit'),
            'raw_text': raw_text,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = self.transactions.insert_one(transaction_data)
        transaction_data['_id'] = str(result.inserted_id)
        transaction_data['id'] = str(result.inserted_id)
        
        return transaction_data
    
    async def get_transactions(self, user_id, limit=50, offset=0):
        """Get user transactions"""
        transactions = list(
            self.transactions.find({'user_id': user_id})
            .sort('created_at', -1)
            .skip(offset)
            .limit(limit)
        )
        
        # Convert ObjectId to string
        for txn in transactions:
            txn['id'] = str(txn['_id'])
            txn['created_at'] = txn['created_at'].isoformat()
        
        return transactions
    
    async def get_transactions_range(self, user_id, start_date, end_date):
        """Get transactions within date range"""
        transactions = list(
            self.transactions.find({
                'user_id': user_id,
                'created_at': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }).sort('created_at', -1)
        )
        
        for txn in transactions:
            txn['id'] = str(txn['_id'])
        
        return transactions
    
    async def update_inventory(self, user_id, item, quantity_change):
        """Update inventory levels"""
        # Try to update existing item
        result = self.inventory.update_one(
            {'user_id': user_id, 'item_name': item},
            {
                '$inc': {'quantity': quantity_change},
                '$set': {'last_updated': datetime.utcnow()}
            }
        )
        
        # If not found, create new
        if result.matched_count == 0:
            inventory_data = {
                'user_id': user_id,
                'item_name': item,
                'quantity': max(0, quantity_change),
                'last_updated': datetime.utcnow()
            }
            result = self.inventory.insert_one(inventory_data)
            inventory_data['id'] = str(result.inserted_id)
            return inventory_data
        
        # Return updated item
        updated = self.inventory.find_one({'user_id': user_id, 'item_name': item})
        updated['id'] = str(updated['_id'])
        return updated
    
    async def get_inventory(self, user_id):
        """Get all inventory items"""
        inventory = list(self.inventory.find({'user_id': user_id}))
        
        for item in inventory:
            item['id'] = str(item['_id'])
        
        return inventory
    
    async def get_cash_flow_summary(self, user_id, days=30):
        """Calculate cash flow summary"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        transactions = await self.get_transactions_range(user_id, start_date, end_date)
        
        total_inflow = sum(t['amount'] for t in transactions if t['type'] == 'sale')
        total_outflow = sum(t['amount'] for t in transactions if t['type'] == 'purchase')
        
        return {
            'period_days': days,
            'total_inflow': total_inflow,
            'total_outflow': total_outflow,
            'net_cash_flow': total_inflow - total_outflow,
            'transaction_count': len(transactions)
        }
    
    async def create_alert(self, user_id, alert_type, message, severity='medium'):
        """Create an alert for the user"""
        alert_data = {
            'user_id': user_id,
            'type': alert_type,
            'message': message,
            'severity': severity,
            'read': False,
            'created_at': datetime.utcnow()
        }
        
        result = self.alerts.insert_one(alert_data)
        alert_data['id'] = str(result.inserted_id)
        
        return alert_data
    
    async def get_alerts(self, user_id, unread_only=False):
        """Get user alerts"""
        query = {'user_id': user_id}
        
        if unread_only:
            query['read'] = False
        
        alerts = list(
            self.alerts.find(query)
            .sort('created_at', -1)
            .limit(20)
        )
        
        for alert in alerts:
            alert['id'] = str(alert['_id'])
            alert['created_at'] = alert['created_at'].isoformat()
        
        return alerts
    
    async def get_user(self, user_id):
        """Get user details"""
        user = self.users.find_one({'_id': ObjectId(user_id)})
        
        if user:
            user['id'] = str(user['_id'])
        
        return user
    
    async def get_user_by_phone(self, phone_number):
        """Get user by phone number"""
        user = self.users.find_one({'phone': phone_number})
        
        if user:
            user['id'] = str(user['_id'])
        
        return user
    
    async def create_user(self, email, phone, name, business_name=None, business_type=None):
        """Create a new user"""
        user_data = {
            'email': email,
            'phone': phone,
            'name': name,
            'business_name': business_name,
            'business_type': business_type,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = self.users.insert_one(user_data)
        user_data['id'] = str(result.inserted_id)
        
        return user_data
    
    async def update_user_settings(self, user_id, settings):
        """Update user settings"""
        settings['updated_at'] = datetime.utcnow()
        
        result = self.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': settings}
        )
        
        if result.modified_count > 0:
            return await self.get_user(user_id)
        
        return None
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()