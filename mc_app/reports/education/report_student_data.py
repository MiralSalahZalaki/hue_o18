
from odoo import models, fields, api
from datetime import datetime, date
from collections import defaultdict


class StudentDataAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_report_student_data'
    _description = 'Student Data Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['student.data.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._generate_report(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'student.data.wizard',
            'docs': [wizard],

            'student_data': main_data['student_data'],
            'company_name': main_data['company_name'],
            'title': main_data['title'],
            'direction': main_data['direction'],
            'age_details': main_data['age_details'],
        }

    
    def _generate_report(self,wizard):
        selected_fields = self._get_selected_fields(wizard)
        student_data = self._prepare_student_data(wizard,wizard.student_resultes, selected_fields)
        direction = "rtl" if wizard.report_view == "ar" else "ltr"
        
        return  {
            'student_data': student_data,
            'company_name': wizard.company_id.name,
            'title': wizard.title or "",
            'direction': direction,
            'age_details':wizard.age_details
        }
        

    
    def _prepare_student_data(self, wizard, students, selected_fields):
        student_data = []
        
        for student in students:
            student_info = {}
            
            for field in selected_fields:
                value = getattr(student, field, '')
                
                # التعامل مع الحقول المرتبطة (Many2one)
                if isinstance(value, models.Model):
                    value = value.name if hasattr(value, 'name') else str(value)
                
                # التعامل مع حقول التاريخ
                elif isinstance(value, (datetime, date)):
                    value = value.strftime('%Y-%m-%d')
                    
                field_label = dict(wizard.FIXED_SELECTION).get(field, field)
                student_info[field_label] = value or '-'
                student_info["Full name"] = student.full_english_name if wizard.display_name == 'en' else student.full_arabic_name,
                if wizard.age_details : 
                    student_info ["age_next_oct"] = student.age_next_oct

            student_data.append(student_info)
        
        return student_data

    
    def _get_selected_fields(self,wizard):

        return [
            field for field in [
                wizard.first_field, wizard.second_field, wizard.third_field,
                wizard.fourth_field, wizard.fifth_field, wizard.sixth_field,
                wizard.seven_field, wizard.eighth_field, wizard.ninth_field, wizard.tenth_field
            ] if field
        ]
    
