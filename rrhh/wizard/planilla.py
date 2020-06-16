# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
import time
import base64
import xlwt
import io
import logging

class rrhh_planilla_wizard(models.TransientModel):
    _name = 'rrhh.planilla.wizard'

    nomina_id = fields.Many2one('hr.payslip.run', 'Nomina', default=lambda self: self.env['hr.payslip.run'].browse(self._context.get('active_id')), required=True)
    planilla_id = fields.Many2one('rrhh.planilla', 'Planilla', required=True)
    archivo = fields.Binary('Archivo')
    name =  fields.Char('File Name', size=32)
    agrupado  = fields.Boolean('Agrupado por cuenta analítica')

    def generar(self):
        for w in self:
            filename = "libro.xls"
            libro = xlwt.Workbook()
            xlwt.add_palette_colour("custom_colour", 0x21)
            libro.set_colour_RGB(0x21, 200, 200, 200)
            estilo = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
            if w.agrupado:
                cuentas_analiticas = set([])
                for l in w.nomina_id.slip_ids:
                    if l.move_id and len(l.move_id.line_ids) > 0 and l.move_id.line_ids[0].analytic_account_id:
                        if l.move_id.line_ids[0].analytic_account_id:
                            cuentas_analiticas.add(l.move_id.line_ids[0].analytic_account_id.name)
                        else:
                            cuentas_analiticas.add('Indefinido')
                    else:
                        if l.contract_id.analytic_account_id.name:
                            cuentas_analiticas.add(l.contract_id.analytic_account_id.name)
                        else:
                            cuentas_analiticas.add('Indefinido')

                for i in cuentas_analiticas:
                    hoja = libro.add_sheet(i)

                    xlwt.add_palette_colour("custom_colour", 0x21)
                    libro.set_colour_RGB(0x21, 200, 200, 200)
                    estilo = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
                    hoja.write(0, 0, 'Planilla', estilo)
                    hoja.write(0, 1, w.nomina_id.name, estilo)
                    hoja.write(0, 2, 'Periodo', estilo)
                    hoja.write(0, 3, w.nomina_id.date_start, estilo)
                    hoja.write(0, 4, w.nomina_id.date_end, estilo)

                    linea = 2
                    num = 1

                    hoja.write(linea, 0, 'No', estilo)
                    hoja.write(linea, 1, 'Cod. de empleado', estilo)
                    hoja.write(linea, 2, 'Nombre de empleado', estilo)
                    hoja.write(linea, 3, 'Fecha de ingreso', estilo)
                    hoja.write(linea, 4, 'Puesto', estilo)
                    hoja.write(linea, 5, 'Dias', estilo)

                    totales = []
                    columna = 6
                    for c in w.planilla_id.columna_id:
                        hoja.write(linea, columna, c.name, estilo)
                        columna += 1
                        totales.append(0)
                    totales.append(0)

                    hoja.write(linea, columna, 'Liquido a recibir', estilo)
                    hoja.write(linea, columna+1, 'Banco a depositar', estilo)
                    hoja.write(linea, columna+2, 'Cuenta a depositar', estilo)
                    hoja.write(linea, columna+3, 'Observaciones', estilo)
                    hoja.write(linea, columna+4, 'Cuenta analítica', estilo)
                    for l in w.nomina_id.slip_ids:
                        if l.move_id and len(l.move_id.line_ids) > 0 and l.move_id.line_ids[0].analytic_account_id:
                            if l.move_id.line_ids[0].analytic_account_id.name == i:
                                linea += 1
                                dias = 0
                                total_salario = 0

                                hoja.write(linea, 0, num)
                                hoja.write(linea, 1, l.employee_id.codigo_empleado)
                                hoja.write(linea, 2, l.employee_id.name)
                                hoja.write(linea, 3, l.contract_id.date_start)
                                hoja.write(linea, 4, l.employee_id.job_id.name)
                                for d in l.worked_days_line_ids:
                                    if d.code == 'TRABAJO100':
                                        dias += d.number_of_days
                                hoja.write(linea, 5, dias)

                                columna = 6
                                for c in w.planilla_id.columna_id:
                                    reglas = [x.id for x in c.regla_id]
                                    entradas = [x.name for x in c.entrada_id]
                                    total_columna = 0
                                    for r in l.line_ids:
                                        if r.salary_rule_id.id in reglas:
                                            total_columna += r.total
                                    for r in l.input_line_ids:
                                        if r.name in entradas:
                                            total_columna += r.amount
                                    if c.sumar:
                                        total_salario += total_columna
                                    totales[columna-6] += total_columna

                                    hoja.write(linea, columna, total_columna)
                                    columna += 1

                                totales[columna-6] += total_salario
                                hoja.write(linea, columna, total_salario)
                                hoja.write(linea, columna+1, l.employee_id.bank_account_id.bank_id.name)
                                hoja.write(linea, columna+2, l.employee_id.bank_account_id.acc_number)
                                hoja.write(linea, columna+3, l.note)
                                hoja.write(linea, columna+4, l.move_id.line_ids[0].analytic_account_id.name)

                                num += 1
                        else:
                            if l.contract_id.analytic_account_id.name == False and i == 'Indefinido':
                                linea += 1
                                dias = 0
                                total_salario = 0

                                hoja.write(linea, 0, num)
                                hoja.write(linea, 1, l.employee_id.codigo_empleado)
                                hoja.write(linea, 2, l.employee_id.name)
                                hoja.write(linea, 3, l.contract_id.date_start)
                                hoja.write(linea, 4, l.employee_id.job_id.name)
                                for d in l.worked_days_line_ids:
                                    if d.code == 'TRABAJO100':
                                        dias += d.number_of_days
                                hoja.write(linea, 5, dias)

                                columna = 6
                                for c in w.planilla_id.columna_id:
                                    reglas = [x.id for x in c.regla_id]
                                    entradas = [x.name for x in c.entrada_id]
                                    total_columna = 0
                                    for r in l.line_ids:
                                        if r.salary_rule_id.id in reglas:
                                            total_columna += r.total
                                    for r in l.input_line_ids:
                                        if r.name in entradas:
                                            total_columna += r.amount
                                    if c.sumar:
                                        total_salario += total_columna
                                    totales[columna-6] += total_columna

                                    hoja.write(linea, columna, total_columna)
                                    columna += 1

                                totales[columna-6] += total_salario
                                hoja.write(linea, columna, total_salario)
                                hoja.write(linea, columna+1, l.employee_id.bank_account_id.bank_id.name)
                                hoja.write(linea, columna+2, l.employee_id.bank_account_id.acc_number)
                                hoja.write(linea, columna+3, l.note)
                                hoja.write(linea, columna+4, 'indefinido')

                                num += 1
                            if l.contract_id.analytic_account_id.name == i:
                                linea += 1
                                dias = 0
                                total_salario = 0

                                hoja.write(linea, 0, num)
                                hoja.write(linea, 1, l.employee_id.codigo_empleado)
                                hoja.write(linea, 2, l.employee_id.name)
                                hoja.write(linea, 3, l.contract_id.date_start)
                                hoja.write(linea, 4, l.employee_id.job_id.name)
                                for d in l.worked_days_line_ids:
                                    if d.code == 'TRABAJO100':
                                        dias += d.number_of_days
                                hoja.write(linea, 5, dias)

                                columna = 6
                                for c in w.planilla_id.columna_id:
                                    reglas = [x.id for x in c.regla_id]
                                    entradas = [x.name for x in c.entrada_id]
                                    total_columna = 0
                                    for r in l.line_ids:
                                        if r.salary_rule_id.id in reglas:
                                            total_columna += r.total
                                    for r in l.input_line_ids:
                                        if r.name in entradas:
                                            total_columna += r.amount
                                    if c.sumar:
                                        total_salario += total_columna
                                    totales[columna-6] += total_columna

                                    hoja.write(linea, columna, total_columna)
                                    columna += 1

                                totales[columna-6] += total_salario
                                hoja.write(linea, columna, total_salario)
                                hoja.write(linea, columna+1, l.employee_id.bank_account_id.bank_id.name)
                                hoja.write(linea, columna+2, l.employee_id.bank_account_id.acc_number)
                                hoja.write(linea, columna+3, l.note)
                                hoja.write(linea, columna+4, l.contract_id.analytic_account_id.name)

                                num += 1
                    columna = 6
                    for t in totales:
                        hoja.write(linea+1, columna, totales[columna-6], estilo)
                        columna += 1
            else:
                hoja = libro.add_sheet('reporte')

                hoja.write(0, 0, 'Planilla', estilo)
                hoja.write(0, 1, w.nomina_id.name, estilo)
                hoja.write(0, 2, 'Periodo', estilo)
                hoja.write(0, 3, w.nomina_id.date_start, estilo)
                hoja.write(0, 4, w.nomina_id.date_end, estilo)

                linea = 2
                num = 1

                hoja.write(linea, 0, 'No', estilo)
                hoja.write(linea, 1, 'Cod. de empleado', estilo)
                hoja.write(linea, 2, 'Nombre de empleado', estilo)
                hoja.write(linea, 3, 'Fecha de ingreso', estilo)
                hoja.write(linea, 4, 'Puesto', estilo)
                hoja.write(linea, 5, 'Dias', estilo)

                totales = []
                columna = 6
                for c in w.planilla_id.columna_id:
                    hoja.write(linea, columna, c.name, estilo)
                    columna += 1
                    totales.append(0)
                totales.append(0)

                hoja.write(linea, columna, 'Liquido a recibir', estilo)
                hoja.write(linea, columna+1, 'Banco a depositar', estilo)
                hoja.write(linea, columna+2, 'Cuenta a depositar', estilo)
                hoja.write(linea, columna+3, 'Observaciones', estilo)
                hoja.write(linea, columna+4, 'Cuenta analítica', estilo)

                linea += 1
                for l in w.nomina_id.slip_ids:
                    dias = 0
                    total_salario = 0

                    hoja.write(linea, 0, num)
                    hoja.write(linea, 1, l.employee_id.codigo_empleado)
                    hoja.write(linea, 2, l.employee_id.name)
                    hoja.write(linea, 3, l.contract_id.date_start)
                    hoja.write(linea, 4, l.employee_id.job_id.name)
                    for d in l.worked_days_line_ids:
                        if d.code == 'TRABAJO100':
                            dias += d.number_of_days
                    hoja.write(linea, 5, dias)

                    columna = 6
                    for c in w.planilla_id.columna_id:
                        reglas = [x.id for x in c.regla_id]
                        entradas = [x.name for x in c.entrada_id]
                        total_columna = 0
                        for r in l.line_ids:
                            if r.salary_rule_id.id in reglas:
                                total_columna += r.total
                        for r in l.input_line_ids:
                            if r.name in entradas:
                                total_columna += r.amount
                        if c.sumar:
                            total_salario += total_columna
                        totales[columna-6] += total_columna

                        hoja.write(linea, columna, total_columna)
                        columna += 1

                    totales[columna-6] += total_salario
                    hoja.write(linea, columna, total_salario)
                    hoja.write(linea, columna+1, l.employee_id.bank_account_id.bank_id.name)
                    hoja.write(linea, columna+2, l.employee_id.bank_account_id.acc_number)
                    hoja.write(linea, columna+3, l.note)
                    if l.move_id and len(l.move_id.line_ids) > 0 and l.move_id.line_ids[0].analytic_account_id:
                        if l.move_id.line_ids[0].analytic_account_id:
                            hoja.write(linea, columna+4, l.move_id.line_ids[0].analytic_account_id.name)
                        else:
                            hoja.write(linea, columna+4, 'indefinido')
                    else:
                        if l.contract_id.analytic_account_id.name:
                            hoja.write(linea, columna+4, l.contract_id.analytic_account_id.name)
                        else:
                            hoja.write(linea, columna+4, 'indefinido')
                    linea += 1
                    num += 1

                columna = 6
                for t in totales:
                    hoja.write(linea, columna, totales[columna-6], estilo)
                    columna += 1

            f = io.BytesIO()
            libro.save(f)
            datos = base64.b64encode(f.getvalue())
            self.archivo = datos
            self.write({'report': self.archivo, 'name':'planilla.xls'})
            return {
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'rrhh.planilla.wizard',
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
