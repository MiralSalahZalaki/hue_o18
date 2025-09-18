from odoo import models, fields, api
from datetime import datetime, date
from collections import Counter

class StudentStatisticAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_report_student_statistics'
    _description = 'Student Statistic Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['student.statistics.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        

        # Process main data using helper method
        main_data = self._prepare_student_statistics(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'student.statistics.wizard',
            'docs': [wizard],

            'report_data' : main_data['report_data'],
            'company_name': main_data['company_name'],
            'direction': main_data['direction'],
    
        }

    def _prepare_student_statistics(self,wizard):
        report_data = []  
        
        direction = "ltr"
        if wizard.report_view == "ar" : 
            direction = "rtl"
        
        if wizard.academic_year_id and wizard.company_id: 
            grade_ids = self.env['education.class'].sudo().search([('school', '=', wizard.company_id.id)], limit=False)

            for grade in grade_ids:
                class_divisions_count = self.env['education.class.division'].sudo().search_count([
                    ('class_id', '=', grade.id),
                    ('academic_year_id', '=', wizard.academic_year_id.id)
                ], limit=False)

                students = self.env['education.student'].sudo().search([
                    ('grade_id', '=', grade.id),
                    ('academic_year_id', '=', wizard.academic_year_id.id)
                ], limit=False)

                ####### Get Ages
                student_ages = students.mapped('age_next_oct')
                student_years = [int(age.split(' year')[0]) for age in student_ages if 'year' in age]

                age_counts = Counter(student_years)

                age_ranges = sorted(set(student_years))  # استخراج القيم الفريدة مرتبة
                age_output = "\n".join(
                                    [f"from {age} to {age+1} : {age_counts.get(age, 0)}" for age in age_ranges]
                                )

                
                ####### Get Nationalities
                nationality_counts = {}

                nationalities = students.mapped('nationality_id.name')
                for nat in nationalities:
                    nationality_counts[nat] = len(students.filtered(lambda s: s.nationality_id.name == nat))
                
                nationality_stats = "\n".join([f"{nat}: {count}" for nat, count in nationality_counts.items()])

                
                male_count = len(students.filtered(lambda s: s.gender == 'male'))
                female_count = len(students.filtered(lambda s: s.gender == 'female'))


                ####### Get Religions
                religion_counts = {}

                religions = students.mapped('religion_id.name')
                for reg in religions:
                    religion_counts[reg] = len(students.filtered(lambda s: s.religion_id.name == reg))
                
                religion_name_count = "\n".join([f"{reg}: {count} \n" for reg, count in religion_counts.items()])

                
                male_count = len(students.filtered(lambda s: s.gender == 'male'))
                female_count = len(students.filtered(lambda s: s.gender == 'female'))


                report_data.append({
                    'Grade': grade.name,
                    'Classes': class_divisions_count,
                    'Males': male_count,
                    'Females': female_count,
                    'Nationlaity' : nationality_stats,
                    'Religion' : religion_name_count,
                    'Ages':age_output
                })

            return {
                'report_data' : report_data,
                'company_name': wizard.company_id.name,
                'direction': direction,
            }
