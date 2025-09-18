
from odoo import models, fields, api
import random  # For employee codes as text


class RevealerReportAbstract(models.AbstractModel):
    _name = 'report.mc_app.template_revealer_reports'
    _description = 'Revealer Report Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['revealer.report.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._prepare_report_data(wizard)
        
        return {
            'doc_ids': docids,
            'doc_model': 'revealer.report.wizard',
            'docs': [wizard],

            # Main data
            'department_data': main_data['department_data'],
            'company_name': main_data['company_name'],
            'total_sessions': main_data['total_sessions'],


        }
        
    def _prepare_report_data(self, wizard):
        department_list = []
        
        departments_per_school = self.env['hr.department'].sudo().search([('company_id', '=', wizard.company_id.id)])
        
        for dept in departments_per_school:
            employees_per_dept = self.env['hr.employee'].sudo().search([('department_id', '=', dept.id)])
            
            faculty_members = []
            
            for employee in employees_per_dept:
                faculty_id = self.env['education.faculty'].sudo().search([('employee_id', '=', employee.id)], limit=1)
                
                if not faculty_id:
                    continue
                    
                faculty_name = faculty_id.name
                total_sessions = 0
                timetable_data = {}  # إعادة التهيئة لكل أستاذ
                
                # إذا تم اختيار مرحلة تعليمية، نطبق الفلترة بناءً على هذه المرحلة
                if wizard.stage_id:
                    # البحث عن الصفوف المرتبطة بالمرحلة التعليمية المحددة
                    classes = self.env['education.class'].sudo().search([
                        ('educational_stages', '=', wizard.stage_id.id)
                    ])
                    
                    if not classes:
                        continue
                    
                    # البحث عن الفصول المرتبطة بالصف المحددة
                    class_divisions = self.env['education.class.division'].sudo().search([
                        ('class_id', 'in', classes.ids)
                    ])
                    
                    if not class_divisions:
                        continue
                    
                    # البحث عن دروس المعلم في هذه الفصول المحددة
                    syllabus_classes = self.env['mc.syllabus.per.class'].sudo().search([
                        '|',
                        ('faculty_regular_id', '=', faculty_id.id),
                        ('faculty_special_id', '=', faculty_id.id),
                        ('class_division_id', 'in', class_divisions.ids)
                    ])

                else:
                    # No Stage Selected استخدام الكود الأصلي إذا لم يتم اختيار مرحلة تعليمية
                    syllabus_classes = faculty_id.mapped('syllabus_class') + faculty_id.mapped('syllabus_special_class')
                
                if not syllabus_classes:
                    continue
                
                for syllabus in syllabus_classes:
                    sessions = self.env['education.timetable.schedule'].sudo().search([
                        ('syllabus', '=', syllabus.syllabus_id.id),
                        ('class_division_id', '=', syllabus.class_division_id.id)
                    ])
                    
                    total_sessions += len(sessions)
                    
                    for schedule in sessions:
                        day_name = dict(schedule._fields['week_day'].selection).get(schedule.week_day)
                        period = schedule.period_id.name
                        time_from = schedule.time_from
                        time_till = schedule.time_till
                        subject = schedule.syllabus.name

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
                        })
                
                # إضافة المعلم فقط إذا كان لديه جلسات
                if total_sessions > 0:
                    faculty_member = {
                        'name': faculty_name,
                        'employee_code': random.randint(2000, 2999),  # Test
                        'sessions_count': total_sessions,
                    }
                    
                    if not wizard.total_sessions:
                        faculty_member['timetable_data'] = timetable_data
                    
                    faculty_members.append(faculty_member)
            
            # إضافة القسم فقط إذا كان يحتوي على معلمين
            if faculty_members:
                department_list.append({
                    'department_name': dept.name,
                    'faculty_members': faculty_members
                })
        
        return {
            'department_data': department_list,
            'company_name': wizard.company_id.name,
            'total_sessions': wizard.total_sessions,
        }

        