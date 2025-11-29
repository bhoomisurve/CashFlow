from datetime import datetime, timedelta
import numpy as np
from config import Config

class LiquidityAgent:
    """
    The CFO Agent - Monitors cash flow and predicts liquidity crunches
    """
    
    def __init__(self, db_service):
        self.db = db_service
        self.alert_threshold_days = Config.LIQUIDITY_ALERT_THRESHOLD_DAYS
    
    async def process_transaction(self, user_id, transaction, entities):
        """
        Process a transaction and update liquidity metrics
        """
        response = {
            'cash_impact': 0,
            'alert': None
        }
        
        # Calculate cash impact
        if entities.get('type') == 'sale':
            response['cash_impact'] = entities.get('amount', 0)
        elif entities.get('type') == 'purchase':
            response['cash_impact'] = -entities.get('amount', 0)
        
        # Check for liquidity crunch
        prediction = await self.predict_liquidity_crunch(user_id)
        
        if prediction['days_until_crunch'] and prediction['days_until_crunch'] <= self.alert_threshold_days:
            alert = await self.create_liquidity_alert(user_id, prediction)
            response['alert'] = alert
        
        return response
    
    async def predict_liquidity_crunch(self, user_id):
        """
        Predict when cash will run out based on burn rate
        """
        try:
            # Get last 30 days of transactions
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            transactions = await self.db.get_transactions_range(user_id, start_date, end_date)
            
            if len(transactions) < 5:
                return {'days_until_crunch': None, 'message': 'Insufficient data'}
            
            # Calculate daily cash flow
            daily_flows = {}
            for txn in transactions:
                date = datetime.fromisoformat(txn['created_at']).date()
                amount = txn['amount']
                
                if txn['type'] == 'sale':
                    daily_flows[date] = daily_flows.get(date, 0) + amount
                elif txn['type'] == 'purchase':
                    daily_flows[date] = daily_flows.get(date, 0) - amount
            
            # Calculate average daily burn rate
            flows = list(daily_flows.values())
            avg_daily_flow = np.mean(flows)
            
            # If positive flow, no crunch predicted
            if avg_daily_flow >= 0:
                return {
                    'days_until_crunch': None,
                    'avg_daily_flow': avg_daily_flow,
                    'message': 'Healthy cash flow'
                }
            
            # Calculate current cash position
            summary = await self.db.get_cash_flow_summary(user_id, days=90)
            current_cash = summary['net_cash_flow']
            
            # Days until cash runs out
            if current_cash > 0:
                days_until_crunch = int(current_cash / abs(avg_daily_flow))
            else:
                days_until_crunch = 0
            
            return {
                'days_until_crunch': days_until_crunch,
                'current_cash': current_cash,
                'avg_daily_burn': abs(avg_daily_flow),
                'message': f'Cash will run out in {days_until_crunch} days'
            }
            
        except Exception as e:
            print(f"Liquidity prediction error: {e}")
            return {'days_until_crunch': None, 'error': str(e)}
    
    async def create_liquidity_alert(self, user_id, prediction):
        """
        Create an alert for liquidity issues
        """
        days = prediction['days_until_crunch']
        
        if days == 0:
            message = "🚨 CRITICAL: You're out of cash! Consider emergency funding."
            severity = 'critical'
        elif days <= 3:
            message = f"⚠️ URGENT: Cash will run out in {days} days. Take action now!"
            severity = 'high'
        else:
            message = f"💡 ALERT: Cash will run out in {days} days. Plan ahead."
            severity = 'medium'
        
        await self.db.create_alert(user_id, 'liquidity_crunch', message, severity)
        
        return {
            'type': 'liquidity_crunch',
            'message': message,
            'severity': severity,
            'days_remaining': days
        }
    
    async def get_cashflow_analysis(self, user_id, days=30):
        """
        Get detailed cash flow analysis
        """
        try:
            summary = await self.db.get_cash_flow_summary(user_id, days)
            prediction = await self.predict_liquidity_crunch(user_id)
            
            # Get daily breakdown
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            transactions = await self.db.get_transactions_range(user_id, start_date, end_date)
            
            daily_data = {}
            for txn in transactions:
                date = datetime.fromisoformat(txn['created_at']).date().isoformat()
                if date not in daily_data:
                    daily_data[date] = {'inflow': 0, 'outflow': 0}
                
                if txn['type'] == 'sale':
                    daily_data[date]['inflow'] += txn['amount']
                elif txn['type'] == 'purchase':
                    daily_data[date]['outflow'] += txn['amount']
            
            return {
                'summary': summary,
                'prediction': prediction,
                'daily_breakdown': daily_data
            }
            
        except Exception as e:
            return {'error': str(e)}