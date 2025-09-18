from odoo import _, api, fields, models


class MCElevationGradingSupervisor(models.Model):
    _name = 'mc.grading.supervisor'
    _description = 'MC Elevation Grades Supervisor'
    _rec_name = "responsible"


    responsible = fields.Many2one('hr.employee','Responsible Person',required=True)
    educational_stage = fields.Many2many('mc.education.stages',string='Educational Stages')
    grade_id = fields.Many2many('education.class',string='Grade', domain="[('educational_stages','=',educational_stage)]")
    syllabus_id = fields.Many2many('education.syllabus',string='Syllabus',domain="[('class_id','=',grade_id)]")
    
