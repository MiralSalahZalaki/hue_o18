
from odoo import models, fields, api

class TimetableMasterAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_report_timetable_master'
    _description = 'Timetable Master Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['timetable.master.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._prepare_timetable_data(wizard)
        
        return {
            'doc_ids': docids,
            'doc_model': 'timetable.master.wizard',
            'docs': [wizard],

            # Main data
            'timetable_data': main_data['timetable_data'],
            'company_name': main_data['company_name'],
            'stage_name': main_data['stage_name'],
         

        }

    def _prepare_timetable_data(self,wizard):
        wizard.ensure_one()
        result = {}

        if wizard.stage_id:
            # البحث عن الصفوف التي تنتمي إلى المرحلة التعليمية المحددة
            grades = self.env['education.class'].sudo().search([
                ('educational_stages', '=', wizard.stage_id.id),
            ])

            # تهيئة قاموس لتخزين البيانات
            result = {
                'Monday': {},
                'Tuesday': {},
                'Wednesday': {},
                'Thursday': {},
                'Friday': {},
                'Saturday': {},
                'Sunday': {}
            }

            day_mapping = {
                '0': 'Monday',
                '1': 'Tuesday',
                '2': 'Wednesday',
                '3': 'Thursday',
                '4': 'Friday',
                '5': 'Saturday',
                '6': 'Sunday'
            }

            # لكل صف، نبحث عن الشعب الدراسية
            for grade in grades:
                class_divisions = self.env['education.class.division'].sudo().search([
                    ('class_id', '=', grade.id),
                ])

                # لكل شعبة، نبحث عن جداول الحصص
                for class_division in class_divisions:
                    class_name = class_division.name

                    # البحث عن جدول الحصص للشعبة
                    timetable = self.env['education.timetable'].sudo().search([
                        ('class_division_id', '=', class_division.id)
                    ], limit=1)

                    if timetable:
                        # البحث عن المرحلة التعليمية والحصول على أيام العطلة
                        educational_stage = grade.educational_stages
                        holiday_days = []
                        
                        if educational_stage:
                            mc_timetable = self.env['mc.timetable'].sudo().search([
                                ('educational_stage_id', '=', educational_stage.id)
                            ], limit=1)
                            
                            if mc_timetable:
                                if mc_timetable.holiday_one:
                                    holiday_days.append(mc_timetable.holiday_one)
                                if mc_timetable.holiday_two:
                                    holiday_days.append(mc_timetable.holiday_two)
                        
                        # الحصول على جداول كل يوم
                        timetable_schedules = {
                            'Monday': timetable.timetable_mon_ids if '0' not in holiday_days else [],
                            'Tuesday': timetable.timetable_tue_ids if '1' not in holiday_days else [],
                            'Wednesday': timetable.timetable_wed_ids if '2' not in holiday_days else [],
                            'Thursday': timetable.timetable_thur_ids if '3' not in holiday_days else [],
                            'Friday': timetable.timetable_fri_ids if '4' not in holiday_days else [],
                            'Saturday': timetable.timetable_sat_ids if '5' not in holiday_days else [],
                            'Sunday': timetable.timetable_sun_ids if '6' not in holiday_days else []
                        }

                        # معالجة كل جدول لكل يوم
                        for day_name, schedules in timetable_schedules.items():
                            if not schedules:  # تخطي الأيام الفارغة (أيام العطلة)
                                continue
                                
                            if class_name not in result[day_name]:
                                result[day_name][class_name] = []

                            for schedule in schedules:
                                # البحث عن المعلم المسؤول عن المادة للشعبة
                                teacher = "N/A"
                                if schedule.syllabus:
                                    syllabus_teacher = self.env['mc.syllabus.per.class'].sudo().search([
                                        ('syllabus_id', '=', schedule.syllabus.id),
                                        ('class_division_id', '=', class_division.id)
                                    ], limit=1)
                                    
                                    if syllabus_teacher and syllabus_teacher.faculty_regular_id:
                                        teacher = syllabus_teacher.faculty_regular_id.name

                                def float_to_time(float_time):
                                    hours = int(float_time)
                                    minutes = round((float_time - hours) * 60)
                                    # معالجة حالة إذا وصلت الدقائق إلى 60 بعد التقريب
                                    if minutes == 60:
                                        hours += 1
                                        minutes = 0
                                    return f"{hours:02d}:{minutes:02d}"
                                
                                period_data = {
                                    'period': schedule.period_id.name if schedule.period_id else "N/A",
                                    'time_from': float_to_time(schedule.time_from),
                                    'time_till': float_to_time(schedule.time_till),
                                    'subject': schedule.syllabus.name if schedule.syllabus else "N/A",
                                    'teacher': teacher,
                                }
                                
                                result[day_name][class_name].append(period_data)

                            # ترتيب الفترات حسب الوقت
                            if class_name in result[day_name]:
                                result[day_name][class_name].sort(key=lambda x: x['time_from'])

        return {
            'timetable_data': result,
            'company_name': wizard.company_id.name,
            'stage_name': wizard.stage_id.name,

        }
   

    