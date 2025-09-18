from odoo import models, fields, api

class MCCFollowUpStudentList(models.Model):
    _name = 'follow.up.student.list'

    connect_id = fields.Many2one('mc.follow.up.record', string="Class")
    student_id = fields.Many2one('education.student', domain="[('company_id', 'in', allowed_company_ids)]")
    quiz = fields.Text(string="Quiz")
    notes = fields.Many2one('mc.follow.up.notes', string='Notes')
    attendence = fields.Selection([
        ('att', 'Attendant'),
        ('abs', 'Absent'),
    ], string='attendence')

    tools = fields.Selection([
        ('committed', 'Committed'),
        ('uncommitted', 'Uncommitted')
    ], string='Tools')
    
    hw = fields.Selection([
        ('committed', 'Committed'),
        ('uncommitted', 'Uncommitted')
    ], string='H.W')
    
    progress = fields.Selection([
        ('1', 'Need More Focus'),
        ('2', 'Good'),
        ('3', 'Very Good'),
        ('4', 'Excellent'),
    
    ], string='Progress')
