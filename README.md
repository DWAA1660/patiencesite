# Patient Eggs - Homestead Store

A charming online store for farm-fresh eggs and homestead products.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Stripe secret key:
```
STRIPE_SECRET_KEY=your_stripe_secret_key
```

4. Run the application:
```bash
python run.py
```

## Features
- Beautiful homestead-style design
- Product catalog with farm-fresh eggs and other products
- Secure payments via Stripe
- Easy to extend with Flask blueprints
