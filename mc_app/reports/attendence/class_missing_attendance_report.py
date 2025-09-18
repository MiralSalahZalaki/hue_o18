
from odoo import models, fields, api
from datetime import timedelta
from collections import defaultdict


class ClassMissingAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_class_missing_attendance_report'
    _description = 'Class Missing Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['class.missing.attendence.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._prepare_report_data(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'class.missing.attendence.wizard',
            'docs': [wizard],

            'wizard_id': main_data['wizard_id'],
            'grade': main_data['grade'],
            'class': main_data['class'],
            'date_from': main_data['date_from'],
            'date_to': main_data['date_to'],
            'company_name': main_data['company_name'],
            'attendance_data': main_data['attendance_data'],
            'students': main_data['students'],
            'total_students': main_data['total_students'],
            'summary': main_data['summary']  # Add summary data to the report context

        }

    def _get_current_academic_year(self):
        current_year = self.env['education.academic.year'].sudo().search([('current', '=', True)], limit=1)
        return current_year.id if current_year else False

    def _get_vacation_days(self):
        """Return list of vacation days as (month, day) tuples"""
        return [
            (10, 6),  # 6 أكتوبر
            (1, 7),  # 7 يناير
            (1, 25),  # 25 يناير
        ]

    def _get_off_days(self,wizard):
        """Get off days from timetable"""
        days_off = set()
        if wizard.grade_id and wizard.grade_id.educational_stages:
            off_days_per_stage = self.env['mc.timetable'].sudo().search([
                ('educational_stage_id', '=', wizard.grade_id.educational_stages.id)
            ], limit=1)
            if off_days_per_stage:
                days_off.update(filter(None, [off_days_per_stage.holiday_one, off_days_per_stage.holiday_two]))
        return {day for day in days_off}

    def _get_date_range(self,wizard):
        """Get academic year date range"""
        academic_year = wizard.academic_year_id
        if academic_year:
            return academic_year.ay_start_date, academic_year.ay_end_date
        else:
            today = fields.Date.today()
            current_year = today.year
            if today.month > 7:
                return (fields.Date.from_string(f'{current_year}-08-01'),
                        fields.Date.from_string(f'{current_year + 1}-07-31'))
            return (fields.Date.from_string(f'{current_year - 1}-08-01'),
                    fields.Date.from_string(f'{current_year}-07-31'))

    def _get_class_students(self,wizard):
        """Get students in the selected class"""
        return self.env['education.student'].sudo().search([
            ('grade_id', '=', wizard.grade_id.id),
            ('class_division_id', '=', wizard.class_division_id.id),
        ])

    def _process_attendance_data(self,wizard):
        """Process attendance data with correct state logic for summary calculation"""
        start_date, end_date = self._get_date_range(wizard)
        students = self._get_class_students(wizard)
        vacation_days = self._get_vacation_days()
        off_days = self._get_off_days(wizard)

        # Get existing attendance records
        attendance_records = self.env['education.attendance'].sudo().search([
            ('division_id', '=', wizard.class_division_id.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
        ])

        # Group attendance by date
        attendance_by_date = {rec.date.strftime('%Y-%m-%d'): rec for rec in attendance_records}

        # Prepare monthly report structure
        result = {}

        # Initialize summary counters
        summary = {
            'total_days': 0,
            'attended_days': 0,
            'missing_days': 0,
            'vacation_days': 0,
            'off_days': 0,
            'draft_days': 0
        }

        current_date = start_date
        while current_date <= end_date:
            month_name = current_date.strftime('%B')
            if month_name not in result:
                result[month_name] = {
                    'days': {},
                    'unexcused_count': 0,
                    'excused_count': 0
                }
            current_date += timedelta(days=30)

        # Process each day
        current_date = start_date
        while current_date <= end_date:
            month_name = current_date.strftime('%B')
            day = current_date.day
            weekday = str(current_date.weekday())
            month_num = current_date.month
            date_str = current_date.strftime('%Y-%m-%d')

            is_vacation_day = (month_num, day) in vacation_days
            is_off_day = weekday in off_days

            day_data = {
                'date': current_date,
                'state': 'draft',  # Default state
                'vacation': is_vacation_day,
                'off': is_off_day,
                'total_students': len(students)
            }

            # Increment total days counter
            summary['total_days'] += 1

            if date_str in attendance_by_date:
                attendance = attendance_by_date[date_str]
                if attendance.state == 'draft':
                    day_data['draft'] = True
                    summary['draft_days'] += 1
                elif attendance.state == 'done':
                    # Check attendance lines to determine if all students are present
                    all_present_morning = all(line.present_morning for line in attendance.attendance_line_ids)
                    if all_present_morning:
                        day_data['attended'] = True
                        summary['attended_days'] += 1
                    else:
                        day_data['missing'] = True
                        summary['missing_days'] += 1
            else:
                # For days without attendance records
                if not is_vacation_day and not is_off_day:
                    day_data['state'] = 'missing'
                    # Don't mark all days without attendance as missing automatically
                    # Only mark specific days as missing based on business logic

            # Handle vacation and off days
            if is_vacation_day:
                summary['vacation_days'] += 1
                day_data['vacation'] = True

            if is_off_day:
                summary['off_days'] += 1
                day_data['off'] = True

            result[month_name]['days'][day] = day_data
            current_date += timedelta(days=1)

        return result, students, start_date, end_date, summary

    def _prepare_report_data(self,wizard):
        """Prepare data for the report"""
        attendance_data, students, start_date, end_date, summary = self._process_attendance_data(wizard)
        return {
            'wizard_id': wizard.id,
            'grade': wizard.grade_id.name,
            'class': wizard.class_division_id.name,
            'date_from': start_date.strftime('%d/%m/%Y'),
            'date_to': end_date.strftime('%d/%m/%Y'),
            'company_name': wizard.company_id.name,
            'attendance_data': attendance_data,
            'students': students,
            'total_students': len(students),
            'summary': summary  # Add summary data to the report context
        }
