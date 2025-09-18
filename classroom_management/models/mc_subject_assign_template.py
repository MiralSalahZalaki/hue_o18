from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MCSubjectAssignTemplate(models.Model):
    _name = 'mc.subject.assign.template'
    _description = 'Syllabus Assign Template' 

    syllabus_id = fields.Many2one('education.syllabus', string="Syllabus") 
    grade_id = fields.Many2one ('education.class', string="Grade") 
    syllabus_assign_templat_id = fields.Many2one('mc.assign.generic.template', string="syllabus_assign_templat_id") 

    