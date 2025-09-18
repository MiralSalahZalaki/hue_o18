from odoo import models, fields, api, _

class MCEducationClass(models.Model):
    _inherit = 'education.class'

    arabic_name = fields.Char()
    other_name = fields.Char()
    educational_stages = fields.Many2one(
        'mc.education.stages',
        string='Educational Stage',
        domain="[('company_id', '=', school)]")
    sequence = fields.Integer()
    school = fields.Many2one('res.company', default=lambda self: self.env.company)
    accepted_age_year = fields.Integer()
    accepted_age_month = fields.Integer()
    accepted_age_day = fields.Integer()
    separated_days = fields.Integer()
    attendance_responsible = fields.Many2one('res.users')
    connected_days = fields.Integer()
    general_microsoft_teams = fields.Char()
    ministerial_number = fields.Char()
    signature = fields.Binary()

    @api.onchange('school')
    def _onchange_school(self):
        if self.school:
            if self.educational_stages and self.educational_stages.company_id != self.school:
                self.educational_stages = False
        else:
            self.educational_stages = False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        company_ids = records.mapped('school').ids
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
        return self.env['csv.handler'].import_csv_with_validation(self._name, csv_data, company_id, company_field='school')