from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta
from collections import defaultdict

class BehaviorReportNo5Wizard(models.TransientModel):
    _name = 'behavior.report.no5.wizard'
    _description = 'Behavior Report No5 Wizard'

    company_id = fields.Many2one('res.company', string='School', 
                                 default=lambda self: self.env.company, 
                                 required=True)
    
    academic_year_id = fields.Many2one('education.academic.year', string='Academic Year',
                                       default=lambda self: self._get_current_academic_year())
    
    grade_id = fields.Many2one('education.class', string="Grade", required=True, 
                               domain="[('school', '=', company_id)]")
    
    class_division_id = fields.Many2one('education.class.division', string="Class",
                                        domain="[('class_id', '=', grade_id)]", 
                                        required=True)

    # Adjust Domain of student_ids
    student_ids_domain = fields.Binary(string="students domain",
                                     help="Dynamic domain for students based on grade and class",
                                     compute="_compute_student_ids_domain")
                                     
    student_id = fields.Many2many('education.student', string="Student", 
                                  required=True,
                                  domain="student_ids_domain")
       
    @api.depends('grade_id', 'class_division_id')
    def _compute_student_ids_domain(self):
        for rec in self:
            domain = [('id','=',-1)]
            if rec.grade_id:
                domain = [('grade_id', '=', rec.grade_id.id)]
                if rec.class_division_id:
                    domain.append(('class_division_id', '=', rec.class_division_id.id))
            rec.student_ids_domain = domain


    def _get_current_academic_year(self):
        """Get current academic year"""
        current_year = self.env['education.academic.year'].sudo().search([('current', '=', True)], limit=1)
        return current_year.id if current_year else False

    def generate_behavior_report_no5(self):
        """Generate the behavior report"""     
        # Validation
        if not all([self.grade_id, self.class_division_id, self.company_id]):
            raise ValidationError("Please fill all required fields: School, Grade, and Class")
        print(len(self.student_id))        
        return self.env.ref('mc_app.action_behavior_report_no5').report_action(self)