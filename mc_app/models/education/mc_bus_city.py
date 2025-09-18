from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCBusCity(models.Model):
    _name = 'mc.bus.city'

    name = fields.Char()
    fee_amount = fields.Monetary(string="Fee Amount", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string="Currency", default= 74)

    @api.model
    def get_csv_template_with_validation(self):
        return self.env['csv.handler'].get_csv_template_with_validation(self._name)
    
    @api.model
    def validate_csv_headers(self, headers):
        return self.env['csv.handler'].validate_csv_headers(self._name, headers)
    
    @api.model
    def import_csv_with_validation(self, csv_data, company_id=None):
        return self.env['csv.handler'].import_csv_with_validation(self._name, csv_data, company_id, company_field=None)

