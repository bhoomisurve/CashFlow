from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import asyncio
from functools import wraps

from services.voice_service import VoiceService
from services.nlp_service import NLPService
from services.mongodb_service import MongoDBService
from agents.liquidity_agent import LiquidityAgent
from agents.supply_chain_agent import SupplyChainAgent
from agents.risk_agent import RiskAgent
from agents.communication_agent import CommunicationAgent

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize services
voice_service = VoiceService()
nlp_service = NLPService()
db_service = MongoDBService()

# Initialize agents
liquidity_agent = LiquidityAgent(db_service)
supply_chain_agent = SupplyChainAgent(db_service)
risk_agent = RiskAgent(db_service)
communication_agent = CommunicationAgent()

def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'CashFlow API is running'}), 200

@app.route('/api/voice-transaction', methods=['POST'])
@async_route
async def process_voice_transaction():
    """
    Main endpoint for voice-based transaction input
    """
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        user_id = request.form.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Step 1: Speech to Text
        transcription = await voice_service.transcribe_audio(audio_file)
        
        # Step 2: NLP Entity Extraction
        entities = nlp_service.extract_entities(transcription)
        
        # Step 3: Store transaction
        transaction = await db_service.create_transaction(user_id, entities, transcription)
        
        # Step 4: Route to appropriate agents
        agent_responses = await route_to_agents(user_id, transaction, entities)
        
        return jsonify({
            'success': True,
            'transcription': transcription,
            'entities': entities,
            'transaction_id': transaction['id'],
            'agent_actions': agent_responses
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manual-transaction', methods=['POST'])
@async_route
async def create_manual_transaction():
    """
    Manual text-based transaction input
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        text = data.get('text')
        
        if not user_id or not text:
            return jsonify({'error': 'user_id and text are required'}), 400
        
        # Process text directly
        entities = nlp_service.extract_entities(text)
        transaction = await db_service.create_transaction(user_id, entities, text)
        
        # Route to agents
        agent_responses = await route_to_agents(user_id, transaction, entities)
        
        return jsonify({
            'success': True,
            'entities': entities,
            'transaction_id': transaction['id'],
            'agent_actions': agent_responses
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/<user_id>', methods=['GET'])
@async_route
async def get_dashboard_data(user_id):
    """
    Get comprehensive dashboard data
    """
    try:
        # Fetch all relevant data
        transactions = await db_service.get_transactions(user_id, limit=50)
        inventory = await db_service.get_inventory(user_id)
        cash_flow = await db_service.get_cash_flow_summary(user_id)
        alerts = await db_service.get_alerts(user_id, unread_only=True)
        
        return jsonify({
            'transactions': transactions,
            'inventory': inventory,
            'cash_flow': cash_flow,
            'alerts': alerts
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/whatsapp-webhook', methods=['POST'])
@async_route
async def whatsapp_webhook():
    """
    Webhook for incoming WhatsApp messages (Twilio)
    """
    try:
        from_number = request.values.get('From', '')
        message_body = request.values.get('Body', '')
        
        # Extract user from phone number
        user = await db_service.get_user_by_phone(from_number)
        
        if not user:
            await communication_agent.send_whatsapp_message(
                from_number,
                "Welcome to CashFlow! Please register first at our portal."
            )
            return '', 200
        
        # Process the message as a transaction
        entities = nlp_service.extract_entities(message_body)
        transaction = await db_service.create_transaction(user['id'], entities, message_body)
        
        # Route to agents
        agent_responses = await route_to_agents(user['id'], transaction, entities)
        
        # Send confirmation
        confirmation = f"✅ Transaction recorded!\n\n"
        if entities.get('type') == 'sale':
            confirmation += f"Sale: {entities.get('quantity', 0)} {entities.get('item', 'items')} for ₹{entities.get('amount', 0)}"
        elif entities.get('type') == 'purchase':
            confirmation += f"Purchase: {entities.get('quantity', 0)} {entities.get('item', 'items')} for ₹{entities.get('amount', 0)}"
        
        await communication_agent.send_whatsapp_message(from_number, confirmation)
        
        return '', 200
        
    except Exception as e:
        print(f"WhatsApp webhook error: {str(e)}")
        return '', 500

async def route_to_agents(user_id, transaction, entities):
    """
    Route transaction to all relevant agents
    """
    responses = {}
    
    # 1. Supply Chain Agent - Update inventory
    if entities.get('item'):
        supply_response = await supply_chain_agent.process_transaction(user_id, transaction, entities)
        responses['supply_chain'] = supply_response
    
    # 2. Liquidity Agent - Update cash flow and check predictions
    liquidity_response = await liquidity_agent.process_transaction(user_id, transaction, entities)
    responses['liquidity'] = liquidity_response
    
    # 3. Risk Agent - Check for anomalies
    risk_response = await risk_agent.analyze_transaction(user_id, transaction, entities)
    responses['risk'] = risk_response
    
    # 4. Communication Agent - Send alerts if needed
    if liquidity_response.get('alert'):
        user = await db_service.get_user(user_id)
        if user.get('phone'):
            await communication_agent.send_whatsapp_message(
                user['phone'],
                liquidity_response['alert']['message']
            )
    
    if risk_response.get('anomaly_detected'):
        user = await db_service.get_user(user_id)
        if user.get('phone'):
            await communication_agent.send_whatsapp_message(
                user['phone'],
                f"⚠️ ALERT: {risk_response['message']}"
            )
    
    return responses

@app.route('/api/inventory/<user_id>', methods=['GET'])
@async_route
async def get_inventory(user_id):
    """Get current inventory status"""
    try:
        inventory = await db_service.get_inventory(user_id)
        return jsonify(inventory), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cashflow/<user_id>', methods=['GET'])
@async_route
async def get_cashflow(user_id):
    """Get cash flow analysis"""
    try:
        days = request.args.get('days', 30, type=int)
        analysis = await liquidity_agent.get_cashflow_analysis(user_id, days)
        return jsonify(analysis), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions/<user_id>', methods=['GET'])
@async_route
async def get_predictions(user_id):
    """Get AI predictions for cash flow and inventory"""
    try:
        predictions = {
            'liquidity': await liquidity_agent.predict_liquidity_crunch(user_id),
            'inventory': await supply_chain_agent.get_reorder_suggestions(user_id)
        }
        return jsonify(predictions), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)