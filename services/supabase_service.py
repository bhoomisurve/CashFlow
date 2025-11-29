from supabase import create_client, Client
from datetime import datetime, timedelta
from config import Config
import asyncio

class SupabaseService:
    def __init__(self):
        self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    async def create_transaction(self, user_id, entities, raw_text):
        """Create a new transaction record"""
        transaction_data = {
            'user_id': user_id,
            'type': entities.get('type', 'unknown'),
            'item': entities.get('item'),
            'quantity': entities.get('quantity', 0),
            'amount': entities.get('amount', 0),
            'raw_text': raw_text,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = self.supabase.table('transactions').insert(transaction_data).execute()
        return result.data[0] if result.data else None
    
    async def get_transactions(self, user_id, limit=50, offset=0):
        """Get user transactions"""
        result = self.supabase.table('transactions')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .offset(offset)\
            .execute()
        
        return result.data
    
    async def get_transactions_range(self, user_id, start_date, end_date):
        """Get transactions within date range"""
        result = self.supabase.table('transactions')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('created_at', start_date.isoformat())\
            .lte('created_at', end_date.isoformat())\
            .order('created_at', desc=True)\
            .execute()
        
        return result.data
    
    async def update_inventory(self, user_id, item, quantity_change):
        """Update inventory levels"""
        # Check if item exists
        existing = self.supabase.table('inventory')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('item_name', item)\
            .execute()
        
        if existing.data:
            # Update existing
            current_qty = existing.data[0]['quantity']
            new_qty = current_qty + quantity_change
            
            result = self.supabase.table('inventory')\
                .update({
                    'quantity': new_qty,
                    'last_updated': datetime.utcnow().isoformat()
                })\
                .eq('id', existing.data[0]['id'])\
                .execute()
        else:
            # Create new
            result = self.supabase.table('inventory')\
                .insert({
                    'user_id': user_id,
                    'item_name': item,
                    'quantity': max(0, quantity_change),
                    'last_updated': datetime.utcnow().isoformat()
                })\
                .execute()
        
        return result.data[0] if result.data else None
    
    async def get_inventory(self, user_id):
        """Get all inventory items"""
        result = self.supabase.table('inventory')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        return result.data
    
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
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = self.supabase.table('alerts').insert(alert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_alerts(self, user_id, unread_only=False):
        """Get user alerts"""
        query = self.supabase.table('alerts')\
            .select('*')\
            .eq('user_id', user_id)
        
        if unread_only:
            query = query.eq('read', False)
        
        result = query.order('created_at', desc=True).limit(20).execute()
        return result.data
    
    async def get_user(self, user_id):
        """Get user details"""
        result = self.supabase.table('users')\
            .select('*')\
            .eq('id', user_id)\
            .execute()
        
        return result.data[0] if result.data else None
    
    async def get_user_by_phone(self, phone_number):
        """Get user by phone number"""
        result = self.supabase.table('users')\
            .select('*')\
            .eq('phone', phone_number)\
            .execute()
        
        return result.data[0] if result.data else None
    
    async def update_user_settings(self, user_id, settings):
        """Update user settings"""
        result = self.supabase.table('users')\
            .update(settings)\
            .eq('id', user_id)\
            .execute()
        
        return result.data[0] if result.data else None