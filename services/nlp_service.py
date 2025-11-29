import re
import openai
from config import Config

openai.api_key = Config.OPENAI_API_KEY

class NLPService:
    def __init__(self):
        self.transaction_keywords = {
            'sale': ['sold', 'sale', 'becha', 'bechne', 'customer', 'revenue'],
            'purchase': ['bought', 'purchase', 'kharida', 'kharidne', 'supplier', 'paid']
        }
    
    def extract_entities(self, text):
        """
        Extract transaction entities from text using GPT + Regex
        
        Returns:
            dict: {
                'type': 'sale' | 'purchase',
                'item': str,
                'quantity': float,
                'amount': float
            }
        """
        # Use GPT for intelligent extraction
        entities = self._gpt_extract(text)
        
        # Fallback to regex if GPT fails
        if not entities.get('amount'):
            entities.update(self._regex_extract(text))
        
        # Determine transaction type
        if not entities.get('type'):
            entities['type'] = self._determine_transaction_type(text)
        
        return entities
    
    def _gpt_extract(self, text):
        """Use GPT for entity extraction"""
        try:
            response = openai.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a financial transaction parser. Extract entities from transaction text.
                        Return ONLY a JSON object with these fields:
                        {
                            "type": "sale" or "purchase",
                            "item": "product name",
                            "quantity": numeric value,
                            "amount": numeric value in rupees,
                            "unit": "kg/liters/pieces/etc"
                        }
                        If any field is not found, set it to null."""
                    },
                    {
                        "role": "user",
                        "content": f"Extract entities from: {text}"
                    }
                ],
                temperature=0
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"GPT extraction failed: {e}")
            return {}
    
    def _regex_extract(self, text):
        """Regex-based entity extraction as fallback"""
        entities = {}
        
        # Extract amount (rupees)
        amount_patterns = [
            r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'rupees?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*rupees?'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                entities['amount'] = float(amount_str)
                break
        
        # Extract quantity
        qty_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:kg|kilo|kilogram)',
            r'(\d+(?:\.\d+)?)\s*(?:liter|litre|l)',
            r'(\d+)\s*(?:piece|pieces|pcs|item|items)'
        ]
        
        for pattern in qty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['quantity'] = float(match.group(1))
                break
        
        # Extract item name (simple approach - get noun phrases)
        # This is basic; GPT will do better
        words = text.split()
        potential_items = [w for w in words if len(w) > 3 and w.isalpha()]
        if potential_items:
            entities['item'] = ' '.join(potential_items[:2])
        
        return entities
    
    def _determine_transaction_type(self, text):
        """Determine if transaction is sale or purchase"""
        text_lower = text.lower()
        
        sale_score = sum(1 for keyword in self.transaction_keywords['sale'] if keyword in text_lower)
        purchase_score = sum(1 for keyword in self.transaction_keywords['purchase'] if keyword in text_lower)
        
        if sale_score > purchase_score:
            return 'sale'
        elif purchase_score > sale_score:
            return 'purchase'
        else:
            return 'unknown'