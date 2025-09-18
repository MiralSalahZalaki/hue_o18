from odoo import models, fields, api
from odoo.exceptions import ValidationError ,UserError


class IGStudentReportAbstract(models.AbstractModel):
    _name = 'report.classroom_management.report_ig_student_template'
    _description = 'IG Student Report Abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Main method to prepare all report data
        docids contains the wizard record IDs
        """
        # Get the wizard record
        wizard = self.env['ig.student.result.wizard'].browse(docids[0])
        
        # Get grading method type
        grading_method_type = self._get_grading_method(wizard)
        
        # Prepare students data
        students_data = self._prepare_students_data(wizard, grading_method_type)
        
        # Prepare syllabus data
        syllabus_data = self._prepare_syllabus_data(wizard, grading_method_type)
        
        # Sort and rank students
        students_data = self._sort_and_rank_students(students_data, wizard.top_rank)
        
        return {
            'doc_ids': docids,
            'doc_model': 'ig.student.result.wizard',
            'docs': [wizard],
            'students_data': students_data,
            'syllabus_data': syllabus_data,
            'term_name': wizard.term_id.name,
            'grade_name': wizard.grade_id.name,
            'class_name': wizard.class_id.name if wizard.class_id else '',
            'grading_method_type': grading_method_type,
            'top_rank': wizard.top_rank,
            'total_students': len(students_data),
            'company': wizard.company_id,
            'system_type': 'british'
        }

    def _get_grading_method(self, wizard):
        """Get grading method type for the given wizard parameters"""
        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', wizard.grade_id.id),
            ('company_id', '=', wizard.company_id.id),
            ('school_year_id', '=', wizard.term_id.academic_year_id.id)
        ], limit=1)
        
        return grading_method.grading_method if grading_method else 'numeric'

    def _prepare_students_data(self, wizard, grading_method_type):
        """Prepare students data based on wizard selections"""
        # Prepare Students List
        student_domain = [
            ('grade_id', '=', wizard.grade_id.id),
            ('company_id', '=', wizard.company_id.id)
        ]
        if wizard.class_id:
            student_domain.append(('class_division_id', '=', wizard.class_id.id))
        
        students = self.env['education.student'].search(student_domain, order="seat_number")
        if wizard.student_ids:
            students = wizard.student_ids

        students_data = []
        for index, student in enumerate(students, 1):
            student_data = self._prepare_single_student_data(
                student, wizard, grading_method_type, index
            )
            students_data.append(student_data)
        
        return students_data

    def _prepare_single_student_data(self, student, wizard, grading_method_type, index):
        """Prepare data for a single student"""
        # Get student's term record
        st_acc_record = self.env['acc.student.term.grades'].search([
            ('company_id', '=', wizard.company_id.id),
            ('student_id', '=', student.id),
            ('term_id', '=', wizard.term_id.id),
            ('grade_id', '=', wizard.grade_id.id)
        ], limit=1)

        # Get elective subjects for this student
        elective_syllabuses = self.env['mc.elective.syllabus.students'].search([
            ('student_id', '=', student.id),
            ('company_id', '=', wizard.company_id.id),
            ('grade_id', '=', wizard.grade_id.id)
        ]).mapped('syllabus_id.id')

        student_data = {
            'serial_no': index,
            'student': student.full_english_name,
            'student_code': getattr(student, 'student_code', '') or '',
            'total_score': st_acc_record.total if st_acc_record else 0.0,
            'total_max': st_acc_record.term_total if st_acc_record else 0.0,
            'subjects_results': {},
            'registered_subjects': [str(syllabus_id) for syllabus_id in elective_syllabuses]
        }

        # Prepare subject results based on grading method
        if st_acc_record:
            if grading_method_type == 'numeric':
                student_data['subjects_results'] = self._prepare_numeric_results(
                    st_acc_record, student_data['registered_subjects']
                )
            elif grading_method_type == 'q_colors':
                student_data['subjects_results'] = self._prepare_qcolors_results(
                    st_acc_record, student_data['registered_subjects'], wizard
                )

        return student_data

    def _prepare_numeric_results(self, st_acc_record, registered_subjects):
        """Prepare results for numeric grading system (British)"""
        subjects_results = {}
        
        for subject_line in st_acc_record.subject_line_ids:
            subject_id = str(subject_line.syllabus_id.id)
            syllabus = self.env['education.syllabus'].browse(int(subject_id))
            
            # Skip elective subjects if not registered
            if hasattr(syllabus, 'elective') and syllabus.elective and subject_id not in registered_subjects:
                continue

            subjects_results[subject_id] = {
                'british_monthly': subject_line.british_monthly or 0.0,
                'british_monthly_max': subject_line.british_monthly_max or 0.0,
                'british_weekly': subject_line.british_weekly or 0.0,
                'british_weekly_max': subject_line.british_weekly_max or 0.0,
                'british_exam': subject_line.british_exam or 0.0,
                'british_exam_max': subject_line.british_exam_max or 0.0,
                'british_total': subject_line.british_total or 0.0,
                'british_total_max': subject_line.british_total_max or 0.0,
                'total': subject_line.total_subject_score or 0.0,
                'max_score': subject_line.total_subject_max or 0.0,
                'grade': subject_line.grading_info or ''
            }
        
        return subjects_results

    def _prepare_qcolors_results(self, st_acc_record, registered_subjects, wizard):
        """Prepare results for q_colors grading system"""
        subjects_results = {}
        
        for subject_line in st_acc_record.subject_line_ids:
            subject_id = str(subject_line.syllabus_id.id)
            syllabus = self.env['education.syllabus'].browse(int(subject_id))
            
            if syllabus.elective and subject_id not in registered_subjects:
                continue

            # Prepare assessments data
            assessments_data = {}
            for assess_line in subject_line.assessment_line_ids:
                assessments_data[str(assess_line.assessment_id.id)] = {
                    'score': assess_line.score or 0.0,
                    'max_score': assess_line.max_score or 0.0
                }
            
            # Prepare distributions data
            distributions_data = {}
            for dist_line in subject_line.distribution_line_ids:
                distributions_data[str(dist_line.distribution_id.id)] = {
                    'score': dist_line.score or 0.0,
                    'max_score': dist_line.max_score or 0.0
                }
            
            subjects_results[subject_id] = {
                'assessments': assessments_data,
                'distributions': distributions_data,
                'total': subject_line.total_subject_score or 0.0,
                'max_score': subject_line.total_subject_max or 0.0,
                'grade': self._get_grade_scale(
                    subject_line.total_subject_score or 0.0,
                    subject_line.total_subject_max or 0.0,
                    wizard
                )
            }
        
        return subjects_results

    def _prepare_syllabus_data(self, wizard, grading_method_type):
        """Prepare syllabus data based on grading method"""
        grade_syllabuses = self.env['education.syllabus'].search([
            ('company_id', '=', wizard.company_id.id),
            ('class_id', '=', wizard.grade_id.id),
            ('hidden_management_report', '=', False)
        ])

        syllabus_data = []
        
        if grading_method_type == 'numeric':
            syllabus_data = self._prepare_numeric_syllabus_data(grade_syllabuses)
        elif grading_method_type == 'q_colors':
            syllabus_data = self._prepare_qcolors_syllabus_data(grade_syllabuses, wizard)
        
        return syllabus_data

    def _prepare_numeric_syllabus_data(self, grade_syllabuses):
        """Prepare syllabus data for numeric system"""
        syllabus_data = []
        
        for syllabus in grade_syllabuses:
            syllabus_info = {
                'id': syllabus.id,
                'name': syllabus.name,
                'certificate_name': syllabus.certificate_name,
                'elective': syllabus.elective if hasattr(syllabus, 'elective') else False,
                'british_categories': {
                    'monthly': {'name': 'Monthly'},
                    'weekly': {'name': 'Weekly'}, 
                    'exam': {'name': 'Exam'}
                }
            }
            syllabus_data.append(syllabus_info)
        
        return syllabus_data

    def _prepare_qcolors_syllabus_data(self, grade_syllabuses, wizard):
        """Prepare syllabus data for q_colors system"""
        syllabus_data = []
        
        for syllabus in grade_syllabuses:
            syllabus_template = self.env['mc.custom.template'].sudo().search([
                ('company_id', '=', wizard.company_id.id),
                ('grade_id', '=', wizard.grade_id.id),
                ('syllabus_id', '=', syllabus.id),
                ('school_year_id', '=', wizard.term_id.academic_year_id.id)
            ], limit=1)
            
            if syllabus_template:
                syllabus_data.append({
                    'certificate_name': syllabus.certificate_name,
                    'syllabus_id': str(syllabus.id),
                    'syllabus_name': syllabus.name,
                    'is_elective': syllabus.elective,
                    'distributions': [
                        {
                            'id': str(dist.id),
                            'name': dist.item.name if hasattr(dist, 'item') and dist.item and hasattr(dist.item, 'name') and dist.item.name else 'N/A'
                        }
                        for dist in syllabus_template.custom_grade_distribution_template
                        if (
                            hasattr(dist, 'item') and dist.item and hasattr(dist.item, 'assessment') and not dist.item.assessment
                            and
                            hasattr(dist, 'control') and dist.control != 'project'
                        )
                    ],
                    'assessments': [
                        {
                            'id': str(assess.id),
                            'name': assess.item.name if hasattr(assess, 'item') and assess.item and hasattr(assess.item, 'name') and assess.item.name else 'N/A'
                        }
                        for assess in syllabus_template.assessments_category_id
                    ],
                    'maximum': syllabus_template.maximum or 0.0
                })
        
        return syllabus_data

    def _sort_and_rank_students(self, students_data, top_rank):
        """Sort students by total score and assign ranks"""
        # Sort students by total score for ranking
        students_data.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Assign ranks
        for rank, student_data in enumerate(students_data, 1):
            student_data['rank'] = rank

        # Apply top rank filter if specified
        if top_rank and top_rank > 0:
            students_data = students_data[:top_rank]
            # Re-assign ranks after filtering
            for rank, student_data in enumerate(students_data, 1):
                student_data['rank'] = rank
        
        return students_data

    def _get_grade_scale(self, score, max_score, wizard):
        """Get grade scale based on percentage"""
        if max_score == 0:
            return ''
        
        percentage = (score / max_score) * 100
        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', wizard.grade_id.id),
            ('company_id', '=', wizard.company_id.id),
            ('school_year_id', '=', wizard.term_id.academic_year_id.id)
        ], limit=1)
        
        if not grading_method:
            return ''
        
        for scale in grading_method.grading_scale_id:
            if scale.minimum <= percentage <= scale.maximum:
                return scale.symbol or ''
        
        return ''