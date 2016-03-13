# coding:utf-8
from email.mime.text import MIMEText
import os
import smtplib
from time import time, strftime, localtime
import MySQLdb
from flask import Flask, request, session, render_template, url_for
from flask.json import dumps
from werkzeug.utils import secure_filename, redirect
import sys
reload(sys)
sys.setdefaultencoding('utf8')
__author__ = 'Hu Xing'

ISSUE_PORT = 4500
ATTACHMENT_ADDR = "/root/issue/static/attachment/"
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif', 'png'])

app = Flask(__name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def check_folder(addr):
    if os.path.exists(addr):
        return True
    else:
        return False


# connect to mysql
def mysql_con():
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin',
                               db='pop2016', port=3306, charset="utf8")
    except Exception, e:
        return None
    return conn


# format current time as a string
def get_current_time(timestamp=None):
    if timestamp is None:
        timestamp = time()
    return strftime("%Y-%m-%d %H:%M:%S", localtime(timestamp))


def check_valid(userid, issueid):
    if userid and issueid:
        conn = mysql_con()
        cursor = conn.cursor()
        sql = "SELECT userid FROM issue WHERE id=%d" % issueid
        count = cursor.execute(sql)

        if count>0:
            uid = cursor.fetchone()[0]
        else:
            return False
        sql = "SELECT is_super FROM user WHERE id = %d" % userid
        count = cursor.execute(sql)
        if count>0:
            is_super = cursor.fetchone()[0]
        else:
            return False
        cursor.close()
        conn.close()
        if userid == uid or is_super == 1:
            return True
        else:
            return False
    else:
        return False


def send_mail(issue):
    SENDER = '胡星<huxing0101@pku.edu.cn>'
    RECEIVIER = 'mass@sei.pku.edu.cn'
    SUBJECT = 'POP2016 工单'
    SMTPSERVER = 'smtp.pku.edu.cn'
    USERNAME = 'huxing0101@pku.edu.cn'
    PASSWORD = 'xinfang1993'
    content = '<html><h1>工单</h1></html>' + '<table border="1"><tr><th>Issue ID</th><th>问题类型</th><th>问题标题</th><th>详细情况</th></tr>'
    content += '<tr><td>' + str(issue['issue_id']) + '</td><td>' + issue['issue_type'] + '</td><td>' + issue[
        'issue_head'] + "</td><td><a href='http://123.57.2.1:4500/detail?uid=111&issueid=" + str(issue[
              'issue_id']) + "' target='_blank'>查看详情</a></td></tr>"
    content += '</table>'
    msg = MIMEText(content, 'html', 'utf-8')
    msg['Subject'] = SUBJECT
    try:
        smtp = smtplib.SMTP()
        smtp.connect(SMTPSERVER)
        smtp.login(USERNAME, PASSWORD)
        smtp.sendmail(SENDER, RECEIVIER, msg.as_string())
        smtp.quit()
    except Exception,e:
        print str(e)
        print "Error: unable to send email"


@app.route('/create', methods=['GET', 'POST'])
def create_issue():
    if request.method == 'GET':
        param = request.args

    else:
        param = request.form
    userid = param.get('uid', None)
    if userid:
        userid = int(userid)
        conn = mysql_con()
        cursor = conn.cursor()
        sql = "SELECT username FROM user WHERE id=%d" % userid
        cursor.execute(sql)
        username = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        session['userid'] = userid
        session['username'] = username
    else:
        userid = session.get('userid')
    global ATTACHMENT_ADDR

    if userid:
        if request.method == 'GET':
            return render_template('createissue.html', username=session.get('username'))
        else:
            conn = mysql_con()
            cursor = conn.cursor()
            issue_type = param.get('type', None)
            issue_head = param.get('head', None)
            issue_body = param.get('body', None)
            email = param.get('email', None)
            create_time = get_current_time()
            attachment = request.files.get('atta', None)

            if not email:
                sql = "SELECT email FROM user WHERE id=%d" % userid
                count = cursor.execute(sql)
                if count > 0:
                    email = cursor.fetchone()[0]

            if attachment and allowed_file(attachment.filename):

                attach_addr = ATTACHMENT_ADDR + str(userid)
                if not os.path.exists(attach_addr):
                    os.makedirs(attach_addr)
                app.config['UPLOAD_FOLDER'] = attach_addr
                filename = secure_filename(attachment.filename)
                attachment.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                img_path = "/static/attachment/"+str(userid)+"/"+filename
                sql = "INSERT INTO issue(userid, create_time,issue_type, issue_head, issue_body, email, attachment) VALUES (%d, '%s','%s' ,'%s', '%s', '%s', '%s')" % (
                    userid, create_time, issue_type, issue_head, issue_body, email, img_path)
            else:
                sql = "INSERT INTO issue(userid, create_time,issue_type ,issue_head, issue_body, email) VALUES (%d, '%s', '%s', '%s', '%s', '%s')" % (
                    userid, create_time, issue_type, issue_head, issue_body, email)
            cursor.execute(sql)
            conn.commit()

            sql = "SELECT id FROM issue WHERE userid = %d AND create_time = '%s'limit 1" % (userid, create_time)
            cursor.execute(sql)
            result = cursor.fetchone()
            issue_id = result[0]
            issue = dict(issue_id=issue_id, issue_head=issue_head, issue_body=issue_body, email=email, issue_type=issue_type)
            send_mail(issue)
            cursor.close()
            conn.close()
            return redirect(url_for("issue_list"))
    else:
        res = dumps({'code': 1, 'msg': "Permission denied"})
        return res


@app.route('/list', methods=['GET', 'POST'])
def issue_list():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form

    issues = []
    userid = param.get('uid', None)
    if userid:
        userid = int(userid)
        conn = mysql_con()
        cursor = conn.cursor()
        sql = "SELECT username FROM user WHERE id=%d" % userid
        cursor.execute(sql)
        username = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        session['userid'] = userid
        session['username'] = username
    else:
        userid = session.get('userid')
    if userid:
        conn = mysql_con()
        cursor = conn.cursor()

        sql = "SELECT is_super FROM user WHERE id = %d" % userid
        cursor.execute(sql)
        is_super = cursor.fetchone()[0]
        if is_super == 0:
            sql = "SELECT * FROM issue WHERE userid = %d ORDER BY create_time DESC " % userid
        else:
            sql = "SELECT * FROM issue ORDER BY create_time DESC"
        count = cursor.execute(sql)
        results = cursor.fetchall()
        for result in results:
            is_deal = result[7]
            if is_deal == 1:
                state = "已解决"
            else:
                state = "未解决"
            issue = dict(id=result[0], create_time=result[2], issue_type=result[3], issue_head=result[4], state=state)
            issues.append(issue)
        cursor.close()
        conn.close()
        return render_template('issue.html', issues=issues, count=count, username=session.get('username'))
    else:
        return dumps({'code': 1, 'msg': "permission denied"})


@app.route('/unsolved')
def unsolved_list():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form
    userid = session.get('userid')
    if userid:
        conn = mysql_con()
        cursor = conn.cursor()
        issues = []
        sql = "SELECT is_super FROM user WHERE id = %d" % userid
        cursor.execute(sql)
        is_super = cursor.fetchone()[0]
        if is_super == 0:
            sql = "SELECT * FROM issue WHERE userid = %d AND is_deal = %d ORDER BY create_time DESC" % (userid, 0)
        else:
            sql = "SELECT * FROM issue WHERE is_deal = 0 ORDER BY create_time DESC"

        count = cursor.execute(sql)
        results = cursor.fetchall()
        for result in results:
            issue = dict(id=result[0], create_time=result[2], issue_type=result[3], issue_head=result[4], state="未解决")
            issues.append(issue)
        cursor.close()
        conn.close()
        return render_template('issue.html', issues=issues, count=count,  username=session.get('username'))
    else:
        return dumps({'code': 1, 'msg': "permission denied"})


@app.route('/solved')
def solved_list():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form
    userid = session.get('userid')
    if userid:
        conn = mysql_con()
        cursor = conn.cursor()
        issues = []
        sql = "SELECT is_super FROM user WHERE id = %d" % userid
        cursor.execute(sql)
        is_super = cursor.fetchone()[0]
        if is_super == 0:
            sql = "SELECT * FROM issue WHERE userid = %d AND is_deal = %d ORDER BY create_time DESC" % (userid, 1)
        else:
            sql = "SELECT * FROM issue WHERE is_deal = 1 ORDER BY create_time DESC"

        count = cursor.execute(sql)
        results = cursor.fetchall()
        for result in results:
            issue = dict(id=result[0], create_time=result[2], issue_type=result[3], issue_head=result[4], state="已解决")
            issues.append(issue)
        cursor.close()
        conn.close()
        return render_template('issue.html', issues=issues, count=count, username=session.get('username'))
    else:
        return dumps({'code': 1, 'msg': "permission denied"})


@app.route('/detail', methods=['GET', 'POST'])
def issue_detail():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form

    issue_id = int(param.get('issueid', None))
    userid = param.get('uid', None)
    if userid:
        userid = int(userid)
        conn = mysql_con()
        cursor = conn.cursor()
        sql = "SELECT username FROM user WHERE id=%d" % userid
        cursor.execute(sql)
        username = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        session['userid'] = userid
        session['username'] = username
    else:
        userid = session.get('userid')
    if check_valid(userid, issue_id):
        conn = mysql_con()
        cursor = conn.cursor()
        sql = "SELECT * FROM issue WHERE id=%d" % issue_id
        cursor.execute(sql)
        result = cursor.fetchone()
        sql = "SELECT * FROM communication WHERE issue_id = '%d' ORDER BY time DESC " % issue_id
        cursor.execute(sql)
        rsts = cursor.fetchall()
        communicates = []
        for rst in rsts:
            sql = "SELECT username FROM user WHERE id = '%d'" % rst[2]
            cursor.execute(sql)
            username = cursor.fetchone()[0]
            communicate = dict(communicate_id=rst[0], sender=username, time=rst[3], content=rst[4])
            communicates.append(communicate)
        if result[7] == 0:
            state = "待解决"
        else:
            state = "已解决"
        issue = dict(issue_id=issue_id, create_time=result[2], issue_type=result[3], issue_head=result[4],
                     issue_body=result[5], email=result[6], is_deal=result[7], solution=result[8], state=state,
                     attachment=result[9], communicates=communicates)
        cursor.close()
        conn.close()
        return render_template('issuedetail.html', issue=issue, username=session.get('username'))
    else:
        return dumps({'code': 1, 'msg': 'Permission denied'})


@app.route('/delete', methods=['GET', 'POST'])
def delete_issue():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form

    issue_id = int(param.get('issueid', None))
    userid = session.get('userid')

    if check_valid(userid, issue_id):
        conn = mysql_con()
        cursor = conn.cursor()
        sql = "delete FROM communication WHERE issue_id = %d" % issue_id
        cursor.execute(sql)
        conn.commit()
        sql = "select attachment FROM issue WHERE id = %d" % issue_id
        cursor.execute(sql)
        attachment = cursor.fetchone()[0]
        if attachment and os.path.exists("/root/issue"+attachment):
            os.remove("/root/issue"+attachment)
        sql = "delete FROM issue WHERE id = %d" % issue_id
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("issue_list"))
    else:
        res = {'code': 1, 'msg': 'Permission denied'}
        return dumps(res)


@app.route('/check', methods=['GET', 'POST'])
def check_solved():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form

    issue_id = int(param.get('issueid'))
    userid = session.get('userid')

    if check_valid(userid, issue_id):
        conn = mysql_con()
        cursor = conn.cursor()
        sql = "UPDATE issue SET is_deal = 1 WHERE id =%d" % issue_id
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("issue_list"))
    else:
        return dumps({'code': 1, 'msg': "Permission denied"})


@app.route('/addcommunication', methods=['GET', 'POST'])
def add_communication():
    if request.method == 'GET':
        param = request.args
    else:
        param = request.form

    issue_id = int(param.get('issueid'))
    content = param.get('content', None)
    userid = session.get('userid')
    create_time = get_current_time()
    if check_valid(userid, issue_id):
        conn = mysql_con()
        cursor = conn.cursor()
        sql = "INSERT INTO communication (issue_id, sender_id, time, content) VALUES (%d, %d, '%s', '%s')" % (
            issue_id, userid, create_time, content)
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        return dumps({'code': 0, 'msg': "Success"})
    else:
        return dumps({'code': 1, 'msg': "Permission denied"})


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=ISSUE_PORT, debug=True, use_reloader=False)