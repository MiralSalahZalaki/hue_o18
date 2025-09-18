from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCAssessmentTimes(models.Model):
    _name = 'mc.assessment.times'
    _description = 'Assessment Times' 

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", default=True)
    distribution = fields.Boolean(string="Distribution")
    stored = fields.Boolean(string="Stored Result")
    publish = fields.Boolean(string="Publish")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)
    grade_ids = fields.Many2many(
        "education.class",
        string="Grades",
        domain="[('school', '=', company_id)]"
    )

    @api.model
    def create(self, vals):
        start_date = vals.get('start_date')
        end_date = vals.get('end_date')

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError("لا يمكن أن يكون تاريخ النهاية قبل تاريخ البداية.")

        return super(MCAssessmentTimes, self).create(vals)
    