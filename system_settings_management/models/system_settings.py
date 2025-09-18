from odoo import models, fields, api
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SystemSettings(models.Model):
    _name = 'system.settings'
    _description = 'System Settings'
    _order = 'name'

    name = fields.Char(string='Setting Name', required=True, index=True)
    description = fields.Text(string='Description')
    company_id = fields.Many2one('res.company', string='Company', required=True, ondelete='cascade', index=True)
    active = fields.Boolean(string='Active', default=True)
    stages = fields.Many2many('mc.education.stages', string='Stages')
    grades = fields.Many2many('education.class', string='Grades')
    student_code_prefix = fields.Integer(
        string="Student Code Prefix",
        help="The starting number for generating student codes."
    )
    system_type = fields.Selection([
        ('british', 'British System'),
        ('american', 'American System'),
        ('general', 'General System'),
    ], string="Education System", required=True, default='general')

    
    _sql_constraints = [
        ('unique_company_setting', 'unique(company_id)', 'Only one system setting per company is allowed!')
    ]

    @api.model
    def sync_companies_to_settings(self):
        """Create system settings for companies without settings"""
        companies = self.env['res.company'].search([])
        for company in companies:
            if not self.search([('company_id', '=', company.id)], limit=1):
                self._create_setting_for_company(company)
        return True

    @api.model
    def server_action_sync_companies_to_settings(self):
        """Sync all companies: create new settings and update existing ones"""
        companies = self.env['res.company'].search([])
        created_count = 0
        updated_count = 0

        for company in companies:
            existing_setting = self.search([('company_id', '=', company.id)], limit=1)

            if not existing_setting:
                self._create_setting_for_company(company)
                created_count += 1
            else:
                self._update_setting_data(existing_setting, company)
                updated_count += 1

        _logger.info(f"Sync completed: {created_count} created, {updated_count} updated")
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def create_setting_for_company(self, company_id):
        """Create system setting for a specific company"""
        company = self.env['res.company'].browse(company_id)
        if not company.exists():
            _logger.warning(f"Company with ID {company_id} does not exist")
            return False

        if self.search([('company_id', '=', company_id)], limit=1):
            _logger.info(f"System setting already exists for company: {company.name}")
            return False

        return self._create_setting_for_company(company)

    def _create_setting_for_company(self, company):
        """Private method to create system setting for a company"""
        grades = self.env['education.class'].search([('school', '=', company.id)])
        stages = self.env['mc.education.stages'].search([('company_id', '=', company.id)])

        return self.create({
            'name': f"{company.name} - Settings",
            'description': f'System configuration for company: {company.name}',
            'company_id': company.id,
            'grades': [(6, 0, grades.ids)],
            'stages': [(6, 0, stages.ids)],
        })

    def _update_setting_data(self, setting, company):
        """Private method to update setting data"""
        grades = self.env['education.class'].search([('school', '=', company.id)])
        stages = self.env['mc.education.stages'].search([('company_id', '=', company.id)])

        setting.write({
            'grades': [(6, 0, grades.ids)],
            'stages': [(6, 0, stages.ids)],
        })

    def fetch_company_data(self):
        """Refresh/sync stages and grades from the company"""
        for record in self:
            if not record.company_id:
                raise UserError("No company assigned to this setting.")

            self._update_setting_data(record, record.company_id)

        return {'type': 'ir.actions.act_window_close'}

    def add_grades_to_company(self):
        """Open form to add new grades to this company"""
        self.ensure_one()

        if not self.company_id:
            raise UserError("No company assigned to this setting.")

        return {
            'type': 'ir.actions.act_window',
            'name': f'Add Grades to {self.company_id.name}',
            'res_model': 'education.class',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_school': self.company_id.id,
                'search_default_school': self.company_id.id,
            },
            'domain': [['school', '=', self.company_id.id]],
        }

    def add_stages_to_company(self):
        """Open form to add new stages to this company"""
        self.ensure_one()

        if not self.company_id:
            raise UserError("No company assigned to this setting.")

        return {
            'type': 'ir.actions.act_window',
            'name': f'Add Educational Stages to {self.company_id.name}',
            'res_model': 'mc.education.stages',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_company_id': self.company_id.id,
            },
            'domain': [['company_id', '=', self.company_id.id]],
        }

    @api.model
    def name_get(self):
        """Custom name_get to show company name in selection"""
        result = []
        for record in self:
            name = f"{record.company_id.name} - Settings"
            result.append((record.id, name))
        return result


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        for company in companies:
            _logger.info(f"Creating system settings for new company: {company.name}")
            self.env['system.settings'].create_setting_for_company(company.id)
        return companies

    def unlink(self):
        """Delete corresponding system settings when company is deleted"""
        for company in self:
            try:
                system_settings = self.env['system.settings'].search([('company_id', '=', company.id)])
                if system_settings:
                    _logger.info(f"Deleting system settings for company: {company.name}")
                    system_settings.unlink()
            except Exception as e:
                _logger.warning(f"Error deleting system settings for company {company.name}: {e}")

        return super().unlink()