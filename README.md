# Prairie Homestead E-Commerce Site

## Tech Stack
- Python (Flask)
- SQLite
- Stripe API (Integration Ready)
- Bootstrap 5

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python run.py
   ```

4. Access the site at `http://127.0.0.1:3236`.

## Features
- **Home Page**: Hero, 3D Icons, Gallery, Featured Items.
- **Adult Birds**: Deposit logic (25% due).
- **Hatching Eggs**: Weekly inventory system.
- **Cart & Checkout**: Mocked Stripe integration, Policy Gate.
- **Admin Dashboard**: Manage orders and weekly egg inventory.

## Admin Access
- Username: `admin`
- Password: `admin`
