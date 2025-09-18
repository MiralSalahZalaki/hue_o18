from odoo import models, fields, api

class TotalStudentResultMonthly(models.Model):
    _name = 'total.student.result.monthly'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)
    student_id = fields.Many2one('education.student' , domain="[('company_id', 'in', allowed_company_ids)]", required=True)
    grade_id = fields.Many2one("education.class", string="Grade")
    class_id = fields.Many2one("education.class.division", string="Class")
    term_id = fields.Many2one("education.academic.term", string="Term",  domain="[('school_year_id.company_id', '=', company_id)]")
    academic_year_id = fields.Many2one('education.academic.year', string="Year")
    syllabus_id = fields.Many2one('education.syllabus', string="Subject")
    degree = fields.Float(string="Degree")
    subject_result = fields.Text(string="Subject Result")
    assesment_time = fields.Many2one('mc.assessment.times', string="Assessment Time")