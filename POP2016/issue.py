from email.mime.text import MIMEText
import os
import smtplib
from time import time, strftime, localtime
import MySQLdb
from flask import Flask, request, session, render_template, url_for
from flask.json import dumps
from werkzeug.utils import secure_filename, redirect

__author__ = 'Hu Xing'

TICKET_PORT = 4500
ATTACHMENT_ADDR = "/attachment/"
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif'])
app = Flask(__name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# connect to mysql
def mysql_con():
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin',
                               db='pop2016', port=3306)
    except Exception, e:
        return None
    return conn


# format current time as a string
def get_current_time(timestamp=None):
    if timestamp is None:
        timestamp = time()
    return strftime("%Y-%m-%d %H:%M:%S", localtime(timestamp))


def send_mail(report):
    SENDER = '2269077178@qq.com'
    RECEIVIER = 'huxing0101@pku.edu.cn'
    SUBJECT = 'POP2016 工单'
    SMTPSERVER = 'smtp.qq.com'
    USERNAME = '2269077178@qq.com'
    PASSWORD = ''
    str = '<html><h1>工单</h1></html>' + '<table border="1"><tr><th>Issue ID</th><th>问题标题</th><th>问题描述</th><th>详细情况</th></tr>'
    for st in report:
        str = str + '<tr><td>' + st['dockerid'] + '</td><td>' + st['cpu'] + '</td><td>' + st[
            'mempercent'] + '</td></tr>'
    str = str + '</table>'
    msg = MIMEText(str, 'html', 'utf-8')
    msg['Subject'] = SUBJECT
    smtp = smtplib.SMTP()
    smtp.connect(SMTPSERVER)
    smtp.login(USERNAME, PASSWORD)
    smtp.sendmail(SENDER, RECEIVIER, msg.as_string())
    smtp.quit()


@app.route('/create', methods=['GET', 'POST'])
def create_issue():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form
    conn = mysql_con()
    cursor = conn.cursor()

    userid = session.get('userid')
    issue_head = param['issue_head']
    issue_body = param['issue_body']
    email = param['email']
    create_time = get_current_time()
    attachment = request.files['attachment']
    attach_addr = ATTACHMENT_ADDR + userid + '/'
    if attachment and allowed_file(attachment.filename):
        filename = secure_filename(attachment.filename)
        attachment.save(os.path.join(app.config['attach_addr'], filename))
        attach_addr = attach_addr + filename
        sql = "INSERT INTO issue(userid, create_time, issue_head, issue_body, email, attachment) VALUES (%d, '%s', '%s', '%s', '%s', '%s', '%s')" % (
            userid, create_time, issue_head, issue_body, email, attach_addr)
    else:
        sql = "INSERT INTO issue(userid, create_time, issue_head, issue_body, email) VALUES (%d, '%s', '%s', '%s', '%s', '%s')" % (
            userid, create_time, issue_head, issue_body, email)
    cursor.execute(sql)
    conn.commit()

    sql = "SELECT id FROM issue WHERE userid = %d AND create_time = '%s'limit 1" % (userid, create_time)
    cursor.execute(sql)
    result = cursor.fetchone()
    issue_id = result[0]
    issue = dict(issue_id=issue_id, issue_head=issue_head, issue_body=issue_body, email=email)
    send_mail(issue)
    cursor.close()
    conn.close()
    return redirect(url_for('issue_list'))


@app.route('/list', methods=['GET', 'POST'])
def issue_list():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form

    issues = []
    userid = param['uid']
    session['userid'] = userid

    conn = mysql_con()
    cursor = conn.cursor()

    sql = "SELECT * FROM issue WHERE userid = %d" % userid
    count = cursor.execute(sql)
    results = cursor.fetchall()
    for result in results:
        is_deal = result[7]
        if is_deal == 0:
            state = "待解决"
        else:
            state = "已解决"

        issue = dict(id=result[0], create_time=result[2], issue_type=result[3], issue_head=result[4], state=state)
        issues.append(issue)

    cursor.close()
    conn.close()
    return render_template('issue.html', issues=issues, count=count)


@app.route('/unsolved')
def unsolved_list():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form
    conn = mysql_con()
    cursor = conn.cursor()
    issues = []
    userid = session.get('userid')
    sql = "SELECT * FROM issue WHERE userid = %d AND state = %d " % (userid, 0)
    count = cursor.execute(sql)
    results = cursor.fetchall()
    for result in results:
        issue = dict(id=result[0], create_time=result[2], issue_type=result[3], issue_head=result[4], state="未解决")
        issues.append(issue)
    cursor.close()
    conn.close()
    return render_template('issue.html', issues=issues, count=count)


@app.route('/solved')
def solved_list():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form
    conn = mysql_con()
    cursor = conn.cursor()
    issues = []
    userid = session.get('userid')
    sql = "SELECT * FROM issue WHERE userid = %d AND state = %d " % (userid, 0)
    count = cursor.execute(sql)
    results = cursor.fetchall()
    for result in results:
        issue = dict(id=result[0], create_time=result[2], issue_type=result[3], issue_head=result[4], state="未解决")
        issues.append(issue)
    cursor.close()
    conn.close()
    return render_template('issue.html', issues=issues, count=count)


@app.route('/issue', methods=['GET', 'POST'])
def issue_detail():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form

    issue_id = param['issueid']
    admin = param['uid']
    userid = session.get('userid')

    conn = mysql_con()
    cursor = conn.cursor()
    sql = "SELECT * FROM issue WHERE id=%d limit 1" % issue_id
    cursor.execute(sql)
    result = cursor.fetchone()
    sql = "SELECT is_super FROM user WHERE id=%d limit 1" % admin
    cursor.execute(sql)
    is_super = cursor.fetchone()
    is_super = is_super[0]
    issue = None

    if result[1] == userid or is_super == 1:

        sql = "SELECT * FROM communication WHERE issue_id = '%d' ORDER BY time DESC " % issue_id
        cursor.execute(sql)
        rsts = cursor.fetchall()
        communicates = []
        for rst in rsts:
            sql = "SELECT is_super FROM user WHERE id = '%d'" % rst[2]
            cursor.execute(sql)
            is_super = cursor.fetchone()
            is_super = is_super[0]
            if is_super == 1:
                sender = "Admin"
            else:
                sender = "自己"
            communicate = dict(communicate_id=rst[0], sender=sender, time=rst[3], content=rst[4])
            communicates.append(communicate)
        if result[7]==0:
            state = "待解决"
        else:
            state = "已解决"
        issue = dict(issue_id=issue_id, create_time=result[2], issue_type=result[3], issue_head=result[4],
                     issue_body=result[5], email=result[6], is_deal=result[7], solution=result[8], state=state,
                     attachment=result[9], communicates=communicates)
        cursor.close()
        conn.close()
        return render_template('', issue=issue)
    else:
        cursor.close()
        conn.close()
        return dumps({'code': 1, 'msg': 'Permission denied'})


@app.route('/delete', methods=['GET', 'POST'])
def delete_issue():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form

    issue_id = param['issueid']
    admin = param['uid']
    userid = session.get('userid')

    conn = mysql_con()
    cursor = conn.cursor()
    sql = "SELECT * FROM issue WHERE id=%d limit 1" % issue_id
    cursor.execute(sql)
    result = cursor.fetchone()
    sql = "SELECT is_super FROM user WHERE id=%d limit 1" % admin
    cursor.execute(sql)
    is_super = cursor.fetchone()
    is_super = is_super[0]

    if result[1] == userid or is_super == 1:
        sql = "delete FROM issue WHERE issue_id = %d" % issue_id
        cursor.execute(sql)
        conn.commit()
        res = {'code': 0, 'msg': 'success'}
    else:
        res = {'code': 0, 'msg': 'Permission denied'}

    cursor.close()
    conn.close()
    return dumps(res)


def communicate_record():
    pass


@app.route('/addcommunication', methods=['GET', 'POST'])
def add_communication():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form

    issue_id = param['issueid']
    content = param['content']
    userid = session.get('userid')
    create_time = get_current_time()
    if userid is None:
        return redirect("http://www.poprogramming.com/login")
    conn = mysql_con()
    cursor = conn.cursor()

    sql = "INSERT INTO communication (issue_id, sender_id, time, content) VALUES (%d, %d, '%s', '%s')" % (
        issue_id, userid, create_time, content)
    cursor.execute(sql)
    conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for('issue_detail'))
