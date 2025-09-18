from odoo import models, fields

class MCEducationInstitute(models.Model):
    _name = 'mc.education.institute'

    name = fields.Char('Institute Name',required=True)
    affiliation	= fields.Char('Affiliation')
    register_number	= fields.Char('Register Number')
    higher_class = fields.Char('Higher class')
    lower_class	= fields.Char('Lower class')
    description	= fields.Text('Description')
