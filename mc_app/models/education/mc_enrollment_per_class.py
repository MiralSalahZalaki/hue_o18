from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

class MCEnrollementPerClass(models.Model):
    _name = 'mc.enrollment.per.class'
    _description = 'Enrollment Per Class'
    
    name = fields.Char(compute="_compute_name")
    school_id = fields.Many2one('res.company')
    teacher_id = fields.Many2one('education.faculty')
    student_id = fields.Many2one('education.student')
    primary = fields.Boolean()
    active = fields.Boolean(default=True)
    role = fields.Selection([
        ('student','Student'),
        ('teacher','Teacher'),
    ])
    begin_date = fields.Date()
    end_date = fields.Date()
    user_class = fields.Many2one('mc.syllabus.per.class')

    _sql_constraints = [
        ('unique_student_id', 'UNIQUE(student_id, user_class)', "This student is already registered in this class."),
        ('unique_teacher_id', 'UNIQUE(teacher_id, user_class)', "This teacher is already registered in this class.")
    ]

    @api.depends('student_id', 'teacher_id')
    def _compute_name(self):
        for rec in self:
            if rec.student_id:
                rec.name = rec.student_id.full_english_name or rec.student_id.name
                rec.school_id = rec.student_id.company_id
                rec.role = 'student'
            elif rec.teacher_id:
                rec.role = 'teacher'
                rec.name = rec.teacher_id.name
                rec.school_id = rec.teacher_id.company_id

            else:
                rec.name = False  # إذا لم يكن هناك طالب أو معلم، يتم إفراغ الاسم

    """ @api.model
    def create(self, vals):
        record = super(MCEnrollementPerClass, self).create(vals)
        if record.role == 'teacher' and record.teacher_id and record.user_class:
            record.user_class.write({
                'faculty_regular_id': record.teacher_id.id
            })
        return record

    def write(self, vals):
        result = super(MCEnrollementPerClass, self).write(vals)
        if 'teacher_id' in vals or 'role' in vals:
            for record in self:
                if record.role == 'teacher' and record.teacher_id and record.user_class:
                    record.user_class.write({
                        'faculty_regular_id': record.teacher_id.id
                    })
        return result"""