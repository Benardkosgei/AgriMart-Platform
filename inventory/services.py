"""
Inventory Management Services
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, F
from typing import Dict, List, Optional

from .models import (InventoryItem, StockMovement, StockAlert, PurchaseOrder, 
                    PurchaseOrderItem, StockBatch, Supplier, Warehouse)
from products.models import Product

class InventoryService:
    """Main inventory management service"""
    
    @staticmethod
    def update_stock(inventory_item: InventoryItem, quantity: Decimal, 
                    movement_type: str, reference_type: str = '', 
                    reference_id: str = '', notes: str = '',
                    unit_cost: Decimal = None, user=None) -> StockMovement:
        """Update stock levels and create movement record"""
        
        stock_before = inventory_item.current_stock
        
        if movement_type in ['purchase', 'return', 'adjustment']:
            inventory_item.current_stock += quantity
        elif movement_type in ['sale', 'waste', 'transfer']:
            inventory_item.current_stock -= quantity
        elif movement_type == 'reservation':
            inventory_item.reserved_stock += quantity
        elif movement_type == 'release':
            inventory_item.reserved_stock -= quantity
        
        inventory_item.update_available_stock()
        
        # Create stock movement record
        movement = StockMovement.objects.create(
            inventory_item=inventory_item,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=unit_cost or inventory_item.unit_cost,
            stock_before=stock_before,
            stock_after=inventory_item.current_stock,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            created_by=user
        )
        
        # Check for alerts
        InventoryService.check_stock_alerts(inventory_item)
        
        return movement
    
    @staticmethod
    def reserve_stock(product: Product, quantity: Decimal, 
                     reference_type: str = '', reference_id: str = '') -> bool:
        """Reserve stock for orders"""
        try:
            inventory_item = product.inventory
            
            if inventory_item.available_stock >= quantity:
                InventoryService.update_stock(
                    inventory_item=inventory_item,
                    quantity=quantity,
                    movement_type='reservation',
                    reference_type=reference_type,
                    reference_id=reference_id
                )
                return True
            return False
        except InventoryItem.DoesNotExist:
            return False
    
    @staticmethod
    def release_stock(product: Product, quantity: Decimal,
                     reference_type: str = '', reference_id: str = '') -> bool:
        """Release reserved stock"""
        try:
            inventory_item = product.inventory
            
            if inventory_item.reserved_stock >= quantity:
                InventoryService.update_stock(
                    inventory_item=inventory_item,
                    quantity=quantity,
                    movement_type='release',
                    reference_type=reference_type,
                    reference_id=reference_id
                )
                return True
            return False
        except InventoryItem.DoesNotExist:
            return False
    
    @staticmethod
    def process_sale(product: Product, quantity: Decimal, 
                    reference_id: str = '', user=None) -> bool:
        """Process product sale"""
        try:
            inventory_item = product.inventory
            
            # Release reservation and process sale
            InventoryService.update_stock(
                inventory_item=inventory_item,
                quantity=quantity,
                movement_type='release',
                reference_type='order',
                reference_id=reference_id
            )
            
            InventoryService.update_stock(
                inventory_item=inventory_item,
                quantity=quantity,
                movement_type='sale',
                reference_type='order',
                reference_id=reference_id,
                user=user
            )
            
            return True
        except InventoryItem.DoesNotExist:
            return False
    
    @staticmethod
    def check_stock_alerts(inventory_item: InventoryItem):
        """Check and create stock alerts"""
        alerts_to_create = []
        
        # Low stock alert
        if inventory_item.is_low_stock and not inventory_item.is_out_of_stock:
            if not StockAlert.objects.filter(
                inventory_item=inventory_item,
                alert_type='low_stock',
                status='active'
            ).exists():
                alerts_to_create.append({
                    'alert_type': 'low_stock',
                    'title': f'Low Stock Alert - {inventory_item.product.name}',
                    'message': f'Stock level ({inventory_item.available_stock}) is below reorder point ({inventory_item.reorder_point})',
                    'severity': 'medium'
                })
        
        # Out of stock alert
        if inventory_item.is_out_of_stock:
            if not StockAlert.objects.filter(
                inventory_item=inventory_item,
                alert_type='out_of_stock',
                status='active'
            ).exists():
                alerts_to_create.append({
                    'alert_type': 'out_of_stock',
                    'title': f'Out of Stock - {inventory_item.product.name}',
                    'message': f'Product is out of stock (Available: {inventory_item.available_stock})',
                    'severity': 'high'
                })
        
        # Overstock alert
        if inventory_item.available_stock > inventory_item.maximum_stock:
            if not StockAlert.objects.filter(
                inventory_item=inventory_item,
                alert_type='overstock',
                status='active'
            ).exists():
                alerts_to_create.append({
                    'alert_type': 'overstock',
                    'title': f'Overstock Alert - {inventory_item.product.name}',
                    'message': f'Stock level ({inventory_item.available_stock}) exceeds maximum ({inventory_item.maximum_stock})',
                    'severity': 'low'
                })
        
        # Create alerts
        for alert_data in alerts_to_create:
            StockAlert.objects.create(
                inventory_item=inventory_item,
                current_stock=inventory_item.available_stock,
                threshold_value=inventory_item.reorder_point,
                **alert_data
            )
    
    @staticmethod
    def generate_reorder_suggestions() -> List[Dict]:
        """Generate automatic reorder suggestions"""
        suggestions = []
        
        # Get items that need reordering
        low_stock_items = InventoryItem.objects.filter(
            available_stock__lte=F('reorder_point'),
            auto_reorder_enabled=True
        )
        
        for item in low_stock_items:
            # Check if there's already a pending purchase order
            pending_po_exists = PurchaseOrderItem.objects.filter(
                product=item.product,
                purchase_order__status__in=['pending', 'approved', 'sent', 'confirmed']
            ).exists()
            
            if not pending_po_exists:
                suggestions.append({
                    'product': item.product,
                    'current_stock': item.available_stock,
                    'reorder_point': item.reorder_point,
                    'suggested_quantity': item.reorder_quantity,
                    'estimated_cost': item.reorder_quantity * item.unit_cost,
                    'priority': 'high' if item.is_out_of_stock else 'medium'
                })
        
        return suggestions

class PurchaseOrderService:
    """Purchase order management service"""
    
    @staticmethod
    def create_purchase_order(supplier: Supplier, warehouse: Warehouse,
                            items_data: List[Dict], user=None) -> PurchaseOrder:
        """Create purchase order"""
        # Generate PO number
        po_count = PurchaseOrder.objects.count() + 1
        po_number = f"PO{timezone.now().year}{po_count:06d}"
        
        # Create purchase order
        po = PurchaseOrder.objects.create(
            po_number=po_number,
            supplier=supplier,
            warehouse=warehouse,
            created_by=user
        )
        
        # Create PO items
        for item_data in items_data:
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                product=item_data['product'],
                quantity_ordered=item_data['quantity'],
                unit_cost=item_data['unit_cost'],
                quality_grade_expected=item_data.get('quality_grade', 'B')
            )
        
        # Calculate totals
        po.calculate_totals()
        
        return po
    
    @staticmethod
    def receive_purchase_order(po: PurchaseOrder, items_received: List[Dict],
                             user=None) -> Dict:
        """Process purchase order receipt"""
        results = []
        
        for item_data in items_received:
            po_item = PurchaseOrderItem.objects.get(
                id=item_data['po_item_id']
            )
            
            quantity_received = item_data['quantity_received']
            quality_grade = item_data.get('quality_grade', 'B')
            
            # Update PO item
            po_item.quantity_received += quantity_received
            po_item.quality_grade_received = quality_grade
            if item_data.get('actual_delivery_date'):
                po_item.actual_delivery_date = item_data['actual_delivery_date']
            po_item.save()
            
            # Update inventory
            try:
                inventory_item = po_item.product.inventory
                
                # Create stock movement
                movement = InventoryService.update_stock(
                    inventory_item=inventory_item,
                    quantity=quantity_received,
                    movement_type='purchase',
                    reference_type='purchase_order',
                    reference_id=po.po_number,
                    unit_cost=po_item.unit_cost,
                    user=user
                )
                
                # Create batch if batch tracking is enabled
                if inventory_item.track_expiry:
                    StockBatch.objects.create(
                        batch_number=item_data.get('batch_number', f"B{timezone.now().strftime('%Y%m%d%H%M%S')}"),
                        inventory_item=inventory_item,
                        quantity=quantity_received,
                        unit_cost=po_item.unit_cost,
                        expiry_date=item_data.get('expiry_date'),
                        quality_grade=quality_grade,
                        supplier=po.supplier,
                        purchase_order=po
                    )
                
                results.append({
                    'product': po_item.product.name,
                    'quantity_received': quantity_received,
                    'status': 'success'
                })
                
            except InventoryItem.DoesNotExist:
                results.append({
                    'product': po_item.product.name,
                    'quantity_received': quantity_received,
                    'status': 'error',
                    'message': 'Inventory item not found'
                })
        
        # Update PO status
        total_ordered = sum(item.quantity_ordered for item in po.items.all())
        total_received = sum(item.quantity_received for item in po.items.all())
        
        if total_received >= total_ordered:
            po.status = 'received'
        elif total_received > 0:
            po.status = 'partially_received'
        
        po.actual_delivery_date = timezone.now().date()
        po.received_by = user
        po.save()
        
        return {
            'success': True,
            'po_status': po.status,
            'items': results
        }

class StockAnalyticsService:
    """Stock analytics and reporting service"""
    
    @staticmethod
    def get_stock_summary() -> Dict:
        """Get overall stock summary"""
        inventory_items = InventoryItem.objects.all()
        
        return {
            'total_products': inventory_items.count(),
            'total_stock_value': sum(item.total_value for item in inventory_items),
            'low_stock_items': inventory_items.filter(
                available_stock__lte=F('reorder_point')
            ).count(),
            'out_of_stock_items': inventory_items.filter(
                available_stock__lte=0
            ).count(),
            'active_alerts': StockAlert.objects.filter(status='active').count()
        }
    
    @staticmethod
    def get_movement_analytics(days: int = 30) -> Dict:
        """Get stock movement analytics"""
        start_date = timezone.now() - timedelta(days=days)
        movements = StockMovement.objects.filter(created_at__gte=start_date)
        
        return {
            'total_movements': movements.count(),
            'purchases': movements.filter(movement_type='purchase').aggregate(
                count=Sum('quantity')
            )['count'] or 0,
            'sales': movements.filter(movement_type='sale').aggregate(
                count=Sum('quantity')
            )['count'] or 0,
            'waste': movements.filter(movement_type='waste').aggregate(
                count=Sum('quantity')
            )['count'] or 0
        }
    
    @staticmethod
    def get_expiry_report() -> Dict:
        """Get expiry report for perishable items"""
        today = timezone.now().date()
        
        # Items expiring in next 7 days
        expiring_soon = StockBatch.objects.filter(
            expiry_date__lte=today + timedelta(days=7),
            expiry_date__gt=today,
            is_active=True
        )
        
        # Already expired items
        expired = StockBatch.objects.filter(
            expiry_date__lte=today,
            is_active=True
        )
        
        return {
            'expiring_soon': expiring_soon.count(),
            'expiring_soon_value': sum(
                batch.quantity * batch.unit_cost for batch in expiring_soon
            ),
            'expired': expired.count(),
            'expired_value': sum(
                batch.quantity * batch.unit_cost for batch in expired
            )
        }
