from datetime import datetime, timedelta
from flask import current_app
from patient_eggs.shop.database import db, WeeklyInventory

class InventoryManager:
    """Class to manage weekly inventory of hatching eggs."""
    
    def __init__(self, eggs_per_week=50):
        self.eggs_per_week = eggs_per_week
        self.initialized = False
    
    def _initialize_inventory(self):
        """Initialize inventory for the next 8 weeks if not already present."""
        if self.initialized:
            return
            
        # Check if we have any inventory records
        inventory_count = WeeklyInventory.query.count()
        
        if inventory_count == 0:
            # Generate inventory for the next year
            weeks = WeeklyInventory.generate_weeks(num_weeks=52, eggs_per_week=self.eggs_per_week)
            
            # Add to database
            for week_data in weeks:
                week = WeeklyInventory(
                    week_id=week_data['week_id'],
                    start_date=week_data['start_date'],
                    end_date=week_data['end_date'],
                    total=week_data['total'],
                    available=week_data['available'],
                    reserved=week_data['reserved'],
                    label=week_data['label']
                )
                db.session.add(week)
            
            db.session.commit()
            current_app.logger.info(f"Initialized inventory with {len(weeks)} weeks")
        
        self.initialized = True
    
    def get_available_weeks(self, num_weeks=8):
        """Get a list of available weeks for ordering eggs."""
        self._initialize_inventory()
        
        today = datetime.now()
        
        # Get weeks starting from today
        weeks = WeeklyInventory.query.filter(
            WeeklyInventory.start_date >= today
        ).order_by(WeeklyInventory.start_date).limit(num_weeks).all()
        
        # Format for API response
        result = []
        for week in weeks:
            result.append({
                "id": week.week_id,
                "label": week.label,
                "start_date": week.start_date.isoformat(),
                "end_date": week.end_date.isoformat(),
                "total": week.total,
                "available": week.available,
                "reserved": week.reserved
            })
        
        return result
    
    def get_inventory(self):
        """Get the current inventory."""
        self._initialize_inventory()
        
        inventory = {}
        weeks = WeeklyInventory.query.all()
        
        for week in weeks:
            inventory[week.week_id] = {
                "total": week.total,
                "available": week.available,
                "reserved": week.reserved,
                "start_date": week.start_date.isoformat(),
                "end_date": week.end_date.isoformat(),
                "label": week.label
            }
        
        return inventory
    
    def check_availability(self, week_id, quantity):
        """Check if the requested quantity is available for the specified week."""
        self._initialize_inventory()
        
        week = WeeklyInventory.query.filter_by(week_id=week_id).first()
        
        if not week:
            current_app.logger.error(f"Week {week_id} not found in inventory")
            return False
        
        return week.available >= quantity
    
    def reserve_eggs(self, week_id, quantity):
        """Reserve eggs for a specific week."""
        self._initialize_inventory()
        
        week = WeeklyInventory.query.filter_by(week_id=week_id).first()
        
        if not week or week.available < quantity:
            return False
        
        week.available -= quantity
        week.reserved += quantity
        db.session.commit()
        return True
    
    def distribute_eggs(self, quantities_by_week):
        """
        Distribute eggs across multiple weeks.
        
        Args:
            quantities_by_week: Dictionary mapping week_ids to quantities
            
        Returns:
            (success, message)
        """
        self._initialize_inventory()
        
        # First check if all requested quantities are available
        for week_id, quantity in quantities_by_week.items():
            if not self.check_availability(week_id, quantity):
                return False, f"Not enough eggs available for {week_id}"
        
        # If all checks pass, reserve the eggs
        for week_id, quantity in quantities_by_week.items():
            self.reserve_eggs(week_id, quantity)
        
        return True, "Eggs reserved successfully"

# Create a singleton instance
inventory_manager = InventoryManager()
