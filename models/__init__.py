"""
Data models for CashFlow
"""

# You can add Pydantic models here for validation
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Transaction(BaseModel):
    """Transaction data model"""
    id: Optional[str] = None
    user_id: str
    type: str  # 'sale', 'purchase', 'expense'
    item: Optional[str] = None
    quantity: Optional[float] = None
    amount: float
    raw_text: Optional[str] = None
    created_at: Optional[datetime] = None

class InventoryItem(BaseModel):
    """Inventory item model"""
    id: Optional[str] = None
    user_id: str
    item_name: str
    quantity: float = 0
    unit: Optional[str] = None
    reorder_level: Optional[float] = None
    last_updated: Optional[datetime] = None

class Alert(BaseModel):
    """Alert model"""
    id: Optional[str] = None
    user_id: str
    type: str  # 'liquidity_crunch', 'low_stock', 'fraud_risk'
    message: str
    severity: str = 'medium'  # 'low', 'medium', 'high', 'critical'
    read: bool = False
    created_at: Optional[datetime] = None

class User(BaseModel):
    """User model"""
    id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    name: str
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    created_at: Optional[datetime] = None

__all__ = [
    'Transaction',
    'InventoryItem',
    'Alert',
    'User'
]