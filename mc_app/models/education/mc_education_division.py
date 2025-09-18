from odoo import models, fields, api

class MCEducationDivision(models.Model):
    _inherit = 'education.division'

        
    @api.model
    def get_csv_template_with_validation(self):
        """Generate CSV template for Academic Year."""
        return self.env['csv.handler'].get_csv_template_with_validation(self._name)
    
    @api.model
    def validate_csv_headers(self, headers):
        """Validate CSV headers for Academic Year."""
        return self.env['csv.handler'].validate_csv_headers(self._name, headers)
    
    @api.model
    def import_csv_with_validation(self, csv_data, company_id=None):
        """Import CSV data for Academic Year with validation."""
        return self.env['csv.handler'].import_csv_with_validation(self._name, csv_data, company_id, company_field=None)