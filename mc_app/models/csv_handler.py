import csv
import io
import logging
from datetime import datetime
from odoo import models, api

_logger = logging.getLogger(__name__)

class CSVHandler(models.AbstractModel):
    _name = 'csv.handler'
    _description = 'CSV Handler Utility'

    @api.model
    def get_model_field_info(self, model_name):
        """Get field information for the specified model, including Selection options."""
        model = self.env[model_name]
        field_info = {}
        required_fields = []

        for field_name, field_obj in model._fields.items():
            # Skip fields that are computed, private, or specific system fields
            if (field_name.startswith('_') or 
                field_obj.compute or  # Skip computed fields regardless of store value
                field_name in ['id', 'write_uid', 'write_date', 'create_uid', 
                             'create_date', 'message_follower_ids', 'message_ids', 
                             'website_message_ids', 'rating_ids', 'message_is_follower', 
                             'message_partner_ids']):
                continue

            field_info[field_name] = {
                'string': field_obj.string,
                'type': field_obj.type,
                'required': field_obj.required,
                'readonly': field_obj.readonly,
                'comodel': field_obj.comodel_name if field_obj.type in ('one2many', 'many2many', 'many2one') else None
            }
            
            # Add selection options for Selection fields
            if field_obj.type == 'selection':
                if hasattr(field_obj, 'selection'):
                    if callable(field_obj.selection):
                        try:
                            selection_options = field_obj.selection(model)
                        except:
                            selection_options = []
                    else:
                        selection_options = field_obj.selection
                    field_info[field_name]['selection_options'] = selection_options

            if field_obj.required and field_name not in ('company_id', 'school'):
                required_fields.append({
                    'name': field_name,
                    'label': field_obj.string
                })

        return {
            'field_info': field_info,
            'required_fields': required_fields
        }

    @api.model
    def get_csv_template_with_validation(self, model_name):
        """Generate CSV template with Selection field options as comments."""
        try:
            field_data = self.get_model_field_info(model_name)
            required_fields = field_data['required_fields']
            all_fields = field_data['field_info']

            if not all_fields:
                return {
                    'success': False,
                    'error': 'No valid fields found for CSV template'
                }

            required_field_labels = [f['label'] for f in required_fields]
            headers = []
            selection_info = {}
            
            for field_name, info in all_fields.items():
                header_label = f"{info['string']}*" if info['string'] in required_field_labels else info['string']
                headers.append(header_label)
                
                # Store selection options for documentation
                if info['type'] == 'selection' and 'selection_options' in info:
                    selection_info[info['string']] = info['selection_options']

            csv_content = ','.join(headers) + '\n'
            
            # Add selection options as comments
            if selection_info:
                csv_content += '# Selection Field Options:\n'
                for field_label, options in selection_info.items():
                    options_str = ' | '.join([f"{key} ({label})" for key, label in options])
                    csv_content += f'# {field_label}: {options_str}\n'
                csv_content += '#\n'
            
            # Add UTF-8 BOM
            csv_content = '\ufeff' + csv_content

            return {
                'success': True,
                'template_content': csv_content,
                'required_fields': required_fields,
                'field_info': all_fields,
                'selection_info': selection_info
            }

        except Exception as e:
            _logger.error(f"Error generating CSV template for {model_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @api.model
    def validate_csv_headers(self, model_name, headers):
        """Validate CSV headers for the specified model."""
        field_data = self.get_model_field_info(model_name)
        field_info = field_data['field_info']
        required_fields = [f['label'] for f in field_data['required_fields']]

        label_to_field = {
            info['string']: field_name
            for field_name, info in field_info.items()
        }

        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'field_mapping': {},
            'missing_required': []
        }

        for header in headers:
            header = header.strip()
            # Remove '*' or '(Required)' from header for validation
            cleaned_header = header.rstrip('*').replace('(Required)', '').strip()
            if cleaned_header in label_to_field:
                validation_result['field_mapping'][header] = label_to_field[cleaned_header]
            else:
                validation_result['errors'].append(
                    f"Unknown field: '{header}'"
                )
                validation_result['valid'] = False

        for req_field in required_fields:
            # Check if the required field exists in headers (with or without marker)
            if not any(req_field == header.rstrip('*').replace('(Required)', '').strip() for header in headers):
                validation_result['missing_required'].append(req_field)
                validation_result['errors'].append(f"Required field missing: '{req_field}'")
                validation_result['valid'] = False

        return validation_result

    @api.model
    def _parse_datetime_value(self, value):
        """Parse datetime value from CSV - returns full datetime"""
        if not value or not value.strip():
            return False
        
        value = value.strip()
        
        # Try different datetime formats
        datetime_formats = [
            '%m/%d/%Y %H:%M',       # 2/13/2025 11:45
            '%Y-%m-%d %H:%M:%S',    # 2025-02-13 11:45:34
            '%d/%m/%Y %H:%M:%S',    # 13/02/2025 11:45:34
            '%m/%d/%Y %H:%M:%S',    # 02/13/2025 11:45:34
            '%Y-%m-%d %H:%M',       # 2025-02-13 11:45
            '%d/%m/%Y %H:%M',       # 13/02/2025 11:45
            
            # If only date is provided, assume 00:00:00
            '%Y-%m-%d',    # 2025-02-13
            '%d/%m/%Y',    # 13/02/2025
            '%m/%d/%Y',    # 02/13/2025
            '%d-%m-%Y',    # 13-02-2025
            '%Y/%m/%d',    # 2025/02/13
        ]
        
        for fmt in datetime_formats:
            try:
                parsed_datetime = datetime.strptime(value, fmt)
                # Return full datetime in ISO format for Odoo
                return parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
                
        raise ValueError(f"Invalid datetime format: {value}")

    @api.model
    def _parse_date_value(self, value):
        """Parse date/datetime value from CSV - returns date only"""
        if not value or not value.strip():
            return False
        
        value = value.strip()
        
        # Try different date and datetime formats
        date_formats = [
            # DateTime formats (with time) - we'll extract date part only
            '%m/%d/%Y %H:%M',       # 2/13/2025 11:45
            '%Y-%m-%d %H:%M:%S',    # 2025-02-13 11:45:34
            '%d/%m/%Y %H:%M:%S',    # 13/02/2025 11:45:34
            '%m/%d/%Y %H:%M:%S',    # 02/13/2025 11:45:34
            '%Y-%m-%d %H:%M',       # 2025-02-13 11:45
            '%d/%m/%Y %H:%M',       # 13/02/2025 11:45
            
            # Date only formats
            '%Y-%m-%d',    # 2025-02-13
            '%d/%m/%Y',    # 13/02/2025
            '%m/%d/%Y',    # 02/13/2025
            '%d-%m-%Y',    # 13-02-2025
            '%Y/%m/%d',    # 2025/02/13
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(value, fmt)
                # Return only the date part (YYYY-MM-DD) even if time was provided
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        raise ValueError(f"Invalid date/datetime format: {value}")

    @api.model
    def _parse_boolean_value(self, value):
        """Parse boolean value from CSV"""
        if not value or not value.strip():
            return False
        
        value = value.strip().upper()
        return value in ['TRUE', '1', 'YES', 'Y', 'ON']

    @api.model
    def _parse_integer_value(self, value):
        """Parse integer value from CSV"""
        if not value or not value.strip():
            return 0
        try:
            return int(value.strip())
        except ValueError:
            raise ValueError(f"Invalid integer value: {value}")

    @api.model
    def _parse_float_value(self, value):
        """Parse float value from CSV"""
        if not value or not value.strip():
            return 0.0
        try:
            return float(value.strip())
        except ValueError:
            raise ValueError(f"Invalid float value: {value}")

    @api.model
    def _parse_selection_value(self, value, field_obj):
        """Parse selection value from CSV - handles empty values properly"""
        if not value or not str(value).strip():
            return False
        
        value = str(value).strip()
        
        # Get selection options
        if hasattr(field_obj, 'selection'):
            if callable(field_obj.selection):
                try:
                    selection_options = field_obj.selection(self)
                except:
                    selection_options = []
            else:
                selection_options = field_obj.selection or []
            
            if not selection_options:
                return value
            
            # Create mapping for both key and value lookups
            key_to_value = {key: key for key, label in selection_options}
            label_to_key = {label.lower(): key for key, label in selection_options}
            value_lower = value.lower()
            
            # Try exact key match first
            if value in key_to_value:
                return value
            
            # Try label match (case insensitive)
            if value_lower in label_to_key:
                return label_to_key[value_lower]
            
            # Try partial label match
            for label, key in label_to_key.items():
                if value_lower in label or label in value_lower:
                    return key
                    
            available_options = [f"{key} ({label})" for key, label in selection_options]
            raise ValueError(f"Invalid selection value: '{value}'. Available options: {', '.join(available_options)}")
        
        return value

    @api.model
    def import_csv_with_validation(self, model_name, csv_data, company_id=None, company_field='company_id', import_mode='create', duplicate_check_field='name'):
        """Import CSV data with validation - handles missing company_id gracefully"""
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_data, newline=''), fieldnames=None, restval='')
            headers = csv_reader.fieldnames

            if not headers:
                return {
                    'success': False,
                    'error': 'CSV file is empty or missing headers'
                }

            header_validation = self.validate_csv_headers(model_name, headers)
            if not header_validation['valid']:
                return {
                    'success': False,
                    'error': 'CSV validation failed: ' + '; '.join(header_validation['errors'])
                }

            records_created = []
            records_updated = []
            errors = []
            skipped_rows = []
            field_mapping = header_validation['field_mapping']
            model = self.env[model_name]
            field_data = self.get_model_field_info(model_name)
            required_fields = [f['name'] for f in field_data['required_fields']]
            
            _logger.info(f"Starting CSV import for model: {model_name} with mode: {import_mode}")
            _logger.info(f"Company ID provided: {company_id}")
            _logger.info(f"Company field: {company_field}")
            _logger.info(f"Required fields: {required_fields}")
            _logger.info(f"Field mapping: {field_mapping}")

            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    has_data = any(row.get(header, '').strip() for header in headers)
                    
                    if not has_data:
                        skipped_rows.append(f"Row {row_num}: Empty row")
                        _logger.info(f"Skipping empty row {row_num}")
                        continue

                    values = {}
                    
                    if (company_field and 
                        company_id and 
                        company_field in field_data['field_info']):
                        values[company_field] = company_id
                        _logger.info(f"Added company_id {company_id} to row {row_num}")
                    else:
                        if company_field and company_field in field_data['field_info']:
                            _logger.info(f"Row {row_num}: Company field '{company_field}' exists but no company_id provided")
                        
                    o2m_values = {}
                    m2m_values = {}
                    row_errors = []

                    for header, field_name in field_mapping.items():
                        cell_value = row.get(header, '').strip() if row.get(header) else ''
                        
                        if not cell_value and field_name not in required_fields:
                            continue
                            
                        field_info = field_data['field_info'][field_name]
                        
                        try:
                            if field_info['type'] == 'selection':
                                parsed_value = self._parse_selection_value(cell_value, model._fields[field_name])
                                if parsed_value is not False:
                                    values[field_name] = parsed_value
                                    _logger.info(f"Row {row_num}: Set selection {field_name} = '{parsed_value}'")
                                else:
                                    _logger.info(f"Row {row_num}: Selection {field_name} left empty (False)")
                                    
                            elif field_info['type'] == 'datetime':
                                if cell_value:
                                    values[field_name] = self._parse_datetime_value(cell_value)
                                    _logger.info(f"Row {row_num}: Set datetime {field_name} = '{values[field_name]}'")
                                    
                            elif field_info['type'] == 'date':
                                if cell_value:
                                    values[field_name] = self._parse_date_value(cell_value)
                                
                            elif field_info['type'] == 'boolean':
                                values[field_name] = self._parse_boolean_value(cell_value)
                                
                            elif field_info['type'] == 'integer':
                                if cell_value:
                                    values[field_name] = self._parse_integer_value(cell_value)
                                elif field_name in required_fields:
                                    values[field_name] = 0
                                    
                            elif field_info['type'] == 'float':
                                if cell_value:
                                    values[field_name] = self._parse_float_value(cell_value)
                                elif field_name in required_fields:
                                    values[field_name] = 0.0
                                    
                            elif field_info['type'] == 'many2one':
                                if cell_value:
                                    related_model = self.env[field_info['comodel']]
                                    search_domain = [('name', '=', cell_value)]
                                    
                                    if (company_field and company_id and 
                                        company_field in getattr(related_model, '_fields', {})):
                                        search_domain.append((company_field, '=', company_id))
                                        _logger.info(f"Row {row_num}: Added company filter for {field_name}")
                                    
                                    related_record = related_model.search(search_domain, limit=1)
                                    if related_record:
                                        values[field_name] = related_record.id
                                        _logger.info(f"Row {row_num}: Found {field_name} '{cell_value}' with ID {related_record.id}")
                                    else:
                                        row_errors.append(f"Row {row_num}: Related record '{cell_value}' not found for field '{header}'")
                                        break
                                        
                            elif field_info['type'] == 'many2many':
                                if cell_value:
                                    related_model = self.env[field_info['comodel']]
                                    related_names = [name.strip() for name in cell_value.split(',') if name.strip()]
                                    related_ids = []
                                    
                                    for name in related_names:
                                        search_domain = [('name', '=', name)]
                                        if (company_field and company_id and 
                                            company_field in getattr(related_model, '_fields', {})):
                                            search_domain.append((company_field, '=', company_id))
                                        
                                        related_record = related_model.search(search_domain, limit=1)
                                        if related_record:
                                            related_ids.append(related_record.id)
                                        else:
                                            row_errors.append(f"Row {row_num}: Related record '{name}' not found for field '{header}'")
                                            break
                                            
                                    if not row_errors and related_ids:
                                        m2m_values[field_name] = [(6, 0, related_ids)]
                                        _logger.info(f"Row {row_num}: Set many2many {field_name} with IDs: {related_ids}")
                                        
                            elif field_info['type'] == 'one2many':
                                if cell_value:
                                    related_model = self.env[field_info['comodel']]
                                    related_names = [name.strip() for name in cell_value.split(',') if name.strip()]
                                    o2m_commands = []
                                    
                                    for name in related_names:
                                        search_domain = [('name', '=', name)]
                                        if (company_field and company_id and 
                                            company_field in getattr(related_model, '_fields', {})):
                                            search_domain.append((company_field, '=', company_id))
                                            
                                        related_record = related_model.search(search_domain, limit=1)
                                        if related_record:
                                            o2m_commands.append((4, related_record.id))
                                        else:
                                            create_vals = {'name': name}
                                            if (company_field and company_id and 
                                                company_field in getattr(related_model, '_fields', {})):
                                                create_vals[company_field] = company_id
                                            o2m_commands.append((0, 0, create_vals))
                                            
                                    if o2m_commands:
                                        o2m_values[field_name] = o2m_commands
                                        _logger.info(f"Row {row_num}: Set one2many {field_name} with commands: {len(o2m_commands)} items")
                            else:
                                if cell_value:
                                    values[field_name] = cell_value
                                    _logger.info(f"Row {row_num}: Set {field_name} = '{cell_value}'")
                                    
                        except ValueError as ve:
                            row_errors.append(f"Row {row_num}: Invalid value for field '{header}': {str(ve)}")
                            _logger.error(f"Row {row_num}: ValueError for field '{header}': {str(ve)}")
                            break

                    errors.extend(row_errors)
                    
                    if row_errors:
                        _logger.warning(f"Row {row_num}: Skipping due to {len(row_errors)} errors")
                        continue

                    if has_data:
                        missing_required = []
                        for req_field in required_fields:
                            field_info = field_data['field_info'][req_field]
                            
                            if req_field == company_field and not company_id:
                                continue
                                
                            if field_info['type'] in ('one2many', 'many2many'):
                                if not (req_field in o2m_values or req_field in m2m_values):
                                    missing_required.append(req_field)
                            elif field_info['type'] == 'many2one':
                                if req_field not in values:
                                    missing_required.append(req_field)
                            elif field_info['type'] in ('boolean', 'integer', 'float'):
                                if req_field not in values:
                                    missing_required.append(req_field)
                            else:
                                if req_field not in values or values[req_field] in ['', None]:
                                    missing_required.append(req_field)
                        
                        if missing_required:
                            missing_fields_str = ', '.join([field_data['field_info'][f]['string'] for f in missing_required])
                            error_msg = f"Row {row_num}: Required fields missing: {missing_fields_str}"
                            errors.append(error_msg)
                            _logger.warning(error_msg)
                            continue
                        
                        existing_record = None
                        search_domain = []

                        if duplicate_check_field in values:
                            search_domain = [(duplicate_check_field, '=', values[duplicate_check_field])]
                            if (company_field and company_id and 
                                company_field in field_data['field_info']):
                                search_domain.append((company_field, '=', company_id))
                            _logger.info(f"Row {row_num}: Search domain: {search_domain}")
                        
                        if search_domain:
                            existing_record = model.search(search_domain, limit=1)
                        
                        if existing_record:
                            record_identifier = values.get(duplicate_check_field) or values.get('name', 'Unknown')
                            if import_mode == 'create':
                                error_msg = f"Row {row_num}: Record '{record_identifier}' already exists - skipped"
                                errors.append(error_msg)
                                _logger.warning(error_msg)
                                continue
                            elif import_mode in ['update', 'create_update']:
                                _logger.info(f"Row {row_num}: Updating existing record '{record_identifier}'")
                                try:
                                    all_values = values.copy()
                                    all_values.update(o2m_values)
                                    all_values.update(m2m_values)
                                    existing_record.write(all_values)
                                    records_updated.append(record_identifier)
                                    _logger.info(f"Row {row_num}: Successfully updated record '{record_identifier}'")
                                    continue
                                except Exception as update_error:
                                    error_msg = f"Row {row_num}: Failed to update record '{record_identifier}' - {str(update_error)}"
                                    errors.append(error_msg)
                                    _logger.error(error_msg)
                                    continue

                        all_values = values.copy()
                        all_values.update(o2m_values)
                        all_values.update(m2m_values)
                        
                        _logger.info(f"Row {row_num}: Creating record with values: {all_values}")
                        
                        try:
                            record = model.create(all_values)
                            record_name = record.name if hasattr(record, 'name') else str(record.id)
                            records_created.append(record_name)
                            _logger.info(f"Row {row_num}: Successfully created record '{record_name}' (ID: {record.id})")
                        except Exception as create_error:
                            error_msg = f"Row {row_num}: Failed to create record - {str(create_error)}"
                            errors.append(error_msg)
                            _logger.error(error_msg)
                            
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    errors.append(error_msg)
                    _logger.error(f"CSV Import Error - {error_msg}")

            _logger.info(f"CSV Import Summary:")
            _logger.info(f"  - Total rows processed: {row_num - 1 if 'row_num' in locals() else 0}")
            _logger.info(f"  - Records created: {len(records_created)}")
            _logger.info(f"  - Records updated: {len(records_updated)}")
            _logger.info(f"  - Errors: {len(errors)}")
            _logger.info(f"  - Skipped rows: {len(skipped_rows)}")

            return {
                'success': True,
                'records_created': records_created,
                'records_updated': records_updated,
                'errors': errors,
                'skipped_rows': skipped_rows,
                'total_created': len(records_created),
                'total_updated': len(records_updated),
                'total_errors': len(errors),
                'total_skipped': len(skipped_rows),
                'validation_info': header_validation
            }

        except Exception as e:
            _logger.error(f"Error importing CSV for {model_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }