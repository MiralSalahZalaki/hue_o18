from odoo import models, fields, api

class TimetableByTeacher(models.TransientModel):
    _name = 'timetable.by.teacher.wizard'
    _description = 'Timetable by teacher Report Wizard'

    name = fields.Many2one(
        'education.faculty',
        string="Faculty",
        required=True
    )

    faculty_syllabus_class = fields.One2many(
        'mc.syllabus.per.class',
        related='name.syllabus_class',
        string="Regular Syllabus",
        readonly=True
    )

    faculty_syllabus_special_class = fields.One2many(
        'mc.syllabus.per.class',
        related='name.syllabus_special_class',
        string="Special Syllabus",
        readonly=True
    )


    def generate_timetable_teacher_report(self):
        return self.env.ref('mc_app.action_report_timetable_by_teacher_template').report_action(self)
