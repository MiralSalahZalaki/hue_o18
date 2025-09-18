from odoo import models, fields, api

class StudentLdapDirectory(models.Model):
    _name = 'student.ldap.directory'
    _description = 'LDAP Directory for Students'

    name = fields.Char( string='G/O Name', required=True, help='Group or Organizational Unit Directory.')
    
    dn = fields.Char( string='LDAP DN', help='Distinguished Name in LDAP.')
    
    obj_id = fields.Char( string='Object ID', help='Object ID in LDAP.')

    parent_id = fields.Many2one('student.ldap.directory', string="Parent Directory")

    @api.model
    def get_csv_template_with_validation(self):
        return self.env['csv.handler'].get_csv_template_with_validation(self._name)
    
    @api.model
    def validate_csv_headers(self, headers):
        return self.env['csv.handler'].validate_csv_headers(self._name, headers)
    
    @api.model
    def import_csv_with_validation(self, csv_data, company_id=None):
        return self.env['csv.handler'].import_csv_with_validation(self._name, csv_data, company_id, company_field=None)