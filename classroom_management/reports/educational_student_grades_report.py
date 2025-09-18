from odoo import models, fields, api
from odoo.exceptions import ValidationError
from collections import defaultdict



class EducationalStudentGradesAbstract(models.AbstractModel):
    _name = 'report.classroom_management.educational_student_grades_template'
    _description = 'Educational Student Grades Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Main method to prepare all report data"""
        wizard = self.env['educational.student.grades.wizard'].browse(docids[0])
        
        if not wizard.exists():
            return {}
        
        # Process main data using helper method
        main_data = self._get_educational_student_grades_wizard(wizard)
        return {
            'doc_ids': docids,
            'doc_model': 'educational.student.grades.wizard',
            'docs': [wizard],
            # Main data from wizard

            'classes': main_data['classes'],
            'assessment_times': main_data['assessment_times'],
            'assessment_categories': main_data['assessment_categories'],
            'students_data': main_data['students_data'],
            'distributions': main_data['distributions'],
            'arabic_report': main_data['arabic_report'],
            'year': main_data['year'],
            'term_en': main_data['term_en'],
            'term_ar': main_data['term_ar'],
            'syllabus_en': main_data['syllabus_en'],
            'syllabus_ar': main_data['syllabus_ar'],
            'garde_en': main_data['garde_en'],
            'garde_ar': main_data['garde_ar'],
            'show_avg': main_data['show_avg'],
            'ministerial_number': main_data['ministerial_number'],
            'grading_method': main_data['grading_method'],
          
        }


    def _get_educational_student_grades_wizard(self, wizard):
        # 1- جلب assessment times من الترم
        assessment_times = self.env['mc.assessment.times'].sudo().search([
            ('company_id', '=', wizard.company_id.id),
            ('grade_ids', 'in', [wizard.grade_id.id]),
            ('start_date', '>=', wizard.term_id.start_date),
            ('end_date', '<=', wizard.term_id.end_date),
            ('distribution', '=', False)
        ], order='start_date')

        # 2- جلب evaluation records لكل assessment time
        evaluation_domain = [
            ('syllabus_id', '=', wizard.syllabus_id.id),
            ('grade_id', '=', wizard.grade_id.id),
            ('assessments_times', 'in', assessment_times.ids),
            ('state', '=', 'done')
        ]
        if wizard.class_division_id:
            evaluation_domain.append(('class_id', '=', wizard.class_division_id.id))
        
        evaluation_records = self.env['mc.evaluation.grades'].sudo().search(evaluation_domain)

        # 3- جلب جميع student grades للتقييمات
        assessment_grades = self.env['mc.evaluation.grades.student.list'].sudo().search([
            ('connect_id', 'in', evaluation_records.ids)
        ])

        # 4- جلب الطلاب
        if not wizard.syllabus_id.elective:  # مادة إجبارية
            student_domain = [('grade_id', '=', wizard.grade_id.id), ('company_id', '=', wizard.company_id.id)]
            if wizard.class_division_id:
                student_domain.append(('class_division_id', '=', wizard.class_division_id.id))
            students = self.env['education.student'].sudo().search(student_domain, order='seat_number, name')
        else:  # مادة اختيارية
            students = wizard.syllabus_id.students.mapped('student_id')
            if wizard.class_division_id:
                students = students.filtered(lambda s: s.class_division_id.id == wizard.class_division_id.id)
            students = students.sorted(key=lambda s: (s.seat_number or '', s.name))

        # 5- جلب الفصول
        if wizard.class_division_id:
            classes = [{'id': wizard.class_division_id.id, 'name': wizard.class_division_id.name}]
        else:
            evaluation_domain = [
                ('syllabus_id', '=', wizard.syllabus_id.id),
                ('grade_id', '=', wizard.grade_id.id),
                ('state', '=', 'done')
            ]
            evaluation_records_class = self.env['mc.evaluation.grades'].sudo().read_group(
                domain=evaluation_domain,
                fields=['class_id'],
                groupby=['class_id'],
                lazy=False
            )
            classes = []
            for record in evaluation_records_class:
                class_id = record['class_id'][0] if record['class_id'] else False
                if class_id:
                    class_record = self.env['education.class.division'].browse(class_id)
                    classes.append({
                        'id': class_record.id,
                        'name': class_record.name
                    })

        # 6- جلب الـ custom template
        custom_template = self.env['mc.custom.template'].sudo().search([
            ('company_id', '=', wizard.company_id.id),
            ('grade_id', '=', wizard.grade_id.id),
            ('syllabus_id', '=', wizard.syllabus_id.id),
        ], limit=1)

        # خريطة لربط كل assessments_category_id بالـ max_score من القالب
        max_score_by_category = {}
        if custom_template:
            for category in custom_template.assessments_category_id:
                max_score_by_category[category.id] = getattr(category, 'max_score', 0)

        # 7- جلب distributions من الـ template
        distributions_data = []
        distribution_grades_dict = defaultdict(lambda: defaultdict(dict))
        
        if custom_template:
            distributions = custom_template.custom_grade_distribution_template.filtered(
                lambda d: hasattr(d, 'item') and hasattr(d.item, 'assessment') and d.item.assessment == False and d.control == 'multi'
            )
            
            for dist in distributions:
                distributions_data.append({
                    'id': dist.id,
                    'item': {
                        'name': getattr(dist.item, 'name', ''),
                    },
                    'maximum': getattr(dist, 'maximum', 0) if getattr(dist, 'maximum', 0) or getattr(dist, 'weight', 0) else 0,
                    'minimum': getattr(dist, 'minimum', 0),
                })

        # 8- جمع جميع assessment categories المستخدمة في الفترات
        all_assessment_categories = set()
        for eval_record in evaluation_records:
            if hasattr(eval_record, 'assessments_category_id') and eval_record.assessments_category_id:
                all_assessment_categories.add(eval_record.assessments_category_id.id)
        
        all_assessment_categories = sorted(list(all_assessment_categories))
        
        # إنشاء خريطة لمعلومات assessment categories
        assessment_categories_info = {}
        for category_id in all_assessment_categories:
            category = self.env['mc.custom.assessments.category'].browse(category_id)
            assessment_categories_info[category_id] = {
                'id': category_id,
                'name': getattr(category.item, 'name', '') if hasattr(category, 'item') and category.item else '',
                'ar_name': getattr(category, 'ar_name', ''),
                'max_score': max_score_by_category.get(category_id, 0)
            }

        # تنظيم البيانات للتقييمات بناءً على assessment_category وليس evaluation record منفرد
        assessments_by_time_and_category = defaultdict(lambda: defaultdict(list))
        for eval_record in evaluation_records:
            if hasattr(eval_record, 'assessments_times') and hasattr(eval_record, 'assessments_category_id'):
                time_id = eval_record.assessments_times.id
                category_id = eval_record.assessments_category_id.id
                template_max_score = max_score_by_category.get(category_id, getattr(eval_record, 'custom_max_score', 0))
                assessments_by_time_and_category[time_id][category_id].append({
                    'id': eval_record.id,
                    'name': getattr(eval_record.assessments_category_id.item, 'name', '') if hasattr(eval_record.assessments_category_id, 'item') else '',
                    'max_score': template_max_score,
                    'eval_max_score': getattr(eval_record, 'custom_max_score', 0)
                })

        # تنظيم درجات الطلاب للتقييمات
        assessment_grades_dict = defaultdict(lambda: defaultdict(dict))
        for grade in assessment_grades:
            student_id = grade.student_id.id
            eval_id = grade.connect_id.id
            assessment_grades_dict[student_id][eval_id] = {
                'score': getattr(grade, 'score', 0),
                'score_selection': getattr(grade, 'score_selection', {}),
                'color': getattr(grade, 'color', ''),
                'check': getattr(grade, 'check', False)
            }

        # تنظيم بيانات الطلاب حسب الفصول
        students_data = {}
        for student in students:
            student_id = student.id
            student_data = {
                'id': student_id,
                'en_name': getattr(student, 'full_english_name', '') or getattr(student, 'name', ''),
                'ar_name': getattr(student, 'full_arabic_name', '') or getattr(student, 'name', ''),
                'grades_by_time': {},
                'distributions': {}
            }
            
            # تعبئة distributions للطالب
            for dist_data in distributions_data:
                dist_id = dist_data['id']
                dist_grade = distribution_grades_dict[student_id].get(dist_id, {})
                student_data['distributions'][dist_id] = dist_grade.get('score', 0)
            
            # تعبئة grades_by_time للتقييمات (بناءً على assessment categories)
            for time in assessment_times:
                time_id = time.id
                time_assessments = []
                
                # لكل assessment category، احسب متوسط الدرجات في هذه الفترة
                for category_id in all_assessment_categories:
                    category_evaluations = assessments_by_time_and_category[time_id].get(category_id, [])
                    if not category_evaluations:
                        continue
                    
                    # جمع جميع الدرجات لهذه الـ category في هذه الفترة
                    category_scores = []
                    category_info = assessment_categories_info[category_id]
                    
                    for eval_data in category_evaluations:
                        eval_id = eval_data['id']
                        grade_data = assessment_grades_dict[student_id].get(eval_id, {})
                        
                        if not grade_data.get('check', False):
                            continue
                        else:
                            score = float(grade_data.get('score', 0)) if grade_data.get('score') else 0
                            if eval_data['eval_max_score'] > 0:
                                normalized_score = (score / eval_data['eval_max_score']) * eval_data['max_score']
                                category_scores.append(normalized_score)
                    
                    # حساب متوسط الدرجات لهذه الـ category
                    if category_scores:
                        average_score = sum(category_scores) / len(category_scores)
                    else:
                        average_score = 'abs'
                    
                    time_assessments.append({
                        'category_id': category_id,
                        'name': category_info['name'],
                        'score': average_score,
                        'max_score': category_info['max_score'],
                        'score_selection': {},
                    })

                # حساب total و average للفترة
                valid_scores = [
                    assess['score'] for assess in time_assessments 
                    if isinstance(assess['score'], (int, float))
                ]
                total_score = sum(valid_scores) if valid_scores else 0
                average_score = total_score / len(valid_scores) if valid_scores else 0
                
                student_data['grades_by_time'][time_id] = {
                    'time_name': time.name,
                    'assessments': time_assessments,
                    'total': total_score,
                    'average': average_score
                }
            
            # حساب Total Assessments والمتوسط الكلي
            total_assessments = sum(time_data['total'] for time_data in student_data['grades_by_time'].values())
            valid_times = [time_data for time_data in student_data['grades_by_time'].values() if time_data['total'] > 0]
            total_average = total_assessments / len(valid_times) if valid_times else 0
            student_data['total_assessments'] = total_assessments
            student_data['average'] = total_average
            
            # تخصيص الطالب لفصله
            class_id = getattr(student.class_division_id, 'id', None) if hasattr(student, 'class_division_id') and student.class_division_id else None
            if not class_id and classes:
                class_id = classes[0]['id']
            if class_id not in students_data:
                students_data[class_id] = []
            students_data[class_id].append(student_data)

        # تحويل assessment times إلى قائمة من القواميس
        assessment_times_data = [{'id': time.id, 'name': time.name} for time in assessment_times]
        
        # تحويل assessment categories إلى قائمة للـ template
        assessment_categories_data = [assessment_categories_info[cat_id] for cat_id in all_assessment_categories]

        # جلب grading_method بشكل آمن
        grading_method_record = self.env['mc.grading.method'].sudo().search([('grade_id', '=', wizard.grade_id.id)], limit=1)
        grading_method = getattr(grading_method_record, 'grading_method', 'normal') if grading_method_record else 'normal'

        return {
            'classes': classes,
            'assessment_times': assessment_times_data,
            'assessment_categories': assessment_categories_data,
            'students_data': students_data,
            'distributions': distributions_data,
            'arabic_report': wizard.arabic_report,
            'year': getattr(wizard.term_id.academic_year_id, 'name', '') if hasattr(wizard.term_id, 'academic_year_id') and wizard.term_id.academic_year_id else '',
            'term_en': getattr(wizard.term_id, 'name', ''),
            'term_ar': getattr(wizard.term_id, 'arabic_name', ''),
            'syllabus_en': getattr(wizard.syllabus_id, 'name', ''),
            'syllabus_ar': getattr(wizard.syllabus_id, 'arabic_name', ''),
            'garde_en': getattr(wizard.grade_id, 'name', ''),
            'garde_ar': getattr(wizard.grade_id, 'arabic_name', ''),
            'show_avg': wizard.show_avg,
            'ministerial_number': getattr(wizard.grade_id, 'ministerial_number', ''),
            'grading_method': grading_method,
        }
    