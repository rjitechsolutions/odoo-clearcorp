# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Addons modules by CLEARCORP S.A.
#    Copyright (C) 2009-TODAY CLEARCORP S.A. (<http://clearcorp.co.cr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.osv import osv, fields
    
class accountAssetreportWizard (osv.osv_memory):
    _name = 'account.asset.report.wiz'
    
    def out_format_get (self, cr, uid, context={}):
        obj = self.pool.get('report.mimetypes')
        ids = []
        list = []
        
        ids = obj.search(cr, uid, [('code','=','oo-pdf')])
        #only include format pdf that match with ods format.
        for type in obj.browse(cr, uid, ids, context=context):
            if type.code == 'oo-pdf' and type.compatible_types == 'oo-odt':
                list.append(type.id)
            
        # If read method isn't call, the value for out_format "disappear",
        # the value is preserved, but disappears from the screen (a rare bug)
        res = obj.read(cr, uid, list, ['name'], context)
        return [(str(r['id']), r['name']) for r in res]
    
    _columns = {
        'state':fields.selection([('draft', 'Draft'), ('open','Open'), ('close','Close')], 'State'),
        'partner_id': fields.many2one('res.partner', 'Empresa'),
        'category_asset_ids': fields.many2many('account.asset.category', 'asset_category_report_wiz', string='Asset Category'),
        'out_format': fields.selection(out_format_get, 'Print Format'), 
    }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        
        result['state'] = 'state' in data['form'] and data['form']['state'] or False
        
        #m2m and m2o fields
        result['partner_id'] = 'partner_id' in data['form'] and data['form']['partner_id'] or False
        result['category_asset_ids'] = 'category_asset_ids' in data['form'] and data['form']['category_asset_ids'] or False      
        
        return result
    
    def _print_report(self, cr, uid, ids, data, context=None):
        mimetype = self.pool.get('report.mimetypes')
        report_obj = self.pool.get('ir.actions.report.xml')
        report_name = ''
      
        context = context or {}
            
        #=======================================================================
        # onchange_in_format method changes variable out_format depending of 
        # which in_format is choose. 
        # If out_format is pdf -> call record in odt format 
        #
        # If mimetype is PDF -> out_format = PDF (search odt record)
        # If record doesn't exist, return a error.
        #=======================================================================
                
        #1. Find out_format selected
        out_format_obj = mimetype.browse(cr, uid, [int(data['form']['out_format'])], context)[0]

        #2. Check out_format and set report_name for each format
        if out_format_obj.code == 'oo-pdf':
            report_name = 'account_asset_report_odt' 
        
        # If there not exist name, it's because not exist a record for this format   
        if report_name == '':
            raise osv.except_osv(_('Error !'), _('There is no template defined for the selected format. Check if aeroo report exist.'))
                
        else:
            #Search record that match with the name, and get some extra information
            report_xml_id = report_obj.search(cr, uid, [('report_name','=', report_name)],context=context)
            report_xml = report_obj.browse(cr, uid, report_xml_id, context=context)[0]
            data.update({'model': report_xml.model, 'report_type':'aeroo', 'id': report_xml.id})
            
            #Write out_format choose in wizard
            report_xml.write({'out_format': out_format_obj.id}, context=context)
           
            return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'datas': data,
                'context':context
            }
            
    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        data = {}
        data['form'] = self.read(cr, uid, ids, ['state', 'partner_id','category_asset_ids','out_format'], context=context)[0]
        #Extract ids for m2m and m2o fields
        for field in ['partner_id', 'category_asset_ids']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        
        #Check if the fields exist, otherwise put false in the field.
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        data['form']['used_context'] = used_context
        
        return self._print_report(cr, uid, ids, data, context=context)
