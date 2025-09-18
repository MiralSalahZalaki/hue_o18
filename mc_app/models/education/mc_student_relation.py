from odoo import models, fields

class MCStudentRelation(models.Model):
    _name = 'mc.student.relation'

    name = fields.Char()