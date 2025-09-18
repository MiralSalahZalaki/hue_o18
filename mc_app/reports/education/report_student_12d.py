
from odoo import models, fields, api
from datetime import datetime, date
from collections import defaultdict


class Student12DAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_report_student_12d'
    _description = 'Student 12D Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['student.12d.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._prepare_12d_report(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'student.12d.wizard',
            'docs': [wizard],

            'students_data': main_data['students_data'],
            'title': main_data['title'],
            'company_name': main_data['company_name'],

     
        }

    def _prepare_12d_report(self,wizard):
        domain = []

        if wizard.grade_id:
            domain.append(('grade_id', '=', wizard.grade_id.id))
            
        if wizard.class_division_id:
            domain.append(('class_division_id', '=', wizard.class_division_id.id))
            
        if wizard.gender:
            domain.append(('gender', '=', wizard.gender))  
            
        if wizard.birth_date:
            domain.append(('date_of_birth', '=', wizard.birth_date))
            
        if wizard.student_status and wizard.student_status != 'all':
            domain.append(('student_status', '=', wizard.student_status))

        if wizard.first_name:
            domain += ['|',
                    ('full_english_name', 'ilike', wizard.first_name),
                    ('full_arabic_name', 'ilike', wizard.first_name)]
            
        if wizard.full_name:
            domain += ['|',
                    ('full_english_name', 'ilike', wizard.full_name),
                    ('full_arabic_name', 'ilike', wizard.full_name)]
        
        if wizard.surname:
            domain += ['|',
                    ('full_english_name', 'ilike', '%' + wizard.surname),
                    ('full_arabic_name', 'ilike', '%' + wizard.surname)]

        # Apply sorting
        order_field = wizard.order_by or 'id'
        students = self.env['education.student'].sudo().search(domain, order=order_field)

        students_data = []
        for student in students:
            students_data.append({
                'name': student.full_english_name if wizard.display_name == 'en' else student.full_arabic_name,
                'full_english_name': student.full_english_name,
                'full_arabic_name': student.full_arabic_name,
                'age_next_oct': student.age_next_oct,
                'date_of_birth': student.date_of_birth,
                'religion_id': student.religion_id.name if student.religion_id else '',
                'student_status': student.student_status,
                'street': student.street,
                'nationality_id': student.nationality_id.name if student.nationality_id else '',
            })

        return {
            'students_data': students_data,
            'title': wizard.title or "",
            'company_name': wizard.company_id.name,
        }
