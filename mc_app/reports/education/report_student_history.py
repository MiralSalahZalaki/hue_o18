
from odoo import models, fields, api
from datetime import datetime, date
from collections import defaultdict


class StudentHistoryAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_report_student_history'
    _description = 'Student History Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['student.history.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        

        # Process main data using helper method
        main_data = self._prepare_student_data(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'student.history.wizard',
            'docs': [wizard],

            'student_data': main_data['student_data'], 
            'company_name': main_data['company_name'],
            'student_name' : main_data['student_name'],
            'direction': main_data['direction'],     
        }

    def _prepare_student_data(self,wizard):
        student_data = []

        direction = "ltr"
        if wizard.report_view == "ar" : 
            direction = "rtl"

        if wizard.student_id or wizard.student_code:
            student = wizard.student_id or self.env['education.student'].sudo().search([('student_code', '=', wizard.student_code)], limit=1)

            student_data = [
                {'field_name': 'Student Name', 'field_value': student.full_arabic_name},
                {'field_name': 'Student Code', 'field_value': student.student_code},
                {'field_name': 'Grade', 'field_value': student.grade_id.name if student.grade_id else ''},
                {'field_name': 'Gender', 'field_value': student.gender if student.gender else ''},
                {'field_name': 'Date of birth', 'field_value': student.date_of_birth if student.date_of_birth else ''},
                {'field_name': 'Religion', 'field_value': student.religion_id.name if student.religion_id else ''},
                {'field_name': 'Nationality', 'field_value': student.nationality_id.name if student.nationality_id else ''},
                {'field_name': 'Class History', 'field_value': [
                    {'class_name': history.class_id.class_id.name, 'academic_year': history.academic_year_id.name} 
                    for history in student.class_history_ids
                ] if student.class_history_ids else []},
            ]

        return {
            'student_data': student_data, 
            'company_name': wizard.company_id.name,
            'student_name' : wizard.student_name,
            'direction': direction,
        }