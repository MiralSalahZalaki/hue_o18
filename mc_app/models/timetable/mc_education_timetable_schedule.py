from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime



class MCTimetableSchedule(models.Model):
    _inherit = 'education.timetable.schedule'
    
    subject_id = fields.Many2one('education.subject',
                              string='Subjects',
                              required=False,
                              help="Subject associated with the schedule")
    faculty_id = fields.Many2one('education.faculty',
                              string='Faculty',
                              required=False, 
                              help="Faculty assigned with the schedule")
    online = fields.Boolean()
    syllabus_special = fields.Boolean()

    syllabus = fields.Many2one(
        'education.syllabus', 
        string="Syllabus",
        domain="[('class_id', '=', parent.grade_id)]"
    )

    period_id = fields.Many2one('timetable.period', string="Period",
                                
                                required=True, help="Select the period for the "
                                                    "timetable schedule.")

    timetable_mon_id = fields.Many2one('education.timetable',
                                       string='Timetable',
                                        help="Timetable associated "
                                                           "with the schedule.")
    timetable_tue_id = fields.Many2one('education.timetable',
                                       string='Timetable',
                                        help="Timetable associated "
                                                           "with the schedule.")
    timetable_wed_id = fields.Many2one('education.timetable',
                                       string='Timetable',
                                       help="Timetable associated "
                                                           "with the schedule.")
    timetable_thur_id = fields.Many2one('education.timetable',
                                        string='Timetable',
                                         help="Timetable associated "
                                                            "with the schedule.")
    timetable_fri_id = fields.Many2one('education.timetable',
                                       string='Timetable',
                                        help="Timetable associated "
                                                           "with the schedule.")
    timetable_sat_id = fields.Many2one('education.timetable',
                                       string='Timetable',
                                      help="Timetable associated "
                                                           "with the schedule.")
    timetable_sun_id = fields.Many2one('education.timetable',
                                       string='Timetable',
                                        help="Timetable associated "
                                                           "with the schedule.")

    """ week_day_str = fields.Char(string="Week Day", compute="_compute_week_day", store=True)

    def _compute_week_day(self):
        for record in self:
            record.week_day_str = str(datetime.today().weekday()) """
            
    @api.model
    def create(self, values):

        # If week_day is set but timetable_id is not, trigger the onchange
        if 'week_day' in values and not 'timetable_id' in values:
            week_day = values.get('week_day')
            if week_day == '0' and 'timetable_mon_id' in values:
                values['timetable_id'] = values['timetable_mon_id']
            elif week_day == '1' and 'timetable_tue_id' in values:
                values['timetable_id'] = values['timetable_tue_id']
            elif week_day == '2' and 'timetable_wed_id' in values:
                values['timetable_id'] = values['timetable_wed_id']
            elif week_day == '3' and 'timetable_thur_id' in values:
                values['timetable_id'] = values['timetable_thur_id']
            elif week_day == '4' and 'timetable_fri_id' in values:
                values['timetable_id'] = values['timetable_fri_id']
            elif week_day == '5' and 'timetable_sat_id' in values:
                values['timetable_id'] = values['timetable_sat_id']
            elif week_day == '6' and 'timetable_sun_id' in values:
                values['timetable_id'] = values['timetable_sun_id']

        return super(MCTimetableSchedule, self).create(values)
    

    @api.onchange('subject_id')
    def _onchange_subject_syllabus(self):
        """Update syllabus domain based on selected subject and class"""
        self.syllabus = False  # Clear previous selection
        domain = [('id', '!=', False)]  # Default domain
        
        if self.subject_id:
            domain = [
                ('subject_id', '=', self.subject_id.id),
              
            ]
        
        return {
            'domain': {
                'syllabus': domain
            }
        }