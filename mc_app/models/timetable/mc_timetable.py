from odoo import models, fields, api, SUPERUSER_ID

class MCTimetable(models.Model):
    _name = 'mc.timetable'
    _description = 'MC Timetable'

    name = fields.Char(string='Name', store=True)

    educational_stage_id = fields.Many2one('mc.education.stages', string='Educational Stage', required=True, store=True)

    grade_id = fields.Many2one('education.class', string='Grade', store=True)

  
    educational_stage_period = fields.One2many(
        'education.stage.timetable',
        'timetable_stage_id',
        string='Periods',
        store=True
    )

    online_period = fields.One2many(
        'education.stage.timetable',
        'online_timetable_stage_id',
        string='Online Period',
        store=True
    )

    holiday_one = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='First Holiday', required=True, default='4')

    holiday_two = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Second Holiday', required=True, default='5')
