from odoo import models, fields, api
from datetime import timedelta
from collections import defaultdict


class StudentsAbsenceDayAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_students_absence_days_report'
    _description = 'Students Absence Day Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['students.absence.days.wizard'].browse(docids[0])
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_absence_data(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'students.absence.days.wizard',
            'docs': [wizard],
            
            'company_name': main_data['company_name'],
            'result': main_data['result'],
            'date_from': main_data['date_from'],
            'date_to': main_data['date_to'],
            'grade': main_data['grade'],
            'class': main_data['class'],
            'total': main_data['total'],
            'total_absence_days': main_data['total_absence_days'],
        }

    def _get_absence_data(self, wizard):
        result = []
        
        if not wizard.grade_id:
            return {
                'company_name': '',
                'result': result,
                'date_from': None,
                'date_to': None,
                'grade': '',
                'class': None,
                'total': 0,
                'total_absence_days': 0
            }
        
        # Search in Attendence Line by class_id which is the grade and absent -> to get the students
        domain = [
            ('class_id', '=', wizard.grade_id.id),
            ('present_morning', '=', False),
            ('date', '>=', wizard.date_from),
            ('date', '<=', wizard.date_to),
        ]
        
        # Customize domain with class divsion if it is set
        if wizard.class_division_id:
            domain.append(('division_id', '=', wizard.class_division_id.id))
        
        # Customize domain with permitted absence if it is set
        if wizard.permitted_absence:
            domain.append(('sickness_absence', '=', True))
        
        grade_lines = self.env['education.attendance.line'].sudo().search(domain)
        
        # Collecting date for each student
        student_absences = defaultdict(lambda: {"name": "", "grade": "", "class": "", "dates": [], "count": 0})
        
        total_absence_days = 0
        
        for line in grade_lines:
            student = line.student_id
            student_absences[student.id]["name"] = student.full_arabic_name
            student_absences[student.id]["grade"] = line.class_id.name
            student_absences[student.id]["class"] = line.division_id.name if line.division_id else "-"
            student_absences[student.id]["dates"].append(line.date)
            student_absences[student.id]["count"] += 1
            
            total_absence_days += 1
        
        result = [
            {
                "name": data["name"],
                "grade": data["grade"],
                "class": data["class"],
                "absence_days_count": data["count"],
                "absence_days": ", ".join(map(str, data["dates"]))
            }
            for data in student_absences.values()
        ]
        
        return {
            'company_name': wizard.company_id.name,
            'result': result,
            'date_from': wizard.date_from.strftime('%d/%m/%Y') if wizard.date_from else None,
            'date_to': wizard.date_to.strftime('%d/%m/%Y') if wizard.date_to else None,
            'grade': wizard.grade_id.name,
            'class': wizard.class_division_id.name if wizard.class_division_id else None,
            'total': total_absence_days,
            'total_absence_days': total_absence_days
        }