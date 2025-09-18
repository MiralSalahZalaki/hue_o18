from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MCAddGradingComments(models.Model):
    _name = 'mc.add.grading.comments'
    _description = 'Add Grading Comments'

    company_id = fields.Many2one('res.company', string='School', default=lambda self: self.env.company)
    term_id = fields.Many2one('education.academic.term', string="Term",  domain="[('school_year_id.company_id', '=', company_id)]")
    grade_id = fields.Many2one('education.class', string="Grade", required=True, domain="[('school', '=', company_id)]")
    syllabus_id = fields.Many2one('education.syllabus', string="Syllabus", domain="[('class_id', '=', grade_id)]")
    grading_type = fields.Many2one('mc.grading.types', string="Grading Type", required=True)
    grading_comment = fields.Many2one('mc.grading.comments', string="Grading Comment", required=True, domain="[('grading_type_id', '=', grading_type)]")
    student_list = fields.One2many('add.grading.comment.student.list', 'connect_id', string="Students")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default="draft", string="State", required=True)
    active = fields.Boolean(string="Active", default=True)
    check_student = fields.Boolean(string="Check Student")
    tree_clo_acl_ids = fields.Char(string="Tree Clo Acl", readonly=True)
    year = fields.Many2one('education.academic.year', string="School Year", required=True)

    def set_done(self):
        for rec in self:
            if rec.student_list and rec.state == "draft":
                if all(student.grading_comment for student in rec.student_list):
                    rec.write({"state": "done"})
                else:
                    raise ValidationError("برجاء إضافة تعليق تقييم لكل الطلاب قبل تغيير الحالة إلى Done.")

    def set_draft(self):
        for rec in self:
            if rec.student_list and rec.state == "done":
                rec.write({"state": "draft"})

    def get_students_list(self):
        for rec in self:
            if rec.syllabus_id and rec.grade_id:
                students = self.env['education.student'].sudo().search([
                    ('grade_id', '=', rec.grade_id.id),
                    ('company_id', '=', rec.company_id.id),
                ])
                existing_student_ids = set(rec.student_list.mapped('student_id.id'))
                new_student_records = [
                    {
                        'connect_id': rec.id,
                        'check': True,
                        'student_id': student.id,
                        'grading_type': rec.grading_type.id,
                    } for student in students if student.id not in existing_student_ids
                ]
                if new_student_records:
                    self.env['add.grading.comment.student.list'].create(new_student_records)
                    rec.check_student = True
                else:
                    rec.check_student = False

    def fill_score(self):
        for rec in self:
            if rec.student_list and rec.grading_comment:
                rec.student_list.write({
                    'grading_comment': rec.grading_comment.id,
                })