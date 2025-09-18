from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccStudentMonthlyGrades(models.Model): 
    _name = 'acc.student.monthly.grades' 
    _description = 'Student Monthly Grades'
    _rec_name = 'name'
    _order = 'student_id, assesment_time'
    
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
    assesment_time = fields.Many2one('mc.assessment.times', string="Assessment Time", required=True)
    academic_year_id = fields.Many2one('education.academic.year', compute="_compute_academic_year_id", store=True)

    absence_days = fields.Float(string="Absence Days", compute="_compute_absence_days", store=True)
    total = fields.Float(string="Total", compute="_compute_total", store=True, digits=(12, 2))
    time_total = fields.Float(string="Assessment Time Total", compute="_compute_total", store=True, digits=(12, 2))
    
    # Lines for subjects
    subject_line_ids = fields.One2many('acc.student.monthly.subject.line', 'parent_id',
                                       string="Subject Lines")
    
    description = fields.Char(string="Description")


   
    @api.depends('assesment_time')
    def _compute_academic_year_id(self):
        for rec in self:
            rec.academic_year_id = False  # Reset first
            if rec.assesment_time and rec.assesment_time.start_date and rec.assesment_time.end_date:
                # Find academic year that contains the assessment time period
                academic_year = self.env['education.academic.year'].sudo().search([
                    ('ay_start_date', '<=', rec.assesment_time.start_date),  # Fixed: start_date -> ay_start_date
                    ('ay_end_date', '>=', rec.assesment_time.end_date)       # Fixed: end_date -> ay_end_date
                ], limit=1)
                rec.academic_year_id = academic_year.id if academic_year else False

    @api.depends('student_id', 'grade_id', 'assesment_time')  # Fixed: Added more dependencies
    def _compute_name(self):
        for rec in self:
            st_name = rec.student_id.full_english_name or 'Unknown'
            grade_name = rec.grade_id.name or 'Unknown'
            time_name = rec.assesment_time.name or 'Unknown'
            rec.name = f"{st_name} - G.{grade_name} - {time_name}"

    @api.constrains('student_id', 'assesment_time')
    def _check_unique_record(self):
        for rec in self:
            if self.env['acc.student.monthly.grades'].sudo().search_count([  # Fixed: model name
                ('student_id', '=', rec.student_id.id),
                ('assesment_time', '=', rec.assesment_time.id),
                ('id', '!=', rec.id)
            ]):
                raise ValidationError(
                    f"Record already exists for student {rec.student_id.name} "
                    f"in time - {rec.assesment_time.name}"
                )

    @api.depends('assesment_time', 'grade_id', 'student_id', 'class_id')
    def _compute_absence_days(self):
        for rec in self:
            rec.absence_days = 0.0  # Default value
            if not all([rec.student_id, rec.assesment_time, rec.grade_id, rec.class_id, 
                       rec.assesment_time.start_date, rec.assesment_time.end_date]):
                continue
            absence_days_count = self.env['education.attendance.line'].sudo().search_count([
                ('company_id', '=', rec.company_id.id),
                ('student_id', '=', rec.student_id.id),
                ('class_id', '=', rec.grade_id.id),
                ('division_id', '=', rec.class_id.id),
                ('date', '>=', rec.assesment_time.start_date),
                ('date', '<=', rec.assesment_time.end_date),
                ('present_morning', '=', False),
                ('sickness_absence', "=", False)
            ])
            rec.absence_days = absence_days_count
    
    @api.depends('subject_line_ids.total_subject_score', 'subject_line_ids.total_subject_max')
    def _compute_total(self):
        for rec in self:
            rec.total = round(sum(line.total_subject_score for line in rec.subject_line_ids), 2)
            rec.time_total = round(sum(line.total_subject_max for line in rec.subject_line_ids))


class AccStudentMonthlySubjectLine(models.Model):
    _name = 'acc.student.monthly.subject.line' 
    _description = 'Student Monthly Subject Lines'
    _rec_name = 'syllabus_id'

    parent_id = fields.Many2one('acc.student.monthly.grades', string="Student Time Grades",  # Fixed: model name
                                required=True, ondelete='cascade')

    syllabus_id = fields.Many2one('education.syllabus', string="Subject", required=True,
                                  domain="[('company_id', '=', company_id), ('class_id', '=', grade_id)]")

    # Reference fields from parent
    student_id = fields.Many2one('education.student', related="parent_id.student_id", store=True)
    assesment_time = fields.Many2one('mc.assessment.times', related="parent_id.assesment_time", store=True)
    grade_id = fields.Many2one('education.class', related="parent_id.grade_id", store=True)
    company_id = fields.Many2one('res.company', related="parent_id.company_id", store=True)
    academic_year_id = fields.Many2one('education.academic.year', related="parent_id.academic_year_id", store=True)

    # Lines for assessments
    assessment_line_ids = fields.One2many('acc.student.monthly.subject.assessment.line', 'parent_id',
                                          string="Assessment Lines")

    total_subject_score = fields.Float(string="Student Subject Total", compute="_compute_totals", store=True, digits=(12, 2))
    total_subject_max = fields.Float(string="Subject Score", compute="_compute_max_subject_score", store=True, digits=(12, 2))


     # Add this field in AccStudentTermSubjectLine class
    grading_info = fields.Char(string="Grading Symbole", compute="_compute_grading_info", store=True)

    grading_method = fields.Char(
        string="Grading Method",
        compute="_compute_grading_method",
        store=True
    )

    @api.depends('grade_id', 'company_id', 'academic_year_id')
    def _compute_grading_method(self):
        """Compute grading method for this subject line"""
        for rec in self:
            rec.grading_method = "numeric"  # default
            if not all([rec.grade_id, rec.company_id, rec.academic_year_id]):
                continue

            grading_method_record = self.env['mc.grading.method'].sudo().search([
                ('company_id', '=', rec.company_id.id),
                ('grade_id', '=', rec.grade_id.id),
                ('school_year_id', '=', rec.academic_year_id.id)
            ], limit=1)

            if grading_method_record:
                rec.grading_method = grading_method_record.grading_method or "numeric"

    @api.depends('total_subject_score', 'total_subject_max', 'grade_id', 'company_id', 'academic_year_id')
    def _compute_grading_info(self):
        for rec in self:
            rec.grading_info = rec._get_grade_scale()

    def _get_grade_scale(self):
        if self.total_subject_max == 0:
            return ''
        
        percentage = (self.total_subject_score / self.total_subject_max) * 100
        
        grading_method = self.env['mc.grading.method'].sudo().search([
            ('grade_id', '=', self.grade_id.id),
            ('company_id', '=', self.company_id.id),
            ('school_year_id', '=', self.academic_year_id.id)
        ], limit=1)
                    
        if not grading_method:
            return ''
                    
        for scale in grading_method.grading_scale_id:
            if scale.minimum <= percentage <= scale.maximum:
                return scale.description or ''
        
        return ''


    @api.depends('assessment_line_ids.score')
    def _compute_totals(self):
        for rec in self:
            # Reset totals
            rec.total_subject_score = 0.0
            
            # Sum scores from assessment lines only (no distribution lines for monthly)
            for line in rec.assessment_line_ids:
                rec.total_subject_score += line.score or 0.0
              
    # Max Total Subject => Come from Syllabus Template 
    @api.depends('syllabus_id', 'company_id', 'grade_id', 'academic_year_id')  # Fixed: dependencies
    def _compute_max_subject_score(self):
        """Update total_subject_max based on syllabus template maximum score."""
        for rec in self:
            rec.total_subject_max = 0.0  # Default value
            if not all([rec.syllabus_id, rec.company_id, rec.grade_id, rec.academic_year_id]):
                continue
                
            max_subject_score = self.env['mc.custom.template'].sudo().search([
                ('company_id', '=', rec.company_id.id),
                ('grade_id', '=', rec.grade_id.id),
                ('school_year_id', '=', rec.academic_year_id.id),  # Fixed: term_id -> academic_year_id
                ('syllabus_id', '=', rec.syllabus_id.id),
            ], limit=1).total_assessments_score or 0.0
            rec.total_subject_max = max_subject_score

    @api.constrains('parent_id', 'syllabus_id')
    def _check_unique_subject(self):
        for rec in self:
            existing = self.env['acc.student.monthly.subject.line'].sudo().search_count([  # Fixed: model name
                ('parent_id', '=', rec.parent_id.id),
                ('syllabus_id', '=', rec.syllabus_id.id),
                ('id', '!=', rec.id)
            ])
            if existing:
                raise ValidationError(
                    f"Subject {rec.syllabus_id.name} already exists for this student time record"
                )


class AccStudentMonthlySubjectAssessmentLine(models.Model):
    _name = 'acc.student.monthly.subject.assessment.line'
    _description = 'Student Monthly Subject Assessment Lines'
    _rec_name = 'assessment_id'

    parent_id = fields.Many2one('acc.student.monthly.subject.line', string="Student Monthly Subject",  # Fixed: model reference
                                required=True, ondelete='cascade')

    assessment_id = fields.Many2one('mc.custom.assessments.category', string="Assessment Category", required=True)
    description = fields.Char(string="Description")

    # Score fields
    max_score = fields.Float(string="Max Score", default=0.0)
    score = fields.Float(string="Student Score", default=0.0)

    # Reference fields from parent
    student_id = fields.Many2one('education.student', related="parent_id.student_id", store=True)
    syllabus_id = fields.Many2one('education.syllabus', related="parent_id.syllabus_id", store=True)
    assesment_time = fields.Many2one('mc.assessment.times', related="parent_id.assesment_time", store=True)  # Fixed: term_id -> assesment_time

    # Assessment details
    assessment_name = fields.Char(related="assessment_id.item.name", string="Assessment Name")
    control_type = fields.Selection(related="assessment_id.control", string="Control Type")

    @api.constrains('parent_id', 'assessment_id')
    def _check_unique_assessment(self):
        for rec in self:
            existing = self.env['acc.student.monthly.subject.assessment.line'].sudo().search_count([
                ('parent_id', '=', rec.parent_id.id),
                ('assessment_id', '=', rec.assessment_id.id),
                ('id', '!=', rec.id)
            ])
            if existing:
                raise ValidationError(
                    f"Assessment {rec.assessment_id.item.name} already exists for this subject"
                )