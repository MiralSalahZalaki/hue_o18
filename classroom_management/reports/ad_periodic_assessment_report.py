from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ADPeriodicReportAbstract(models.AbstractModel):
    _name = 'report.classroom_management.ad_periodic_assessment_template'
    _description = 'AD Periodic Report Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['periodic.assessment.report.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_periodic_assessment_report_data(wizard)
        
        return {
            'doc_ids': docids,
            'doc_model': 'periodic.assessment.report.wizard',
            'docs': [wizard],
            # Main data from wizard

            'students_data': main_data['students_data'],
            'term': main_data['term'],
            'grade': main_data['grade'],
            'class': main_data['class'],
            'company': main_data['company'],
            'assessment_times': main_data['assessment_times'],
            'assessment_times_count':main_data['assessment_times_count'],
            'total_students': main_data['total_students'],
            'syllabus_data': main_data['syllabus_data'],
            'assessments_data': main_data['assessments_data'],
            'student_view':main_data['student_view'],
         
        }
    
    def _get_periodic_assessment_report_data(self,wizard):
        
            # تحديد domain للطلاب
            student_domain = [
                ('grade_id', '=', wizard.grade_id.id),
                ('company_id', '=', wizard.company_id.id)
            ]
            if wizard.class_id:
                student_domain.append(('class_division_id', '=', wizard.class_id.id))

            students = self.env['education.student'].sudo().search(student_domain, order="seat_number")

            # إذا تم اختيار طلاب محددين، استخدمهم
            if wizard.student_ids:
                students = wizard.student_ids

            # جلب جميع المواد للصف مع تفاصيل التقييمات
            grade_syllabuses = self.env['education.syllabus'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('class_id', '=', wizard.grade_id.id),
            ])

            # إعداد بيانات المواد مع التقييمات
            syllabus_data = []
            assessments_data = {}  # لتخزين تفاصيل التقييمات

            for syllabus in grade_syllabuses:
                syllabus_template = self.env['mc.custom.template'].sudo().search([
                    ('company_id', '=', wizard.company_id.id),
                    ('grade_id', '=', wizard.grade_id.id),
                    ('syllabus_id', '=', syllabus.id),
                    ('school_year_id', '=', wizard.term_id.academic_year_id.id)
                ], limit=1)
                
                if syllabus_template:
                    assessments_list = []
                    for assess in syllabus_template.assessments_category_id:
                        assess_info = {
                            'id': str(assess.id),
                            'name': assess.item.name if hasattr(assess, 'item') and assess.item and hasattr(assess.item, 'name') and assess.item.name else 'N/A',
                            'max_score': assess.max_score if hasattr(assess, 'max_score') else 0.0,
                            'hidden_student_report' :  assess.item.hidden_student_report if hasattr(assess, 'item') and assess.item and hasattr(assess.item, 'hidden_student_report') and assess.item.hidden_student_report else False,

                        }
                        assessments_list.append(assess_info)
                        assessments_data[str(assess.id)] = assess_info

                    syllabus_data.append({
                        'syllabus_id': str(syllabus.id),
                        'syllabus_name': syllabus.name,
                        'is_elective': syllabus.elective,
                        'assessments': assessments_list,
                    })

            students_data = []
            
            for index, student in enumerate(students, 1):
                # جلب المواد الاختيارية المسجلة للطالب
                elective_syllabuses = self.env['mc.elective.syllabus.students'].sudo().search([
                    ('student_id', '=', student.id),
                    ('company_id', '=', wizard.company_id.id),
                    ('grade_id', '=', wizard.grade_id.id)
                ]).mapped('syllabus_id.id')

                student_data = {
                    'serial_no': index,
                    'name': student.full_english_name,
                    'grade_name': student.grade_id.name,
                    'class_id': student.class_division_id.name if student.class_division_id else '',
                    'seat_number': getattr(student, 'seat_number', '') or '',
                    'registered_subjects': [str(syllabus_id) for syllabus_id in elective_syllabuses],
                    'assessment_times_data': []  # بيانات كل فترة تقييم منفردة
                }

                # لكل فترة تقييم، اجمع البيانات منفردة
                for assessment_time in wizard.assessments_times:
                    # جلب سجلات درجات الطالب لهذه الفترة فقط
                    st_acc_records = self.env['acc.student.monthly.grades'].sudo().search([
                        ('company_id', '=', wizard.company_id.id),
                        ('student_id', '=', student.id),
                        ('assesment_time', '=', assessment_time.id),
                        ('grade_id', '=', wizard.grade_id.id),
                        ('class_id', '=', student.class_division_id.id)
                    ])

                    # جلب أيام الغياب لهذه الفترة
                    absence_days = self.env['education.attendance.line'].sudo().search_count([
                        ('company_id', '=', wizard.company_id.id),
                        ('student_id', '=', student.id),
                        ('class_id', '=', wizard.grade_id.id),
                        ('division_id', '=', student.class_division_id.id),
                        ('date', '>=', assessment_time.start_date),
                        ('date', '<=', assessment_time.end_date),
                        ('present_morning', '=', False),
                        ('sickness_absence', '=', False)
                    ]) if assessment_time.start_date and assessment_time.end_date else 0

                    subjects_results = {}
                    
                    # معالجة نتائج الطالب لهذه الفترة
                    for st_acc_record in st_acc_records:
                        for subject_line in st_acc_record.subject_line_ids:
                            subject_id = str(subject_line.syllabus_id.id)
                            syllabus = subject_line.syllabus_id
                            
                            # تجاهل المواد الاختيارية غير المسجلة
                            if syllabus.elective and subject_id not in student_data['registered_subjects']:
                                continue

                            assessments_scores = {}
                            for assess_line in subject_line.assessment_line_ids:
                                assess_key = str(assess_line.assessment_id.id)
                                assessments_scores[assess_key] = {
                                    'score': assess_line.score or 0.0,
                                    'max_score': assess_line.max_score or 0.0
                                }
                            
                            subjects_results[subject_id] = {
                                'subject_name': syllabus.name,
                                'assessments': assessments_scores,
                                'total': subject_line.total_subject_score or 0.0,
                                'max_score': subject_line.total_subject_max or 0.0,
                            }

                    # إضافة المواد المفقودة بدرجات صفر
                    for syllabus_info in syllabus_data:
                        subject_id = syllabus_info['syllabus_id']
                        
                        # تجاهل المواد الاختيارية غير المسجلة
                        if syllabus_info['is_elective'] and subject_id not in student_data['registered_subjects']:
                            continue
                        
                        if subject_id not in subjects_results:
                            # إضافة تقييمات فارغة لكل assessment
                            empty_assessments = {}
                            for assess_info in syllabus_info['assessments']:
                                empty_assessments[assess_info['id']] = {
                                    'score': 0.0,
                                    'max_score': assess_info['max_score']
                                }
                            
                            subjects_results[subject_id] = {
                                'subject_name': syllabus_info['syllabus_name'],
                                'assessments': empty_assessments,
                                'total': 0.0,
                                'max_score': 0.0,
                            }

                    # إضافة بيانات هذه الفترة للطالب
                    student_data['assessment_times_data'].append({
                        'assessment_time': assessment_time.name,
                        'absence_days': absence_days,
                        'subjects_results': subjects_results
                    })

                students_data.append(student_data)

            return {
                'students_data': students_data,
                'term': wizard.term_id,
                'grade': wizard.grade_id,
                'class': wizard.class_id,
                'company': wizard.company_id,
                'assessment_times': wizard.assessments_times,
                'assessment_times_count': len(wizard.assessments_times),
                'total_students': len(students_data),
                'syllabus_data': syllabus_data,
                'assessments_data': assessments_data,
                'student_view':wizard.student_view,
            }
    
