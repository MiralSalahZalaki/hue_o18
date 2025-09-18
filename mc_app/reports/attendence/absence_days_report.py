
from odoo import models, fields, api
from datetime import timedelta
from collections import defaultdict


class AbsenceDayAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_absence_days_report'
    _description = 'Absence Day Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['absence.days.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_absence_data(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'absence.days.wizard',
            'docs': [wizard],

            'result': main_data['result'],
            'company_name': main_data['company_name'],

        }

    def _get_absence_data(self,wizard):
        result = []

        students = self.env['education.student'].sudo().search([
            ('grade_id', '=', wizard.grade_id.id),
            ('class_division_id', '=', wizard.class_division_id.id),
        ])

        if not students:
            return result

        for student in students:
            absence_lines = self.env['education.attendance.line'].sudo().search([
                ('student_id', '=', student.id),
                ('present_morning', '=', False)
            ])

            # حساب عدد الأيام المعذورة وغير المعذورة قبل الدخول في اللوب
            excused_count = sum(1 for line in absence_lines if line.sickness_absence)
            unexcused_count = len(absence_lines) - excused_count

            for line in absence_lines:
                record = {
                    'student_name': student.full_english_name,
                    'grade': student.grade_id.name,
                    'class': student.class_division_id.name,
                    'date_of_birth': student.date_of_birth,
                    'guardian_name': student.guardian,
                    'guardian_address': student.detailed_address,
                    'guardian_job': student.guardian_profession, 

                    'date': line.date.strftime("%d/%m/%Y"),
                    'state': 'Excused' if line.sickness_absence else 'Unexcused',
                    'reasons': line.sickness_reason.name if line.sickness_absence else '---',
                    
                    # القيم الصحيحة للغياب والمعذور
                    'excused_count': excused_count,
                    'unexcused_count': unexcused_count,
                }
                result.append(record)

        return {
            'result': result,
            'company_name': wizard.company_id.name,
        }

