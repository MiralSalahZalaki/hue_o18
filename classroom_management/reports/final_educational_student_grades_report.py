from odoo import models, fields, api
from odoo.exceptions import ValidationError
from collections import defaultdict



class FinalEducationalStudentGradeAbstract(models.AbstractModel):
    _name = 'report.classroom_management.final_educational_student_template'
    _description = 'Final Educational Student Grade Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['final.educational.student.grades.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._generate_report(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'final.educational.student.grades.wizard',
            'docs': [wizard],
            # Main data from wizard


            'classes': main_data['classes'],
            'grading_method': main_data['grading_method'],
            'assessments_times': main_data['assessments_times'],
            'assessments_data': main_data['assessments_data'],
            'distributions_data': main_data['distributions_data'],
            'arabic_report': main_data['arabic_report'],
            'year': main_data['year'],
            'term_en': main_data['term_en'],
            'term_ar': main_data['term_ar'],
            'syllabus_en': main_data['syllabus_en'],
            'syllabus_ar': main_data['syllabus_ar'],
            'garde_en': main_data['garde_en'],
            'garde_ar': main_data['garde_ar'],
            'ministerial_number': main_data['ministerial_number'],
          
        }


    def _calculate_student_grades(self,wizard, student, custom_template, assessments_times_ids):   
        student_assessments = []
        student_distributions = []
        
        # حساب درجات الـ Assessments - نفس منطق Abstract Report
        if custom_template and custom_template.assessments_category_id:
            for assessment_time in assessments_times_ids:
                time_assessments = []
                
                for assessment in custom_template.assessments_category_id:
                    # domain للبحث في mc.evaluation.grades لهذا الـ time تحديداً
                    eval_domain = [
                        ('company_id', '=', wizard.company_id.id),
                        ('assessments_times', '=', assessment_time.id),  # time محدد
                        ('grade_id', '=', wizard.grade_id.id),
                        ('syllabus_id', '=', wizard.syllabus_id.id),
                        ('assessments_category_id', '=', assessment.id),
                        ('state', '=', 'done'),
                    ]
                    if wizard.class_id:
                        eval_domain.append(('class_id', '=', wizard.class_id.id))
                    
                    # جلب eval_grades لهذا الـ time فقط
                    eval_grades = self.env['mc.evaluation.grades'].sudo().search(eval_domain)
                    
                    # حساب الدرجة لهذا الـ assessment في هذا الـ time فقط
                    final_score = self._calculate_assessment_score_per_time(
                        wizard,student, assessment, eval_grades
                    )
                    
                    time_assessments.append({
                        'assessment_id': assessment.id,
                        'scaled_score': final_score
                    })
                
                if time_assessments:
                    student_assessments.append({
                        'time': assessment_time.name,
                        'assessments': time_assessments
                    })
        
        # حساب درجات الـ Distributions (نفس الكود الموجود)
        if custom_template and custom_template.custom_grade_distribution_template:
            distributions = custom_template.custom_grade_distribution_template.filtered(
                lambda d: hasattr(d, 'item') and hasattr(d.item, 'assessment') and not d.item.assessment
            )
            
            for dist in distributions:
                # domain للبحث في mc.control.grades
                control_domain = [
                    ('company_id', '=', wizard.company_id.id),
                    ('grade_id', '=', wizard.grade_id.id),
                    ('syllabus_id', '=', wizard.syllabus_id.id),
                    ('distribution_id', '=', dist.id),
                    ('state', '=', 'done'),
                ]
                
                # جلب control_grades
                control_grades = self.env['mc.control.grades'].sudo().search(control_domain)
                
                # حساب الدرجة للـ distribution
                dist_score = self._calculate_distribution_score(
                    wizard,student, dist, control_grades
                )
                
                student_distributions.append({
                    'dis_id': str(dist.id),
                    'score': dist_score
                })

        return student_assessments, student_distributions

    def _calculate_assessment_score_per_time(self,wizard, student, assessment, eval_grades):
        
        max_score = assessment.max_score or 0
        category_scores = []
        
        # جمع جميع الدرجات لهذا الـ assessment في هذا الـ time فقط
        for grade in eval_grades:
            student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
            
            if student_record and student_record[0].check:
                if student_record[0].score:
                    actual_score = float(student_record[0].score)
                    eval_max_score = float(grade.custom_max_score) if grade.custom_max_score else max_score
                    
                    # تطبيق نفس منطق Abstract Report
                    if eval_max_score > 0:
                        normalized_score = (actual_score / eval_max_score) * max_score
                        category_scores.append(normalized_score)
                    else:
                        category_scores.append(0.0)
                else:
                    category_scores.append(0.0)
        
        # حساب متوسط الدرجات في هذا الـ time فقط
        if category_scores:
            return sum(category_scores) / len(category_scores)
        else:
            return 0.0

    def _calculate_assessment_score(self,wizard, student, assessment, eval_grades, custom_template):
        """حساب درجة الـ assessment للطالب (نفس المنطق اللي كان موجود)"""
        
        max_score = assessment.max_score or 0
        
        # جلب كل درجات الطالب
        all_scores = [
            float(student_record.score) for grade in eval_grades
            for student_record in grade.student_list.filtered(lambda s: s.student_id.id == student.id)
            if student_record.score
        ]
        
        # البحث عن best_of من template
        best_of = 0
        if custom_template:
            distribution_with_assessment = custom_template.custom_grade_distribution_template.filtered(
                lambda d: d.item.id == assessment.item.id and d.item.assessment
            )
            if distribution_with_assessment:
                best_of = distribution_with_assessment[0].best_of or 0
            else:
                best_of = assessment.best_of or 0
        else:
            best_of = assessment.best_of or 0
        
        # حساب الدرجة النهائية
        if best_of > 0:
            # طريقة الـ best_of
            top_scores = sorted(all_scores, reverse=True)[:best_of]
            final_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
        else:
            # طريقة الـ time-based
            scores_by_assessment_time = {}
            for grade in eval_grades:
                student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
                eval_max_score = float(grade.custom_max_score) or max_score
                assessment_time_id = grade.assessments_times.id
                
                if assessment_time_id not in scores_by_assessment_time:
                    scores_by_assessment_time[assessment_time_id] = []
                
                if student_record:
                    if student_record[0].check:
                        if student_record[0].score:
                            scaled_score = (float(student_record[0].score) / eval_max_score) * max_score
                            scores_by_assessment_time[assessment_time_id].append(float(scaled_score))
                        else:
                            scores_by_assessment_time[assessment_time_id].append(0.0)
                    else:
                        scores_by_assessment_time[assessment_time_id].append(0.0)
                else:
                    scores_by_assessment_time[assessment_time_id].append(0.0)
            
            avg_scores = [sum(scores) / len(scores) for scores in scores_by_assessment_time.values() if scores]
            final_score = sum(avg_scores) / len(avg_scores) if avg_scores else 0.0
        
        return final_score

    def _calculate_distribution_score(self,wizard, student, distribution, control_grades):
        """حساب درجة الـ distribution للطالب مع التعايير (scaled)"""
        
        total_score = 0.0
        count = 0
        
        # الحد الأقصى للدرجة من الـ distribution
        max_score = getattr(distribution, 'maximum', 0)
        
        for grade in control_grades:
            student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
            if student_record and student_record.score:
                # الحد الأقصى لدرجة هذا الـ control grade
                grade_max_score = float(grade.custom_max_score) if hasattr(grade, 'custom_max_score') and grade.custom_max_score else max_score
                
                # الدرجة الفعلية للطالب
                actual_score = float(student_record.score)
                
                # حساب الدرجة المعايرة (scaled)
                if grade_max_score > 0:
                    scaled_score = (actual_score / grade_max_score) * max_score
                else:
                    scaled_score = 0.0
                
                total_score += scaled_score
                count += 1
        
        return total_score / count if count > 0 else 0.0

    def _generate_report(self, wizard):

        # جلب الفصول
        if wizard.class_id:
            classes = [{'id': wizard.class_id.id, 'name': wizard.class_id.name}]
        else:
            all_classes = self.env['education.class.division'].sudo().search([
                ('class_id', '=', wizard.grade_id.id)
            ])
            classes = [{'id': cls.id, 'name': cls.name} for cls in all_classes]

        # جلب assessment times من الترم
        assessments_times_ids = self.env['mc.assessment.times'].sudo().search([
            ('company_id', '=', wizard.company_id.id),
            ('grade_ids', 'in', [wizard.grade_id.id]),
            ('start_date', '>=', wizard.term_id.start_date),
            ('end_date', '<=', wizard.term_id.end_date),
            ('distribution', '=', False)
        ], order='start_date')

        assessments_times = []
        for time in assessments_times_ids:
            assessments_times.append({
                'name': time.name,
                'start_date': time.start_date,
                'end_date': time.end_date,
            })

        # جلب الـ custom template
        custom_template = self.env['mc.custom.template'].sudo().search([
            ('company_id', '=', wizard.company_id.id),
            ('grade_id', '=', wizard.grade_id.id),
            ('syllabus_id', '=', wizard.syllabus_id.id),
        ], limit=1)

        # جلب distributions
        distributions_data = []
        assessments_data = []
        if custom_template:
            distributions = custom_template.custom_grade_distribution_template.filtered(
                lambda d: hasattr(d, 'item') and hasattr(d.item, 'assessment') and not d.item.assessment
            )
            
            for dist in distributions:
                distributions_data.append({
                    'id': str(dist.id),
                    'name': dist.item.name,
                    'weight': getattr(dist, 'weight', 0),
                    'maximum': getattr(dist, 'maximum', 0)
                })

            assessments = custom_template.assessments_category_id
            for assessment in assessments:
                assessments_data.append({
                    'id': assessment.id,
                    'name': assessment.item.name,
                    'maximum': assessment.max_score,
                })

        # جلب grading method
        grading_method_record = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', wizard.grade_id.id)
        ], limit=1)
        grading_method = getattr(grading_method_record, 'grading_method', 'normal') if grading_method_record else 'normal'

        # معالجة كل فصل على حدة
        for cls in classes:
            # جلب طلبة هذا الفصل فقط
            if not wizard.syllabus_id.elective:  # مادة إجبارية
                student_domain = [
                    ('grade_id', '=', wizard.grade_id.id), 
                    ('company_id', '=', wizard.company_id.id),
                    ('class_division_id', '=', cls['id'])
                ]
                students = self.env['education.student'].sudo().search(student_domain, order='seat_number, name')
            else:  # مادة اختيارية
                students = wizard.syllabus_id.students.mapped('student_id')
                students = students.filtered(lambda s: s.class_division_id.id == cls['id'])
                students = students.sorted(key=lambda s: (s.seat_number or '', s.name))
            
            # حساب درجات طلبة هذا الفصل
            students_data = []
            for student in students:
                student_id = student.id
                
                # حساب درجات الطالب
                student_assessments, student_distributions = self._calculate_student_grades(
                    wizard,student, custom_template, assessments_times_ids
                )
                
                # حساب المجاميع
                total_assessments = sum([
                    sum([ass['scaled_score'] for ass in time_data['assessments']])
                    for time_data in student_assessments
                ])
                
                total_distributions = sum([dist['score'] for dist in student_distributions])
                final_total = total_assessments + total_distributions
                
                student_data = {
                    'id': student_id,
                    'en_full_name': getattr(student, 'full_english_name', '') or getattr(student, 'name', ''),
                    'ar_full_name': getattr(student, 'full_arabic_name', '') or getattr(student, 'name', ''),
                    'distributions': student_distributions,
                    'assessments': student_assessments,
                    'total_assessments': total_assessments,
                    'total_distributions': total_distributions,
                    'final_total': final_total
                }
                students_data.append(student_data)
            
            # إضافة قائمة الطلبة لهذا الفصل
            cls['students_data'] = students_data

        return {
            'classes': classes,
            'grading_method': grading_method,
            'assessments_times': assessments_times,
            'assessments_data': assessments_data,
            'distributions_data': distributions_data,
            'arabic_report': wizard.arabic_report,
            'year': getattr(wizard.term_id.academic_year_id, 'name', ''),
            'term_en': getattr(wizard.term_id, 'name', ''),
            'term_ar': getattr(wizard.term_id, 'arabic_name', ''),
            'syllabus_en': getattr(wizard.syllabus_id, 'name', ''),
            'syllabus_ar': getattr(wizard.syllabus_id, 'arabic_name', ''),
            'garde_en': getattr(wizard.grade_id, 'name', ''),
            'garde_ar': getattr(wizard.grade_id, 'arabic_name', ''),
            'ministerial_number': getattr(wizard.grade_id, 'ministerial_number', ''),
        }