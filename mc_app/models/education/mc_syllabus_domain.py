from odoo import models, fields

class MCSyllabusDomain(models.Model):
    _name = 'mc.syllabus.domain'

    english_name = fields.Char(required=True)
    arabic_name = fields.Char()
    sep_syllabus= fields.Char()