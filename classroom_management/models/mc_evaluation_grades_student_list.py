from odoo import models, fields, api

class MCEvaluationGradesStudentList(models.Model):
    _name = 'mc.evaluation.grades.student.list'

    connect_id = fields.Many2one('mc.evaluation.grades', string="Class")
    student_id = fields.Many2one('education.student', readonly=True, domain="[('company_id', 'in', allowed_company_ids)]")
    score = fields.Char(string="Score")

    """ score_selection = fields.Many2one(
    'mc.grading.scale',
    string="Score",
    domain="[('grading_scale_id', '=', grading_method), ('grading_scale_id.grade_id', '=', class_id)]"
    ) """

    score_selection = fields.Many2one(
    'mc.grading.scale',
    string="Score",
    domain="[('grading_scale_id', '=', grading_method)]"
    )
    
    color = fields.Char(string="Symbol Color", readonly=True, compute="_compute_color", store=True)

    comment = fields.Text(string="Comment")
    check = fields.Boolean(string="Attendence")
    class_id = fields.Many2one('education.class')

    grading_method = fields.Many2one('mc.grading.method', string="Class")
    
    # استخدم related بدل onchange
    seat_number = fields.Char(string="Seat Number", related="student_id.seat_number", store=True, readonly=True)
    student_code = fields.Char(string="Student Code", related="student_id.student_code", store=True, readonly=True)

    @api.depends('score_selection')
    def _compute_color(self):
        for rec in self:
            rec.color = rec.score_selection.color if rec.score_selection else False
