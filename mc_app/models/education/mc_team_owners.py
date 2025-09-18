from odoo import models, fields, api

class MCTeamOwners(models.Model):
    _name = 'mc.team.owners'

    name = fields.Char()
    
    grade = fields.Many2many('education.class', required=True, string="Grade")
    syllabus = fields.Many2many('education.syllabus', string="Syllabus",
                               domain="[('class_id', 'in', grade)]")
    responsibles = fields.Many2many('education.faculty', string="Grade")

    @api.onchange('grade')
    def _onchange_grade(self):
        """Clear syllabus selection when grade changes"""
        self.syllabus = False