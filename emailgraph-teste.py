#!/usr/bin/python
# -*- coding: utf-8 -*-

# Envio de gráfico por Email através do ZABBIX (Send zabbix alerts graph Mail)
#
# 
# Copyright (C) <2016>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contacts:
# Eracydes Carvalho (Sansão Simonton) - NOC Analyst - sansaoipb@gmail.com
# Thiago Paz - NOC Analyst - thiagopaz1986@gmail.com

import os, sys, re, json, time, requests, smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

import ConfigParser
class PropertiesReaderX:
    config = None
    def __init__(self,pathToProperties):
        PropertiesReaderX.config = ConfigParser.RawConfigParser()
        PropertiesReaderX.config.read(pathToProperties)

    def getValue(self,section,key):
        # type: (object, object) -> object
        return PropertiesReaderX.config.get(section, key)

    def setValue(self,section,key):
        PropertiesReaderX.config.set(section, key)

path="/usr/local/share/zabbix/alertscripts/"

if not os.path.exists(path):
    path="/usr/lib/zabbix/alertscripts/{0}"
else:
    path="/usr/local/share/zabbix/alertscripts/{0}"

itemname = 'ITEM'
color    = '00C800'
period   = 3600
subject = itemname+ " Teste,"
body     = 'testando o envio'

# Zabbix settings | Dados do Zabbix #############################################################################################################
zbx_server = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSection', 'url')
zbx_user   = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSection', 'user')
zbx_pass   = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSection', 'pass')

# Graph settings | Configuracao do Grafico ######################################################################################################
height     = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSection', 'height')    # Graph height | Altura
width      = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSection', 'width')     # Graph width  | Largura
stime      = int(PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSection', 'stime'))    # Graph start time [3600 = 1 hour ago]  |  Hora inicial do grafico [3600 = 1 hora atras]

# Salutation | Saudação ########################################################################################################################
Salutation = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSection', 'salutation')
if re.search("(sim|s|yes|y)", str(Salutation).lower()):
    good_morning   = 'Bom dia'
    good_afternoon = 'Boa Tarde'
    good_evening   = 'Boa Noite'

    hora = int(time.strftime("%H"))

    if hora < 12:
        salutation = "<p>{0},<p/>".format(good_morning)
    elif hora >= 18:
        salutation = "<p>{0},<p/>".format(good_evening)
    else:
        salutation = "<p>{0},<p/>".format(good_afternoon)
else:
    salutation = ""

# Diretórios
# Log path | Diretório do log
projeto = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSectionEmail', 'nome')
logName = '{0}graph-teste.log'.format(projeto)
pathLogs = path.format("log")
arqLog = "{0}".format(os.path.join(pathLogs, logName))

if not os.path.exists(pathLogs):
    os.makedirs(pathLogs)

# Mail settings | Configrações de e-mail #######################################################################################################
email_from  = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSectionEmail', 'email_from')
smtp_server = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSectionEmail', 'smtp_server')
smtp_server = re.search("(\w.+):(\d+)", smtp_server).groups()
mail_user   = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSectionEmail', 'mail_user')
mail_pass   = PropertiesReaderX(path.format('configScrips.properties')).getValue('PathSectionEmail', 'mail_pass')

############################################################################################################
############################################################################################################
############################################################################################################
############################################################################################################

import logging.config
import traceback

file = """{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s][%(levelname)s] - %(message)s"
        }
    },

    "handlers": {
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 5242880,
            "backupCount":5,
            "level": "DEBUG",
            "formatter": "simple",
            "filename": "python_logging.log",
            "encoding": "utf8"
        }
    },

    "root": {
        "level": "DEBUG",
        "handlers": ["file_handler"]
    }
}
"""

arqConfig = "logging_configuration.json"
pathDefault = ""

class Log:
    @staticmethod
    def writelog(entry, pathfile, log_level):
        global pathDefault

        try:
            Log.log(entry, pathfile, log_level)
        except Exception:
            try:
                if "\\" in traceback.format_exc():
                    linha = re.search("(File)[A-Za-z0-9_\"\\\\\s:.]+", traceback.format_exc()).group()[5:].replace("\"","")
                    pathDefault = "{0}\\".format("\\".join(linha.split("\\")[:-1]))
                else:
                    linha = re.search("(File)[A-Za-z0-9_\"/\s:.]+", traceback.format_exc()).group()[5:].replace("\"", "")
                    pathDefault = "{0}/".format("/".join(linha.split("/")[:-1]))
                arquivo = open("{0}{1}".format(pathDefault, arqConfig), "w")
                arquivo.writelines(file)
                arquivo.close()
                Log.log(entry, pathfile, log_level)
            except Exception:
                pass

    @staticmethod
    def log(entry, pathfile, log_level):
        logging.getLogger('suds.client').setLevel(logging.CRITICAL)
        logging.getLogger('suds.wsdl').setLevel(logging.CRITICAL)
        with open("{0}{1}".format(pathDefault, arqConfig), 'r+') as logging_configuration_file:
            config_dict = json.load(logging_configuration_file)
            config_dict["handlers"]["file_handler"]['filename'] = pathfile
        logging.config.dictConfig(config_dict)
        logger = logging.getLogger(__name__)
        logging.getLogger("suds").setLevel(logging.CRITICAL)
        if log_level.upper() == "INFO":
            logger.info(str(entry))
        elif log_level.upper() == "WARNING":
            logger.warning(str(entry))
        elif log_level.upper() == "CRITICAL":
            logger.critical(str(entry))
        elif log_level.upper() == "ERROR":
            logger.error(str(entry))

log = Log


def send_mail(x, i):
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = subject
    msgRoot['From'] = email_from
    msgRoot['To'] = sys.argv[1]

    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)
    text = '{0}<p>{1}</p>'.format(salutation, body)

    if re.search("(0|3)", x):
        URL = "{0}/history.php?action=showgraph&itemids[]={1}"
        text += '<br><a href="{0}"><img src="cid:image1"></a>'.format(URL.format(zbx_server, itemid))
        msgImage = MIMEImage(i)
        msgImage.add_header('Content-ID', '<image1>')
        msgRoot.attach(msgImage)

    msgText = MIMEText(text, 'html', _charset='utf-8')
    msgAlternative.attach(msgText)

    try:
        smtp = smtplib.SMTP(smtp_server[0], smtp_server[1])
        smtp.ehlo()

        try:
            smtp.starttls()
        except Exception:
            pass

        try:
            smtp.login(mail_user, mail_pass)
        except smtplib.SMTPAuthenticationError as msg:
            print("Error: Unable to send email | Não foi possível enviar o e-mail - {0}".format(msg[1]))
            log.writelog('Error: Unable to send email | Não foi possível enviar o e-mail - {0}'.format(msg[1]),arqLog, "WARNING")
            smtp.quit()
            exit()
        except smtplib.SMTPException:
            pass

        try:
            smtp.sendmail(email_from, sys.argv[1], msgRoot.as_string())
        except Exception as msg:
            print("Error: Unable to send email | Não foi possível enviar o e-mail - {0}".format(msg[1]))
            log.writelog('Error: Unable to send email | Não foi possível enviar o e-mail - {0}'.format(msg[1]), arqLog,
                         "WARNING")
            smtp.quit()
            exit()
        logout_api()
        print("Successfully sent email | Email enviado com sucesso ({0})".format(sys.argv[1]))
        log.writelog('Successfully sent email | Email enviado com sucesso ({0})'.format(sys.argv[1]), arqLog, "INFO")
        smtp.quit()
    except smtplib.SMTPException as msg:
        print("Error: Unable to send email | Não foi possível enviar o e-mail ({0})".format(msg))
        log.writelog('Error: Unable to send email | Não foi possível enviar o e-mail ({0})'.format(msg), arqLog, "WARNING")
        logout_api()
        smtp.quit()
        exit()
try:
    login_api = requests.post('%s/api_jsonrpc.php' % zbx_server, headers = {'Content-type': 'application/json'},\
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": zbx_user,
                    "password": zbx_pass
                },
                "id": 1
            }
        )
    )

    login_api = json.loads(login_api.text.encode('utf-8'))

    if 'result' in login_api:
        auth = login_api["result"]
    elif 'error' in login_api:
        print('Zabbix: %s' % login_api["error"]["data"])
        exit()
    else:
        print(login_api)
        exit()

except ValueError as e:
    print('Check declared zabbix URL/IP and try again | Valide a URL/IP do Zabbix declarada e tente novamente\nCurrent: %s' % zbx_server)
    log.writelog('Check declared zabbix URL/IP and try again | Valide a URL/IP do Zabbix declarada e tente novamente. (Current: {0})'.format(zbx_server), arqLog, "WARNING")
    exit()
except Exception as e:
    print(e)
    log.writelog('{0}'.format(str(e)), arqLog, "WARNING")
    exit()

def version_api():
    resultado = requests.post('{0}/api_jsonrpc.php'.format(zbx_server), headers = {'Content-type': 'application/json'},\
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "apiinfo.version",
                "params": [],
                "id": 5
            }
        )
    )
    resultado = json.loads(resultado.content.encode('utf-8'))
    if 'result' in resultado:
        resultado = resultado["result"]
    return resultado

def logout_api():
    requests.post('%s/api_jsonrpc.php' % zbx_server, headers = {'Content-type': 'application/json'},\
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "user.logout",
                "params": [],
                "auth": auth,
                "id": 4
            }
        )
    )
    
itemid = requests.post('%s/api_jsonrpc.php' % zbx_server, headers = {'Content-type': 'application/json'},\
    data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["itemid"],
                "hostid": "",
                "search": {"key_": "agent.ping"}
            },
            "auth": auth,
            "id": 3
        }
    )
)
itemid = json.loads(itemid.text.encode('utf-8'))['result'][0]['itemid']

itemtype_api = requests.post('%s/api_jsonrpc.php' % zbx_server, headers = {'Content-type': 'application/json'},\
    data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["value_type"], "itemids": itemid, "webitems": itemid
            },
            "auth": auth,
            "id": 2
        }
    )
)

itemtype_api = json.loads(itemtype_api.text.encode('utf-8'))

try:
    if itemtype_api["result"]:
        item_type = itemtype_api["result"][0]['value_type']
except Exception:
    print('Invalid ItemID or user has no read permission on item/host | ItemID inválido ou usuário sem permissão de leitura no item/host')
    log.writelog('Invalid ItemID or user has no read permission on item/host | ItemID inválido ou usuário sem permissão de leitura no item/host', arqLog, "WARNING")
    logout_api()
    exit()

if __name__ == '__main__':
    if re.search("(0|3)", item_type):
        try:
            loginpage = requests.get('%s/index.php' % zbx_server).text
            enter = re.search('<button.*value=".*>(.*?)</button>', loginpage)
            enter = str(enter.group(1))

            s = requests.session()
            s.post('%s/index.php?login=1' % zbx_server,  params = {'name': zbx_user, 'password': zbx_pass, 'enter': enter}).text

            stime = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time() -stime))

            get_graph = s.get('%s/chart3.php?name=%s&period=%s&width=%s&height=%s&stime=%s&items[0][itemid]=%s&items[0][drawtype]=5&items[0][color]=%s' % (zbx_server, itemname, period, width, height, stime, itemid, color))
        except BaseException as e:
            print('Can\'t connect to %(ip)s/index.php | Não foi possível conectar-se à %(ip)s/index.php' % {'ip': zbx_server})
            log.writelog('Can\'t connect to %(ip)s/index.php | Não foi possível conectar-se à {0}/index.php'.format(zbx_server), arqLog, "WARNING")
            logout_api()
            exit()

        send_mail(item_type, get_graph.content)

    else:
        send_mail(item_type, None)

