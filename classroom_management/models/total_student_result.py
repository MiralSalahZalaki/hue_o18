from odoo import models, fields, api

class TotalStudentResult(models.Model):
    _name = 'total.student.result'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)
    student_id = fields.Many2one('education.student' , domain="[('company_id', 'in', allowed_company_ids)]", required=True)
    grade_id = fields.Many2one("education.class", string="Grade")
    class_id = fields.Many2one("education.class.division", string="Class")
    term_id = fields.Many2one("education.academic.term", string="Term",  domain="[('school_year_id.company_id', '=', company_id)]")
    academic_year_id = fields.Many2one('education.academic.year', string="Year")
    result = fields.Text(string="Result")
    total  = fields.Float(string="Total")
    absence_days = fields.Float(string="Absence Days")
    ministry_total = fields.Float(string="Ministry Total")
