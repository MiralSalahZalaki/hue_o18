from odoo import _, api, fields, models


class MCFollowSupervisor(models.Model):
    _name = 'mc.follow.supervisor'
    _description = 'Manage Follow Supervisor'
    _rec_name = "responsible"


    responsible = fields.Many2one('hr.employee','Responsible Person',required=True)
    grade_id = fields.Many2many('education.class',string='Grade')
    syllabus_id = fields.Many2many('education.syllabus',string='Syllabus',domain="[('class_id','=',grade_id)]")
    
