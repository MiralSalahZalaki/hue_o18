from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccStudentTermGrades(models.Model):
    _name = 'acc.student.term.grades'
    _description = 'Student Term Grades'
    _rec_name = 'name'
    _order = 'seat_number, term_id'
    
    name = fields.Char(
        string="Reference",
        compute="_compute_name",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)
    student_id = fields.Many2one('education.student', string="Student", required=True,
                                 domain="[('company_id', '=', company_id)]")
    grade_id = fields.Many2one('education.class', related="student_id.grade_id")
    class_id = fields.Many2one('education.class.division', related="student_id.class_division_id")
    seat_number = fields.Char(related='student_id.seat_number', string="Seat Number", store=True)
    term_id = fields.Many2one('education.academic.term', string="Term", required=True)
    academic_year_id = fields.Many2one('education.academic.year', related="term_id.academic_year_id")

    absence_days = fields.Float(string="Absence Days", compute="_compute_absence_days", store=True)
    ministry_total = fields.Float(string="Ministry Total")
    total = fields.Float(string="Total", compute="_compute_total", store=True, digits=(12, 2))
    term_total = fields.Float(string="Term Total", compute="_compute_total", store=True, digits=(12, 2))
    # Lines for subjects
    subject_line_ids = fields.One2many('acc.student.term.subject.line', 'parent_id',
                                       string="Subject Lines")

    @api.depends('student_id', 'grade_id', 'term_id')
    def _compute_name(self):
        for rec in self:
            st_name = rec.student_id.full_english_name or 'Unknown'
            grade_number = rec.grade_id.name or 'Unknown'
            term_name = rec.term_id.name or ''
            term_number = ''.join(filter(str.isdigit, term_name)) or 'Unknown'
            rec.name = f"{st_name} - G.{grade_number}-T{term_number}"

    @api.constrains('student_id', 'term_id')
    def _check_unique_record(self):
        for rec in self:
            if self.env['acc.student.term.grades'].sudo().search_count([
                ('student_id', '=', rec.student_id.id),
                ('term_id', '=', rec.term_id.id),
                ('id', '!=', rec.id)
            ]):
                raise ValidationError(
                    f"Record already exists for student {rec.student_id.name} "
                    f"in term {rec.term_id.name}"
                )

    @api.depends('term_id', 'grade_id', 'student_id', 'class_id')
    def _compute_absence_days(self):
        for rec in self:
            rec.absence_days = 0.0  # Default value
            if not all([rec.student_id, rec.term_id, rec.grade_id, rec.class_id, 
                       rec.term_id.start_date, rec.term_id.end_date]):
                continue
            absence_days_count = self.env['education.attendance.line'].sudo().search_count([
                ('company_id', '=', rec.company_id.id),
                ('student_id', '=', rec.student_id.id),
                ('class_id', '=', rec.grade_id.id),
                ('division_id', '=', rec.class_id.id),
                ('date', '>=', rec.term_id.start_date),
                ('date', '<=', rec.term_id.end_date),
                ('present_morning', '=', False),
                ('sickness_absence',"=",False)
            ])
            rec.absence_days = absence_days_count

    def _get_company_system_type(self):
        """Get the system type for the current company."""
        system_setting = self.env['system.settings'].sudo().search([
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        return system_setting.system_type if system_setting else 'general'

    @api.depends('subject_line_ids.total_subject_score', 'subject_line_ids.total_subject_max')
    def _compute_total(self):
        for rec in self:
            rec.total = round(sum(line.total_subject_score for line in rec.subject_line_ids),2)
            rec.term_total = round(sum(line.total_subject_max for line in rec.subject_line_ids))



class AccStudentTermSubjectLine(models.Model):
    _name = 'acc.student.term.subject.line'
    _description = 'Student Term Subject Lines'
    _rec_name = 'syllabus_id'

    parent_id = fields.Many2one('acc.student.term.grades', string="Student Term Grades",
                                required=True, ondelete='cascade')

    syllabus_id = fields.Many2one('education.syllabus', string="Subject", required=True,
                                  domain="[('company_id', '=', company_id), ('class_id', '=', grade_id)]")

    # Reference fields from parent
    student_id = fields.Many2one('education.student', related="parent_id.student_id", store=True)
    term_id = fields.Many2one('education.academic.term', related="parent_id.term_id", store=True)
    grade_id = fields.Many2one('education.class', related="parent_id.grade_id", store=True)
    company_id = fields.Many2one('res.company', related="parent_id.company_id", store=True)

    # British System specific fields
    british_monthly = fields.Float(string="British Monthly", default=0.0, digits=(12, 2))
    british_weekly = fields.Float(string="British Weekly", default=0.0, digits=(12, 2))
    british_exam = fields.Float(string="British Exam", default=0.0, digits=(12, 2))
    british_total = fields.Float(string="British Total", compute="_compute_british_total", store=True, digits=(12, 2))

    british_monthly_max = fields.Float(string="British Monthly Max", default=0.0, digits=(12, 2))
    british_weekly_max = fields.Float(string="British Weekly Max", default=0.0, digits=(12, 2))
    british_exam_max = fields.Float(string="British Exam Max", default=0.0, digits=(12, 2))
    british_total_max = fields.Float(string="British Total Max", compute="_compute_british_total_max", store=True, digits=(12, 2))

    grading_method = fields.Char(
        string="Grading Method",
        compute="_compute_grading_method",
        store=True
    )

    @api.depends('grade_id', 'company_id', 'term_id.academic_year_id')
    def _compute_grading_method(self):
        """Compute grading method for this subject line"""
        for rec in self:
            rec.grading_method = "numeric"  # default
            if not all([rec.grade_id, rec.company_id, rec.term_id.academic_year_id]):
                continue

            grading_method_record = self.env['mc.grading.method'].sudo().search([
                ('company_id', '=', rec.company_id.id),
                ('grade_id', '=', rec.grade_id.id),
                ('school_year_id', '=', rec.term_id.academic_year_id.id)
            ], limit=1)

            if grading_method_record:
                rec.grading_method = grading_method_record.grading_method or "numeric"

            
    @api.depends('british_monthly_max', 'british_weekly_max', 'british_exam_max')
    def _compute_british_total_max(self):
        """حساب المجموع الكلي للدرجات القصوى في النظام البريطاني"""
        for rec in self:
            rec.british_total_max = rec.british_monthly_max + rec.british_weekly_max + rec.british_exam_max

    # Lines for distributions (for non-British systems)
    distribution_line_ids = fields.One2many('acc.student.term.subject.distribution.line', 'parent_id',
                                            string="Distribution Lines")

    # Lines for assessments (for non-British systems)
    assessment_line_ids = fields.One2many('acc.student.term.subject.assessment.line', 'parent_id',
                                          string="Assessment Lines")

    total_subject_score = fields.Float(string="Student Subject Total", compute="_compute_totals", store=True, digits=(12, 2))
    total_subject_max = fields.Float(string="Subject Score", compute="_compute_max_subject_score", store=True, digits=(12, 2))
   
    # Add this field in AccStudentTermSubjectLine class
    grading_info = fields.Char(string="Grading Symbole", compute="_compute_grading_info", store=True)

    @api.depends('british_monthly', 'british_weekly', 'british_exam')
    def _compute_british_total(self):
        for rec in self:
            rec.british_total = rec.british_monthly + rec.british_weekly + rec.british_exam

    @api.depends('total_subject_score', 'total_subject_max', 'grade_id', 'company_id', 'term_id.academic_year_id')
    def _compute_grading_info(self):
        """Compute grading symbol based on percentage and grading scale."""
        for rec in self:
            rec.grading_info = rec._get_grade_scale()

    def _get_grade_scale(self):
        """Get grade scale symbol based on percentage."""
        if self.total_subject_max == 0:
            return ''
        
        percentage = (self.total_subject_score / self.total_subject_max) * 100
        
        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', self.grade_id.id),
            ('company_id', '=', self.company_id.id),
            ('school_year_id', '=', self.term_id.academic_year_id.id)
        ], limit=1)
                    
        if not grading_method:
            return ''
                    
        for scale in grading_method.grading_scale_id:
            if scale.minimum <= percentage <= scale.maximum:
                return scale.symbol or ''
        
        return ''

    def _get_company_system_type(self):
        """Get the system type for the current company."""
        system_setting = self.env['system.settings'].sudo().search([
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        return system_setting.system_type if system_setting else 'general'
    
    @api.depends('distribution_line_ids.score', 'assessment_line_ids.score', 'british_total')
    def _compute_totals(self):
        for rec in self:
            system_type = rec._get_company_system_type()
            if system_type == 'british':
                rec.total_subject_score = rec.british_total
            else:
                # Reset totals
                rec.total_subject_score = 0.0
     
                # Sum scores from distribution lines
                for line in rec.distribution_line_ids:
                    rec.total_subject_score += line.score or 0.0
                    
                # Sum scores from assessment lines
                for line in rec.assessment_line_ids:
                    rec.total_subject_score += line.score or 0.0
              
    
    # Max Total Subject => Come from Syllabus Template 
    @api.depends('syllabus_id', 'company_id', 'grade_id', 'term_id.academic_year_id', 'british_total_max')
    def _compute_max_subject_score(self):
        """Update total_subject_max based on system type."""
        for rec in self:
            system_type = rec._get_company_system_type()
            
            if system_type == 'british':
                # For British system, use the sum of max scores
                rec.total_subject_max = rec.british_total_max
            else:
                # Existing logic for other systems
                rec.total_subject_max = 0.0
                if not all([rec.syllabus_id, rec.company_id, rec.grade_id, rec.term_id.academic_year_id]):
                    continue

                grading_method_record = rec.env['mc.grading.method'].sudo().search([
                    ('company_id', '=', rec.company_id.id),
                    ('grade_id', '=', rec.grade_id.id),
                    ('school_year_id', '=', rec.term_id.academic_year_id.id),
                ], limit=1)

                use_weight_scoring = False
                if grading_method_record and grading_method_record.grading_method not in ['numeric']:
                    use_weight_scoring = True

                subject_temp = rec.env['mc.custom.template'].sudo().search([
                    ('company_id', '=', rec.company_id.id),
                    ('grade_id', '=', rec.grade_id.id),
                    ('school_year_id', '=', rec.term_id.academic_year_id.id),
                    ('syllabus_id', '=', rec.syllabus_id.id),
                ], limit=1)
                    
                total_score = subject_temp.weight if use_weight_scoring else subject_temp.maximum or 0
                project_distribution_score = sum(
                    dist.weight if use_weight_scoring else dist.maximum for dist in subject_temp.custom_grade_distribution_template 
                    if dist.control == 'project'
                )
                max_subject_score = total_score - project_distribution_score
                rec.total_subject_max = max_subject_score


    @api.constrains('parent_id', 'syllabus_id')
    def _check_unique_subject(self):
        for rec in self:
            existing = self.sudo().search([
                ('parent_id', '=', rec.parent_id.id),
                ('syllabus_id', '=', rec.syllabus_id.id),
                ('id', '!=', rec.id)
            ])
            if existing:
                raise ValidationError(
                    f"Subject {rec.syllabus_id.name} already exists for this student term record"
                )


class AccStudentTermSubjectDistributionLine(models.Model):
    _name = 'acc.student.term.subject.distribution.line'
    _description = 'Student Term Subject Distribution Lines'
    _rec_name = 'distribution_id'

    parent_id = fields.Many2one('acc.student.term.subject.line', string="Student Term Subject",
                                required=True, ondelete='cascade')

    distribution_id = fields.Many2one('mc.custom.distribution', string="Distribution", required=True)
    description = fields.Char(string="Description")

    # Score fields
    max_score = fields.Float(string="Max Score", default=0.0)
    score = fields.Float(string="Student Score", default=0.0)
    check = fields.Boolean(string='Check', default=True)  # حقل جديد لتخزين حالة الحضور

    # Reference fields from parent
    student_id = fields.Many2one('education.student', related="parent_id.student_id", store=True)
    syllabus_id = fields.Many2one('education.syllabus', related="parent_id.syllabus_id", store=True)
    term_id = fields.Many2one('education.academic.term', related="parent_id.term_id", store=True,  domain="[('school_year_id.company_id', '=', company_id)]")

    # Distribution details
    distribution_name = fields.Char(related="distribution_id.item.name", string="Distribution Name")
    control_type = fields.Selection(related="distribution_id.control", string="Control Type")



    @api.constrains('parent_id', 'distribution_id')
    def _check_unique_distribution(self):
        for rec in self:
            existing = self.sudo().search([
                ('parent_id', '=', rec.parent_id.id),
                ('distribution_id', '=', rec.distribution_id.id),
                ('id', '!=', rec.id)
            ])
            if existing:
                raise ValidationError(
                    f"Distribution {rec.distribution_id.item.name} already exists for this subject"
                )


class AccStudentTermSubjectAssessmentLine(models.Model):
    _name = 'acc.student.term.subject.assessment.line'
    _description = 'Student Term Subject Assessment Lines'
    _rec_name = 'assessment_id'

    parent_id = fields.Many2one('acc.student.term.subject.line', string="Student Term Subject",
                                required=True, ondelete='cascade')

    assessment_id = fields.Many2one('mc.custom.assessments.category', string="Assessment Category", required=True)
    description = fields.Char(string="Description")


    # Score fields
    max_score = fields.Float(string="Max Score", default=0.0)
    score = fields.Float(string="Student Score", default=0.0)

    # Reference fields from parent
    student_id = fields.Many2one('education.student', related="parent_id.student_id", store=True)
    syllabus_id = fields.Many2one('education.syllabus', related="parent_id.syllabus_id", store=True)
    term_id = fields.Many2one('education.academic.term', related="parent_id.term_id", store=True)

    # Assessment details
    assessment_name = fields.Char(related="assessment_id.item.name", string="Assessment Name")
    control_type = fields.Selection(related="assessment_id.control", string="Control Type")

    @api.constrains('parent_id', 'assessment_id')
    def _check_unique_assessment(self):
        for rec in self:
            existing = self.sudo().search([
                ('parent_id', '=', rec.parent_id.id),
                ('assessment_id', '=', rec.assessment_id.id),
                ('id', '!=', rec.id)
            ])
            if existing:
                raise ValidationError(
                    f"Assessment {rec.assessment_id.item.name} already exists for this subject"
                )