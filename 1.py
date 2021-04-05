import os
import io
from flask import Flask, render_template, url_for, request, redirect
import pymysql
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
from google.cloud import storage
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import date
import matplotlib.pyplot as plt
import numpy as np
import sys
import matplotlib
from fpdf import FPDF
import base64

#global operations
WIDTH = 210
HEIGHT = 297
pdf = FPDF()
pdf.set_title("Google cloud Platform")
pdf.add_page()


db_user = "baarath"
db_password = "baarath"
db_name = "certdets"
db_connection_name = "tasko-task:asia-south1:mydbinsta"
host='127.0.0.1'

app = Flask(__name__)


@app.route('/')
def main():
    return render_template('regist.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/addcertificate')
def addcertificate():
    return render_template('addcertificate.html')

@app.route('/usercertificate')
def usercertificate():
    return render_template('usercertificate.html')

@app.route('/quizdisplay')
def quizdisplay():
    return render_template('quizdisplay.html')

@app.route('/content')
def content():
    return render_template('content.html')

@app.route('/brainstroming')
def brainstorming():
    return render_template('brainstroming.html')

@app.route('/register', methods = ["POST","GET"])
def register():
    global email
    empname =  request.form.get("empname")
    email =  request.form.get("email")
    password =  request.form.get("password")
    tableboo=register_table(empname,email,password)
    msgs='<p>Thanks for Registering</p><br><strong><a href="http://34.70.143.201/">Go ahead and Please login...</a></strong>'
    send_mail(email,msgs)

    if tableboo=="ok":
        return render_template('home.html')
    else:
        return render_template('regist.html')


def register_table(empname,email,password):
    tableboo = "ok"
    sqlin="insert into personal (name,email,password) values(%s,%s,%s)"
    val=(empname,email,password)
    # SQL Connection Establish
    cnx = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    try:
        with cnx.cursor() as cursor:
            cursor.execute(sqlin,val)
            cnx.commit()
        cursor.close()
    except:
        tableboo="1"
    return tableboo

@app.route('/login', methods = ["POST","GET"])
def login():
    global email
    email =  request.form.get("email")
    password =  request.form.get("password")
    pwd=login_table(email)
    if pwd==password:
        return render_template('home.html')
    else:
        return render_template('regist.html')

def login_table(email):
    sqlcheck="select password from personal where email = %s;"
    val=(email)
    cnx = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    try:
        with cnx.cursor() as cursor:
            cursor.execute(sqlcheck,val)
            pwd =cursor.fetchone() 
            cnx.commit()
        cursor.close()
    except:
        pwd="fail"
    return pwd[0]

@app.route("/ajaxgetcertificate",methods=["POST","GET"])
def ajaxgetcertificate():
    cnxa = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    with cnxa.cursor() as cursor:
        if request.method == 'POST':
            search_word = request.form['query']
            if search_word == '':
                pass
            elif search_word == 'all':
                sqlque = "SELECT csp,cid,cname from cert where email='{}' order by csp;".format(email)
                cursor.execute(sqlque)
                certificatetable = cursor.fetchall()
                cnxa.commit()
            else:    
                sqlque = "SELECT csp,cid,cname from cert WHERE csp = '{}' and email='{}';".format(search_word,email)
                cursor.execute(sqlque)
                certificatetable = cursor.fetchall()
                cnxa.commit()
    cursor.close()
    return  render_template('certificatecard.html', certificatetable=certificatetable)


@app.route('/upload-cert', methods = ["POST","GET"])
def uploadcert():
    if request.method == "POST":
      file = request.files["file"]
      cid = request.form["cid"]
      csp = request.form["csp"]
      cname = request.form["cname"]
      idate = request.form["idate"]
      edate = request.form["edate"]
      path = '/home/hari_98_d/certapp/vircertify/pdfs/'
      file.save(os.path.join(path, file.filename))

      certboo=1
      msgs, certboo = pdfparser(file,cid,csp,email)
      html_msg="<p>The Certificate has been Validated.</p><br><strong>{}</strong>".format(msgs)
      send_mail(email,html_msg)
      if certboo == 1:
          sqlin="insert into cert (cid,cname,idate,edate,email,csp) values(%s,%s,%s,%s,%s,%s);"
          val=(cid,cname,idate,edate,email,csp)
          cnx = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
          try:
              with cnx.cursor() as cursor:
                  cursor.execute(sqlin,val)
                  cnx.commit()
              cursor.close()
          except Exception as e:
              pass
          return render_template("home.html", message = "Certificate Added")
      else:
          return render_template("home.html", message = "Certificate ID Mismatch")
    else:
        #for post method else
        pass
    return render_template("home.html")

def pdfparser(data,cid,csp,email):
    
    destination_blob_name = cid
    bucket_name = "certdetsimage"
    source_file_name = "/home/hari_98_d/certapp/vircertify/pdfs/" + data.filename
    destination_blob_name = destination_blob_name 
    filepath= "/home/hari_98_d/certapp/vircertify/pdfs/" + data.filename
    fp = open(filepath, 'rb')
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    # Create a PDF interpreter object.
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    # Process each page contained in the document.

    for page in PDFPage.get_pages(fp):
        interpreter.process_page(page)
        data =  retstr.getvalue()
    
    idcheck = data.find(cid)
    
    if idcheck != -1:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        mail_msg="The Certificate details provided is Valid. The Certifcate is added to your profile"
        certboo=1
    
    else:
        mail_msg="The Certificate details provided is not valid."
        certboo=0

    return(mail_msg,certboo)


def send_mail(email,msgs):
    message = Mail(
        from_email='balaji.m.2016.cse@rajalakshmi.edu.in',
        to_emails=email,
        subject='....Certificate Validation....',
        html_content = msgs)
    try:
        sg = SendGridAPIClient('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')
        sg.send(message)
    except:
        pass

@app.route("/studyboard",methods=["POST","GET"])
def studyboard():
    cnxa = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    with cnxa.cursor() as cursor:
            csplist=["GCP","AWS","Azure"]
            attended=[]
            totalquiz=[]
            lprogress=[]
            for pcsp in csplist:
                try:
                    cspquery = "select distinct email,quizname from {}score where email='{}';".format(pcsp,email)
                    cursor.execute(cspquery)
                    attended.append(float(cursor.rowcount))
                except Exception as e:
                    attended.append(0.00)
                    print(e)
                try:
                    allquiz = "select distinct quizname from {}quiz;".format(pcsp)
                    cursor.execute(allquiz)
                    totalquiz.append(float(cursor.rowcount))
                except:
                    totalquiz.append(0.00)
            for i in range(0,len(totalquiz)):
                if totalquiz[i]!=0.0:
                    lprogress.append(attended[i]/totalquiz[i])
                else:
                    lprogress.append(0.0)
            print("Lprogress")
            print(lprogress[0])
            print(lprogress[1])
            print(lprogress[2])
    cursor.close()
    return  render_template('progress-bar.html', gcp=lprogress[0],aws=lprogress[1],azure=lprogress[2])

@app.route("/ajaxdisplayquiz",methods=["POST","GET"])
def ajaxdisplayquiz():
    cnxa = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    with cnxa.cursor() as cursor:
        if request.method == 'POST':
            search_word = request.form['query']
            print(search_word)
            if search_word == '':
                pass
            else:    
                sqlque = "SELECT distinct quizname from {}quiz order by quizname;".format(search_word)
                cursor.execute(sqlque)
                quizavailtable = cursor.fetchall()
                cnxa.commit()
    cursor.close()
    return  render_template('takequizcard.html', quizavailtable=quizavailtable, quizcsp=search_word)


@app.route("/takequiz",methods=["POST","GET"])
def takequiz():
    cnxa = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    with cnxa.cursor() as cursor:
        if request.method == 'POST':
            global iqcsp, iquizname
            iqcsp = request.form.get('iqcsp')
            iquizname = request.form.get('iquizname')
            print(iqcsp)
            sqlquery = "select question from {}quiz where quizname='{}'".format(iqcsp,iquizname)
            cursor.execute(sqlquery)
            qquestiontuple = cursor.fetchall()
            sqlquery = "select option1,option2,option3,option4 from {}quiz where quizname='{}'".format(iqcsp,iquizname)
            cursor.execute(sqlquery)
            qoptiontuple = cursor.fetchall()
            sqlquery = "select correct from {}quiz where quizname='{}'".format(iqcsp,iquizname)
            cursor.execute(sqlquery)
            qcorrecttuple = cursor.fetchall()
            qquestionlist = []

            for row in qquestiontuple:
                for data in row:
                    qquestionlist.append(data)
            qoptionlist0 = []
            qoptionlist1 = []
            qoptionlist2 = []
            qoptionlist3 = []
            qoptionlist4 = []
            qoptionlist5 = []
            qoptionlist6 = []
            qoptionlist7 = []
            qoptionlist8 = []
            qoptionlist9 = []
            if qoptiontuple:
                qoptionlist0.append(list(qoptiontuple[0]))
                qoptionlist1.append(list(qoptiontuple[1]))
                qoptionlist2.append(list(qoptiontuple[2]))
                qoptionlist3.append(list(qoptiontuple[3]))
                qoptionlist4.append(list(qoptiontuple[4]))
                qoptionlist5.append(list(qoptiontuple[5]))
                qoptionlist6.append(list(qoptiontuple[6]))
                qoptionlist7.append(list(qoptiontuple[7]))
                qoptionlist8.append(list(qoptiontuple[8]))
                qoptionlist9.append(list(qoptiontuple[9]))
            qcorrectlist = []
            for ans in qcorrecttuple:
                for data in ans:
                    qcorrectlist.append(int(data))

            cnxa.commit()
    cursor.close()
    print(qquestionlist)
    print("Correct ok , Options")
    print(qoptionlist9[0])
    print(qcorrectlist)
    print(type(qquestionlist))
    print("Correct ok , Options")
    print(type(qoptionlist9[0]))
    print(type(qcorrectlist))
    return  render_template('takequiz.html', email=email, quizcsp=iqcsp, quizname=iquizname, question = qquestionlist, ans = qcorrectlist, opt1 = qoptionlist0[0],opt2 = qoptionlist1[0],opt3 = qoptionlist2[0],opt4 = qoptionlist3[0],opt5 = qoptionlist4[0],opt6 = qoptionlist5[0],opt7 = qoptionlist6[0],opt8 = qoptionlist7[0],opt9 = qoptionlist8[0],opt10 = qoptionlist9[0])
    # return "ok"

@app.route("/quizdone",methods=["POST","GET"])
def quizdone():
    cnxa = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    with cnxa.cursor() as cursor:
        if request.method == 'POST':
            # csp,quizname,totalscore,attempt
            #iqcsp = request.form['quizcsp']
            sec1 = int(request.form['sec1'])*10
            sec2 = int(request.form['sec2'])*10
            sec3 = int(request.form['sec3'])*10
            sec4 = int(request.form['sec4'])*10
            sec5 = int(request.form['sec5'])*10
            #iquizname = request.form['quizname']
            totalscore = int(request.form['numCorrect'])*10
            print(totalscore)
            print("toatalsasdad")
            
            #if totalscore > 70:
                #result = True
            # get the above things
            try:
                sqlattemp= "select attempt from {}score where email='{}' and quizname='{}' order by attempt desc".format(iqcsp,email,iquizname)
                cursor.execute(sqlattemp)
                prevattempt = cursor.fetchone()
                newattempt=str(int(prevattempt[0])+1)
                #sqlque = "insert into {}score(quizname,email,totalscore,sec1,sec2,sec3,sec4,sec5,attempt) values(%s,%s,%d,%d,%d,%d,%d,%d,%s);".format(iqcsp)
                #vals = (iquizname,email,totalscore,sec1,sec2,sec3,sec4,sec5,newattempt)
                sqlque = "insert into {}score(quizname,email,totalscore,sec1,sec2,sec3,sec4,sec5,attempt) values(%s,%s,%s,%s,%s,%s,%s,%s,%s);".format(iqcsp)
                vals = (iquizname,email,str(totalscore),str(sec1),str(sec2),str(sec3),str(sec4),str(sec5),newattempt)
                cursor.execute(sqlque,vals)
                cnxa.commit()
                #call the send report function
                # onpdf(iqcsp,email,result,newattempt,totalscore) 
            except Exception as e:
                print("first try out")
                print(e)
                try:
                    #sqlque = "insert into {}score(quizname,email,totalscore,sec1,sec2,sec3,sec4,sec5,attempt) values(%s,%s,%s,%s,%s,%s,%s,%s,%s);".format(iqcsp)
                    sqlque = "insert into {}score(quizname,email,totalscore,sec1,sec2,sec3,sec4,sec5,attempt) values(%s,%s,%s,%s,%s,%s,%s,%s,%s);".format(iqcsp)
                    vals = (iquizname,email,str(totalscore),str(sec1),str(sec2),str(sec3),str(sec4),str(sec5),"1")
                    cursor.execute(sqlque,vals)
                    cnxa.commit()
                    #call the send report function 
                except Exception as e:
                    print("second also out idiot")
                    print(e)
                else:
                    print("Nothing Went wrong")
            else:
                print("hoho nothing went wrong")
    cursor.close()
    return studyboard()

@app.route("/ajaxgetcontent",methods=["POST","GET"])
def ajaxgetcontent():
    cnxa = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    with cnxa.cursor() as cursor:
        if request.method == 'POST':
            search_word = request.form['query']
            print(search_word)
            if search_word == 'all':
                sqlque = "SELECT * from content order by csp;".format(search_word)
                cursor.execute(sqlque)
                content = cursor.fetchall()
                cnxa.commit()
            else:    
                sqlque = "SELECT * from content WHERE csp = '{}';".format(search_word)
                cursor.execute(sqlque)
                content = cursor.fetchall()
                cnxa.commit()
    cursor.close()
    return  render_template('contentcard.html', contenttable=content)


@app.route("/ajaxgetbrainstorm",methods=["POST","GET"])
def ajaxgetbrainstorm():
    cnxa = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    with cnxa.cursor() as cursor:
        if request.method == 'POST':
            search_word = request.form['query']
            print(search_word)
            if search_word == 'all':
                pass
            else:    
                sqlque = "SELECT * from {}cards;".format(search_word)
                cursor.execute(sqlque)
                flashtable = cursor.fetchall()
                cnxa.commit()
    cursor.close()
    return  render_template('brainnewcard.html', flashtable=flashtable)

@app.route("/signout")
def signout():
    email=""
    return render_template('regist.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3306, debug=True)
