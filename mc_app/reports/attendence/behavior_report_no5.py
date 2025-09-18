
from odoo import models, fields, api
from datetime import timedelta
from collections import defaultdict


class BehaviorReportNo5Abstract(models.AbstractModel):
    _name = 'report.mc_app.template_behavior_report_no5'
    _description = 'Behavior Report No5 Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['behavior.report.no5.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._generate_report(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'behavior.report.no5.wizard',
            'docs': [wizard],
            'company_name':main_data['company_name'],
            'students': main_data['students'],
        }



    def get_attendance_data(self,wizard,students):

        academic_year = wizard.academic_year_id
        start_date = academic_year.ay_start_date
        end_date = academic_year.ay_end_date

        if not academic_year:
            today = fields.Date.today()
            current_year = today.year
            if today.month > 7:
                start_date = fields.Date.from_string(f'{current_year}-08-01')
                end_date = fields.Date.from_string(f'{current_year + 1}-07-31')
            else:
                start_date = fields.Date.from_string(f'{current_year - 1}-08-01')
                end_date = fields.Date.from_string(f'{current_year}-07-31')

        attendance_data = {}
        permitted_absences = {}
        
        for student in students:
            attendance_lines = self.env['education.attendance.line'].sudo().search([
                ('student_id', '=', student.id),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
            ])
            attendance_data[student.id] = attendance_lines

            permitted_absences_records = self.env['mc.student.permitted.absence'].sudo().search([
                ('student_id', '=', student.id)
            ])
            permitted_absences[student.id] = permitted_absences_records

        return attendance_data, start_date, end_date, permitted_absences

    def process_attendance_data(self,wizard, attendance_lines, start_date, end_date, permitted_absences):
        result = {}

        days_off = set()
        if wizard.grade_id and wizard.grade_id.educational_stages:
            off_days_per_stage = self.env['mc.timetable'].sudo().search([
                ('educational_stage_id', '=', wizard.grade_id.educational_stages.id)
            ], limit=1)
            if off_days_per_stage:
                days_off.update(filter(None, [off_days_per_stage.holiday_one, off_days_per_stage.holiday_two]))

        days_off = {str(day) for day in days_off}

        vacation_days = [
            (10, 6),
            (1, 7),
            (1, 25),
        ]

        for student_id in attendance_lines.keys():
            result[student_id] = {}
            current_date = start_date
            while current_date <= end_date:
                month_name = current_date.strftime('%B')
                if month_name not in result[student_id]:
                    result[student_id][month_name] = {
                        'days': {},
                        'unexcused_count': 0,
                        'excused_count': 0,
                        'total_days': 0,
                        'attended_days': 0,
                        'vacation_days': 0,
                        'off_days': 0
                    }

                day = current_date.day
                weekday = str(current_date.weekday())
                month_num = current_date.month
                is_vacation_day = (month_num, day) in vacation_days
                is_off_day = weekday in days_off

                result[student_id][month_name]['days'][day] = {
                    'attended': False,
                    'excused': False,
                    'unexcused': False,
                    'vacation': is_vacation_day,
                    'off': is_off_day
                }

                result[student_id][month_name]['total_days'] += 1
                if is_vacation_day:
                    result[student_id][month_name]['vacation_days'] += 1
                if is_off_day:
                    result[student_id][month_name]['off_days'] += 1

                current_date += timedelta(days=1)

            for line in attendance_lines[student_id]:
                month_name = line.date.strftime('%B')
                day = line.date.day

                if line.date < start_date or line.date > end_date:
                    continue

                is_vacation_day = result[student_id][month_name]['days'][day]['vacation']
                is_off_day = result[student_id][month_name]['days'][day]['off']

                if line.present_morning:
                    result[student_id][month_name]['days'][day]['attended'] = True
                    result[student_id][month_name]['attended_days'] += 1
                elif line.sickness_absence and not is_vacation_day and not is_off_day:
                    result[student_id][month_name]['days'][day]['excused'] = True
                    result[student_id][month_name]['excused_count'] += 1
                elif not is_vacation_day and not is_off_day:
                    result[student_id][month_name]['days'][day]['unexcused'] = True
                    result[student_id][month_name]['unexcused_count'] += 1

        for student_id in result.keys():
            result[student_id]['summary'] = {
                'total_days': sum(month_data['total_days'] for month_data in result[student_id].values()
                                  if isinstance(month_data, dict) and 'total_days' in month_data),
                'attended_days': sum(month_data['attended_days'] for month_data in result[student_id].values()
                                     if isinstance(month_data, dict) and 'attended_days' in month_data),
                'unexcused_days': sum(month_data['unexcused_count'] for month_data in result[student_id].values()
                                      if isinstance(month_data, dict) and 'unexcused_count' in month_data),
                'excused_days': sum(month_data['excused_count'] for month_data in result[student_id].values()
                                    if isinstance(month_data, dict) and 'excused_count' in month_data),
                'vacation_days': sum(month_data['vacation_days'] for month_data in result[student_id].values()
                                     if isinstance(month_data, dict) and 'vacation_days' in month_data),
                'off_days': sum(month_data['off_days'] for month_data in result[student_id].values()
                                if isinstance(month_data, dict) and 'off_days' in month_data)
            }

        return result

    def _generate_report(self,wizard):
        students = self.env['education.student'].sudo().search([
            ('grade_id', '=', wizard.grade_id.id),
            ('class_division_id', '=', wizard.class_division_id.id),
        ])
         
        attendance_lines, start_date, end_date, permitted_absences = self.get_attendance_data(wizard,students)
        attendance_data = self.process_attendance_data(wizard,attendance_lines, start_date, end_date, permitted_absences)
        

        students_data = []
        for student in students:
            print(f"Attendance for {student.name}: {attendance_data.get(student.id)}")
            permitted_list = []
            for rec in permitted_absences.get(student.id, []):
                permitted_list.append({
                    'start_date': rec.start_date,
                    'end_date': rec.end_date,
                    'days_count': rec.days_count,
                    'reason': rec.reason_id.name or '--'
                })

            students_data.append({
                'id': student.id,
                'name': student.full_english_name,
                'birth_date': student.date_of_birth or '--',
                'grade': wizard.grade_id.name or '--',
                'class': wizard.class_division_id.name or '--',
                'guardian_name': student.guardian or '--',
                'guardian_job': student.guardian or '--',
                'guardian_address': student.detailed_address or '--',
                'attendance': attendance_data.get(student.id, {}),
                'permitted_absences': permitted_list,
            })

        return {
            'company_name': wizard.company_id.name,
            'students': students_data,
        }
