from odoo import models, fields, api

class AddGradingCommentStudentList(models.Model):
    _name = 'add.grading.comment.student.list'

    connect_id = fields.Many2one('mc.add.grading.comments', string="Class")
    check = fields.Boolean(string="Attendence")
    student_id = fields.Many2one('education.student', readonly=True, domain="[('company_id', 'in', allowed_company_ids)]")
    class_id = fields.Many2one('education.class.division',  related="student_id.class_division_id", store=True)
    grading_type = fields.Many2one('mc.grading.types', string="Grading Type", required=True)
    seat_number = fields.Char(string="Seat Number", related="student_id.seat_number", store=True, readonly=True)
    grading_comment = fields.Many2one('mc.grading.comments', string="Notes")

  