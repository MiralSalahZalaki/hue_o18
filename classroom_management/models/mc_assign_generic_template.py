from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MCAssignGenericTemplate(models.Model):
    _name = 'mc.assign.generic.template'
    _description = 'Assign Generic Template to Grades and add Syllabus'

    temp_id = fields.Many2one('mc.generic.template', string="Temp ID", required=True)
    grade_ids = fields.Many2many('education.class', string="Grades", required=True)
    syllabus_assign_templat_id = fields.One2many('mc.subject.assign.template','syllabus_assign_templat_id', string="Syllabus Assign Template")
    bool_field = fields.Boolean(string="Same text")

    def add_syllabus(self):
        for rec in self:
            rec.syllabus_assign_templat_id.unlink()  

            if rec.grade_ids:
                syllabuses = self.env['education.syllabus'].sudo().search([('class_id', 'in', rec.grade_ids.ids)])
                for syllabus in syllabuses:
                    self.env['mc.subject.assign.template'].create({
                        'syllabus_id': syllabus.id,
                        'grade_id': syllabus.class_id.id,
                        'syllabus_assign_templat_id': rec.id,
                    })