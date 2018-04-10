# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 NaN Projectes de Programari Lliure, S.L.
#                         All Rights Reserved.
#                         http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from decimal import Decimal
import math

SUPPORTED_LANGS = ('en_US', 'es_ES', 'ca_ES')

TENS_UNITS_SEP = {
    'en_US': "-",
    'es_ES': " y ", 
    'ca_ES': "-",
}
CURRENCY_DECIMALS_SEP = {
    'en_US': "with", 
    'es_ES': "con", 
    'ca_ES': "amb",
}
NOT_CURRENCY_DECIMALS_SEP = {
    'en_US': "dot", 
    'es_ES': "coma", 
    'ca_ES': "coma",
}

CURRENCY_INTEGER_NAME = {
    0: {'en_US': "Euros", 'es_ES': "Euros", 'ca_ES': "Euros"},
    1: {'en_US': "Euro", 'es_ES': "Euro", 'ca_ES': "Euro"},
    2: {'en_US': "Euros", 'es_ES': "Euros", 'ca_ES': "Euros"},
}
CURRENCY_DECIMALS_NAME = {
    0: {'en_US': "Cents", 'es_ES': "Céntimos", 'ca_ES': "Cèntims"},
    1: {'en_US': "Cent", 'es_ES': "Céntimo", 'ca_ES': "Cèntim"},
    2: {'en_US': "Cents", 'es_ES': "Céntimos", 'ca_ES': "Cèntims"},
}

TENS = {
    20: {'en_US': "Twenty", 'es_ES': "Venti", 'ca_ES': "Vint"},
    30: {'en_US': "Thirty", 'es_ES': "Treinta", 'ca_ES': "Trenta"},
    40: {'en_US': "Forty", 'es_ES': "Cuarenta", 'ca_ES': "Quaranta"},
    50: {'en_US': "Fifty", 'es_ES': "Cincuenta", 'ca_ES': "Cinquanta"},
    60: {'en_US': "Sixty", 'es_ES': "Sesenta", 'ca_ES': "Seixanta"},
    70: {'en_US': "Seventy", 'es_ES': "Setenta", 'ca_ES': "Setanta"},
    80: {'en_US': "Eighty", 'es_ES': "Ochenta", 'ca_ES': "Vuitanta"},
    90: {'en_US': "Ninety", 'es_ES': "Noventa", 'ca_ES': "Noranta"},
}

HUNDREDS = {
    100: {'en_US': "One Hundred", 'es_ES': "Ciento", 'ca_ES': "Cent"},
    200: {'en_US': "Two Hundred", 'es_ES': "Doscientos", 'ca_ES': "Dos-cents"},
    300: {'en_US': "Three Hundred", 'es_ES': "Trescientos", 'ca_ES': "Tres-ents"},
    400: {'en_US': "Four Hundred", 'es_ES': "Cuatrocientos", 'ca_ES': "Quatre-cents"},
    500: {'en_US': "Five Hundred", 'es_ES': "Quinientos", 'ca_ES': "Cinc-cents"},
    600: {'en_US': "Six Hundred", 'es_ES': "Seiscientos", 'ca_ES': "Sis-cents"},
    700: {'en_US': "Seven Hundred", 'es_ES': "Setecientos", 'ca_ES': "Set-cents"},
    800: {'en_US': "Eight Hundred", 'es_ES': "Ochocientos", 'ca_ES': "Vuit-cents"},
    900: {'en_US': "Nine Hundred", 'es_ES': "Novecientos", 'ca_ES': "Nou-cents"},
}

GREATER = {
    1000: {'en_US': "One Thousand", 'es_ES': "Mil", 'ca_ES': "Mil"},
    1000000: {'en_US': "One Million", 'es_ES': "Millones", 'ca_ES': "Milions"},
}

UNITS = TENS.copy()
UNITS.update(HUNDREDS)
UNITS.update(GREATER)
UNITS.update({
    0: {'en_US': "Zero", 'es_ES': "Cero", 'ca_ES': "Zero"},
    1: {'en_US': "One", 'es_ES': "Un", 'ca_ES': "Un"},
    2: {'en_US': "Two",'es_ES': "Dos", 'ca_ES': "Dos"},
    3: {'en_US': "Three",'es_ES': "Tres", 'ca_ES': "Tres"},
    4: {'en_US': "Four",'es_ES': "Cuatro", 'ca_ES': "Quatre"},
    5: {'en_US': "Five",'es_ES': "Cinco", 'ca_ES': "Cinc"},
    6: {'en_US': "Six",'es_ES': "Seis", 'ca_ES': "Sis"},
    7: {'en_US': "Seven",'es_ES': "Siete", 'ca_ES': "Set"},
    8: {'en_US': "Eight",'es_ES': "Ocho", 'ca_ES': "Vuit"},
    9: {'en_US': "Nine",'es_ES': "Nueve", 'ca_ES': "Nou"},
    10: {'en_US': "Ten",'es_ES': "Diez", 'ca_ES': "Deu"},
    11: {'en_US': "Eleven",'es_ES': "Once", 'ca_ES': "Onze"},
    12: {'en_US': "Twelve",'es_ES': "Doce", 'ca_ES': "Dotze"},
    13: {'en_US': "Thirteen",'es_ES': "Trece", 'ca_ES': "Tretze"},
    14: {'en_US': "Fourteen",'es_ES': "Catorce", 'ca_ES': "Catorze"},
    15: {'en_US': "Fifteen",'es_ES': "Quince", 'ca_ES': "Quinze"},
    16: {'en_US': "Sixteen",'es_ES': "Dieciséis", 'ca_ES': "Setze"},
    17: {'en_US': "Seventeen",'es_ES': "Diecisiete", 'ca_ES': "Disset"},
    18: {'en_US': "Eighteen",'es_ES': "Dieciocho", 'ca_ES': "Divuit"},
    19: {'en_US': "Nineteen",'es_ES': "Diecinueve", 'ca_ES': "Dinou"},
    # When the values is exactly '20', is so called
    20: {'es_ES': "Veinte", 'ca_ES': "Vint"},
    21: {'es_ES': "Veintiún", 'ca_ES': "Vint-i-un"},
    22: {'es_ES': "Veintidós", 'ca_ES': "Vint-i-dos"},
    23: {'es_ES': "Veintitrés", 'ca_ES': "Vint-i-tres"},
    24: {'es_ES': "Veinticuatro", 'ca_ES': "Vint-i-quatre"},
    25: {'es_ES': "Veinticinco", 'ca_ES': "Vint-i-cinc"},
    26: {'es_ES': "Veintiséis", 'ca_ES': "Vint-i-sis"},
    27: {'es_ES': "Veintisiete", 'ca_ES': "Vint-i-set"},
    28: {'es_ES': "Veintiocho", 'ca_ES': "Vint-i-vuit"},
    29: {'es_ES': "Veintinueve", 'ca_ES': "Vint-i-nou"},
    # When the values is exactly '100', is so called
    100: {'en_US': "Hundred", 'es_ES': "Cien", 'ca_ES': "Cent"},
    1000: {'en_US': "Thousand", 'es_ES': "Mil", 'ca_ES': "Mil"},
    1000000: {'en_US': "Million", 'es_ES': "Un Millón", 'ca_ES': "Un Milió"},
})


def integer_to_literal(input_int, lang_code):
    assert type(input_int) == int, "Invalid type of parameter. Expected 'int' "\
            "but found %s" % str(type(input_int))
    assert lang_code and lang_code in SUPPORTED_LANGS, "The Language Code " \
            "is not supported. The suported languages are: %s" \
                    % ", ".join(SUPPORTED_LANGS[:-1]) + " and " + \
                            SUPPORTED_LANGS[-1]
    
    if input_int in UNITS and lang_code in UNITS[input_int]:
        return UNITS[input_int][lang_code]
    
    million = int(math.floor(Decimal(str(input_int)) / 1000000))
    thousands = input_int - million * 1000000
    thousands = int(math.floor(Decimal(str(thousands)) / 1000))
    hundreds = input_int - million * 1000000 - thousands * 1000
    
    
    def __convert_hundreds(input_hundred):
        assert (input_hundred and 
                type(input_hundred) == int and 
                input_hundred < 1000), "Invalid Hundred input"
        
        if input_hundred in UNITS and lang_code in UNITS[input_hundred]:
            return [UNITS[input_hundred][lang_code]]
        
        res = []
        
        hundreds_value = (input_hundred / 100) * 100
        if hundreds_value:
            res.append(HUNDREDS[hundreds_value][lang_code])
            input_hundred -= hundreds_value
            if not input_hundred:
                return res
        
        if input_hundred in UNITS and lang_code in UNITS[input_hundred]:
            # values <= 30 or X0
            res.append(UNITS[input_hundred][lang_code])
            return res
        
        # XY; X >= 3 and y != 0
        tens_value = (input_hundred / 10) * 10
        units_value = input_hundred - tens_value
        if TENS_UNITS_SEP and lang_code in TENS_UNITS_SEP:
            res.append(TENS[tens_value][lang_code] + TENS_UNITS_SEP[lang_code] +
                    UNITS[units_value][lang_code])
        else:
            res.append(TENS[tens_value][lang_code])
            res.append(UNITS[units_value][lang_code])
        
        return res
    
    converted = []
    if million:
        if million == 1:
            converted.append(UNITS[1000000][lang_code])
        else:
            converted += __convert_hundreds(million)
            converted.append(GREATER[1000000][lang_code])
        
        input_int -= million * 1000000
    
    if thousands:
        if thousands == 1:
            converted.append(UNITS[1000][lang_code])
        else:
            converted += __convert_hundreds(thousands)
            converted.append(GREATER[1000][lang_code])
    
    if hundreds:
        # exactly 100 is already contempleted
        converted += __convert_hundreds(hundreds)
    return " ".join(converted)


def number_to_literal(input_number, lang_code, rounding=0.01, is_currency=True):
    assert lang_code and lang_code in SUPPORTED_LANGS, "The Language Code " \
            "is not supported. The suported languages are: %s" \
                    % ", ".join(SUPPORTED_LANGS[:-1]) + " and " + \
                            SUPPORTED_LANGS[-1]
    
    PREC = Decimal(str(rounding))
    
    input_number = Decimal(str(input_number)).quantize(PREC)
    
    number_int = int(math.floor(input_number))
    decimals = int((input_number - number_int) * (1 / PREC))
    
    res = []
    res.append(integer_to_literal(number_int, lang_code))
    
    if is_currency:
        if (number_int in CURRENCY_INTEGER_NAME and 
                lang_code in CURRENCY_INTEGER_NAME[number_int]):
            res.append(CURRENCY_INTEGER_NAME[number_int][lang_code])
        else:
            res.append(CURRENCY_INTEGER_NAME[2][lang_code])
        
        if decimals:
            res.append(CURRENCY_DECIMALS_SEP[lang_code])
    elif decimals:
        res.append(NOT_CURRENCY_DECIMALS_SEP[lang_code])
    
    if decimals:
        res.append(integer_to_literal(decimals, lang_code))
        if is_currency:
            if (decimals in CURRENCY_DECIMALS_NAME and 
                    lang_code in CURRENCY_DECIMALS_NAME[decimals]):
                res.append(CURRENCY_DECIMALS_NAME[decimals][lang_code])
            else:
                res.append(CURRENCY_DECIMALS_NAME[2][lang_code])
    
    return " ".join(res)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
