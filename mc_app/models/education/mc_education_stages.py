from odoo import models, fields, api, _

class MCEducationStages(models.Model):
    _name = 'mc.education.stages'
    _description = 'Education Stages'

    name = fields.Char(string='name', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='School',
        default=lambda self: self.env.company,
        required=True
    )
    grades = fields.One2many('education.class', 'educational_stages')
    vice_headmasters = fields.Many2many('education.faculty', string='Channel Book Owners')
    vice_headmasters2 = fields.Many2many('hr.employee', string='Vice Headmasters')
    credit = fields.Boolean()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        company_ids = records.mapped('company_id').ids
        settings = self.env['system.settings'].sudo().search([('company_id', 'in', company_ids)])
        for setting in settings:
            setting.fetch_company_data()
        return records

    @api.model
    def get_csv_template_with_validation(self):
        return self.env['csv.handler'].get_csv_template_with_validation(self._name)

    @api.model
    def validate_csv_headers(self, headers):
        return self.env['csv.handler'].validate_csv_headers(self._name, headers)

    @api.model
    def import_csv_with_validation(self, csv_data, company_id):
        return self.env['csv.handler'].import_csv_with_validation(self._name, csv_data, company_id, company_field='company_id')