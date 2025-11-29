from twilio.rest import Client
from config import Config
import asyncio

class CommunicationAgent:
    """
    The Messenger Agent - Handles WhatsApp and SMS communications
    """
    
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.whatsapp_number = Config.TWILIO_WHATSAPP_NUMBER
    
    async def send_whatsapp_message(self, to_number, message):
        """
        Send WhatsApp message via Twilio
        
        Args:
            to_number: Recipient phone number (format: whatsapp:+919876543210)
            message: Message text
        """
        try:
            # Ensure number has whatsapp: prefix
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            message_obj = self.client.messages.create(
                from_=self.whatsapp_number,
                body=message,
                to=to_number
            )
            
            return {
                'success': True,
                'message_sid': message_obj.sid,
                'status': message_obj.status
            }
            
        except Exception as e:
            print(f"WhatsApp send error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_bulk_whatsapp(self, recipients, message):
        """
        Send WhatsApp message to multiple recipients
        
        Args:
            recipients: List of phone numbers
            message: Message text
        """
        results = []
        
        for recipient in recipients:
            result = await self.send_whatsapp_message(recipient, message)
            results.append({
                'recipient': recipient,
                'result': result
            })
            
            # Rate limiting - wait 1 second between messages
            await asyncio.sleep(1)
        
        return results
    
    async def send_liquidity_alert(self, to_number, days_remaining, current_cash):
        """
        Send formatted liquidity alert
        """
        message = f"""
🚨 *CashFlow Alert*

Your cash will run out in *{days_remaining} days*.

Current Position: ₹{current_cash:,.2f}

*Recommended Actions:*
1. Delay non-urgent payments
2. Follow up on pending receivables
3. Consider short-term funding

Reply HELP for support.
        """.strip()
        
        return await self.send_whatsapp_message(to_number, message)
    
    async def send_low_stock_alert(self, to_number, item, quantity):
        """
        Send low stock alert
        """
        message = f"""
⚠️ *Low Stock Alert*

Item: *{item}*
Current Stock: *{quantity} units*

Time to reorder! 

Reply with quantity to auto-create purchase order.
        """.strip()
        
        return await self.send_whatsapp_message(to_number, message)
    
    async def send_fraud_alert(self, to_number, transaction_details):
        """
        Send fraud detection alert
        """
        message = f"""
🔴 *FRAUD ALERT*

Suspicious transaction detected:

Amount: ₹{transaction_details.get('amount', 0)}
Type: {transaction_details.get('type', 'Unknown')}
Time: {transaction_details.get('time', 'Now')}

If this wasn't you, contact support immediately.

Reply CONFIRM if legitimate.
        """.strip()
        
        return await self.send_whatsapp_message(to_number, message)
    
    async def send_daily_summary(self, to_number, summary_data):
        """
        Send daily business summary
        """
        message = f"""
📊 *Daily Summary*

*Sales:* ₹{summary_data.get('total_sales', 0):,.2f}
*Purchases:* ₹{summary_data.get('total_purchases', 0):,.2f}
*Net Cash Flow:* ₹{summary_data.get('net_flow', 0):,.2f}

*Transactions:* {summary_data.get('transaction_count', 0)}
*Items Sold:* {summary_data.get('items_sold', 0)}

Great work! 💪
        """.strip()
        
        return await self.send_whatsapp_message(to_number, message)
    
    async def send_reorder_suggestion(self, to_number, items):
        """
        Send intelligent reorder suggestions
        """
        item_list = "\n".join([
            f"• {item['name']}: {item['suggested_qty']} units"
            for item in items[:5]  # Top 5 items
        ])
        
        message = f"""
🛒 *Smart Reorder Suggestions*

Based on your sales velocity:

{item_list}

Reply ORDER to create purchase orders.
        """.strip()
        
        return await self.send_whatsapp_message(to_number, message)
    
    async def send_welcome_message(self, to_number, user_name):
        """
        Send welcome message to new user
        """
        message = f"""
👋 Welcome to *CashFlow*, {user_name}!

Your AI-powered CFO is ready.

*How to use:*
1. Send voice or text messages
2. Example: "Sold 5kg rice for 500 rupees"
3. Get instant insights & alerts

Start by recording your first transaction!
        """.strip()
        
        return await self.send_whatsapp_message(to_number, message)
    
    async def parse_whatsapp_response(self, message_body):
        """
        Parse incoming WhatsApp message for commands
        """
        message_lower = message_body.lower().strip()
        
        commands = {
            'help': 'help_requested',
            'summary': 'daily_summary',
            'stock': 'check_inventory',
            'cash': 'check_cash_flow',
            'order': 'create_order',
            'confirm': 'confirm_transaction',
            'cancel': 'cancel_transaction'
        }
        
        for keyword, command in commands.items():
            if keyword in message_lower:
                return {'command': command, 'original': message_body}
        
        # Default: treat as transaction
        return {'command': 'transaction', 'original': message_body}