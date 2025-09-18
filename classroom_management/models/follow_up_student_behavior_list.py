from odoo import models, fields, api

class MCCFollowUpStudentBehaviorList(models.Model):
    _name = 'follow.up.student.behavior.list'

    connect_id = fields.Many2one('mc.follow.up.behavior', string="Class")
    student_id = fields.Many2one('education.student', domain="[('company_id', 'in', allowed_company_ids)]")
    class_id = fields.Many2one("education.class.division", string="Class",  related="student_id.class_division_id")
    notes = fields.Text(string="Notes")
    situation = fields.Many2one('mc.follow.up.situation',string='Situation')
