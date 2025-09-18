from odoo import models, fields, api

class MCEducationStageTimetable(models.Model):
    _name = 'education.stage.timetable'
    _description = 'MC Education Stage Timetable'

    period_id = fields.Many2one('timetable.period', string="Period",
                                required=True, help="Select the period for the "
                                                    "timetable schedule.")
    time_from = fields.Float(string='From', required=True,
                             index=True, help="Start time of Period.")
    time_till = fields.Float(string='Till', required=True,
                             help="End time of Period.")
    
    timetable_stage_id = fields.Many2one('mc.timetable')
    online_timetable_stage_id = fields.Many2one('mc.timetable')


    @api.onchange('period_id')
    def _onchange_period_id(self):
        """Gets the start and end time of the period"""
        self.time_from = self.period_id.time_from
        self.time_till = self.period_id.time_to
  