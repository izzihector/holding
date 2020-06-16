# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
import time
import base64
import xlwt
import io
import logging
import datetime
from datetime import datetime

class rrhh_igss_wizard(models.TransientModel):
    _name = 'rrhh.igss.wizard'

    def _default_payslip_run(self):
        logging.warn(self.env.context.get('active_ids'))
        if len(self.env.context.get('active_ids', [])) > 0:
            return self.env.context.get('active_ids')[0]
        else:
            return None

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip run',default=_default_payslip_run)
    archivo = fields.Binary('Archivo')
    name =  fields.Char('File Name', size=32)

    def generar(self):
        datos = ''
        for w in self:
            datos += str(w.payslip_run_id.slip_ids[0].company_id.version_mensaje) + '|' + str(datetime.today().strftime('%d/%m/%Y')) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.numero_patronal) + '|'+ str(datetime.strptime(w.payslip_run_id.date_start,'%Y-%m-%d').date().strftime('%m')).lstrip('0')+ '|' + str(datetime.strptime(w.payslip_run_id.date_start,'%Y-%m-%d').date().strftime('%Y')).lstrip('0') + '|' + str(w.payslip_run_id.slip_ids[0].company_id.name) + '|' +str(w.payslip_run_id.slip_ids[0].company_id.vat) + '|'+ str(w.payslip_run_id.slip_ids[0].company_id.email) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.tipo_planilla) + '\r\n'
            datos += '[centros]' + '\r\n'
            datos += str(w.payslip_run_id.slip_ids[0].company_id.codigo_centro_trabajo) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.nombre_centro_trabajo) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.direccion_centro_trabajo) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.zona_centro_trabajo) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.telefonos) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.fax) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.nombre_contacto) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.correo_electronico) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.codigo_departamento) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.codigo_municipio) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.codigo_actividad_economica) + '\r\n'
            datos += '[tiposplanilla]' + '\r\n'
            datos += str(w.payslip_run_id.slip_ids[0].company_id.identificacion_tipo_planilla) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.nombre_tipo_planilla) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.tipo_afiliados) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.periodo_planilla) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.departamento_republica) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.actividad_economica) + '|' + str(w.payslip_run_id.slip_ids[0].company_id.clase_planilla) + '\r\n'
            datos += '[liquidaciones]' + '\r\n'
            datos += '[empleados]' + '\r\n'
            for slip in w.payslip_run_id.slip_ids:
                fecha_planilla = datetime.strptime(w.payslip_run_id.date_start, '%Y-%m-%d')
                mes_planilla = fecha_planilla.month
                anio_planilla = fecha_planilla.year
                contrato_ids = self.env['hr.contract'].search( [['employee_id', '=', slip.employee_id.id]],offset=0,limit=1,order='date_start desc')
                logging.warn(contrato_ids)
                empleado = slip.employee_id.name.split()
                if len(empleado) == 4:
                    datos += '1' + '|' + str(slip.employee_id.igss) + '|' + empleado[0] + '|'+ empleado[1] + '|' + empleado[2] + '|' + empleado[3] + '|' + '|'
                if len(empleado) == 3:
                    datos += '1' + '|' + str(slip.employee_id.igss) + '|' + empleado[0] +  '|'+'|'+ empleado[1] + '|' + empleado[2]  + '|' + '|'
                if contrato_ids:
                    contrato = self.env['hr.contract'].browse([contrato_ids.id])
                    if contrato.date_end:
                        mes_contrato= datetime.strptime(contrato.date_end, '%Y-%m-%d')
                        mes_final_contrato = mes_contrato.month
                        anio_final_contrato = mes_contrato.year
                        if mes_planilla == mes_final_contrato and anio_final_contrato == anio_planilla:
                            datos += str(contrato.wage) + '|' + str(datetime.strptime(contrato.date_start,'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|' + str(datetime.strptime(contrato.date_end,'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|'
                    else:
                        mes_contrato = datetime.strptime(contrato.date_start, '%Y-%m-%d')
                        mes_final_contrato = mes_contrato.month
                        anio_final_contrato = mes_contrato.year
                        if mes_final_contrato == mes_planilla and anio_final_contrato == anio_planilla:
                            datos += str(contrato.wage) + '|' + str(datetime.strptime(contrato.date_start,'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|' + '|'
                        else:
                            datos += str(contrato.wage) + '|' + '|' + '' + '|'
                else:
                    datos += '|' + '|' + '|'
                datos += str(slip.employee_id.codigo_centro_trabajo) + '|' + str(slip.employee_id.nit) + '|' + str(slip.employee_id.codigo_ocupacion) + '|' + str(slip.employee_id.condicion_laboral) + '|' + '|' + '\r\n'
            datos += '[suspendidos]' + '\r\n'
            datos += '[licencias]' + '\r\n'
            datos += '[juramento]' + '\r\n'
            datos += 'BAJO MI EXCLUSIVA Y ABSOLUTA RESPONSABILIDAD, DECLARO QUE LA INFORMACION QUE AQUI CONSIGNO ES FIEL Y EXACTA, QUE ESTA PLANILLA INCLUYE A TODOS LOS TRABAJADORES QUE ESTUVIERON A MI SERVICIO Y QUE SUS SALARIOS SON LOS EFECTIVAMENTE DEVENGADOS, DURANTE EL MES ARRIBA INDICADO' + '\r\n'
            datos += '[finplanilla]' + '\r\n'
            datos = datos.replace('False', '')
        datos = base64.b64encode(datos.encode("utf-8"))
        self.write({'archivo': datos, 'name':'planilla.txt'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.igss.wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
