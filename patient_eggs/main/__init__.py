from flask import Blueprint

bp = Blueprint('main', __name__)

from patient_eggs.main import routes
