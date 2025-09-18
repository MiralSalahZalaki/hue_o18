from odoo import http, models
from odoo.http import request
from datetime import date
from werkzeug.utils import redirect

class AdmissionApplicationReactController(http.Controller):  
    @http.route('/schools', methods=["GET"], type="json", auth="public", csrf=False)
    def fetch_schools(self, **kwargs):
        schools = request.env['res.company'].sudo().search([('name', 'ilike', 'Mansoura')])
        data = [{'id': school.id, 'name': school.name} for school in schools]
        
        # رجع الـ data بشكل JSON
        return {"status": "success", "data": data}
