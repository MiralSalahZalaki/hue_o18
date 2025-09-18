
from odoo import models, fields, api

class TimetableByTeacherAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_report_timetable_by_teacher'
    _description = 'Timetable By Teacher Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['timetable.by.teacher.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._prepare_timetable_data(wizard)
        
        return {
            'doc_ids': docids,
            'doc_model': 'timetable.by.teacher.wizard',
            'docs': [wizard],

            # Main data
            'timetable_data': main_data['timetable_data'],
            'teacher': main_data['teacher'],

        }

    def _prepare_timetable_data(self,wizard):
        wizard.ensure_one()

        timetable_data = {}
        all_timetable_records = []

        if wizard.name:

            for syllabus_class in wizard.faculty_syllabus_class:
                syllabus_id = syllabus_class.syllabus_id
                class_division_id = syllabus_class.class_division_id

                regular_timetable_records = self.env['education.timetable.schedule'].sudo().search([
                    ('syllabus', '=', syllabus_id.id),
                    ('class_division_id', '=', class_division_id.id)
                ])

                all_timetable_records.extend(regular_timetable_records)

            for syllabus_special_class in wizard.faculty_syllabus_special_class:
                syllabus_id = syllabus_special_class.syllabus_id  
                class_division_id = syllabus_special_class.class_division_id  

                special_timetable_records = self.env['education.timetable.schedule'].sudo().search([
                    ('syllabus', '=', syllabus_id.id),
                    ('class_division_id', '=', class_division_id.id)
                ])

                all_timetable_records.extend(special_timetable_records)  
            
            for schedule in all_timetable_records:
                day_name = dict(schedule._fields['week_day'].selection).get(schedule.week_day)
                period = schedule.period_id.name
                time_from = schedule.time_from
                time_till = schedule.time_till
                subject = schedule.syllabus.name
                class_division = schedule.class_division_id.name

                if day_name not in timetable_data:
                    timetable_data[day_name] = []

                def float_to_time(float_time):
                    hours = int(float_time)
                    minutes = round((float_time - hours) * 60)

                    if minutes == 60:
                        hours += 1
                        minutes = 0
                    return f"{hours:02d}:{minutes:02d}"

                timetable_data[day_name].append({
                    'period': period,
                    'subject': subject,
                    'time_from': float_to_time(time_from),
                    'time_till': float_to_time(time_till),
                    'class_division': class_division
                })

        return {
            'timetable_data':timetable_data,
            'teacher':wizard.name.name,
        }