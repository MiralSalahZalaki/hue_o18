from odoo import models, fields,api


class MCPublishAssessmentConfg(models.Model):
    _name = 'mc.publish.assessment.confg'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required= True)
    academic_year_id = fields.Many2one('education.academic.year', string="School Year", required= True)
    term_id = fields.Many2one('education.academic.term', required= True ,  domain="[('school_year_id.company_id', '=', company_id)]")
    grade_id = fields.Many2one("education.class", string="Grade", required=True,  domain="[('school', '=', company_id)]")
    assessments_times = fields.Many2one("mc.assessment.times", string="Assessments Times", required=True)
    second_assessments_times = fields.Many2one("mc.assessment.times", string="Second Assessments Times")
    publish = fields.Boolean(string="Publish")