from odoo import models, fields, api
from odoo.exceptions import ValidationError


class IGMonthlyReportAbstract(models.AbstractModel):
    _name = 'report.classroom_management.ig_monthly_report_template'
    _description = 'IG Monthly Report Abstract Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['ig.monthly.report.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_ig_monthly_report_data(wizard)
        
        return {
            'doc_ids': docids,
            'doc_model': 'ig.monthly.report.wizard',
            'docs': [wizard],
            # Main data from wizard
            'students_data': main_data['students_data'],
            'term': main_data['term'],
            'grade': main_data['grade'],
            'class': main_data['class'],
            'company': main_data['company'],
            'top_rank': main_data['top_rank'],
            'assessment_times': main_data['assessment_times'],
            'assessment_times_count': main_data['assessment_times_count'],
            'total_students': main_data['total_students'],
            'grade_syllabuses': main_data['grade_syllabuses'],
        }

    def _get_ig_monthly_report_data(self, wizard):
        """Get the main report data"""
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
        ], order='sequence')
    
        students_data = []
        
        for index, student in enumerate(students, 1):
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
                'assessment_times_data': []  # قائمة لحفظ بيانات كل assessment time
            }

            # لكل assessment time نبني جدول منفصل
            for assessment_time in wizard.assessments_times:
                # جلب records الدرجات لهذا الطالب والفترة المحددة
                eval_records = self.env['mc.evaluation.grades'].sudo().search([
                    ('grade_id', '=', wizard.grade_id.id),
                    ('assessments_times', '=', assessment_time.id),
                    ('state', '=', 'done')  # فقط السجلات المكتملة
                ])
                
                # بناء قائمة المواد مع الدرجات لهذا assessment time
                subjects_data = []
                total_score = 0
                
                for seq, syllabus in enumerate(grade_syllabuses):
                    if syllabus.elective and syllabus.id not in elective_syllabuses:
                        continue
                    subject_data = {
                        'sequence': seq,
                        'subject_name': syllabus.name,
                        'score': 0  
                    }
                    
                    # البحث عن درجة الطالب في هذه المادة لهذا assessment time
                    for eval_record in eval_records:
                        if eval_record.syllabus_id.id == syllabus.id:
                            # البحث عن الطالب في قائمة طلاب السجل
                            student_line = eval_record.student_list.filtered(
                                lambda line: line.student_id.id == student.id and line.check
                            )
                            if student_line:
                                eval_score = float(student_line[0].score) or 0.00
                                eval_max = float(eval_record.custom_max_score) or 1.00  

                                template = self.env['mc.custom.template'].sudo().search([
                                    ('syllabus_id', '=', syllabus.id),
                                    ('grade_id', '=', wizard.grade_id.id),
                                    ('company_id', '=', wizard.company_id.id),
                                    ('school_year_id', '=', wizard.term_id.academic_year_id.id)
                                ], limit=1)

                                template_max = 0
                                if template and eval_record.distribution_id:
                                    dist_template = template.custom_grade_distribution_template.filtered(
                                        lambda d: d.id == eval_record.distribution_id.id
                                    )
                                    if dist_template:
                                        if dist_template.report_mark > 0 :
                                            template_max = dist_template.report_mark
                                        else:
                                            template_max = float(dist_template[0].maximum) or 0.00

                                if template_max > 0:
                                    subject_data['score'] = (eval_score * template_max ) / eval_max
                                else:
                                    subject_data['score'] = eval_score  # fallback لو مفيش تمبلت
                                total_score += float(subject_data['score'])
                                break

                    
                    # التحقق من المواد الاختيارية
                    if syllabus.elective:
                        # إذا كانت المادة اختيارية والطالب غير مسجل فيها
                        if syllabus.id not in elective_syllabuses:
                            subject_data['score'] = 0  # أو يمكن تجاهلها
                    
                    subjects_data.append(subject_data)
                
                # إضافة بيانات هذا assessment time للطالب
                assessment_data = {
                    'assessment_time_name': assessment_time.name,
                    'assessment_time_id': assessment_time.id,
                    'subjects': subjects_data,
                    'total_score': total_score
                }
                
                student_data['assessment_times_data'].append(assessment_data)
            
            students_data.append(student_data)

        assessment_times = []
        for time in wizard.assessments_times:
            assessment_times.append({
                'id': time.id,
                'name': time.name,
                'start_date': time.start_date,
                'end_date': time.end_date,
            })
        return {
            'students_data': students_data,
            'term': wizard.term_id,
            'grade': wizard.grade_id,
            'class': wizard.class_id,
            'company': wizard.company_id,
            'top_rank': wizard.top_rank,
            'assessment_times': assessment_times,
            'assessment_times_count': len(wizard.assessments_times),
            'total_students': len(students_data),
            'grade_syllabuses': grade_syllabuses,
        }