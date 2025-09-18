from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class MCPermittedAbsence(models.Model):
    _name = 'mc.student.permitted.absence'
    _description = 'Student Absence'

    student_id = fields.Many2one('education.student', string='Student', required=True)
    grade_id = fields.Many2one('education.class', string='Grade', compute='_on_change_student_id', store=True)
    class_division_id = fields.Many2one('education.class.division', string='Class', compute='_on_change_student_id', store=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    reason_id = fields.Many2one('mc.student.permitted.absence.reason', string='Absence Reason', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    days_count = fields.Integer(string='Days')

    @api.depends('student_id')
    def _on_change_student_id(self):
        for record in self:
            if record.student_id:
                record.grade_id = record.student_id.grade_id.id if record.student_id.grade_id else False
                record.class_division_id = record.student_id.class_division_id.id if record.student_id.class_division_id else False
            else:
                record.grade_id = False
                record.class_division_id = False

    @api.onchange('start_date', 'days_count')
    def _onchange_days_count(self):
        for record in self:
            if record.start_date and record.days_count and record.days_count > 0:
                record.end_date = record.start_date + timedelta(days=record.days_count - 1)

    @api.onchange('start_date', 'end_date')
    def _onchange_end_date(self):
        for record in self:
            if record.start_date and record.end_date and record.end_date >= record.start_date:
                record.days_count = (record.end_date - record.start_date).days + 1
            else:
                record.days_count = 0

    @api.model
    def create(self, vals):
        student_id = vals.get('student_id')
        start_date = fields.Date.from_string(vals.get('start_date'))
        end_date = fields.Date.from_string(vals.get('end_date'))
        reason_id = vals.get('reason_id')

        if end_date < start_date:
            raise ValidationError("لا يمكن أن يكون تاريخ النهاية قبل تاريخ البداية.")

        overlapping_absence = self.sudo().search([
            ('student_id', '=', student_id),
            ('end_date', '>=', start_date),
            ('start_date', '<=', end_date)
        ], limit=1)

        if overlapping_absence:
            if overlapping_absence.reason_id.id == reason_id:
                overlapping_absence.write({
                    'start_date': min(overlapping_absence.start_date, start_date),
                    'end_date': max(overlapping_absence.end_date, end_date),
                    'days_count': (max(overlapping_absence.end_date, end_date) - min(overlapping_absence.start_date, start_date)).days + 1
                })
                return overlapping_absence
            else:
                new_periods = []
                
                if start_date < overlapping_absence.start_date:
                    new_periods.append({
                        'student_id': student_id,
                        'start_date': start_date,
                        'end_date': overlapping_absence.start_date - timedelta(days=1),
                        'reason_id': reason_id,
                        'days_count': (overlapping_absence.start_date - start_date).days
                    })

                if end_date > overlapping_absence.end_date:
                    new_periods.append({
                        'student_id': student_id,
                        'start_date': overlapping_absence.end_date + timedelta(days=1),
                        'end_date': end_date,
                        'reason_id': reason_id,
                        'days_count': (end_date - (overlapping_absence.end_date + timedelta(days=1))).days + 1
                    })

                if new_periods:
                    return super(MCPermittedAbsence, self).create(new_periods)
                
                raise ValidationError("هناك تعارض مع فترة غياب أخرى.")

        return super(MCPermittedAbsence, self).create(vals)