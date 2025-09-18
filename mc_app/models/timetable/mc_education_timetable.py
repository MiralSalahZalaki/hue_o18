from odoo import models, fields, api

class MCEducationTimetable(models.Model):
    _inherit = 'education.timetable'
    
    published = fields.Boolean()
    grade_id = fields.Many2one('education.class', string="Grade",  domain="[('school', '=', company_id)]", required=True)
    class_division_id = fields.Many2one(
        'education.class.division',
        string='Class', required=True,
        domain="[('class_id', '=', grade_id)]",
        help="Select the class and division for the timetable."
    )

    timetable_mon_ids = fields.One2many('education.timetable.schedule',
                                        'timetable_mon_id',
                                        string='Monday Timetable',
                                        help="Timetable schedules for Monday.")
    timetable_tue_ids = fields.One2many('education.timetable.schedule',
                                        'timetable_tue_id',
                                        string='Tuesday Timetable',
                                        help="Timetable schedules for Tuesday.")
    timetable_wed_ids = fields.One2many('education.timetable.schedule',
                                        'timetable_wed_id',
                                        string='Wednesday Timetable',
                                        help="Timetable schedules for Wednesday.")
    timetable_thur_ids = fields.One2many('education.timetable.schedule',
                                         'timetable_thur_id',
                                         string='Thursday Timetable',
                                         help="Timetable schedules for Thursday.")
    timetable_fri_ids = fields.One2many('education.timetable.schedule',
                                        'timetable_fri_id',
                                        string='Friday Timetable',
                                        help="Timetable schedules for Friday.")
    timetable_sat_ids = fields.One2many('education.timetable.schedule',
                                        'timetable_sat_id',
                                        string='Saturday Timetable',
                                        help="Timetable schedules for Saturday.")
    timetable_sun_ids = fields.One2many('education.timetable.schedule',
                                        'timetable_sun_id',
                                        string='Sunday Timetable',
                                        help="Timetable schedules for Sunday.")
    @api.onchange('grade_id')
    def _onchange_grade_id(self):
        self.class_division_id = False

        # تصفية جميع الجداول السابقة
        self.timetable_mon_ids = [(5, 0, 0)]
        self.timetable_tue_ids = [(5, 0, 0)]
        self.timetable_wed_ids = [(5, 0, 0)]
        self.timetable_thur_ids = [(5, 0, 0)]
        self.timetable_fri_ids = [(5, 0, 0)]
        self.timetable_sat_ids = [(5, 0, 0)]
        self.timetable_sun_ids = [(5, 0, 0)]

        if self.grade_id:
            educational_stage = self.grade_id.educational_stages

            if educational_stage:
                # البحث عن جدول المراحل التعليمية
                timetable = self.env['mc.timetable'].sudo().search([
                    ('educational_stage_id', '=', educational_stage.id)
                ], limit=1)
                
                if timetable:
                    stage_periods = timetable.mapped('educational_stage_period.period_id')
                    
                    # الحصول على أيام العطلة
                    holiday_days = []
                    if timetable.holiday_one:
                        holiday_days.append(timetable.holiday_one)
                    if timetable.holiday_two:
                        holiday_days.append(timetable.holiday_two)
                    
                    # قاموس لتخزين البيانات قبل تعيينها للحفاظ على الأداء
                    new_timetable_data = {
                        '0': [],  # الإثنين
                        '1': [],  # الثلاثاء
                        '2': [],  # الأربعاء
                        '3': [],  # الخميس
                        '4': [],  # الجمعة
                        '5': [],  # السبت
                        '6': []   # الأحد
                    }

                    # إنشاء فترات لكل يوم ما عدا أيام العطلة
                    for period in stage_periods:
                        for day_number in new_timetable_data.keys():
                            # تخطي أيام العطلة
                            if day_number in holiday_days:
                                continue
                                
                            period_line = {
                                'period_id': period.id,
                                'time_from': period.time_from,
                                'time_till': period.time_to,
                                'week_day': day_number  
                            }
                            new_timetable_data[day_number].append((0, 0, period_line))

                    # تعيين البيانات المحفوظة إلى الحقول المناسبة فقط للأيام التي ليست أيام عطلة
                    day_to_field_mapping = {
                        '0': 'timetable_mon_ids',
                        '1': 'timetable_tue_ids',
                        '2': 'timetable_wed_ids',
                        '3': 'timetable_thur_ids',
                        '4': 'timetable_fri_ids',
                        '5': 'timetable_sat_ids',
                        '6': 'timetable_sun_ids'
                    }
                    
                    for day_number, field_name in day_to_field_mapping.items():
                        # تعيين قيمة فارغة لأيام العطلة، وإلا تعيين البيانات المجهزة
                        if day_number in holiday_days:
                            pass
                        else:
                            # إذا لم يكن يوم عطلة، قم بتعيين البيانات
                            setattr(self, field_name, new_timetable_data[day_number])


    def create(self, values):
        res = super().create(values)  
        
        if 'class_division_id' in values and values['class_division_id']:
            class_division = self.env['education.class.division'].browse(values['class_division_id'])
            year_suffix = class_division.academic_year_id.name[-3:]
            new_name = "/".join([class_division.name, year_suffix])
            
            res.write({'name': new_name})  
        
        return res