from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessError


class MCEvaluationGrades(models.Model):
    _name = 'mc.evaluation.grades'
    _rec_name = 'syllabus_id'
    _inherit = ['mail.thread']


    active = fields.Boolean(string="Active", default=True)
    syllabus_id = fields.Many2one("education.syllabus", string="Syllabus", required=True)
    student_list = fields.One2many("mc.evaluation.grades.student.list", "connect_id", string="Students")
    grade_id = fields.Many2one("education.class", string="Grade", readonly=True, related="syllabus_id.class_id")
    class_id = fields.Many2one("education.class.division", string="Class", required=True, domain="[('class_id', '=', grade_id)]")
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)
    date = fields.Date(string="Date", required=True)
    distribution_id = fields.Many2one("mc.custom.distribution", string="Grade Distribution", required=True)
    assessments_category_id = fields.Many2one("mc.custom.assessments.category", string="Assessment Category")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string="State", default='draft', required=True,  tracking=True)
    grading_method_type = fields.Char(string="Grading Method Type", compute="_compute_grading_method_type", store=True)
    assessments_times = fields.Many2one("mc.assessment.times", string="Assessments Times", readonly=True, compute="_compute_assessment_time", store=True)
    another_max_score = fields.Float(string="Maximum")
    filter_comp = fields.Boolean(string="Filter Comp")
    check_student = fields.Boolean(string="Check Student")
    max_score = fields.Float(string="Max Score")
    custom_max_score = fields.Float(string="Max Score", required=True)
    syllabus_seq = fields.Integer(string="Sequence", readonly=True)
    tree_clo_acl_ids = fields.Char(string="Tree Clo Acl")
    
    # Add computed field to check if distribution is assessment
    is_distribution_assessment = fields.Boolean(string="Is Assessment", compute="_compute_is_distribution_assessment", store=True)

    assessments_domain = fields.Char(compute='_compute_distribution_assessments_domain')
    distribution_domain = fields.Char(compute='_compute_distribution_assessments_domain')

    syllabus_domain = fields.Char(compute='_compute_faculty_domains')
    class_division_domain = fields.Char(compute='_compute_faculty_domains')

    @api.depends('distribution_id', 'distribution_id.item', 'distribution_id.item.assessment')
    def _compute_is_distribution_assessment(self):
        for rec in self:
            rec.is_distribution_assessment = bool(rec.distribution_id and rec.distribution_id.item and rec.distribution_id.item.assessment)
    
    @api.depends('syllabus_id', 'grade_id')
    def _compute_distribution_assessments_domain(self):
            for rec in self:
                if rec.syllabus_id and rec.grade_id:
                    custom_templates = self.env['mc.custom.template'].search([
                        ('syllabus_id', '=', rec.syllabus_id.id),
                        ('grade_id', '=', rec.grade_id.id),
                        ('company_id', '=', rec.company_id.id),
                    ])  
                    
                    if custom_templates:
                        distribution_ids = []
                        assessments_ids = []
                        
                        for template in custom_templates:
                            distribution_ids.extend(template.custom_grade_distribution_template.ids)
                            assessments_ids.extend(template.assessments_category_id.ids)
                        
                        distribution_ids = list(set(distribution_ids))
                        assessments_ids = list(set(assessments_ids))
                        
                        rec.distribution_domain = str([
                            ('id', 'in', distribution_ids),
                            ('control', 'not in', ['control', 'project'])
                        ])
                        
                        rec.assessments_domain = str([('id', 'in', assessments_ids)])
                    else:
                        rec.distribution_domain = str([('id', '=', False)])
                        rec.assessments_domain = str([('id', '=', False)])
                else:
                    rec.distribution_domain = str([('id', '=', False)])
                    rec.assessments_domain = str([('id', '=', False)])

    @api.depends('grade_id')
    def _compute_grading_method_type(self):
        for rec in self:
            if rec.grade_id:
                grading_method = self.env['mc.grading.method'].search([('grade_id', '=', rec.grade_id.id)], limit=1)
                rec.grading_method_type = grading_method.grading_method if grading_method else ''
            else:
                rec.grading_method_type = ''

    @api.onchange('grade_id')
    def _onchange_grade(self):
        if self.grade_id:
            self.class_id = False

    @api.onchange('assessments_category_id')
    def _onchange_assessments_category_id(self):
        for rec in self:
            if rec.assessments_category_id :
                rec.custom_max_score = rec.assessments_category_id.max_score
            else:
                rec.custom_max_score = False

    @api.depends('company_id', 'grade_id', 'date', 'distribution_id', 'distribution_id.item', 'distribution_id.item.assessment')
    def _compute_assessment_time(self):
        for rec in self:
            rec.assessments_times = False
            if rec.company_id and rec.grade_id and rec.date and rec.distribution_id:
                # Determine the distribution filter based on distribution_id.item.assessment
                if rec.distribution_id.item and rec.distribution_id.item.assessment:
                    # If distribution is assessment, get times where distribution = False
                    distribution_filter = False
                else:
                    # If distribution is control, get times where distribution = True  
                    distribution_filter = True
                
                assessment_time_id = self.env['mc.assessment.times'].search([
                    ('company_id', '=', rec.company_id.id),
                    ('grade_ids', 'in', [rec.grade_id.id]),
                    ('start_date', '<=', rec.date),
                    ('end_date', '>=', rec.date),
                    ('distribution', '=', distribution_filter)
                ], limit=1)
                rec.assessments_times = assessment_time_id.id if assessment_time_id else False

    def set_done(self):
        for rec in self:
            if rec.assessments_times and rec.student_list and rec.state == "draft":
                rec.check_access('write')   # <-- يمنع المستخدم غير المصرح له
                rec.write({"state": "done"})
                rec.check_student = True


    def set_draft(self):
        for rec in self:
            if rec.assessments_times and rec.student_list and rec.state == "done":
                rec.check_access('write')
                rec.write({"state": "draft"})
                rec.check_student = False


    # Delete all related student_list records before deleting the main record
    def unlink(self):
        for record in self:
            # تحقق صلاحية حذف على السجل الرئيسي
            record.check_access('unlink')
            if record.student_list:
                # تحقق صلاحية حذف على موديل student list
                self.env['mc.evaluation.grades.student.list'].check_access_rights('unlink')
                record.student_list.unlink()
        return super(MCEvaluationGrades, self).unlink()



    def get_students_list(self):
        for rec in self:
            # تحقق بسيط إن فقط المدرس أو الادمن يقدر ينفذ
            if not (self.env.user._has_group('mc_app.employee_group') or self.env.user._has_group('base.group_system')):
                raise AccessError("ليس لديك صلاحية لجلب قائمة الطلاب")
            
            if rec.syllabus_id and rec.class_id:
                if not rec.syllabus_id.elective:
                    enrolled_students = self.env['education.student'].search([
                        ('grade_id', '=', rec.grade_id.id),
                        ('class_division_id', '=', rec.class_id.id),
                        ('company_id', '=', rec.company_id.id),
                    ])
                else:
                    enrolled_students = rec.syllabus_id.students.mapped('student_id')     

                # Get existing student IDs in the student_list
                existing_student_ids = rec.student_list.mapped('student_id.id')

                # Prepare new student records for those not already in student_list
                new_student_records = [
                    {
                        'connect_id': rec.id,
                        'check': True,
                        'student_id': student.id,
                        'grading_method': self.env['mc.grading.method'].search([
                            ('grade_id', '=', rec.grade_id.id)
                        ], limit=1).id or False,
                    } for student in enrolled_students if student.id not in existing_student_ids
                ]

                # Create new student records if any
                if new_student_records:
                    # تحقق إن المستخدم له صلاحية إنشاء على موديل student list
                    self.env['mc.evaluation.grades.student.list'].check_access_rights('create')
                    # (اختياري) تحقق على كل سجل إن لديه صلاحية لربطه - هنا نعتبر كافياً check_access_rights
                    self.env['mc.evaluation.grades.student.list'].create(new_student_records)
                    rec.check_student = True
                else:
                    rec.check_student = False
            else:
                # If no syllabus per class is found, set check_student to False
                rec.check_student = False

    def fill_score(self):
        for rec in self:
            rec.check_access('write')   # صلاحية تعديل على السجل الرئيسي
            if rec.custom_max_score and rec.custom_max_score > 0:
                for student in rec.student_list:
                    student.check_access('write')   # اختياري لكن موصى به
                    student.score = rec.custom_max_score
            else:
                raise ValidationError("Please set a valid Maximum Score greater than 0 before filling scores.")


    
    def open_garde_dist(self):
        pass


    # Faculty Access 

    # Get Current User

    # if he is faculty get his syllbaus

    @api.model
    def _get_current_faculty(self):
        """جلب بيانات المدرس الحالي"""
        if self.env.user:
            faculty = self.env['education.faculty'].sudo().search([
                ('user_id', '=', self.env.user.id)
            ], limit=1)
            return faculty
        return False
    
    @api.depends('syllabus_id', 'class_id')
    def _compute_faculty_domains(self):
        """حساب domains للمناهج والفصول"""
        for rec in self:
            try:
                # لو المستخدم له صلاحية admin (مدير)
                if self.env.user._has_group('base.group_system'):
                    # كل المناهج الخاصة بالشركة (المدرسة)
                    syllabus_ids = self.env['education.syllabus'].search([
                        ('company_id', '=', rec.company_id.id)
                    ]).ids
                    rec.syllabus_domain = str([('id', 'in', syllabus_ids)])
                    
                    # كل الفصول الخاصة بالشركة (المدرسة)
                    class_division_ids = self.env['education.class.division'].search([
                        ('school_id', '=', rec.company_id.id),
                        ('class_id','=',rec.grade_id.id)
                    ]).ids
                    rec.class_division_domain = str([('id', 'in', class_division_ids)])
                    continue  # نكمل للسجل التالي، مفيش فلترة خاصة بالمدرس
                    
                # لو مش admin نطبق فلترة المدرس
                faculty = self._get_current_faculty()
                if faculty:
                    # جمع IDs المناهج المسموح بها
                    allowed_syllabus_ids = list(set(
                        [line.syllabus_id.id for line in faculty.syllabus_special_class if line.syllabus_id] +
                        [line.syllabus_id.id for line in faculty.syllabus_class if line.syllabus_id]
                    ))
                    rec.syllabus_domain = str([('id', 'in', allowed_syllabus_ids)]) if allowed_syllabus_ids else str([('id', '=', False)])

                    # حساب الفصول المسموح بها
                    allowed_class_divisions = []
                    if rec.syllabus_id:
                        allowed_class_divisions = list(set(
                            [line.class_division_id.id for line in faculty.syllabus_special_class if line.syllabus_id and line.syllabus_id.id == rec.syllabus_id.id and line.class_division_id] +
                            [line.class_division_id.id for line in faculty.syllabus_class if line.syllabus_id and line.syllabus_id.id == rec.syllabus_id.id and line.class_division_id]
                        ))
                    else:
                        allowed_class_divisions = list(set(
                            [line.class_division_id.id for line in faculty.syllabus_special_class if line.class_division_id] +
                            [line.class_division_id.id for line in faculty.syllabus_class if line.class_division_id]
                        ))
                    rec.class_division_domain = str([('id', 'in', allowed_class_divisions), ('school_id', '=', rec.company_id.id),
                                    ('class_id', '=', rec.grade_id.id)]) if allowed_class_divisions else str([('id', '=', False)])
                else:
                    rec.syllabus_domain = str([('id', '=', False)])
                    rec.class_division_domain = str([('id', '=', False)])

            except Exception:
                rec.syllabus_domain = str([('id', '=', False)])
                rec.class_division_domain = str([('id', '=', False)])