"""Educational routes."""
from flask import Blueprint, render_template

education_bp = Blueprint('education', __name__)

@education_bp.route('/how-it-works')
def how_it_works():
    return render_template('education/how_it_works.html')
