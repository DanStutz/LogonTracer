#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# LICENSE
# Please refer to the LICENSE.txt in the https://github.com/JPCERTCC/aa-tools/
#

import os
import sys
import re
import argparse
import datetime
import subprocess

try:
    from lxml import etree
    has_lxml = True
except ImportError:
    has_lxml = False

try:
    from Evtx.Evtx import Evtx
    from Evtx.Views import evtx_file_xml_view
    has_evtx = True
except ImportError:
    has_evtx = False

try:
    from py2neo import Graph
    has_py2neo = True
except ImportError:
    has_py2neo = False

try:
    import numpy as np
    has_numpy = True
except ImportError:
    has_numpy = False

try:
    import changefinder
    has_changefinder = True
except ImportError:
    has_changefinder = False

try:
    from flask import Flask, render_template, request
    has_flask = True
except ImportError:
    has_flask = False

try:
    import pandas as pd
    has_pandas = True
except ImportError:
    has_pandas = False

try:
    from hmmlearn import hmm
    has_hmmlearn = True
except ImportError:
    has_hmmlearn = False

try:
    from sklearn.externals import joblib
    has_sklearn = True
except ImportError:
    has_sklearn = False

# neo4j password
NEO4J_PASSWORD = "password"
# neo4j user name
NEO4J_USER = "neo4j"
# neo4j server
NEO4J_SERVER = "localhost"
# neo4j listen port
NEO4J_PORT = "7474"
# Web application port
WEB_PORT = 8080
# Web application address
WEB_HOST = "0.0.0.0"

# Check Event Id
EVENT_ID = [4624, 4625, 4662, 4768, 4769, 4776, 4672, 4720, 4726, 4728, 4729, 4732, 4733, 4756, 4757, 4719, 5137, 5141]

# EVTX Header
EVTX_HEADER = b"\x45\x6C\x66\x46\x69\x6C\x65\x00"

# String Check list
UCHECK = r"[%*+=\[\]\\/|;:\"<>?,&]"
HCHECK = r"[*\\/|:\"<>?&]"

# IPv4 regex
IPv4_PATTERN = re.compile(r"\A\d+\.\d+\.\d+\.\d+\Z", re.DOTALL)

# IPv6 regex
IPv6_PATTERN = re.compile(r"\A(::(([0-9a-f]|[1-9a-f][0-9a-f]{1,3})(:([0-9a-f]|[1-9a-f][0-9a-f]{1,3})){0,5})?|([0-9a-f]|[1-9a-f][0-9a-f]{1,3})(::(([0-9a-f]|[1-9a-f][0-9a-f]{1,3})(:([0-9a-f]|[1-9a-f][0-9a-f]{1,3})){0,4})?|:([0-9a-f]|[1-9a-f][0-9a-f]{1,3})(::(([0-9a-f]|[1-9a-f][0-9a-f]{1,3})(:([0-9a-f]|[1-9a-f][0-9a-f]{1,3})){0,3})?|:([0-9a-f]|[1-9a-f][0-9a-f]{1,3})(::(([0-9a-f]|[1-9a-f][0-9a-f]{1,3})(:([0-9a-f]|[1-9a-f][0-9a-f]{1,3})){0,2})?|:([0-9a-f]|[1-9a-f][0-9a-f]{1,3})(::(([0-9a-f]|[1-9a-f][0-9a-f]{1,3})(:([0-9a-f]|[1-9a-f][0-9a-f]{1,3}))?)?|:([0-9a-f]|[1-9a-f][0-9a-f]{1,3})(::([0-9a-f]|[1-9a-f][0-9a-f]{1,3})?|(:([0-9a-f]|[1-9a-f][0-9a-f]{1,3})){3}))))))\Z", re.DOTALL)

# LogonTracer folder path
FPATH = os.path.dirname(os.path.abspath(__file__))

# CategoryId
CATEGORY_IDs = {
    "%%8280": "Account_Logon",
    "%%8270": "Account_Management",
    "%%8276": "Detailed_Tracking",
    "%%8279": "DS_Access",
    "%%8273": "Logon/Logoff",
    "%%8274": "Object_Access",
    "%%8277": "Policy_Change",
    "%%8275": "Privilege_Use",
    "%%8272": "System"}

# Auditing Constants
AUDITING_CONSTANTS = {
    "{0cce9210-69ae-11d9-bed3-505054503030}": "SecurityStateChange",
    "{0cce9211-69ae-11d9-bed3-505054503030}": "SecuritySubsystemExtension",
    "{0cce9212-69ae-11d9-bed3-505054503030}": "Integrity",
    "{0cce9213-69ae-11d9-bed3-505054503030}": "IPSecDriverEvents",
    "{0cce9214-69ae-11d9-bed3-505054503030}": "Others",
    "{0cce9215-69ae-11d9-bed3-505054503030}": "Logon",
    "{0cce9216-69ae-11d9-bed3-505054503030}": "Logoff",
    "{0cce9217-69ae-11d9-bed3-505054503030}": "AccountLockout",
    "{0cce9218-69ae-11d9-bed3-505054503030}": "IPSecMainMode",
    "{0cce9219-69ae-11d9-bed3-505054503030}": "IPSecQuickMode",
    "{0cce921a-69ae-11d9-bed3-505054503030}": "IPSecUserMode",
    "{0cce921b-69ae-11d9-bed3-505054503030}": "SpecialLogon",
    "{0cce921c-69ae-11d9-bed3-505054503030}": "Others",
    "{0cce921d-69ae-11d9-bed3-505054503030}": "FileSystem",
    "{0cce921e-69ae-11d9-bed3-505054503030}": "Registry",
    "{0cce921f-69ae-11d9-bed3-505054503030}": "Kernel",
    "{0cce9220-69ae-11d9-bed3-505054503030}": "Sam",
    "{0cce9221-69ae-11d9-bed3-505054503030}": "CertificationServices",
    "{0cce9222-69ae-11d9-bed3-505054503030}": "ApplicationGenerated",
    "{0cce9223-69ae-11d9-bed3-505054503030}": "Handle",
    "{0cce9224-69ae-11d9-bed3-505054503030}": "Share",
    "{0cce9225-69ae-11d9-bed3-505054503030}": "FirewallPacketDrops",
    "{0cce9226-69ae-11d9-bed3-505054503030}": "FirewallConnection",
    "{0cce9227-69ae-11d9-bed3-505054503030}": "Other",
    "{0cce9228-69ae-11d9-bed3-505054503030}": "Sensitive",
    "{0cce9229-69ae-11d9-bed3-505054503030}": "NonSensitive",
    "{0cce922a-69ae-11d9-bed3-505054503030}": "Others",
    "{0cce922b-69ae-11d9-bed3-505054503030}": "ProcessCreation",
    "{0cce922c-69ae-11d9-bed3-505054503030}": "ProcessTermination",
    "{0cce922d-69ae-11d9-bed3-505054503030}": "DpapiActivity",
    "{0cce922e-69ae-11d9-bed3-505054503030}": "RpcCall",
    "{0cce922f-69ae-11d9-bed3-505054503030}": "AuditPolicy",
    "{0cce9230-69ae-11d9-bed3-505054503030}": "AuthenticationPolicy",
    "{0cce9231-69ae-11d9-bed3-505054503030}": "AuthorizationPolicy",
    "{0cce9232-69ae-11d9-bed3-505054503030}": "MpsscvRulePolicy",
    "{0cce9233-69ae-11d9-bed3-505054503030}": "WfpIPSecPolicy",
    "{0cce9234-69ae-11d9-bed3-505054503030}": "Others",
    "{0cce9235-69ae-11d9-bed3-505054503030}": "UserAccount",
    "{0cce9236-69ae-11d9-bed3-505054503030}": "ComputerAccount",
    "{0cce9237-69ae-11d9-bed3-505054503030}": "SecurityGroup",
    "{0cce9238-69ae-11d9-bed3-505054503030}": "DistributionGroup",
    "{0cce9239-69ae-11d9-bed3-505054503030}": "ApplicationGroup",
    "{0cce923a-69ae-11d9-bed3-505054503030}": "Others",
    "{0cce923b-69ae-11d9-bed3-505054503030}": "DSAccess",
    "{0cce923c-69ae-11d9-bed3-505054503030}": "AdAuditChanges",
    "{0cce923d-69ae-11d9-bed3-505054503030}": "Replication",
    "{0cce923e-69ae-11d9-bed3-505054503030}": "DetailedReplication",
    "{0cce923f-69ae-11d9-bed3-505054503030}": "CredentialValidation",
    "{0cce9240-69ae-11d9-bed3-505054503030}": "Kerberos",
    "{0cce9241-69ae-11d9-bed3-505054503030}": "Others",
    "{0cce9242-69ae-11d9-bed3-505054503030}": "KerbCredentialValidation",
    "{0cce9243-69ae-11d9-bed3-505054503030}": "NPS"}

# Flask instance
if not has_flask:
    sys.exit("[!] Flask must be installed for this script.")
else:
    app = Flask(__name__)

parser = argparse.ArgumentParser(description="Visualizing and analyzing active directory Windows logon event logs.")
parser.add_argument("-r", "--run", action="store_true", default=False,
                    help="Start web application.")
parser.add_argument("-l", "--learn", action="store_true", default=False,
                    help="Machine learning event logs using Hidden Markov Model.")
parser.add_argument("-o", "--port", dest="port", action="store", type=int, metavar="PORT",
                    help="Port number to be started web application. (default: 8080).")
parser.add_argument("--host", dest="host", action="store", type=str, metavar="HOST",
                    help="Host address to bind the web application. (default: 0.0.0.0).")
parser.add_argument("-s", "--server", dest="server", action="store", type=str, metavar="SERVER",
                    help="Neo4j server. (default: localhost)")
parser.add_argument("-u", "--user", dest="user", action="store", type=str, metavar="USERNAME",
                    help="Neo4j account name. (default: neo4j)")
parser.add_argument("-p", "--password", dest="password", action="store", type=str, metavar="PASSWORD",
                    help="Neo4j password. (default: password).")
parser.add_argument("-e", "--evtx", dest="evtx", nargs="*", action="store", type=str, metavar="EVTX",
                    help="Import to the AD EVTX file. (multiple files OK)")
parser.add_argument("-x", "--xml", dest="xmls", nargs="*", action="store", type=str, metavar="XML",
                    help="Import to the XML file for event log. (multiple files OK)")
parser.add_argument("-z", "--timezone", dest="timezone", action="store", type=int, metavar="UTC",
                    help="Event log time zone. (for example: +9) (default: GMT)")
parser.add_argument("-f", "--from", dest="fromdate", action="store", type=str, metavar="DATE",
                    help="Parse Security Event log from this time. (for example: 20170101000000)")
parser.add_argument("-t", "--to", dest="todate", action="store", type=str, metavar="DATE",
                    help="Parse Security Event log to this time. (for example: 20170228235959)")
parser.add_argument("--delete", action="store_true", default=False,
                    help="Delete all nodes and relationships from this Neo4j database. (default: False)")
args = parser.parse_args()

statement_user = """
  MERGE (user:Username{ user:{user} }) set user.rights={rights}, user.sid={sid}, user.rank={rank}, user.status={status}, user.counts={counts}, user.counts4624={counts4624}, user.counts4625={counts4625}, user.counts4768={counts4768}, user.counts4769={counts4769}, user.counts4776={counts4776}, user.detect={detect}
  RETURN user
  """

statement_ip = """
  MERGE (ip:IPAddress{ IP:{IP} }) set ip.rank={rank}, ip.hostname={hostname}
  RETURN ip
  """

statement_r = """
  MATCH (user:Username{ user:{user} })
  MATCH (ip:IPAddress{ IP:{IP} })
  CREATE (ip)-[event:Event]->(user) set event.id={id}, event.logintype={logintype}, event.status={status}, event.count={count}, event.authname={authname}, event.date={date}

  RETURN user, ip
  """

statement_date = """
  MERGE (date:Date{ date:{Daterange} }) set date.start={start}, date.end={end}
  RETURN date
  """

statement_domain = """
  MERGE (domain:Domain{ domain:{domain} })
  RETURN domain
  """

statement_dr = """
  MATCH (domain:Domain{ domain:{domain} })
  MATCH (user:Username{ user:{user} })
  CREATE (user)-[group:Group]->(domain)

  RETURN user, domain
  """

statement_del = """
  MERGE (date:Deletetime{ date:{deletetime} }) set date.user={user}, date.domain={domain}
  RETURN date
  """

statement_pl = """
  MERGE (id:ID{ id:{id} }) set id.changetime={changetime}, id.category={category}, id.sub={sub}
  RETURN id
  """

statement_pr = """
  MATCH (id:ID{ id:{id} })
  MATCH (user:Username{ user:{user} })
  CREATE (user)-[group:Policy]->(id) set group.date={date}

  RETURN user, id
  """

if args.user:
    NEO4J_USER = args.user

if args.password:
    NEO4J_PASSWORD = args.password

if args.server:
    NEO4J_SERVER = args.server

if args.port:
    WEB_PORT = args.port

if args.host:
    WEB_HOST = args.host

# Web application index.html
@app.route('/')
def index():
    return render_template("index.html", server_ip=NEO4J_SERVER, neo4j_password=NEO4J_PASSWORD, neo4j_user=NEO4J_USER)


# Timeline view
@app.route('/timeline')
def timeline():
    return render_template("timeline.html", server_ip=NEO4J_SERVER, neo4j_password=NEO4J_PASSWORD, neo4j_user=NEO4J_USER)


# Web application logs
@app.route('/log')
def logs():
    with open(FPATH + "/static/logontracer.log", "r") as lf:
        logdata = lf.read()
    return logdata


# Web application upload
@app.route("/upload", methods=["POST"])
def do_upload():
    UPLOAD_DIR = os.path.join(FPATH, 'upload')
    filelist = ""

    if os.path.exists(UPLOAD_DIR) is False:
        os.mkdir(UPLOAD_DIR)
        print("[*] make upload folder %s." % UPLOAD_DIR)

    try:
        timezone = request.form["timezone"]
        logtype = request.form["logtype"]
        for i in range(0, len(request.files)):
            loadfile = "file" + str(i)
            file = request.files[loadfile]
            if file and file.filename:
                if "EVTX" in logtype:
                    filename = os.path.join(UPLOAD_DIR, str(i) + ".evtx")
                elif "XML" in logtype:
                    filename = os.path.join(UPLOAD_DIR, str(i) + ".xml")
                else:
                    continue
                file.save(filename)
                filelist += filename + " "
        if "EVTX" in logtype:
            logoption = " -e "
        elif "XML" in logtype:
            logoption = " -x "
        else:
            return "FAIL"
        if not re.search(r"\A-{0,1}[0-9]{1,2}\Z", timezone):
            return "FAIL"

        parse_command = "nohup python3 " + FPATH + "/logontracer.py --delete -z " + timezone + logoption + filelist + " -u " + NEO4J_USER + " -p " + NEO4J_PASSWORD + " >  " + FPATH + "/static/logontracer.log 2>&1 &"
        subprocess.call("rm -f " + FPATH + "/static/logontracer.log > /dev/null", shell=True)
        subprocess.call(parse_command, shell=True)
        # parse_evtx(filename)
        return "SUCCESS"

    except:
        return "FAIL"


# Calculate ChangeFinder
def adetection(counts, users, starttime, tohours):
    count_array = np.zeros((5, len(users), tohours + 1))
    count_all_array = []
    result_array = []
    cfdetect = {}
    for _, event in counts.iterrows():
        column = int((datetime.datetime.strptime(event["dates"], "%Y-%m-%d  %H:%M:%S") - starttime).total_seconds() / 3600)
        row = users.index(event["username"])
        # count_array[row, column, 0] = count_array[row, column, 0] + count
        if event["eventid"] == 4624:
            count_array[0, row, column] = event["count"]
        elif event["eventid"] == 4625:
            count_array[1, row, column] = event["count"]
        elif event["eventid"] == 4768:
            count_array[2, row, column] = event["count"]
        elif event["eventid"] == 4769:
            count_array[3, row, column] = event["count"]
        elif event["eventid"] == 4776:
            count_array[4, row, column] = event["count"]
        elif event["eventid"] == 4719:
            count_array[5, row, column] = event["count"]

    count_sum = np.sum(count_array, axis=0)
    count_average = count_sum.mean(axis=0)
    num = 0
    for udata in count_sum:
        cf = changefinder.ChangeFinder(r=0.04, order=1, smooth=5)
        ret = []
        for i in count_average:
            cf.update(i)

        for i in udata:
            score = cf.update(i)
            ret.append(round(score, 2))
        result_array.append(ret)

        cfdetect[users[num]] = max(ret)

        count_all_array.append(udata.tolist())
        for var in range(0, 6):
            con = []
            for i in range(0, tohours + 1):
                con.append(count_array[var, num, i])
            count_all_array.append(con)
        num += 1

    return count_all_array, result_array, cfdetect


# Calculate PageRank
def pagerank(event_set, admins, hmm, cf, ntml):
    graph = {}
    nodes = []
    for _, events in event_set.iterrows():
        nodes.append(events["ipaddress"])
        nodes.append(events["username"])

    for node in list(set(nodes)):
        links = []
        for _, events in event_set.iterrows():
            if node in events["ipaddress"]:
                links.append(events["username"])
            if node in events["username"]:
                links.append(events["ipaddress"])
        graph[node] = links

    # d = 0.85
    numloops = 30
    ranks = {}
    d = {}
    npages = len(graph)

    # Calc damping factor and initial value
    for page in graph:
        if page in admins:
            df = 0.6
        elif "@" in page[-1]:
            df = 0.85
        else:
            df = 0.8
        if page in hmm:
            df -= 0.2
        if page in ntml:
            df -= 0.1
        if page in cf:
            df -= cf[page] / 200

        d[page] = df
        ranks[page] = 1.0 / npages

    for i in range(0, numloops):
        newranks = {}
        for page in graph:
            newrank = (1 - d[page]) / npages
            for node in graph:
                if page in graph[node]:
                    newrank = newrank + d[node] * ranks[node]/len(graph[node])
            newranks[page] = newrank
        ranks = newranks

    nranks = {}
    max_v = max(ranks.values())
    min_v = min(ranks.values())
    for key, value in ranks.items():
        nranks[key] = (value - min_v) / (max_v - min_v)

    return nranks


# Calculate Hidden Markov Model
def decodehmm(frame, users, stime):
    detect_hmm = []
    model = joblib.load(FPATH + "/model/hmm.pkl")
    while(1):
        date = stime.strftime("%Y-%m-%d")
        for user in users:
            hosts = np.unique(frame[(frame["user"] == user)].host.values)
            for host in hosts:
                udata = []
                for _, data in frame[(frame["date"].str.contains(date)) & (frame["user"] == user) & (frame["host"] == host)].iterrows():
                    id = data["id"]
                    if id == 4776:
                        udata.append(0)
                    elif id == 4768:
                        udata.append(1)
                    elif id == 4769:
                        udata.append(2)
                    elif id == 4624:
                        udata.append(3)
                    elif id == 4625:
                        udata.append(4)
                    elif id == 4719:
                        udata.append(5)
                if len(udata) > 2:
                    data_decode = model.predict(np.array([np.array(udata)], dtype="int").T)
                    unique_data = np.unique(data_decode)
                    if unique_data.shape[0] == 2:
                        if user not in detect_hmm:
                            detect_hmm.append(user)

        stime += datetime.timedelta(days=1)
        if frame.loc[(frame["date"].str.contains(date))].empty:
            break

    return detect_hmm


# Learning Hidden Markov Model
def learnhmm(frame, users, stime):
    lengths = []
    data_array = np.array([])
    
    emission_probability = np.array([[0.09,   0.05,   0.35,   0.51],
                                     [0.0003, 0.0004, 0.0003, 0.999],
                                     [0.0003, 0.0004, 0.0003, 0.999]])
    while(1):
        date = stime.strftime("%Y-%m-%d")
        for user in users:
            hosts = np.unique(frame[(frame["user"] == user)].host.values)
            for host in hosts:
                udata = np.array([])
                for _, data in frame[(frame["date"].str.contains(date)) & (frame["user"] == user) & (frame["host"] == host)].iterrows():
                    id = data["id"]
                    udata = np.append(udata, id)
               
                if udata.shape[0] > 2:
                    data_array = np.append(data_array, udata)
                    lengths.append(udata.shape[0])

        stime += datetime.timedelta(days=1)
        if frame.loc[(frame["date"].str.contains(date))].empty:
            break

    data_array[data_array == 4776] = 0
    data_array[data_array == 4768] = 1
    data_array[data_array == 4769] = 2
    data_array[data_array == 4624] = 3
    data_array[data_array == 4625] = 4
    data_array[data_array == 4719] = 5
    
    model = hmm.MultinomialHMM(n_components=3, n_iter=10000)
    
    model.emissionprob_ = emission_probability
    model.fit(np.array([data_array], dtype="int").T, lengths)
    joblib.dump(model, FPATH + "/model/hmm.pkl")


def to_lxml(record_xml):
    rep_xml = record_xml.replace("xmlns=\"http://schemas.microsoft.com/win/2004/08/events/event\"", "")
    set_xml = "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\" ?>%s" % rep_xml
    fin_xml = set_xml.encode("utf-8")
    parser = etree.XMLParser(resolve_entities=False)
    return etree.fromstring(fin_xml, parser)


def xml_records(filename):
    if args.evtx:
        with Evtx(filename) as evtx:
            for xml, record in evtx_file_xml_view(evtx.get_file_header()):
                try:
                    yield to_lxml(xml), None
                except etree.XMLSyntaxError as e:
                    yield xml, e

    if args.xmls:
        with open(filename, 'r') as fx:
            xdata = fx.read()
            fixdata = xdata.replace("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>", "").replace("</Events>", "").replace("<Events>", "")
            # fixdata = xdata.replace("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>", "")
            del xdata
            xml_list = re.split("<Event xmlns=[\'\"]http://schemas.microsoft.com/win/2004/08/events/event[\'\"]>", fixdata)
            del fixdata
            for xml in xml_list:
                if xml.startswith("<System>"):
                    try:
                        yield to_lxml("<Event>" + xml), None
                    except etree.XMLSyntaxError as e:
                        yield xml, e


# Parse the EVTX file
def parse_evtx(evtx_list):
    event_set = pd.DataFrame(index=[], columns=["eventid", "ipaddress", "username", "logintype", "status", "authname", "date"])
    count_set = pd.DataFrame(index=[], columns=["dates", "eventid", "username"])
    ml_frame = pd.DataFrame(index=[], columns=["date", "user", "host", "id"])
    username_set = []
    domain_set = []
    admins = []
    domains = []
    ntmlauth = []
    deletelog = []
    policylist = []
    addusers = {}
    delusers = {}
    addgroups = {}
    removegroups = {}
    sids = {}
    hosts = {}
    dcsync_count = {}
    dcsync = {}
    dcshadow_check = []
    dcshadow = {}
    count = 0
    record_sum = 0
    starttime = None
    endtime = None

    if args.timezone:
        try:
            datetime.timezone(datetime.timedelta(hours=args.timezone))
            tzone = args.timezone
            print("[*] Time zone is %s." % args.timezone)
        except:
            sys.exit("[!] Can't load time zone '%s'." % args.timezone)
    else:
        tzone = 0

    if args.fromdate:
        try:
            fdatetime = datetime.datetime.strptime(args.fromdate, "%Y%m%d%H%M%S")
            print("[*] Parse the EVTX from %s." % fdatetime.strftime("%Y-%m-%d %H:%M:%S"))
        except:
            sys.exit("[!] From date does not match format '%Y%m%d%H%M%S'.")

    if args.todate:
        try:
            tdatetime = datetime.datetime.strptime(args.todate, "%Y%m%d%H%M%S")
            print("[*] Parse the EVTX from %s." % tdatetime.strftime("%Y-%m-%d %H:%M:%S"))
        except:
            sys.exit("[!] To date does not match format '%Y%m%d%H%M%S'.")

    for evtx_file in evtx_list:
        if args.evtx:
            with open(evtx_file, "rb") as fb:
                fb_data = fb.read()[0:8]
                if fb_data != EVTX_HEADER:
                    sys.exit("[!] This file is not EVTX format {0}.".format(evtx_file))

            chunk = -2
            with Evtx(evtx_file) as evtx:
                fh = evtx.get_file_header()
                try:
                    while True:
                        last_chunk = list(evtx.chunks())[chunk]
                        last_record = last_chunk.file_last_record_number()
                        chunk -= 1
                        if last_record > 0:
                            record_sum = record_sum + last_record
                            break
                except:
                    record_sum = record_sum + fh.next_record_number()

        if args.xmls:
            with open(evtx_file, "r") as fb:
                fb_data = fb.read()
                if "<?xml" not in fb_data[0:6]:
                    sys.exit("[!] This file is not XML format {0}.".format(evtx_file))
                record_sum += fb_data.count("<System>")
                del fb_data

    print("[*] Last record number is %i." % record_sum)

    # Parse Event log
    print("[*] Start parsing the EVTX file.")

    for evtx_file in evtx_list:
        print("[*] Parse the EVTX file %s." % evtx_file)

        for node, err in xml_records(evtx_file):
            if err is not None:
                continue
            count += 1
            eventid = int(node.xpath("/Event/System/EventID")[0].text)

            if not count % 100:
                sys.stdout.write("\r[*] Now loading %i records." % count)
                sys.stdout.flush()

            if eventid in EVENT_ID:
                logtime = node.xpath("/Event/System/TimeCreated")[0].get("SystemTime")
                try:
                    etime = datetime.datetime.strptime(logtime.split(".")[0], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=tzone)
                except:
                    etime = datetime.datetime.strptime(logtime.split(".")[0], "%Y-%m-%dT%H:%M:%S") + datetime.timedelta(hours=tzone)
                stime = datetime.datetime(*etime.timetuple()[:4])
                if args.fromdate or args.todate:
                    if args.fromdate and fdatetime > etime:
                        continue
                    if args.todate and tdatetime < etime:
                        endtime = stime
                        break

                if starttime is None:
                    starttime = stime
                elif starttime > etime:
                    starttime = stime

                if endtime is None:
                    endtime = stime
                elif endtime < etime:
                    endtime = stime

                event_data = node.xpath("/Event/EventData/Data")
                logintype = "-"
                username = "-"
                domain = "-"
                ipaddress = "-"
                hostname = "-"
                status = "-"
                sid = "-"
                authname = "-"

                ###
                # Detect admin users
                #  EventID 4672: Special privileges assigned to new logon
                ###
                if eventid == 4672:
                    for data in event_data:
                        if data.get("Name") in "SubjectUserName" and data.text is not None and not re.search(UCHECK, data.text):
                            username = data.text.split("@")[0]
                            if username[-1:] not in "$":
                                username = username.lower() + "@"
                            else:
                                username = "-"
                    if username not in admins and username != "-":
                        admins.append(username)
                ###
                # Detect removed user account and added user account.
                #  EventID 4720: A user account was created
                #  EventID 4726: A user account was deleted
                ###
                elif eventid in [4720, 4726]:
                    for data in event_data:
                        if data.get("Name") in "TargetUserName" and data.text is not None and not re.search(UCHECK, data.text):
                            username = data.text.split("@")[0]
                            if username[-1:] not in "$":
                                username = username.lower() + "@"
                            else:
                                username = "-"
                    if eventid == 4720:
                        addusers[username] = etime.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        delusers[username] = etime.strftime("%Y-%m-%d %H:%M:%S")
                ###
                # Detect Audit Policy Change
                #  EventID 4719: System audit policy was changed
                ###
                elif eventid == 4719:
                    for data in event_data:
                        if data.get("Name") in "SubjectUserName" and data.text is not None and not re.search(UCHECK, data.text):
                            username = data.text.split("@")[0]
                            if username[-1:] not in "$":
                                username = username.lower() + "@"
                            else:
                                username = "-"
                        if data.get("Name") in "CategoryId" and data.text is not None and re.search(r"\A%%\d{4}\Z", data.text):
                            category = data.text
                        if data.get("Name") in "SubcategoryGuid" and data.text is not None and re.search(r"\A{[\w\-]*}\Z", data.text):
                            guid = data.text
                    policylist.append([etime.strftime("%Y-%m-%d %H:%M:%S"), username, category, guid.lower(), int(stime.strftime("%s"))])
                ###
                # Detect added users from specific group
                #  EventID 4728: A member was added to a security-enabled global group
                #  EventID 4732: A member was added to a security-enabled local group
                #  EventID 4756: A member was added to a security-enabled universal group
                ###
                elif eventid in [4728, 4732, 4756]:
                    for data in event_data:
                        if data.get("Name") in "TargetUserName" and data.text is not None and not re.search(UCHECK, data.text):
                            groupname = data.text
                        elif data.get("Name") in "MemberSid" and data.text not in "-" and data.text is not None and re.search(r"\AS-[0-9\-]*\Z", data.text):
                            usid = data.text
                    addgroups[usid] = "AddGroup: " + groupname + "(" + etime.strftime("%Y-%m-%d %H:%M:%S") + ") "
                ###
                # Detect removed users from specific group
                #  EventID 4729: A member was removed from a security-enabled global group
                #  EventID 4733: A member was removed from a security-enabled local group
                #  EventID 4757: A member was removed from a security-enabled universal group
                ###
                elif eventid in [4729, 4733, 4757]:
                    for data in event_data:
                        if data.get("Name") in "TargetUserName" and data.text is not None and not re.search(UCHECK, data.text):
                            groupname = data.text
                        elif data.get("Name") in "MemberSid" and data.text not in "-" and data.text is not None and re.search(r"\AS-[0-9\-]*\Z", data.text):
                            usid = data.text
                    removegroups[usid] = "RemoveGroup: " + groupname + "(" + etime.strftime("%Y-%m-%d %H:%M:%S") + ") "
                ###
                # Detect DCSync
                #  EventID 4662: An operation was performed on an object
                ###
                elif eventid == 4662:
                    for data in event_data:
                        if data.get("Name") in "SubjectUserName" and data.text is not None and not re.search(UCHECK, data.text):
                            username = data.text.split("@")[0]
                            if username[-1:] not in "$":
                                username = username.lower() + "@"
                            else:
                                username = "-"
                        dcsync_count[username] = dcsync_count.get(username, 0) + 1
                        if dcsync_count[username] == 3:
                            dcsync[username] = etime.strftime("%Y-%m-%d %H:%M:%S")
                            dcsync_count[username] = 0
                ###
                # Detect DCShadow
                #  EventID 5137: A directory service object was created
                #  EventID 5141: A directory service object was deleted
                ###
                elif eventid in [5137, 5141]:
                    for data in event_data:
                        if data.get("Name") in "SubjectUserName" and data.text is not None and not re.search(UCHECK, data.text):
                            username = data.text.split("@")[0]
                            if username[-1:] not in "$":
                                username = username.lower() + "@"
                            else:
                                username = "-"
                        if etime.strftime("%Y-%m-%d %H:%M:%S") in dcshadow_check:
                            dcshadow[username] = etime.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            dcshadow_check.append(etime.strftime("%Y-%m-%d %H:%M:%S"))
                ###
                # Parse logon logs
                #  EventID 4624: An account was successfully logged on
                #  EventID 4625: An account failed to log on
                #  EventID 4768: A Kerberos authentication ticket (TGT) was requested
                #  EventID 4769: A Kerberos service ticket was requested
                #  EventID 4776: The domain controller attempted to validate the credentials for an account
                ###
                else:
                    for data in event_data:
                        # parse IP Address
                        if data.get("Name") in ["IpAddress", "Workstation"] and data.text is not None and (not re.search(HCHECK, data.text) or re.search(IPv4_PATTERN, data.text) or re.search(r"\A::ffff:\d+\.\d+\.\d+\.\d+\Z", data.text) or re.search(IPv6_PATTERN, data.text)):
                            ipaddress = data.text.split("@")[0]
                            ipaddress = ipaddress.lower().replace("::ffff:", "")
                            ipaddress = ipaddress.replace("\\", "")
                        # Parse hostname
                        if data.get("Name") == "WorkstationName" and data.text is not None and (not re.search(HCHECK, data.text) or re.search(IPv4_PATTERN, data.text) or re.search(r"\A::ffff:\d+\.\d+\.\d+\.\d+\Z", data.text) or re.search(IPv6_PATTERN, data.text)):
                            hostname = data.text.split("@")[0]
                            hostname = hostname.lower().replace("::ffff:", "")
                            hostname = hostname.replace("\\", "")
                        # Parse username
                        if data.get("Name") in "TargetUserName" and data.text is not None and not re.search(UCHECK, data.text):
                            username = data.text.split("@")[0]
                            if username[-1:] not in "$":
                                username = username.lower() + "@"
                            else:
                                username = "-"
                        # Parse targeted domain name
                        if data.get("Name") in "TargetDomainName" and data.text is not None and not re.search(HCHECK, data.text):
                            domain = data.text
                        # parse trageted user SID
                        if data.get("Name") in ["TargetUserSid", "TargetSid"] and data.text is not None and re.search(r"\AS-[0-9\-]*\Z", data.text):
                            sid = data.text
                        # parse lonon type
                        if data.get("Name") in "LogonType" and re.search(r"\A\d{1,2}\Z", data.text):
                            logintype = int(data.text)
                        # parse status
                        if data.get("Name") in "Status" and re.search(r"\A0x\w{8}\Z", data.text):
                            status = data.text
                        # parse Authentication package name
                        if data.get("Name") in "AuthenticationPackageName" and re.search(r"\A\w*\Z", data.text):
                            authname = data.text

                    if username != "-" and username != "anonymous logon" and ipaddress != "::1" and ipaddress != "127.0.0.1" and (ipaddress != "-" or hostname != "-"):
                        # generate pandas series
                        if ipaddress != "-":
                            event_series = pd.Series([eventid, ipaddress, username, logintype, status, authname, int(stime.strftime("%s"))], index=event_set.columns)
                            ml_series = pd.Series([etime.strftime("%Y-%m-%d %H:%M:%S"), username, ipaddress, eventid],  index=ml_frame.columns)
                        else:
                            event_series = pd.Series([eventid, hostname, username, logintype, status, authname, int(stime.strftime("%s"))], index=event_set.columns)
                            ml_series = pd.Series([etime.strftime("%Y-%m-%d %H:%M:%S"), username, hostname, eventid],  index=ml_frame.columns)
                        # append pandas series to dataframe
                        event_set = event_set.append(event_series, ignore_index=True)
                        ml_frame = ml_frame.append(ml_series, ignore_index=True)
                        # print("%s,%i,%s,%s,%s,%s" % (eventid, ipaddress, username, comment, logintype))
                        count_series = pd.Series([stime.strftime("%Y-%m-%d %H:%M:%S"), eventid, username], index=count_set.columns)
                        count_set = count_set.append(count_series, ignore_index=True)
                        # print("%s,%s" % (stime.strftime("%Y-%m-%d %H:%M:%S"), username))

                        if domain != "-":
                            domain_set.append([username, domain])

                        if username not in username_set:
                            username_set.append(username)

                        if domain not in domains and domain != "-":
                            domains.append(domain)

                        if sid != "-":
                            sids[username] = sid

                        if hostname != "-" and ipaddress != "-":
                            hosts[hostname] = ipaddress

                        if authname in "NTML" and authname not in ntmlauth:
                            ntmlauth.append(username)
            ###
            # Detect the audit log deletion
            # EventID 1102: The audit log was cleared
            ###
            if eventid == 1102:
                logtime = node.xpath("/Event/System/TimeCreated")[0].get("SystemTime")
                try:
                    etime = datetime.datetime.strptime(logtime.split(".")[0], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=tzone)
                except:
                    etime = datetime.datetime.strptime(logtime.split(".")[0], "%Y-%m-%dT%H:%M:%S") + datetime.timedelta(hours=tzone)
                deletelog.append(etime.strftime("%Y-%m-%d %H:%M:%S"))

                namespace = "http://manifests.microsoft.com/win/2004/08/windows/eventlog"
                user_data = node.xpath("/Event/UserData/ns:LogFileCleared/ns:SubjectUserName", namespaces={"ns": namespace})
                domain_data = node.xpath("/Event/UserData/ns:LogFileCleared/ns:SubjectDomainName", namespaces={"ns": namespace})

                if user_data[0].text is not None:
                    username = user_data[0].text.split("@")[0]
                    if username[-1:] not in "$":
                        deletelog.append(username.lower())
                    else:
                        deletelog.append("-")
                else:
                    deletelog.append("-")

                if domain_data[0].text is not None:
                    deletelog.append(domain_data[0].text)
                else:
                    deletelog.append("-")

    print("\n[*] Load finished.")
    print("[*] Total Event log is %i." % count)

    if not username_set:
        sys.exit("[!] This event log did not include logs to be visualized. Please check the details of the event log.")

    tohours = int((endtime - starttime).total_seconds() / 3600)

    if hosts:
        event_set = event_set.replace(hosts)
    event_set_bydate = event_set
    event_set_bydate["count"] = event_set_bydate.groupby(["eventid", "ipaddress", "username", "logintype", "status", "authname", "date"])["eventid"].transform("count")
    event_set_bydate = event_set_bydate.drop_duplicates()
    event_set = event_set.drop("date", axis=1)
    event_set["count"] = event_set.groupby(["eventid", "ipaddress", "username", "logintype", "status", "authname"])["eventid"].transform("count")
    event_set = event_set.drop_duplicates()
    count_set["count"] = count_set.groupby(["dates", "eventid", "username"])["dates"].transform("count")
    count_set = count_set.drop_duplicates()
    domain_set_uniq = list(map(list, set(map(tuple, domain_set))))

    # Learning event logs using Hidden Markov Model
    if hosts:
        ml_frame = ml_frame.replace(hosts)
    ml_frame = ml_frame.sort_values(by="date")
    if args.learn:
        print("[*] Learning event logs using Hidden Markov Model.")
        learnhmm(ml_frame, username_set, datetime.datetime(*starttime.timetuple()[:3]))

    # Calculate ChangeFinder
    print("[*] Calculate ChangeFinder.")
    timelines, detects, detect_cf = adetection(count_set, username_set, starttime, tohours)

    # Calculate Hidden Markov Model
    print("[*] Calculate Hidden Markov Model.")
    detect_hmm = decodehmm(ml_frame, username_set, datetime.datetime(*starttime.timetuple()[:3]))

    # Calculate PageRank
    print("[*] Calculate PageRank.")
    ranks = pagerank(event_set, admins, detect_hmm, detect_cf, ntmlauth)

    # Create node
    print("[*] Creating a graph data.")

    try:
        graph_http = "http://" + NEO4J_USER + ":" + NEO4J_PASSWORD + "@" + NEO4J_SERVER + ":" + NEO4J_PORT + "/db/data/"
        GRAPH = Graph(graph_http)
    except:
        sys.exit("[!] Can't connect Neo4j Database.")

    tx = GRAPH.begin()
    hosts_inv = {v: k for k, v in hosts.items()}
    for ipaddress in event_set["ipaddress"].drop_duplicates():
        if ipaddress in hosts_inv:
            hostname = hosts_inv[ipaddress]
        else:
            hostname = ipaddress
        # add the IPAddress node to neo4j
        tx.append(statement_ip, {"IP": ipaddress, "rank": ranks[ipaddress], "hostname": hostname})

    i = 0
    for username in username_set:
        if username in sids:
            sid = sids[username]
        else:
            sid = "-"
        if username in admins:
            rights = "system"
        else:
            rights = "user"
        ustatus = ""
        if username in addusers:
            ustatus += "Created(" + addusers[username] + ") "
        if username in delusers:
            ustatus += "Deleted(" + delusers[username] + ") "
        if sid in addgroups:
            ustatus += addgroups[sid]
        if sid in removegroups:
            ustatus += removegroups[sid]
        if username in dcsync:
            ustatus += "DCSync(" + dcsync[username] + ") "
        if username in dcshadow:
            ustatus += "DCShadow(" + dcshadow[username] + ") "
        if not ustatus:
            ustatus = "-"

        # add the username node to neo4j
        tx.append(statement_user, {"user": username[:-1], "rank": ranks[username], "rights": rights, "sid": sid, "status": ustatus,
                                   "counts": ",".join(map(str, timelines[i*6])), "counts4624": ",".join(map(str, timelines[i*6+1])),
                                   "counts4625": ",".join(map(str, timelines[i*6+2])), "counts4768": ",".join(map(str, timelines[i*6+3])),
                                   "counts4769": ",".join(map(str, timelines[i*6+4])), "counts4776": ",".join(map(str, timelines[i*6+5])),
                                   "detect": ",".join(map(str, detects[i]))})
        i += 1

    for domain in domains:
        # add the domain node to neo4j
        tx.append(statement_domain, {"domain": domain})

    for _, events in event_set_bydate.iterrows():
        # add the (username)-(event)-(ip) link to neo4j
        tx.append(statement_r, {"user": events["username"][:-1], "IP": events["ipaddress"], "id": events["eventid"], "logintype": events["logintype"],
                                "status": events["status"], "count": events["count"], "authname": events["authname"], "date": events["date"]})

    for username, domain in domain_set_uniq:
        # add (username)-()-(domain) link to neo4j
        tx.append(statement_dr, {"user": username[:-1], "domain": domain})

    # add the date node to neo4j
    tx.append(statement_date, {"Daterange": "Daterange", "start": datetime.datetime(*starttime.timetuple()[:4]).strftime("%Y-%m-%d %H:%M:%S"),
                               "end": datetime.datetime(*endtime.timetuple()[:4]).strftime("%Y-%m-%d %H:%M:%S")})

    if len(deletelog):
        # add the delete flag node to neo4j
        tx.append(statement_del, {"deletetime": deletelog[0], "user": deletelog[1], "domain": deletelog[2]})

    if len(policylist):
        id = 0
        for policy in policylist:
            if policy[2] in CATEGORY_IDs:
                category = CATEGORY_IDs[policy[2]]
            else:
                category = policy[2]
            if policy[3] in AUDITING_CONSTANTS:
                sub = AUDITING_CONSTANTS[policy[3]]
            else:
                sub = policy[3]
            username = policy[1]
            # add the policy id node to neo4j
            tx.append(statement_pl, {"id": id, "changetime": policy[0], "category": category, "sub": sub})
            # add (username)-(policy)-(id) link to neo4j
            tx.append(statement_pr, {"user": username[:-1], "id": id, "date": policy[4]})
            id += 1

    tx.process()
    tx.commit()
    print("[*] Creation of a graph data finished.")


def main():
    if not has_py2neo:
        sys.exit("[!] py2neo must be installed for this script.")

    if not has_evtx:
        sys.exit("[!] python-evtx must be installed for this script.")

    if not has_lxml:
        sys.exit("[!] lxml must be installed for this script.")

    if not has_numpy:
        sys.exit("[!] numpy must be installed for this script.")

    if not has_changefinder:
        sys.exit("[!] changefinder must be installed for this script.")

    if not has_pandas:
        sys.exit("[!] pandas must be installed for this script.")

    if not has_hmmlearn:
        sys.exit("[!] hmmlearn must be installed for this script.")

    if not has_sklearn:
        sys.exit("[!] scikit-learn must be installed for this script.")

    try:
        graph_http = "http://" + NEO4J_USER + ":" + NEO4J_PASSWORD + "@" + NEO4J_SERVER + ":" + NEO4J_PORT + "/db/data/"
        GRAPH = Graph(graph_http)
    except:
        sys.exit("[!] Can't connect Neo4j Database.")

    print("[*] Script start. %s" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))

    if args.run:
        try:
            app.run(threaded=True, host=WEB_HOST, port=WEB_PORT)
        except:
            sys.exit("[!] Can't runnning web application.")

    # Delete database data
    if args.delete:
        GRAPH.delete_all()
        print("[*] Delete all nodes and relationships from this Neo4j database.")

    if args.evtx:
        for evtx_file in args.evtx:
            if not os.path.isfile(evtx_file):
                sys.exit("[!] Can't open file {0}.".format(evtx_file))
        parse_evtx(args.evtx)

    if args.xmls:
        for xml_file in args.xmls:
            if not os.path.isfile(xml_file):
                sys.exit("[!] Can't open file {0}.".format(xml_file))
        parse_evtx(args.xmls)

    print("[*] Script end. %s" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


if __name__ == "__main__":
    main()
