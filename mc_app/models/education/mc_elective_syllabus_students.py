from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

class MCElectiveSyllabus(models.Model):
    _name = 'mc.elective.syllabus.students'
    _description = 'Elective Syllabus'
    
   
    syllabus_id = fields.Many2one('education.syllabus')
  

    
    student_id = fields.Many2one('education.student' , required=True, domain="[('company_id', 'in', allowed_company_ids)]")
    class_id = fields.Many2one('education.class.division',compute='_compute_student_info',store = True)
    grade_id = fields.Many2one('education.class',compute='_compute_student_info',store = True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    year_id = fields.Many2one('education.academic.year',default=lambda self: self._get_current_academic_year())

  
    @api.depends('student_id')
    def _compute_student_info(self):
        for rec in self:
            rec.class_id = rec.student_id.class_division_id.id if rec.student_id.class_division_id else False
            rec.grade_id = rec.student_id.grade_id.id if rec.student_id.grade_id else False
    
    def _get_current_academic_year(self):
        today = date.today()
        
        academic_year = self.env['education.academic.year'].sudo().search([
            ('ay_start_date', '<=', today),
            ('ay_end_date', '>=', today),
            ('active', '=', True)
        ], limit=1)
        
        return academic_year.id if academic_year else False
