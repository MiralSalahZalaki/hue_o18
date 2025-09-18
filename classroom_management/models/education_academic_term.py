from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EducationAcademicTerm(models.Model):
    _name = 'education.academic.term'

    name = fields.Char(string="Name", required = True)
    arabic_name = fields.Char(string="Arabic Name")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    academic_year_id = fields.Many2one('education.academic.year', string="School Year")
    active_term = fields.Boolean(string="Active Term")
    kpi_publish = fields.Boolean(string="Kpi Publish")
    publish = fields.Boolean(string="Publish")
    school_year_id = fields.Many2one('education.school.year', string='School Year')

    @api.model
    def create(self, vals):
        start_date = fields.Date.from_string(vals.get('start_date'))
        end_date = fields.Date.from_string(vals.get('end_date'))

        if end_date and start_date and end_date < start_date:
            raise ValidationError("لا يمكن أن يكون تاريخ النهاية قبل تاريخ البداية.")

        return super().create(vals)