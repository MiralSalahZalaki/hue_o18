from odoo import models, fields,api
from odoo.exceptions import ValidationError


class MCControlGrade(models.Model):
    _name = 'mc.control.grades'
    _inherit = ['mail.thread']

 
    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company, required=True)
    grade_id = fields.Many2one('education.class',  string="Grade")
    term_id = fields.Many2one('education.academic.term', domain="[('school_year_id.company_id', '=', company_id)]", required=True)
    syllabus_id = fields.Many2one("education.syllabus", string="Syllabus", required=True, domain="[('company_id', '=', company_id),('class_id', '=', grade_id)]")
    syllabus_grade = fields.Many2one('education.class', string="Syllabus Grade", related="syllabus_id.class_id")
    distribution_id = fields.Many2one('mc.custom.distribution', string="Grade Distribution", required=True)
    date = fields.Date()
    custom_max_score = fields.Float(string="Max Score", required=True)
    another_max_score = fields.Float(string="Maximum")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string="State", default='draft', required=True)
    student_list = fields.One2many("control.grades.student.list", "connect_id", string="Students")
    check_student = fields.Boolean(default=False)

    
    distribution_domain = fields.Char(compute='_compute_distribution_domain')

    
    syllabus_domain = fields.Char(compute='_compute_faculty_domains')
    grade_domain = fields.Char(compute='_compute_faculty_domains')

    @api.constrains('custom_max_score')
    def _check_max_score(self):
        for rec in self:
            if rec.custom_max_score == 0:
                raise ValidationError("Max Score mustn't equal 0")


    @api.depends('syllabus_id', 'grade_id', 'term_id')
    def _compute_distribution_domain(self):
        for rec in self:
            if rec.syllabus_id and rec.grade_id and rec.term_id:
                if rec.term_id.academic_year_id:
                    custom_templates = self.env['mc.custom.template'].sudo().search([
                        ('syllabus_id', '=', rec.syllabus_id.id),
                        ('grade_id', '=', rec.grade_id.id),
                        ('company_id', '=', rec.company_id.id),
                        ('school_year_id', '=', rec.term_id.academic_year_id.id),  # term is in the school year of template
                    ])
                    
                    if custom_templates:
                        distribution_ids = []
                        
                        for template in custom_templates:
                            distribution_ids.extend(template.custom_grade_distribution_template.ids)
                        
                        distribution_ids = list(set(distribution_ids))
                        
                        rec.distribution_domain = str([
                            ('id', 'in', distribution_ids),
                            ('control', 'in', ['control'])
                        ])
                    else:
                        rec.distribution_domain = str([('id', '=', False)])
                else:
                    rec.distribution_domain = str([('id', '=', False)])
            else:
                rec.distribution_domain = str([('id', '=', False)])

    @api.onchange('term_id')
    def _onchange_term(self):
        # عند تغيير الترم، للتأكد من أن التاريخ ضمن فترة الترم
        if self.term_id and self.date:
            if not (self.term_id.start_date <= self.date <= self.term_id.end_date):
                self.date = False
                return {
                    'warning': {
                        'title': 'Warning',
                        'message': 'التاريخ يجب أن يكون ضمن فترة الترم المحددة'
                    }
                }

    @api.onchange('date')
    def _onchange_date(self):
        # التحقق من أن التاريخ ضمن فترة الترم
        if self.date and self.term_id:
            if not (self.term_id.start_date <= self.date <= self.term_id.end_date):
                return {
                    'warning': {
                        'title': 'Warning',
                        'message': f'التاريخ يجب أن يكون بين {self.term_id.start_date} و {self.term_id.end_date}'
                    }
                }

    @api.constrains('date', 'term_id')
    def _check_date_within_term(self):
        """التحقق من أن التاريخ ضمن فترة الترم"""
        for rec in self:
            if rec.date and rec.term_id:
                if not (rec.term_id.start_date <= rec.date <= rec.term_id.end_date):
                    raise ValidationError(
                        f'التاريخ {rec.date} يجب أن يكون ضمن فترة الترم '
                        f'من {rec.term_id.start_date} إلى {rec.term_id.end_date}'
                    )

    @api.constrains('term_id')
    def _check_term_within_academic_year(self):
        """التحقق من أن الترم ضمن السنة الأكاديمية"""
        for rec in self:
            if rec.term_id and rec.term_id.academic_year_id:
                academic_year = rec.term_id.academic_year_id
                if not (academic_year.ay_start_date <= rec.term_id.start_date and 
                        rec.term_id.end_date <= academic_year.ay_end_date):
                    raise ValidationError(
                        f'الترم {rec.term_id.name} يجب أن يكون ضمن السنة الأكاديمية '
                        f'{academic_year.name}'
                    )

    @api.onchange('grade_id')
    def _onchange_grade(self):
        self.syllabus_id = False

    @api.onchange('distribution_id')
    def _onchange_distribution_id(self):
        for rec in self:
            if rec.distribution_id :
                rec.custom_max_score = rec.distribution_id.maximum
            else:
                rec.custom_max_score = False

    def set_done(self):
        for rec in self:
            if rec.student_list and rec.state == "draft":
                rec.write({"state": "done"})
                rec.check_student = True

    def set_draft(self):
        for rec in self:
            if rec.student_list and rec.state == "done":
                rec.write({"state": "draft"})
                rec.check_student = False

    # Delete all related student_list records before deleting the main record
    def unlink(self):
        for record in self:
            if record.student_list:
                record.student_list.unlink()  # Delete all related records in control.grades.student.list
        return super(MCControlGrade, self).unlink()


    def get_students_list(self):
        for rec in self:
            if rec.syllabus_id and rec.grade_id:
                if not rec.syllabus_id.elective : # Not Elective
                    enrolled_students = self.env['education.student'].sudo().search([
                    ('grade_id', '=', rec.grade_id.id),
                    ('company_id', '=', rec.company_id.id),
                ])
                    
                if rec.syllabus_id.elective :  # Elective
                    enrolled_students = rec.syllabus_id.students.mapped('student_id')        

                # Get existing student IDs in the student_list
                existing_student_ids = rec.student_list.mapped('student_id.id')

                new_student_records = [
                    {
                        'connect_id': rec.id,
                        'check': True,
                        'student_id': student.id,
                        'grading_method': self.env['mc.grading.method'].sudo().search([
                                ('grade_id', '=', rec.grade_id.id)
                            ], limit=1).id or False,
                    } for student in enrolled_students if student.id not in existing_student_ids
                ]
                if new_student_records:
                    self.env['control.grades.student.list'].create(new_student_records)
                    rec.check_student = True
                else:
                    rec.check_student = False

    def fill_score(self):
        for rec in self:
            if rec.custom_max_score and rec.custom_max_score > 0:
                for student in rec.student_list:
                    student.score = rec.custom_max_score
            else:
                raise ValidationError("Please set a valid Maximum Score greater than 0 before filling scores.")

    
    @api.model
    def _get_current_faculty(self):
        """جلب بيانات المدرس الحالي"""
        if self.env.user:
            faculty = self.env['education.faculty'].sudo().search([
                ('user_id', '=', self.env.user.id)
            ], limit=1)
            return faculty
        return False
    
    @api.depends('syllabus_id', 'grade_id')
    def _compute_faculty_domains(self):
        """حساب domains للمناهج والفصول"""
        for rec in self:
            try:
                # لو المستخدم له صلاحية admin (مدير)
                if self.env.user._has_group('base.group_system'):
                    # كل المناهج الخاصة بالشركة (المدرسة)
                    syllabus_ids = self.env['education.syllabus'].sudo().search([
                        ('company_id', '=', rec.company_id.id)
                    ]).ids
                    rec.syllabus_domain = str([('id', 'in', syllabus_ids)])
                    
                    # كل الفصول الخاصة بالشركة (المدرسة)
                    garde_ids = self.env['education.class'].sudo().search([
                        ('school', '=', rec.company_id.id)
                    ]).ids
                    rec.grade_domain = str([('id', 'in', garde_ids)])
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
                    allowed_grades = []
                    if rec.syllabus_id:
                        allowed_grades = list(set(
                            [line.class_id.id for line in faculty.syllabus_special_class if line.syllabus_id and line.syllabus_id.id == rec.syllabus_id.id and line.class_id] +
                            [line.class_id.id for line in faculty.syllabus_class if line.syllabus_id and line.syllabus_id.id == rec.syllabus_id.id and line.class_id]
                        ))
                    else:
                        allowed_grades = list(set(
                            [line.class_id.id for line in faculty.syllabus_special_class if line.class_id] +
                            [line.class_id.id for line in faculty.syllabus_class if line.class_id]
                        ))
                    rec.grade_domain = str([('id', 'in', allowed_grades)]) if allowed_grades else str([('id', '=', False)])
                else:
                    rec.syllabus_domain = str([('id', '=', False)])
                    rec.grade_domain = str([('id', '=', False)])

            except Exception:
                rec.syllabus_domain = str([('id', '=', False)])
                rec.grade_domain = str([('id', '=', False)])


