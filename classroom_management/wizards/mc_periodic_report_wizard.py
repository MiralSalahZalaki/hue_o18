from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MCPeriodicReportWizard(models.TransientModel):
    _name = 'mc.periodic.report.wizard'
    _description = 'MC Periodic Report Wizard'

    company_id = fields.Many2one('res.company', string='School',  default=lambda self: self.env.company, required=True )
    term_id = fields.Many2one('education.academic.term',  domain="[('school_year_id.company_id', '=', company_id)]", required=True)
    grade_id = fields.Many2one('education.class', string="Grade", required=True , domain="[('school','=',company_id)]")
    class_id = fields.Many2one("education.class.division", string="Class", domain="[('class_id','=',grade_id)]")
    student_view = fields.Boolean(string="Student View")
    distribution = fields.Boolean(string="Distribution")
    arabic_report = fields.Boolean(string="Arabic Report")
    full_academic_year = fields.Boolean(string="Full Academic Year")

    
    # Adjust Domain of assessment_times
    assessment_times_domain = fields.Char(string="assessment domain", 
                                          help="Dynamic domain used for assessment times", 
                                          compute="_compute_assessment_times_domain")
    
    assessments_times = fields.Many2many("mc.assessment.times", string="Assessment Time",
                                        domain="assessment_times_domain", required=True)
    
    # Adjust Domain of student_ids
    student_ids_domain = fields.Char(string="students domain",
                                     help="Dynamic domain for students based on grade and class",
                                     compute="_compute_student_ids_domain")
                                     
    student_ids = fields.Many2many('education.student', string="Student", 
                                  required=True,
                                  domain="student_ids_domain")
    
    @api.depends('company_id', 'term_id', 'grade_id', 'distribution')
    def _compute_assessment_times_domain(self):
        for rec in self:
            domain = [('id', '=', -1)]
            if rec.distribution:
                domain = [('distribution', '=', True)]
            elif rec.company_id and rec.grade_id and rec.term_id:
                domain = [
                    ('company_id', '=', rec.company_id.id),
                    ('grade_ids', 'in', rec.grade_id.id),
                    ('start_date', '>=', rec.term_id.start_date),
                    ('end_date', '<=', rec.term_id.end_date),
                    ('distribution', '=', False)
                ]
            rec.assessment_times_domain = domain

    @api.depends('grade_id', 'class_id')
    def _compute_student_ids_domain(self):
        for rec in self:
            domain = [('id','=',-1)]
            if rec.grade_id:
                domain = [('grade_id', '=', rec.grade_id.id)]
                if rec.class_id:
                    domain.append(('class_division_id', '=', rec.class_id.id))
            rec.student_ids_domain = domain
    
    @api.onchange('class_id')
    def _onchange_class_id(self):
        self.student_ids = False

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.student_ids = False
        self.class_id = False

    def _get_grade_scale_data(self, score, max_score):
        """Get grade scale data based on score percentage"""
        if max_score <= 0:
            return None
            
        percentage = (score / max_score) * 100
        
        # Get grading method
        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', self.grade_id.id),
            ('company_id', '=', self.company_id.id),
            ('school_year_id', '=', self.term_id.academic_year_id.id)
        ], limit=1)
        
        if grading_method and grading_method.grading_method == 'evaluation':
            # Find appropriate scale
            for scale in grading_method.grading_scale_id:
                if scale.minimum <= percentage <= scale.maximum:
                    return {
                        'scale_symbol': scale.symbol,
                        'scale_comment': scale.description,
                        'scale_color': scale.color,
                    }
        
        return None

    def generate_mc_periodic_report_wizard(self):

        if not all([self.grade_id, self.term_id, self.company_id, self.assessments_times]):
            raise ValidationError("Please fill all required fields: School, Grade, Term and at least one Assessment Time")

        return self.env.ref('classroom_management.action_report_mc_periodic_assessment').report_action(self)