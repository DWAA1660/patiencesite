from flask import session, current_app
import json
import uuid
from datetime import datetime
from patient_eggs.shop.database import db, CartItem, CartItemWeek

class Cart:
    """Class to manage shopping cart functionality using SQLite database."""
    
    CART_SESSION_KEY = 'shopping_cart'
    
    @classmethod
    def get_cart(cls):
        """Get the current cart from session or create a new one."""
        # Initialize an empty cart if it doesn't exist
        if cls.CART_SESSION_KEY not in session:
            cart_id = str(uuid.uuid4())
            session[cls.CART_SESSION_KEY] = {
                'cart_id': cart_id,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            # Ensure session is marked as modified
            session.modified = True
            current_app.logger.info(f"Created new cart with ID: {cart_id}")
        
        # Get cart ID from session - ensure we're working with string data
        cart_data = session.get(cls.CART_SESSION_KEY, {})
        
        # Convert to dict if it's not already (handling potential serialization issues)
        if not isinstance(cart_data, dict):
            try:
                if isinstance(cart_data, bytes):
                    cart_data = json.loads(cart_data.decode('utf-8'))
                elif isinstance(cart_data, str):
                    cart_data = json.loads(cart_data)
            except (TypeError, json.JSONDecodeError) as e:
                current_app.logger.error(f"Error decoding cart data: {e}")
                # Reset the cart if we can't decode it
                cart_id = str(uuid.uuid4())
                cart_data = {
                    'cart_id': cart_id,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                session[cls.CART_SESSION_KEY] = cart_data
                session.modified = True
        
        cart_id = cart_data.get('cart_id')
        if not cart_id:
            # If cart_id is missing, create a new one
            cart_id = str(uuid.uuid4())
            cart_data['cart_id'] = cart_id
            cart_data['created_at'] = datetime.now().isoformat()
            cart_data['updated_at'] = datetime.now().isoformat()
            session[cls.CART_SESSION_KEY] = cart_data
            session.modified = True
            current_app.logger.info(f"Created new cart with ID: {cart_id}")
        
        # Get cart items from database
        cart_items = CartItem.query.filter_by(cart_id=cart_id).all()
        
        # Build cart data structure
        items = []
        for item in cart_items:
            # Get week selections for this item
            week_selections = {}
            week_items = CartItemWeek.query.filter_by(cart_item_id=item.id).all()
            
            for week_item in week_items:
                week_selections[week_item.week_id] = week_item.quantity
            
            items.append({
                'item_id': item.id,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'price_per_unit': item.price_per_unit,
                'week_selections': week_selections,
                'total_quantity': item.total_quantity,
                'total_price': item.total_price,
                'product_image': item.product_image,
                'added_at': item.created_at.isoformat()
            })
        
        # Add items to cart data
        cart_data['items'] = items
        
        current_app.logger.info(f"Retrieved cart {cart_id} with {len(items)} items")
        return cart_data

    @classmethod
    def add_item(cls, product_id, product_name, price, week_selections, product_image=None):
        """
        Add an item to the cart.
        
        Args:
            product_id: ID of the product
            product_name: Name of the product
            price: Price per unit
            week_selections: Dictionary mapping week IDs to quantities
            product_image: Optional URL to product image
        
        Returns:
            Updated cart
        """
        # Get cart ID from session
        cart_data = cls.get_cart()
        cart_id = cart_data['cart_id']
        
        # Calculate total quantity and price
        total_quantity = sum(int(week_selections.get(week_id, 0)) for week_id in week_selections)
        total_price = float(price) * total_quantity
        
        # Create new cart item in database
        cart_item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            product_name=product_name,
            price_per_unit=float(price),
            total_quantity=total_quantity,
            total_price=total_price,
            product_image=product_image
        )
        
        db.session.add(cart_item)
        db.session.flush()  # Get the ID without committing
        
        # Add week selections
        for week_id, quantity in week_selections.items():
            week_item = CartItemWeek(
                cart_item_id=cart_item.id,
                week_id=week_id,
                quantity=int(quantity)
            )
            db.session.add(week_item)
        
        # Commit all changes
        db.session.commit()
        
        current_app.logger.info(f"Added item to cart {cart_id}: {product_id}, {week_selections}")
        
        # Return updated cart
        return cls.get_cart()
    
    @classmethod
    def update_item(cls, item_id, week_selections):
        """
        Update an existing item in the cart.
        
        Args:
            item_id: ID of the item to update
            week_selections: New week selections dictionary
        
        Returns:
            Updated cart or None if item not found
        """
        # Find the cart item
        cart_item = CartItem.query.get(item_id)
        
        if not cart_item:
            current_app.logger.error(f"Cart item {item_id} not found")
            return None
        
        # Delete existing week selections
        CartItemWeek.query.filter_by(cart_item_id=item_id).delete()
        
        # Calculate new totals
        total_quantity = sum(int(week_selections.get(week_id, 0)) for week_id in week_selections)
        total_price = float(cart_item.price_per_unit) * total_quantity
        
        # Update cart item
        cart_item.total_quantity = total_quantity
        cart_item.total_price = total_price
        cart_item.updated_at = datetime.now()
        
        # Add new week selections
        for week_id, quantity in week_selections.items():
            week_item = CartItemWeek(
                cart_item_id=item_id,
                week_id=week_id,
                quantity=int(quantity)
            )
            db.session.add(week_item)
        
        # Commit all changes
        db.session.commit()
        
        current_app.logger.info(f"Updated cart item {item_id} with {week_selections}")
        
        # Return updated cart
        return cls.get_cart()
    
    @classmethod
    def remove_item(cls, item_id):
        """
        Remove an item from the cart.
        
        Args:
            item_id: ID of the item to remove
        
        Returns:
            Updated cart
        """
        # Delete week selections first (foreign key constraint)
        CartItemWeek.query.filter_by(cart_item_id=item_id).delete()
        
        # Delete cart item
        CartItem.query.filter_by(id=item_id).delete()
        
        # Commit changes
        db.session.commit()
        
        current_app.logger.info(f"Removed cart item {item_id}")
        
        # Return updated cart
        return cls.get_cart()
    
    @classmethod
    def clear_cart(cls):
        """Clear all items from the cart."""
        # Get cart ID from session
        cart_data = cls.get_cart()
        cart_id = cart_data['cart_id']
        
        # Get all cart items
        cart_items = CartItem.query.filter_by(cart_id=cart_id).all()
        
        # Delete all week selections and cart items
        for item in cart_items:
            CartItemWeek.query.filter_by(cart_item_id=item.id).delete()
        
        CartItem.query.filter_by(cart_id=cart_id).delete()
        
        # Commit changes
        db.session.commit()
        
        current_app.logger.info(f"Cleared cart {cart_id}")
        
        # Return updated cart
        return cls.get_cart()
    
    @classmethod
    def get_cart_count(cls):
        """Get the total number of items in the cart."""
        cart_data = cls.get_cart()
        return len(cart_data.get('items', []))
    
    @classmethod
    def get_cart_total(cls):
        """Get the total price of all items in the cart."""
        cart_data = cls.get_cart()
        return sum(item.get('total_price', 0) for item in cart_data.get('items', []))
