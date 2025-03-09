from flask import Blueprint

bp = Blueprint('shop', __name__)

from patient_eggs.shop import routes
