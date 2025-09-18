from odoo import models, fields, api

class McRooms(models.Model):
    _name = 'mc.rooms'
    _description = 'Rooms'
    
    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)

    capacity = fields.Integer(string='Capacity')
    period_type = fields.Selection([
        ('regular', 'Regular Period'),
        ('special', 'Special Period'),
    ], string='Period Type')



    @api.model
    def get_csv_template_with_validation(self):
        return self.env['csv.handler'].get_csv_template_with_validation(self._name)

    @api.model
    def validate_csv_headers(self, headers):
        return self.env['csv.handler'].validate_csv_headers(self._name, headers)

    @api.model
    def import_csv_with_validation(self, csv_data, company_id):
        return self.env['csv.handler'].import_csv_with_validation(self._name, csv_data, company_id, company_field='company_id')