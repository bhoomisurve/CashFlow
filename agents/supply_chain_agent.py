from datetime import datetime, timedelta
from collections import defaultdict
from config import Config

class SupplyChainAgent:
    """
    Procurement Agent - Tracks inventory and optimizes supply chain
    """
    
    def __init__(self, db_service):
        self.db = db_service
        self.low_stock_threshold = Config.LOW_STOCK_THRESHOLD
    
    async def process_transaction(self, user_id, transaction, entities):
        """
        Update inventory based on transaction
        """
        response = {
            'inventory_updated': False,
            'alerts': []
        }
        
        item = entities.get('item')
        quantity = entities.get('quantity', 0)
        txn_type = entities.get('type')
        
        if not item or not quantity:
            return response
        
        # Calculate quantity change
        if txn_type == 'sale':
            qty_change = -quantity  # Reduce inventory
        elif txn_type == 'purchase':
            qty_change = quantity   # Increase inventory
        else:
            return response
        
        # Update inventory
        updated_item = await self.db.update_inventory(user_id, item, qty_change)
        response['inventory_updated'] = True
        
        # Check for low stock
        if updated_item and updated_item['quantity'] <= self.low_stock_threshold:
            alert = await self.create_low_stock_alert(user_id, item, updated_item['quantity'])
            response['alerts'].append(alert)
        
        # Check for dead stock
        dead_stock = await self.detect_dead_stock(user_id)
        if dead_stock:
            response['dead_stock_warning'] = dead_stock
        
        return response
    
    async def create_low_stock_alert(self, user_id, item, current_qty):
        """
        Alert for low stock levels
        """
        message = f"⚠️ LOW STOCK: {item} has only {current_qty} units left. Reorder soon!"
        
        await self.db.create_alert(user_id, 'low_stock', message, 'medium')
        
        return {
            'type': 'low_stock',
            'item': item,
            'quantity': current_qty,
            'message': message
        }
    
    async def detect_dead_stock(self, user_id):
        """
        Identify items with no sales in last 30 days (dead stock)
        """
        try:
            # Get all inventory
            inventory = await self.db.get_inventory(user_id)
            
            # Get transactions from last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            transactions = await self.db.get_transactions_range(user_id, start_date, end_date)
            
            # Track which items were sold
            sold_items = set()
            for txn in transactions:
                if txn['type'] == 'sale' and txn.get('item'):
                    sold_items.add(txn['item'].lower())
            
            # Find dead stock
            dead_stock = []
            for item in inventory:
                if item['quantity'] > 0 and item['item_name'].lower() not in sold_items:
                    dead_stock.append({
                        'item': item['item_name'],
                        'quantity': item['quantity'],
                        'days_idle': 30
                    })
            
            return dead_stock if dead_stock else None
            
        except Exception as e:
            print(f"Dead stock detection error: {e}")
            return None
    
    async def calculate_item_velocity(self, user_id, item, days=30):
        """
        Calculate sales velocity for an item
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            transactions = await self.db.get_transactions_range(user_id, start_date, end_date)
            
            # Sum quantities sold
            total_sold = sum(
                txn['quantity'] 
                for txn in transactions 
                if txn['type'] == 'sale' and txn.get('item', '').lower() == item.lower()
            )
            
            # Average daily velocity
            velocity = total_sold / days if days > 0 else 0
            
            return {
                'item': item,
                'total_sold': total_sold,
                'days': days,
                'daily_velocity': velocity
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def get_reorder_suggestions(self, user_id):
        """
        Generate AI-powered reorder suggestions
        """
        try:
            inventory = await self.db.get_inventory(user_id)
            suggestions = []
            
            for item in inventory:
                # Calculate velocity
                velocity = await self.calculate_item_velocity(user_id, item['item_name'])
                
                if velocity['daily_velocity'] > 0:
                    # Calculate days until stockout
                    days_until_stockout = item['quantity'] / velocity['daily_velocity']
                    
                    # Suggest reorder if less than 7 days stock
                    if days_until_stockout <= 7:
                        reorder_qty = int(velocity['daily_velocity'] * 14)  # 2 weeks worth
                        suggestions.append({
                            'item': item['item_name'],
                            'current_stock': item['quantity'],
                            'days_until_stockout': int(days_until_stockout),
                            'suggested_reorder_qty': reorder_qty,
                            'daily_velocity': round(velocity['daily_velocity'], 2),
                            'priority': 'high' if days_until_stockout <= 3 else 'medium'
                        })
            
            return suggestions
            
        except Exception as e:
            return {'error': str(e)}
    
    async def get_inventory_insights(self, user_id):
        """
        Get comprehensive inventory insights
        """
        try:
            inventory = await self.db.get_inventory(user_id)
            dead_stock = await self.detect_dead_stock(user_id)
            reorder_suggestions = await self.get_reorder_suggestions(user_id)
            
            # Calculate total inventory value (simplified)
            total_items = sum(item['quantity'] for item in inventory)
            
            return {
                'total_items': total_items,
                'unique_products': len(inventory),
                'dead_stock': dead_stock or [],
                'reorder_suggestions': reorder_suggestions,
                'low_stock_items': [
                    item for item in inventory 
                    if item['quantity'] <= self.low_stock_threshold
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}