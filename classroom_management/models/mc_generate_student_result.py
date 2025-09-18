from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
import math

class MCGenerateStudentResult(models.TransientModel):
    _name = 'mc.generate.student.result'
    _description = 'Generate Student Result'

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)
    grade_ids = fields.Many2many('education.class', string="Grades", domain="[('school', '=', company_id)]")
    term_id = fields.Many2one('education.academic.term', string="Term",  domain="[('school_year_id.company_id', '=', company_id)]")
    class_division_ids = fields.Many2many('education.class.division', string='Class',
                                         domain="[('class_id', 'in', grade_ids)]")
    assesment_time = fields.Many2one('mc.assessment.times', string="Assessment Time")
    student_ids = fields.Many2many('education.student', string='Students',
                                  domain="[('grade_id', 'in', grade_ids), ('class_division_id', 'in', class_division_ids)]")
    assesment_time_ids = fields.Char(compute="_compute_by_grades_divs")
    student_ids_domain = fields.Char(compute="_compute_by_grades_divs")
    is_british_system = fields.Boolean(
                            string="Is British System",
                            compute="_compute_is_british_system",
                            store=False
                        )

    @api.depends('company_id')
    def _compute_is_british_system(self):
        """Compute if the selected company uses the British system."""
        for record in self:
            record.is_british_system = record._get_company_system_type() == 'british'

    def _get_company_system_type(self):
        """Get the system type for the current company."""
        system_setting = self.env['system.settings'].sudo().search([
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        return system_setting.system_type if system_setting else 'general'


    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.grade_ids = False

    @api.depends('grade_ids', 'class_division_ids')
    def _compute_by_grades_divs(self):
        """Compute domains for assessment times and students based on grades and divisions."""
        for rec in self:
            if rec.grade_ids:
                assessment_domain = [('grade_ids', 'in', rec.grade_ids.ids)]
                student_domain = [('grade_id', 'in', rec.grade_ids.ids)]
                if rec.class_division_ids:
                    student_domain.append(('class_division_id', 'in', rec.class_division_ids.ids))
            else:
                assessment_domain = [('id', '=', -1)]
                student_domain = [('id', '=', -1)]
            rec.assesment_time_ids = json.dumps(assessment_domain)
            rec.student_ids_domain = json.dumps(student_domain)

    def button_generate(self):
        """Generate student results based on selected filters."""
        self.ensure_one()
        system_type = self._get_company_system_type()
        
        if not self.term_id:
            raise ValidationError("Please select a Term first.")
        if not self.grade_ids:
            raise ValidationError("Please select at least one Grade.")

        # Build student domain
        student_domain = [('company_id', '=', self.company_id.id)]
        if self.grade_ids:
            student_domain.append(('grade_id', 'in', self.grade_ids.ids))
        if self.class_division_ids:
            student_domain.append(('class_division_id', 'in', self.class_division_ids.ids))

        # Fetch students
        students = self.student_ids if self.student_ids else self.env['education.student'].sudo().search(student_domain)
        if not students:
            raise ValidationError("No students found matching the selected criteria.")

        results = {}
        for student in students:
            # Determine grading method record
            academic_year_id = self.term_id.academic_year_id
            grading_method_record = self.env['mc.grading.method'].sudo().search([
                ('company_id', '=', self.company_id.id),
                ('grade_id', '=', student.grade_id.id),
                ('school_year_id', '=', academic_year_id.id)
            ], limit=1)

            grading_method = grading_method_record.grading_method if grading_method_record else 'general'

            # British + numeric → البريطاني
            if system_type == 'british' and grading_method == 'numeric':
                student_result = self._generate_british_student_result(student)
            else:
                # أي حالة تانية → العادي
                self._cleanup_invalid_acc_records(student)
                student_result = self._generate_student_result(student)

            if student_result:
                results[student.name] = student_result

        return results

    
    def button_generate_monthly(self):
        """Generate student monthly results based on selected filters."""
        self.ensure_one()
        system_type = self._get_company_system_type()
        
        # British system doesn't support monthly generation
        if system_type == 'british':
            raise ValidationError("Monthly grade generation is not supported for British system.")
    
        if not self.grade_ids:
            raise ValidationError("Please select at least one Grade.")

        # Determine assessment times to process
        assessment_times = []
        if self.assesment_time:
            assessment_times = [self.assesment_time]
        elif self.term_id:
            assessment_times = self.env['mc.assessment.times'].sudo().search([
                ('start_date', '>=', self.term_id.start_date),
                ('end_date', '<=', self.term_id.end_date)
            ])
        else:
            raise ValidationError("Please select either an Assessment Time or a Term.")

        if not assessment_times:
            raise ValidationError("No assessment times found for the selected criteria.")

        # Build student domain
        student_domain = [('company_id', '=', self.company_id.id)]
        if self.grade_ids:
            student_domain.append(('grade_id', 'in', self.grade_ids.ids))
        if self.class_division_ids:
            student_domain.append(('class_division_id', 'in', self.class_division_ids.ids))

        # Fetch students
        students = self.student_ids if self.student_ids else self.env['education.student'].sudo().search(student_domain)
        if not students:
            raise ValidationError("No students found matching the selected criteria.")

        # Process each student for each assessment time
        for assessment_time in assessment_times:
            original_assessment_time = self.assesment_time
            self.assesment_time = assessment_time
            
            for student in students:
                self._cleanup_invalid_acc_monthly_records(student)
                self._generate_student_monthly_result(student)
            
            self.assesment_time = original_assessment_time

    def _cleanup_invalid_acc_records(self, student):
        """Remove invalid ACC records for the student and term, but keep all template IDs."""
        acc_record = self.env['acc.student.term.grades'].sudo().search([
            ('student_id', '=', student.id),
            ('term_id', '=', self.term_id.id)
        ], limit=1)

        if not acc_record:
            return

        templates = self.env['mc.custom.template'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id)
        ])

        for subject_line in acc_record.subject_line_ids:
            template = templates.filtered(lambda t: t.syllabus_id.id == subject_line.syllabus_id.id)
            if not template:
                subject_line.unlink()
                continue

            valid_dist_ids = template.custom_grade_distribution_template.filtered(lambda d: not d.item.assessment).mapped('id')
            valid_ass_ids = template.assessments_category_id.mapped('id')

            invalid_dist_lines = subject_line.distribution_line_ids.filtered(
                lambda l: l.distribution_id.id not in valid_dist_ids
            )
            invalid_ass_lines = subject_line.assessment_line_ids.filtered(
                lambda l: l.assessment_id.id not in valid_ass_ids
            )
            invalid_dist_lines.unlink()
            invalid_ass_lines.unlink()

    def _cleanup_invalid_acc_monthly_records(self, student):
        """Remove invalid ACC monthly records for the student and assessment time."""
        acc_record = self.env['acc.student.monthly.grades'].sudo().search([
            ('student_id', '=', student.id),
            ('assesment_time', '=', self.assesment_time.id)
        ], limit=1)

        if not acc_record:
            return

        templates = self.env['mc.custom.template'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id)
        ])

        for subject_line in acc_record.subject_line_ids:
            template = templates.filtered(lambda t: t.syllabus_id.id == subject_line.syllabus_id.id)
            if not template:
                subject_line.unlink()
                continue

            valid_ass_ids = template.assessments_category_id.mapped('id')
            invalid_ass_lines = subject_line.assessment_line_ids.filtered(
                lambda l: l.assessment_id.id not in valid_ass_ids
            )
            invalid_ass_lines.unlink()

    def _validate_distribution_source(self, student, syllabus, distribution_id):
        """Validate distribution source data."""
        tables_domains = {
            'mc.control.grades': [
                ('company_id', '=', self.company_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('grade_id', '=', student.grade_id.id),
                ('distribution_id', '=', distribution_id.id),
                ('term_id', '=', self.term_id.id),
                ('state', '=', 'done')
            ],
            'mc.evaluation.grades': [
                ('company_id', '=', self.company_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('grade_id', '=', student.grade_id.id),
                ('distribution_id', '=', distribution_id.id),
                ('state', '=', 'done')
            ]
        }

        for table_name, domain in tables_domains.items():
            records = self.env[table_name].sudo().search(domain)
            for record in records:
                if record.student_list.filtered(lambda s: s.student_id.id == student.id):
                    return True
        return False

    def _validate_assessment_source(self, student, syllabus, assessment_id):
        """Validate assessment source data."""
        domain = [
            ('company_id', '=', self.company_id.id),
            ('syllabus_id', '=', syllabus.id),
            ('grade_id', '=', student.grade_id.id),
            ('assessments_category_id', '=', assessment_id.id),
            ('state', '=', 'done')
        ]
        if self.assesment_time:
            domain.append(('assessments_times', '=', self.assesment_time.id))
        elif self.term_id:
            domain.extend([
                ('assessments_times.start_date', '>=', self.term_id.start_date),
                ('assessments_times.end_date', '<=', self.term_id.end_date)
            ])

        records = self.env['mc.evaluation.grades'].sudo().search(domain)
        return bool(records.student_list.filtered(lambda s: s.student_id.id == student.id))

    def _validate_assessment_source_monthly(self, student, syllabus, assessment_id):
        """Validate assessment source data for monthly records."""
        domain = [
            ('company_id', '=', self.company_id.id),
            ('syllabus_id', '=', syllabus.id),
            ('grade_id', '=', student.grade_id.id),
            ('assessments_category_id', '=', assessment_id.id),
            ('assessments_times', '=', self.assesment_time.id),
            ('state', '=', 'done')
        ]

        records = self.env['mc.evaluation.grades'].sudo().search(domain)
        return bool(records.student_list.filtered(lambda s: s.student_id.id == student.id))

    def _is_syllabus_selected_by_student(self, student, syllabus):
        """Check if the syllabus is selected by the student (for optional subjects)."""
        # لو المادة مش اختيارية، يتم احتسابها لكل الطلاب في الصف
        if not syllabus.elective:
            return True
        # لو المادة اختيارية، نتأكد إن الطالب مسجل فيها في mc.elective.syllabus.students
        return bool(self.env['mc.elective.syllabus.students'].sudo().search([
            ('student_id', '=', student.id),
            ('syllabus_id', '=', syllabus.id),
            ('company_id', '=', self.company_id.id)
        ], limit=1))

    def _generate_student_result(self, student):
        """Generate result for a single student."""
        
        system_type = self._get_company_system_type()
        
        # Determine grading method
        academic_year_id = self.term_id.academic_year_id
        grading_method_record = self.env['mc.grading.method'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id),
            ('school_year_id', '=', academic_year_id.id)
        ], limit=1)

        grading_method = grading_method_record.grading_method if grading_method_record else 'general'
        
        if system_type == 'british' and grading_method == 'numeric':
            return self._generate_british_student_result(student)
        
        elif system_type in ['british','american','general'] and grading_method == 'q_colors':
            return self._generate_qcolor_student_result(student)
        else:
            # النظام العادي
            result = {}
            acc_record = self._get_or_create_acc_record(student)

            templates = self.env['mc.custom.template'].sudo().search([
                ('company_id', '=', self.company_id.id),
                ('grade_id', '=', student.grade_id.id)
            ])

            for template in templates:
                # التأكد إن المادة مختارة من الطالب
                if not self._is_syllabus_selected_by_student(student, template.syllabus_id):
                    continue

                syllabus_name = template.syllabus_id.name or f"Template {template.id}"
                subject_result = {}
                total_score = 0.0
                subject_line = self._get_or_create_subject_line(acc_record, template.syllabus_id)

                for distribution in template.custom_grade_distribution_template:
                    if distribution.item.assessment:
                        continue  # تخطي التوزيعات اللي فيها item.assessment = true
                    item_name = distribution.item.name or f"Item {distribution.id}"
                    student_scores = self._get_student_scores_by_control(student, template.syllabus_id, distribution, subject_line)
                    subject_result[item_name] = student_scores
                    if len(student_scores) >= 2 and isinstance(student_scores[1], (int, float)):
                        total_score += student_scores[1]

                for assessment in template.assessments_category_id:
                    item_name = assessment.item.name or f"Assessment {assessment.id}"
                    student_scores = self._get_assessment_category_scores(student, template.syllabus_id, assessment, subject_line)
                    subject_result[item_name] = student_scores
                    if len(student_scores) >= 2 and isinstance(student_scores[1], (int, float)):
                        total_score += student_scores[1]

                if subject_result:
                    result[syllabus_name] = [subject_result]

            return result

    def _generate_british_student_result(self, student):
        """Generate British system result for a single student and save to ACC records."""
        result = {}
        
        # Create ACC record
        acc_record = self._get_or_create_acc_record(student)
        
        templates = self.env['mc.custom.template'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id)
        ])

        for template in templates:
            if not self._is_syllabus_selected_by_student(student, template.syllabus_id):
                continue

            syllabus_name = template.syllabus_id.name or f"Template {template.id}"
            
            # Get or create subject line
            subject_line = self._get_or_create_subject_line(acc_record, template.syllabus_id)
            
            # Initialize British system structure with max scores
            british_result = {
                "monthly": 0,
                "monthly_max": 0,
                "weekly": 0, 
                "weekly_max": 0,
                "exam": 0,
                "exam_max": 0,
                "total": 0,
                "total_max": 0
            }

            # Determine if we should use weight scoring
            academic_year_id = self.term_id.academic_year_id
            grading_method_record = self.env['mc.grading.method'].sudo().search([
                ('company_id', '=', self.company_id.id),
                ('grade_id', '=', student.grade_id.id),
                ('school_year_id', '=', academic_year_id.id)
            ], limit=1)

            use_weight_scoring = False
            if grading_method_record and grading_method_record.grading_method not in ['numeric']:
                use_weight_scoring = True

            # Process distributions
            for distribution in template.custom_grade_distribution_template:
                max_score = distribution.weight if use_weight_scoring else distribution.maximum or 0
                weight = distribution.weight 
                
                if distribution.control == 'control':
                    # This is exam
                    exam_score = self._get_british_exam_score(student, template.syllabus_id, distribution)
                    british_result["exam"] = exam_score
                    british_result["exam_max"] = max_score
                    
                elif distribution.control == 'multi' and not distribution.item.assessment:
                    # This is monthly - only if weight != 0
                    if max_score and weight != 0:
                        monthly_score = self._get_british_monthly_score(student, template.syllabus_id, distribution)
                        british_result["monthly"] = monthly_score
                        british_result["monthly_max"] = max_score
                    else:
                        british_result["monthly"] = 0
                        british_result["monthly_max"] = 0
                        
                elif distribution.control == 'multi' and distribution.item.assessment:
                    # This is weekly (assessments)
                    if  weight != 0:
                        weekly_score = self._get_british_weekly_score(student, template.syllabus_id, distribution, template)
                        british_result["weekly"] = weekly_score
                        british_result["weekly_max"] = max_score

            # Calculate totals
            british_result["total"] = british_result["monthly"] + british_result["weekly"] + british_result["exam"]
            british_result["total_max"] = british_result["monthly_max"] + british_result["weekly_max"] + british_result["exam_max"]
            
            # Save to ACC record with maximum scores
            subject_line.write({
                'british_monthly': british_result["monthly"],
                'british_weekly': british_result["weekly"], 
                'british_exam': british_result["exam"],
                'british_monthly_max': british_result["monthly_max"],
                'british_weekly_max': british_result["weekly_max"],
                'british_exam_max': british_result["exam_max"]
            })
            
            result[syllabus_name] = [british_result]

        return result

    def _get_british_exam_score(self, student, syllabus, distribution):
        """Get exam score for British system."""
        # Determine if we should use weight scoring
        academic_year_id = self.term_id.academic_year_id
        grading_method_record = self.env['mc.grading.method'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id),
            ('school_year_id', '=', academic_year_id.id) 
        ], limit=1)

        use_weight_scoring = False
        if grading_method_record and grading_method_record.grading_method not in ['numeric']:
            use_weight_scoring = True

        target_max_score = distribution.weight if use_weight_scoring else distribution.maximum or 0
        
        # Search in mc.control.grades
        domain = [
            ('company_id', '=', self.company_id.id),
            ('syllabus_id', '=', syllabus.id),
            ('grade_id', '=', student.grade_id.id),
            ('distribution_id', '=', distribution.id),
            ('term_id', '=', self.term_id.id),
            ('state', '=', 'done')
        ]
        
        grades = self.env['mc.control.grades'].sudo().search(domain)
        for grade in grades:
            student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
            if student_record:
                original_score = float(student_record[0].score) if student_record[0].score else 0.0
                
                # Apply scaling if needed
                if (hasattr(grade, 'custom_max_score') and 
                    grade.custom_max_score and 
                    grade.custom_max_score > 0):
                    source_max_score = float(grade.custom_max_score)
                    if source_max_score != target_max_score:
                        scaled_score = (original_score / source_max_score) * target_max_score
                        return scaled_score
                return original_score
        return 0.0

    def _get_british_monthly_score(self, student, syllabus, distribution):
        """Get monthly score for British system."""
        # Determine if we should use weight scoring
        academic_year_id = self.term_id.academic_year_id
        grading_method_record = self.env['mc.grading.method'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id),
            ('school_year_id', '=', academic_year_id.id) 
        ], limit=1)

        use_weight_scoring = False
        if grading_method_record and grading_method_record.grading_method not in ['numeric']:
            use_weight_scoring = True

        target_max_score = distribution.weight if use_weight_scoring else distribution.maximum or 0
        
        # Search in mc.evaluation.grades
        domain = [
            ('company_id', '=', self.company_id.id),
            ('syllabus_id', '=', syllabus.id),
            ('grade_id', '=', student.grade_id.id),
            ('distribution_id', '=', distribution.id),
            ('state', '=', 'done')
        ]
        
        if self.term_id:
            domain.extend([
                ('assessments_times.start_date', '>=', self.term_id.start_date),
                ('assessments_times.end_date', '<=', self.term_id.end_date)
            ])
        
        grades = self.env['mc.evaluation.grades'].sudo().search(domain)
        for grade in grades:
            student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
            if student_record:
                original_score = float(student_record[0].score) if student_record[0].score else 0.0
                
                # Apply scaling if needed
                if (hasattr(grade, 'custom_max_score') and 
                    grade.custom_max_score and 
                    grade.custom_max_score > 0):
                    source_max_score = float(grade.custom_max_score)
                    if source_max_score != target_max_score:
                        scaled_score = (original_score / source_max_score) * target_max_score
                        return scaled_score
                return original_score
        return 0.0
    
    def _get_british_weekly_score(self, student, syllabus, distribution, template):
        """Get weekly score for British system (assessments with best_of logic)."""
        target_max_score =  distribution.maximum or 0
        best_of = distribution.best_of or 0
        
        # Get all assessment categories for this template
        assessment_categories = template.assessments_category_id
        total_assessment_scores = 0.0
        total_assessment_max = 0.0
        
        for assessment in assessment_categories:
            assessment_max = assessment.max_score or 0
            total_assessment_max += assessment_max
            
            # Find the actual assessment category record
            assessments_category = self.env['mc.custom.assessments.category'].sudo().search([
                ('item', '=', assessment.item.id),
                ('assessments_custom_category_id.company_id', '=', self.company_id.id),
                ('assessments_custom_category_id.grade_id', '=', student.grade_id.id),
                ('assessments_custom_category_id.syllabus_id', '=', syllabus.id)
            ], limit=1)
            
            if not assessments_category:
                continue
                
            # Get evaluation grades for this assessment
            domain = [
                ('company_id', '=', self.company_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('grade_id', '=', student.grade_id.id),
                ('assessments_category_id', '=', assessments_category.id),
                ('state', '=', 'done')
            ]
            
            if self.term_id:
                domain.extend([
                    ('assessments_times.start_date', '>=', self.term_id.start_date),
                    ('assessments_times.end_date', '<=', self.term_id.end_date)
                ])
            
            eval_grades = self.env['mc.evaluation.grades'].sudo().search(domain)
            all_scores = []
            
            for grade in eval_grades:
                student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
                if student_record and student_record[0].score:
                    eval_max_score = float(grade.custom_max_score) or assessment_max
                    if eval_max_score > 0:
                        # Scale to assessment max score
                        scaled_score = (float(student_record[0].score) / eval_max_score) * assessment_max
                        all_scores.append(scaled_score)
            
            # Apply best_of logic if specified
            if best_of > 0 and all_scores:
                top_scores = sorted(all_scores, reverse=True)[:best_of]
                assessment_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
            else:
                assessment_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
            
            total_assessment_scores += assessment_score
        
        # Scale to distribution weight/maximum
        if total_assessment_max > 0:
            final_score = (total_assessment_scores / total_assessment_max) * target_max_score
            return final_score
        
        return 0.0
    
    def _generate_qcolor_student_result(self, student):
        """Generate Q-Color system result for a single student."""
        result = {}
        acc_record = self._get_or_create_acc_record(student)
        
        templates = self.env['mc.custom.template'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id)
        ])

        for template in templates:
            # التأكد إن المادة مختارة من الطالب
            if not self._is_syllabus_selected_by_student(student, template.syllabus_id):
                continue

            syllabus_name = template.syllabus_id.name or f"Template {template.id}"
            subject_result = {}
            subject_line = self._get_or_create_subject_line(acc_record, template.syllabus_id)

            # معالجة Distribution Lines
            for distribution in template.custom_grade_distribution_template:
                item_name = distribution.item.name or f"Item {distribution.id}"
                
                if distribution.item.assessment:
                    # هذا assessment - نحسب متوسط الدرجات من الـ assessment lines
                    assessment_score = self._get_qcolor_assessment_scores(student, template, distribution, subject_line)
                    subject_result[item_name] = assessment_score
                elif distribution.control not in ['control', 'project']:
                    # هذا distribution عادي - نجيب الدرجة من mc.evaluation.grades
                    dist_score = self._get_qcolor_distribution_scores(student, template.syllabus_id, distribution, subject_line)
                    subject_result[item_name] = dist_score

            if subject_result:
                result[syllabus_name] = [subject_result]

        return result

    def _get_qcolor_distribution_scores(self, student, syllabus, distribution, subject_line):
        """Get distribution scores for Q-Color system from mc.evaluation.grades."""
        
        # البحث في mc.evaluation.grades
        domain = [
            ('company_id', '=', self.company_id.id),
            ('syllabus_id', '=', syllabus.id),
            ('grade_id', '=', student.grade_id.id),
            ('distribution_id', '=', distribution.id),
            ('state', '=', 'done')
        ]
        
        if self.term_id:
            domain.extend([
                ('assessments_times.start_date', '>=', self.term_id.start_date),
                ('assessments_times.end_date', '<=', self.term_id.end_date)
            ])
        
        eval_grades = self.env['mc.evaluation.grades'].sudo().search(domain)
        
        for grade in eval_grades:
            student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
            if student_record and student_record[0].score_selection:
                student_score = float(student_record[0].score_selection.symbol)
                
                # جلب الـ description من mc.grading.scale
                description = student_record[0].score_selection.description or ''
                
                # حفظ في ACC record مع الـ description
                self._create_or_update_qcolor_distribution_line(subject_line, distribution.id, student_score, description, True)
                
                return [[student_score, description], 0]
        
        # لو مفيش درجة
        self._create_or_update_qcolor_distribution_line(subject_line, distribution.id, 0.0, '', False)
        return [[0.0, ''], 0]

    def _get_qcolor_assessment_scores(self, student, template, distribution, subject_line):
        """Get assessment scores for Q-Color system distribution that has assessment=True."""
        
        # جلب الـ assessment categories من التمبلت
        assessment_categories = template.assessments_category_id
        
        if not assessment_categories:
            return [[0.0, ''], 0]
        
        all_scores = []
        all_descriptions = []
        
        for assessment in assessment_categories:
            # البحث عن الـ assessment category الفعلي
            assessments_category = self.env['mc.custom.assessments.category'].sudo().search([
                ('item', '=', assessment.item.id),
                ('assessments_custom_category_id.company_id', '=', self.company_id.id),
                ('assessments_custom_category_id.grade_id', '=', student.grade_id.id),
                ('assessments_custom_category_id.syllabus_id', '=', template.syllabus_id.id)
            ], limit=1)

            if not assessments_category:
                continue

            # البحث في mc.evaluation.grades للـ assessments
            domain = [
                ('company_id', '=', self.company_id.id),
                ('syllabus_id', '=', template.syllabus_id.id),
                ('grade_id', '=', student.grade_id.id),
                ('assessments_category_id', '=', assessments_category.id),
                ('state', '=', 'done')
            ]
            
            if self.term_id:
                domain.extend([
                    ('assessments_times.start_date', '>=', self.term_id.start_date),
                    ('assessments_times.end_date', '<=', self.term_id.end_date)
                ])

            eval_grades = self.env['mc.evaluation.grades'].sudo().search(domain)
            
            # جمع كل الدرجات والأوصاف
            assessment_scores = []
            assessment_descriptions = []
            
            for grade in eval_grades:
                student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
                if student_record and student_record[0].score_selection:
                    score = float(student_record[0].score_selection.symbol)
                    description = student_record[0].score_selection.description or ''
                    assessment_scores.append(score)
                    assessment_descriptions.append(description)

            # تطبيق best_of إذا كان موجود في distribution
            best_of = distribution.best_of or 0
            
            if best_of > 0 and assessment_scores:
                # أخذ أفضل عدد من الدرجات
                top_indices = sorted(range(len(assessment_scores)), 
                                key=lambda i: assessment_scores[i], reverse=True)[:best_of]
                
                final_score = sum(assessment_scores[i] for i in top_indices) / len(top_indices)
                # أخذ وصف أعلى درجة
                best_description = assessment_descriptions[top_indices[0]] if top_indices else ''
            else:
                # حساب المتوسط العادي
                final_score = sum(assessment_scores) / len(assessment_scores) if assessment_scores else 0.0
                # أخذ أول وصف متاح
                best_description = assessment_descriptions[0] if assessment_descriptions else ''
            
            all_scores.append(final_score)
            all_descriptions.append(best_description)
            
            # حفظ كل assessment في ACC record مع الوصف
            self._create_or_update_qcolor_assessment_line(subject_line, assessments_category.id, final_score, best_description)

        # حساب المجموع النهائي
        total_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
        # أخذ وصف أعلى درجة
        final_description = max(zip(all_scores, all_descriptions), key=lambda x: x[0])[1] if all_scores else ''

        return [[total_score, final_description], 0]

    def _create_or_update_qcolor_distribution_line(self, subject_line, distribution_id, score, description, check=True):
        """Create or update a Q-Color distribution line with score and description."""
        if not (distribution_id and subject_line and score is not None):
            return
        existing_dist_line = subject_line.distribution_line_ids.filtered(lambda l: l.distribution_id.id == distribution_id)
        if existing_dist_line:
            existing_dist_line.write({
                'score': score,
                'description': description,
                'check': check
            })
        else:
            self.env['acc.student.term.subject.distribution.line'].create({
                'parent_id': subject_line.id,
                'distribution_id': distribution_id,
                'score': score,
                'description': description,
                'check': check
            })

    def _create_or_update_qcolor_assessment_line(self, subject_line, assessment_id, score, description):
        """Create or update a Q-Color assessment line with score and description."""
        if not (assessment_id and subject_line and score is not None):
            return
        existing_ass_line = subject_line.assessment_line_ids.filtered(lambda l: l.assessment_id.id == assessment_id)
        if existing_ass_line:
            existing_ass_line.write({
                'score': score,
                'description': description
            })
        else:
            self.env['acc.student.term.subject.assessment.line'].create({
                'parent_id': subject_line.id,
                'assessment_id': assessment_id,
                'score': score,
                'description': description
            })
    
    def _generate_student_monthly_result(self, student):
        """Generate monthly result for a single student."""
        result = {}
        acc_record = self._get_or_create_acc_monthly_record(student)

        templates = self.env['mc.custom.template'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id)
        ])

        for template in templates:
            # التأكد إن المادة مختارة من الطالب
            if not self._is_syllabus_selected_by_student(student, template.syllabus_id):
                continue

            syllabus_name = template.syllabus_id.name or f"Template {template.id}"
            subject_result = {}
            total_score = 0.0
            subject_line = self._get_or_create_monthly_subject_line(acc_record, template.syllabus_id)

            for assessment in template.assessments_category_id:
                item_name = assessment.item.name or f"Assessment {assessment.id}"
                student_scores = self._get_assessment_category_scores_monthly(student, template.syllabus_id, assessment, subject_line)
                subject_result[item_name] = student_scores
                if len(student_scores) >= 2 and isinstance(student_scores[1], (int, float)):
                    total_score += student_scores[1]

            if subject_result:
                result[syllabus_name] = [subject_result]

        return result

    def _check_student_has_grades_in_subject(self, student, syllabus):
        """Check if the student has grades for the given syllabus."""
        base_domain = [
            ('company_id', '=', self.company_id.id),
            ('syllabus_id', '=', syllabus.id),
            ('grade_id', '=', student.grade_id.id),
            ('state', '=', 'done')
        ]

        control_domain = base_domain + [('term_id', '=', self.term_id.id)]
        if self.env['mc.control.grades'].sudo().search(control_domain).student_list.filtered(lambda s: s.student_id.id == student.id):
            return True

        eval_domain = base_domain.copy()
        if self.assesment_time:
            eval_domain.append(('assessment_time_id', '=', self.assesment_time.id))
        elif self.term_id:
            eval_domain.extend([
                ('assessments_times.start_date', '>=', self.term_id.start_date),
                ('assessments_times.end_date', '<=', self.term_id.end_date)
            ])
        if self.env['mc.evaluation.grades'].sudo().search(eval_domain).student_list.filtered(lambda s: s.student_id.id == student.id):
            return True

        return False

    def _check_student_has_assessment_grades_in_subject(self, student, syllabus):
        """Check if the student has assessment grades for the given syllabus."""
        base_domain = [
            ('company_id', '=', self.company_id.id),
            ('syllabus_id', '=', syllabus.id),
            ('grade_id', '=', student.grade_id.id),
            ('state', '=', 'done')
        ]
        
        eval_domain = base_domain.copy()
        eval_domain.append(('assessments_times', '=', self.assesment_time.id))
        
        if self.env['mc.evaluation.grades'].sudo().search(eval_domain).student_list.filtered(lambda s: s.student_id.id == student.id):
            return True

        return False

    def _get_or_create_acc_record(self, student):
        """Get or create an ACC record for the student and term."""
        existing_record = self.env['acc.student.term.grades'].sudo().search([
            ('student_id', '=', student.id),
            ('term_id', '=', self.term_id.id)
        ], limit=1)
        if existing_record:
            return existing_record
        return self.env['acc.student.term.grades'].create({
            'student_id': student.id,
            'term_id': self.term_id.id,
            'company_id': student.company_id.id,
        })

    def _get_or_create_acc_monthly_record(self, student):
        """Get or create an ACC monthly record for the student and assessment time."""
        existing_record = self.env['acc.student.monthly.grades'].sudo().search([
            ('student_id', '=', student.id),
            ('assesment_time', '=', self.assesment_time.id)
        ], limit=1)
        if existing_record:
            return existing_record
        return self.env['acc.student.monthly.grades'].create({
            'student_id': student.id,
            'assesment_time': self.assesment_time.id,
            'company_id': student.company_id.id,
        })

    def _get_or_create_subject_line(self, acc_record, syllabus):
        """Get or create a subject line for the syllabus in the ACC record."""
        existing_subject = acc_record.subject_line_ids.filtered(lambda s: s.syllabus_id.id == syllabus.id)
        if existing_subject:
            return existing_subject[0]
        return self.env['acc.student.term.subject.line'].create({
            'parent_id': acc_record.id,
            'syllabus_id': syllabus.id,
        })

    def _get_or_create_monthly_subject_line(self, acc_record, syllabus):
        """Get or create a monthly subject line for the syllabus in the ACC record."""
        existing_subject = acc_record.subject_line_ids.filtered(lambda s: s.syllabus_id.id == syllabus.id)
        if existing_subject:
            return existing_subject[0]
        return self.env['acc.student.monthly.subject.line'].create({
            'parent_id': acc_record.id,
            'syllabus_id': syllabus.id,
        })

    def _create_or_update_distribution_line(self, subject_line, distribution_id, max_score, student_score, check=True):
        """Create or update a distribution line for the subject with check status."""
        if not (distribution_id and subject_line and max_score is not None and student_score is not None):
            return
        existing_dist_line = subject_line.distribution_line_ids.filtered(lambda l: l.distribution_id.id == distribution_id)
        if existing_dist_line:
            existing_dist_line.write({
                'max_score': max_score,
                'score': student_score,
                'check': check
            })
        else:
            self.env['acc.student.term.subject.distribution.line'].create({
                'parent_id': subject_line.id,
                'distribution_id': distribution_id,
                'max_score': max_score,
                'score': student_score,
                'check': check
            })

    def _create_or_update_assessment_line(self, subject_line, assessment_id, max_score, student_score):
        """Create or update an assessment line for the subject."""
        if not (assessment_id and subject_line and max_score is not None and student_score is not None):
            return
        existing_ass_line = subject_line.assessment_line_ids.filtered(lambda l: l.assessment_id.id == assessment_id)
        if existing_ass_line:
            existing_ass_line.write({'max_score': max_score, 'score': student_score})
        else:
            self.env['acc.student.term.subject.assessment.line'].create({
                'parent_id': subject_line.id,
                'assessment_id': assessment_id,
                'max_score': max_score,
                'score': student_score,
            })

    def _create_or_update_monthly_assessment_line(self, subject_line, assessment_id, max_score, student_score):
        """Create or update a monthly assessment line for the subject."""
        if not (assessment_id and subject_line and max_score is not None and student_score is not None):
            return
        existing_ass_line = subject_line.assessment_line_ids.filtered(lambda l: l.assessment_id.id == assessment_id)
        if existing_ass_line:
            existing_ass_line.write({'max_score': max_score, 'score': student_score})
        else:
            self.env['acc.student.monthly.subject.assessment.line'].create({
                'parent_id': subject_line.id,
                'assessment_id': assessment_id,
                'max_score': max_score,
                'score': student_score,
            })

    def _search_in_grades_table(self, table_name, student, syllabus, distribution_id=None, target_max_score=None):
        """Search for student grades in the specified table with scaled score support and check status for mc.control.grades."""
        base_domain = [
            ('company_id', '=', self.company_id.id),
            ('syllabus_id', '=', syllabus.id),
            ('grade_id', '=', student.grade_id.id),
            ('state', '=', 'done')
        ]
        if distribution_id:
            base_domain.append(('distribution_id', '=', distribution_id))
        if table_name == 'mc.control.grades' and self.term_id:
            base_domain.append(('term_id', '=', self.term_id.id))

        grades = self.env[table_name].sudo().search(base_domain)
        for grade in grades:
            student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
            if student_record:
                check = student_record[0].check if table_name == 'mc.control.grades' else True  # استرجاع check بس من mc.control.grades
                original_score = float(student_record[0].score) if student_record[0].score else 0.0
                
                # Apply scaled score if target_max_score is provided and grade has custom_max_score
                if (target_max_score and 
                    hasattr(grade, 'custom_max_score') and 
                    grade.custom_max_score and 
                    grade.custom_max_score > 0):
                    source_max_score = float(grade.custom_max_score)
                    if source_max_score != target_max_score:
                        scaled_score = (original_score / source_max_score) * target_max_score
                        return scaled_score, check
                    return original_score, check
                return original_score, check
        return None, False  # لو مفيش سجل، بنرجع درجة 0 وحضور False

    def _get_student_scores_by_control(self, student, syllabus, distribution, subject_line):
        """Get student scores by control for the given syllabus and distribution."""
        if distribution.item.assessment or distribution.control == 'project':
            return [[0, 0], 0]  # لا نعالج التوزيعات التي تحتوي على item.assessment = true

        academic_year_id = self.term_id.academic_year_id
        grading_method_record = self.env['mc.grading.method'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id),
            ('school_year_id', '=', academic_year_id.id) 
        ], limit=1)

        use_weight_scoring = False
        if grading_method_record and grading_method_record.grading_method not in ['numeric']:
            use_weight_scoring = True

        max_score = distribution.weight if use_weight_scoring else distribution.maximum or 0

        control_type = distribution.control
        tables_to_search = (
            ['mc.control.grades'] if control_type == 'control' else
            ['mc.evaluation.grades'] if control_type == 'multi' else
            []
        )

        for table_name in tables_to_search:
            # Pass the target max_score and get check status
            score, check = self._search_in_grades_table(table_name, student, syllabus, distribution.id, max_score)
            if score is not None:
                self._create_or_update_distribution_line(subject_line, distribution.id, max_score, score, check)
                return [[max_score, score], 0]

            # لو مفيش درجة، بننشئ السجل مع check=False لـ mc.control.grades
            self._create_or_update_distribution_line(subject_line, distribution.id, max_score, 0.0, check=False if table_name == 'mc.control.grades' else True)
            return [[max_score, 0.0], 0]

    def _get_assessment_category_scores(self, student, syllabus, assessment, subject_line):
        """Get assessment category scores, keep assessment ID even if no score."""
        max_score = assessment.max_score or 0
        assessments_category = self.env['mc.custom.assessments.category'].sudo().search([
            ('item', '=', assessment.item.id),
            ('assessments_custom_category_id.company_id', '=', self.company_id.id),
            ('assessments_custom_category_id.grade_id', '=', student.grade_id.id),
            ('assessments_custom_category_id.syllabus_id', '=', syllabus.id)
        ], limit=1)

        if not assessments_category:
            self._create_or_update_assessment_line(subject_line, assessment.id, max_score, 0.0)
            return [[max_score, 0.0], 0]

        try:
            control = assessments_category.control if hasattr(assessments_category, 'control') else False
            attendance_assessment = getattr(assessments_category.item, 'attendance_assessment', False)
            if control == 'system' and attendance_assessment:
                return self._calculate_attendance_grade(student, syllabus, assessments_category, subject_line, max_score)
        except Exception:
            self._create_or_update_assessment_line(subject_line, assessments_category.id, max_score, 0.0)
            return [[max_score, 0.0], 0]

        domain = [
            ('company_id', '=', self.company_id.id),
            ('syllabus_id', '=', syllabus.id),
            ('grade_id', '=', student.grade_id.id),
            ('assessments_category_id', '=', assessments_category.id),
            ('state', '=', 'done')
        ]
        if self.assesment_time:
            domain.append(('assessments_times', '=', self.assesment_time.id))
        elif self.term_id:
            domain.extend([
                ('assessments_times.start_date', '>=', self.term_id.start_date),
                ('assessments_times.end_date', '<=', self.term_id.end_date)
            ])

        eval_grades = self.env['mc.evaluation.grades'].sudo().search(domain)
        all_scores = [
            float(student_record.score) for grade in eval_grades
            for student_record in grade.student_list.filtered(lambda s: s.student_id.id == student.id)
            if student_record.score
        ]

        # البحث عن best_of من template.custom_grade_distribution_template
        template = self.env['mc.custom.template'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id),
            ('syllabus_id', '=', syllabus.id)
        ], limit=1)
        
        best_of = 0
        if template:
            # البحث في template.custom_grade_distribution_template عن العنصر الذي له نفس item الخاص بـ assessment
            # وله item.assessment = True
            distribution_with_assessment = template.custom_grade_distribution_template.filtered(
                lambda d: d.item.id == assessment.item.id and d.item.assessment
            )
            if distribution_with_assessment:
                best_of = distribution_with_assessment[0].best_of or 0
            else:
                # إذا لم يوجد في distribution_template، استخدم القيمة الافتراضية من assessment
                best_of = assessment.best_of or 0
        else:
            best_of = assessment.best_of or 0

        if best_of > 0:
            top_scores = sorted(all_scores, reverse=True)[:best_of]
            final_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
        else:
            scores_by_assessment_time = {}
            for grade in eval_grades:
                student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
                eval_max_score = float(grade.custom_max_score) or max_score
                assessment_time_id = grade.assessments_times.id
                if assessment_time_id not in scores_by_assessment_time:
                    scores_by_assessment_time[assessment_time_id] = []
                if student_record:
                    if student_record.check:
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

        self._create_or_update_assessment_line(subject_line, assessments_category.id, max_score, final_score)
        return [[max_score, final_score], 0]

    def _get_assessment_category_scores_monthly(self, student, syllabus, assessment, subject_line):
        """Get assessment category scores for a student for monthly records."""
        max_score = assessment.max_score or 0
        assessments_category = self.env['mc.custom.assessments.category'].sudo().search([
            ('item', '=', assessment.item.id),
            ('assessments_custom_category_id.company_id', '=', self.company_id.id),
            ('assessments_custom_category_id.grade_id', '=', student.grade_id.id),
            ('assessments_custom_category_id.syllabus_id', '=', syllabus.id)
        ], limit=1)

        if not assessments_category:
            self._create_or_update_monthly_assessment_line(subject_line, assessment.id, max_score, 0.0)
            return [[max_score, 0.0], 0]

        try:
            control = assessments_category.control if hasattr(assessments_category, 'control') else False
            attendance_assessment = getattr(assessments_category.item, 'attendance_assessment', False)
            if control == 'system' and attendance_assessment:
                return self._calculate_attendance_grade_monthly(student, syllabus, assessments_category, subject_line, max_score)
        except Exception:
            self._create_or_update_monthly_assessment_line(subject_line, assessments_category.id, max_score, 0.0)
            return [[max_score, 0.0], 0]

        domain = [
            ('company_id', '=', self.company_id.id),
            ('syllabus_id', '=', syllabus.id),
            ('grade_id', '=', student.grade_id.id),
            ('assessments_category_id', '=', assessments_category.id),
            ('assessments_times', '=', self.assesment_time.id),
            ('state', '=', 'done')
        ]

        eval_grades = self.env['mc.evaluation.grades'].sudo().search(domain)
        
        # البحث عن best_of من template.custom_grade_distribution_template
        template = self.env['mc.custom.template'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('grade_id', '=', student.grade_id.id),
            ('syllabus_id', '=', syllabus.id)
        ], limit=1)
        
        best_of = 0
        if template:
            # البحث في template.custom_grade_distribution_template عن العنصر الذي له نفس item الخاص بـ assessment
            # وله item.assessment = True
            distribution_with_assessment = template.custom_grade_distribution_template.filtered(
                lambda d: d.item.id == assessment.item.id and d.item.assessment
            )
            if distribution_with_assessment:
                best_of = distribution_with_assessment[0].best_of or 0
            else:
                # إذا لم يوجد في distribution_template، استخدم القيمة الافتراضية من assessment
                best_of = assessment.best_of or 0
        else:
            best_of = assessment.best_of or 0

        all_scores = []
        for grade in eval_grades:
            student_record = grade.student_list.filtered(lambda s: s.student_id.id == student.id)
            eval_max_score = float(grade.custom_max_score) or max_score
            if student_record:
                if student_record.check:
                    if student_record[0].score:
                        scaled_score = (float(student_record[0].score) / eval_max_score) * max_score
                        all_scores.append(float(scaled_score))
                    else:
                        all_scores.append(0.0)
                else:
                    all_scores.append(0.0)
            else:
                all_scores.append(0.0)

        # تطبيق best_of إذا كان أكبر من 0
        if best_of > 0 and all_scores:
            top_scores = sorted(all_scores, reverse=True)[:best_of]
            final_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
        else:
            final_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

        self._create_or_update_monthly_assessment_line(subject_line, assessments_category.id, max_score, final_score)
        return [[max_score, final_score], 0]

    def _calculate_attendance_grade(self, student, syllabus, assessment, subject_line, max_score):
        """Calculate attendance grade for the student based on 'system' control type."""
        max_score = max_score or assessment.max_score or 0
        total_attendance_days = 0
        total_present_days = 0
        total_score_per_term = 0.0

        if not self.term_id:
            return [[max_score, 0.0], 0]

        attendance_records_per_term = self.env['education.attendance'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('class_id', '=', student.grade_id.id),
            ('division_id', '=', student.class_division_id.id),
            ('date', '>=', self.term_id.start_date),
            ('date', '<=', self.term_id.end_date),
            ('state', '=', 'done')
        ])

        total_attendance_days = len(attendance_records_per_term)
        absent_days_without_excuse = 0
        for record in attendance_records_per_term:
            line = record.attendance_line_ids.filtered(lambda l: l.student_id.id == student.id)
            if not line:
                continue
            line = line[0]
            if not line.present_morning and not line.sickness_absence:
                absent_days_without_excuse += 1

        effective_days = total_attendance_days - absent_days_without_excuse
        if total_attendance_days > 0:
            total_score_per_term = math.ceil((effective_days / total_attendance_days) * max_score)
        else:
            total_score_per_term = 0.0

        self._create_or_update_assessment_line(subject_line, assessment.id, max_score, total_score_per_term)
        return [[max_score, total_score_per_term], 0]

    def _calculate_attendance_grade_monthly(self, student, syllabus, assessment, subject_line, max_score):
        """Calculate attendance grade for the student for monthly records."""
        max_score = max_score or assessment.max_score or 0
        total_attendance_days = 0
        total_score_per_assessment_time = 0.0

        if not self.assesment_time:
            return [[max_score, 0.0], 0]

        attendance_records_per_assessment_time = self.env['education.attendance'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('class_id', '=', student.grade_id.id),
            ('division_id', '=', student.class_division_id.id),
            ('date', '>=', self.assesment_time.start_date),
            ('date', '<=', self.assesment_time.end_date),
            ('state', '=', 'done')
        ])

        total_attendance_days = len(attendance_records_per_assessment_time)
        absent_days_without_excuse = 0
        for record in attendance_records_per_assessment_time:
            line = record.attendance_line_ids.filtered(lambda l: l.student_id.id == student.id)
            if not line:
                continue
            line = line[0]
            if not line.present_morning and not line.sickness_absence:
                absent_days_without_excuse += 1

        effective_days = total_attendance_days - absent_days_without_excuse
        if total_attendance_days > 0:
            total_score_per_assessment_time = math.ceil((effective_days / total_attendance_days) * max_score)
        else:
            total_score_per_assessment_time = 0.0

        self._create_or_update_monthly_assessment_line(subject_line, assessment.id, max_score, total_score_per_assessment_time)
        return [[max_score, total_score_per_assessment_time], 0]