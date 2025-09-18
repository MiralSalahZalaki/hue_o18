from odoo import _, api, fields, models

class EducationSchoolYear(models.Model):
    _name = 'education.school.year'
    _description = 'School Year'

    name = fields.Many2one('education.academic.year', string="Year")
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)
    active = fields.Boolean(string="Active", help="If unchecked, it will allow you to hide the Academic Year without removing it.")
    school_year = fields.Char(string='School Year')
    ay_start_date = fields.Date(string="Start date", help='Starting date of academic year', required=True)
    ay_end_date = fields.Date(string="End date", help='Ending of academic year', required=True)
    ay_description = fields.Text(string="Description", help='Description about the academic year')
    current = fields.Boolean(string="Current", help="If checked, it will be the current Academic Year.")
    term_ids = fields.One2many('education.academic.term', 'school_year_id', string="Academic Terms")
