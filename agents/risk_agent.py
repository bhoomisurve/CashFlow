from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import IsolationForest
from config import Config

class RiskAgent:
    """
    The Auditor Agent - Detects fraud and transaction anomalies
    """
    
    def __init__(self, db_service):
        self.db = db_service
        self.anomaly_threshold = Config.ANOMALY_THRESHOLD
    
    async def analyze_transaction(self, user_id, transaction, entities):
        """
        Analyze transaction for anomalies and fraud
        """
        response = {
            'anomaly_detected': False,
            'risk_score': 0,
            'alerts': []
        }
        
        # Get historical data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=60)
        historical = await self.db.get_transactions_range(user_id, start_date, end_date)
        
        if len(historical) < 10:
            return response  # Not enough data for analysis
        
        # Run multiple fraud checks
        checks = [
            await self.check_amount_anomaly(transaction, historical),
            await self.check_quantity_anomaly(transaction, historical),
            await self.check_unusual_timing(transaction, historical),
            await self.check_price_deviation(transaction, historical, entities)
        ]
        
        # Aggregate risk
        anomaly_count = sum(1 for check in checks if check['is_anomaly'])
        response['risk_score'] = anomaly_count / len(checks)
        
        if response['risk_score'] > 0.5:
            response['anomaly_detected'] = True
            response['message'] = self.generate_risk_message(checks)
            
            # Create alert
            await self.db.create_alert(
                user_id,
                'fraud_risk',
                response['message'],
                'high'
            )
        
        response['details'] = checks
        return response
    
    async def check_amount_anomaly(self, transaction, historical):
        """
        Check if transaction amount is anomalous using Isolation Forest
        """
        try:
            amounts = [txn['amount'] for txn in historical if txn['amount'] > 0]
            
            if len(amounts) < 10:
                return {'check': 'amount', 'is_anomaly': False}
            
            # Reshape for sklearn
            X = np.array(amounts).reshape(-1, 1)
            
            # Train Isolation Forest
            clf = IsolationForest(contamination=self.anomaly_threshold, random_state=42)
            clf.fit(X)
            
            # Check current transaction
            current_amount = transaction['amount']
            prediction = clf.predict([[current_amount]])
            
            is_anomaly = prediction[0] == -1
            
            return {
                'check': 'amount',
                'is_anomaly': is_anomaly,
                'value': current_amount,
                'mean': np.mean(amounts),
                'std': np.std(amounts)
            }
            
        except Exception as e:
            print(f"Amount anomaly check error: {e}")
            return {'check': 'amount', 'is_anomaly': False, 'error': str(e)}
    
    async def check_quantity_anomaly(self, transaction, historical):
        """
        Check for unusual quantities
        """
        try:
            quantities = [txn['quantity'] for txn in historical if txn.get('quantity', 0) > 0]
            
            if len(quantities) < 10:
                return {'check': 'quantity', 'is_anomaly': False}
            
            mean_qty = np.mean(quantities)
            std_qty = np.std(quantities)
            current_qty = transaction.get('quantity', 0)
            
            # Flag if more than 3 standard deviations away
            z_score = abs((current_qty - mean_qty) / std_qty) if std_qty > 0 else 0
            is_anomaly = z_score > 3
            
            return {
                'check': 'quantity',
                'is_anomaly': is_anomaly,
                'value': current_qty,
                'z_score': z_score
            }
            
        except Exception as e:
            return {'check': 'quantity', 'is_anomaly': False, 'error': str(e)}
    
    async def check_unusual_timing(self, transaction, historical):
        """
        Check if transaction timing is unusual
        """
        try:
            # Get transaction hour
            txn_time = datetime.fromisoformat(transaction['created_at'])
            txn_hour = txn_time.hour
            
            # Get historical hours
            historical_hours = [
                datetime.fromisoformat(txn['created_at']).hour 
                for txn in historical
            ]
            
            # Check if hour is unusual (outside typical business hours)
            # Flag if transaction is between 11 PM and 5 AM
            is_unusual = txn_hour >= 23 or txn_hour <= 5
            
            # Also check if this hour has never been used before
            never_used = txn_hour not in historical_hours
            
            return {
                'check': 'timing',
                'is_anomaly': is_unusual and never_used,
                'hour': txn_hour,
                'typical_hours': list(set(historical_hours))
            }
            
        except Exception as e:
            return {'check': 'timing', 'is_anomaly': False, 'error': str(e)}
    
    async def check_price_deviation(self, transaction, historical, entities):
        """
        Check if price per unit deviates significantly from historical
        """
        try:
            item = entities.get('item')
            if not item:
                return {'check': 'price', 'is_anomaly': False}
            
            # Get historical prices for same item
            historical_prices = []
            for txn in historical:
                if txn.get('item', '').lower() == item.lower():
                    qty = txn.get('quantity', 0)
                    amt = txn.get('amount', 0)
                    if qty > 0:
                        historical_prices.append(amt / qty)
            
            if len(historical_prices) < 3:
                return {'check': 'price', 'is_anomaly': False}
            
            # Calculate current price per unit
            current_qty = entities.get('quantity', 0)
            current_amt = transaction.get('amount', 0)
            
            if current_qty == 0:
                return {'check': 'price', 'is_anomaly': False}
            
            current_price = current_amt / current_qty
            
            # Check deviation
            mean_price = np.mean(historical_prices)
            std_price = np.std(historical_prices)
            
            deviation = abs((current_price - mean_price) / mean_price) if mean_price > 0 else 0
            
            # Flag if deviation > 50%
            is_anomaly = deviation > 0.5
            
            return {
                'check': 'price',
                'is_anomaly': is_anomaly,
                'current_price': current_price,
                'mean_price': mean_price,
                'deviation_pct': deviation * 100
            }
            
        except Exception as e:
            return {'check': 'price', 'is_anomaly': False, 'error': str(e)}
    
    def generate_risk_message(self, checks):
        """
        Generate human-readable risk message
        """
        anomalies = [check for check in checks if check.get('is_anomaly')]
        
        if not anomalies:
            return "Transaction appears normal"
        
        messages = []
        for check in anomalies:
            if check['check'] == 'amount':
                messages.append(f"Unusual amount: ₹{check['value']:.2f}")
            elif check['check'] == 'quantity':
                messages.append(f"Unusual quantity: {check['value']}")
            elif check['check'] == 'timing':
                messages.append(f"Unusual timing: {check['hour']}:00")
            elif check['check'] == 'price':
                messages.append(f"Price deviation: {check['deviation_pct']:.1f}%")
        
        return "Suspicious transaction detected: " + ", ".join(messages)