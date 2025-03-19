from datetime import datetime, timedelta
from patient_eggs.shop.database import db, WeeklyInventory
from flask import current_app

class InventoryManager:
    """Class to manage weekly inventory using SQLite database."""
    
    @staticmethod
    def get_available_weeks(num_weeks=8):
        """Get a list of available weeks for ordering eggs."""
        # Query the database for available weeks
        weeks = WeeklyInventory.query.order_by(WeeklyInventory.start_date).limit(num_weeks).all()
        
        # If no weeks in database, generate them
        if not weeks:
            current_app.logger.info("No weeks found in database. Generating new weeks.")
            InventoryManager.initialize_inventory()
            weeks = WeeklyInventory.query.order_by(WeeklyInventory.start_date).limit(num_weeks).all()
        
        # Convert to dictionary format for compatibility with existing code
        result = []
        for week in weeks:
            result.append({
                "id": week.week_id,
                "label": week.label,
                "start_date": week.start_date,
                "end_date": week.end_date,
                "available": week.available,
                "total": week.total
            })
        
        return result
    
    @staticmethod
    def initialize_inventory(eggs_per_week=50, num_weeks=52):
        """Initialize inventory for the next year."""
        current_app.logger.info(f"Initializing inventory for {num_weeks} weeks with {eggs_per_week} eggs per week.")
        
        # Generate weeks
        weeks_data = WeeklyInventory.generate_weeks(num_weeks=num_weeks, eggs_per_week=eggs_per_week)
        
        # Add to database
        for week_data in weeks_data:
            # Check if week already exists
            existing_week = WeeklyInventory.query.filter_by(week_id=week_data["week_id"]).first()
            if not existing_week:
                week = WeeklyInventory(
                    week_id=week_data["week_id"],
                    start_date=week_data["start_date"],
                    end_date=week_data["end_date"],
                    total=week_data["total"],
                    available=week_data["available"],
                    reserved=week_data["reserved"],
                    label=week_data["label"]
                )
                db.session.add(week)
        
        db.session.commit()
        current_app.logger.info("Inventory initialization complete.")
    
    @staticmethod
    def check_availability(week_id, quantity):
        """Check if the requested quantity is available for the specified week."""
        week = WeeklyInventory.query.filter_by(week_id=week_id).first()
        
        if not week:
            current_app.logger.error(f"Week {week_id} not found in inventory.")
            return False
        
        available = week.available >= quantity
        current_app.logger.info(f"Checking availability for week {week_id}: requested={quantity}, available={week.available}, result={available}")
        return available
    
    @staticmethod
    def reserve_eggs(week_id, quantity):
        """Reserve eggs for a specific week."""
        week = WeeklyInventory.query.filter_by(week_id=week_id).first()
        
        if not week or week.available < quantity:
            current_app.logger.error(f"Cannot reserve {quantity} eggs for week {week_id}. Available: {week.available if week else 'Week not found'}")
            return False
        
        week.available -= quantity
        week.reserved += quantity
        db.session.commit()
        
        current_app.logger.info(f"Reserved {quantity} eggs for week {week_id}. Now available: {week.available}")
        return True
    
    @staticmethod
    def distribute_eggs(quantities_by_week):
        """
        Distribute eggs across multiple weeks.
        
        Args:
            quantities_by_week: Dictionary mapping week_ids to quantities
            
        Returns:
            (success, message)
        """
        # Validate all quantities first
        for week_id, quantity in quantities_by_week.items():
            if not InventoryManager.check_availability(week_id, quantity):
                return False, f"Not enough inventory available for week {week_id}"
        
        # If all are valid, reserve them
        for week_id, quantity in quantities_by_week.items():
            InventoryManager.reserve_eggs(week_id, quantity)
        
        return True, "Eggs reserved successfully"

# Create a singleton instance
inventory_manager = InventoryManager()

# Initialize the inventory
inventory_manager.initialize_inventory()
