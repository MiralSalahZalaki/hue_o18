from odoo import models, fields, api, SUPERUSER_ID

class MCWeekDays(models.Model):
    _name = 'mc.week.days'
    _description = 'Week days'

    name = fields.Char(string='Name')


