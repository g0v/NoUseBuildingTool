#coding=utf-8
import httplib2
import pprint
import os
import sys
import getopt
import shutil
import subprocess
import re
import json
import codecs

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow
#from oauth2client.client import SignedJwtAssertionCredentials
from oauth2client.file import Storage

# Email of the Service Account.
SERVICE_ACCOUNT_EMAIL = '798462891532-f7dccq3hfrebaf5io4jnka1ndu4c299p@developer.gserviceaccount.com'

# Path to the Service Account's Private Key file.
SERVICE_ACCOUNT_PKCS12_FILE_PATH = 'b9cd686ca80a0178cfc30ac1afea2ce32e3d7125-privatekey.p12'

# Copy your credentials from the console
CLIENT_ID = '798462891532.apps.googleusercontent.com'
CLIENT_SECRET = 'IchNK02O7ZvRnUI2l9EspXRn'

# folderID and tableID of twangery
HtmlFolder_ID = '0B1hVi2nr20zYMEhKelRQMHVpQmM'
AttrTable_ID = '1vtFn9HdBevas98G1J9pkkrtkSKFSwkrw5vRBreSq'
# fodlerID and tableID of Mine
#HtmlFolder_ID = '0B1VcEjNwxq8SOERvWWF2ZFpINWs'
#AttrTable_ID = '1vnBhbJmwhV1w6VR4J5Odn0zjVFILzgrc7eYEOh6Y'

# Check https://developers.google.com/drive/scopes for all available scopes
OAUTH_SCOPE = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/fusiontables']

# Redirect URI for installed apps
REDIRECT_URI = 'http://lingdisk.synology.me/'

# test Path to the file to upload
FILENAME = 'Document2.txt'

def findID(filename):
    start=filename.find('(')
    end=filename.find(')')
    if(end>start):
        ID=filename[start+1:end]
        return int(ID)
    else:
        return -1    
    
def CreateServicecredentials():
    f = file(SERVICE_ACCOUNT_PKCS12_FILE_PATH, 'rb')
    key = f.read()
    f.close()
    credentials = SignedJwtAssertionCredentials(SERVICE_ACCOUNT_EMAIL, key, scope='https://www.googleapis.com/auth/drive')
    return credentials 
    
def Createcredentials():
    storage = Storage('a_credentials_file')
    credentials = storage.get()
    if credentials == None :
        flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)
        authorize_url = flow.step1_get_authorize_url()
        print 'Go to the following link in your browser: ' + authorize_url
        code = raw_input('Enter verification code: ').strip()
        credentials = flow.step2_exchange(code)
        storage.put(credentials)
    
    return credentials
            
def UploadFiles(folderPath): 
    for (dirpath, dirnames, filenames) in os.walk(folderPath):
        for filename in filenames:
            if filename[-5:] == '.html':
                filepath=os.path.join(dirpath,filename)
                print filepath
       
                media_body = MediaFileUpload(filepath, mimetype='text/plain', resumable=False)
                parent_ID='"'+HtmlFolder_ID+'"'
                print parent_ID
                body = {
                    'title': filename,
                    'description': 'content',
                    'mimeType': 'text/plain', 
                    'parents':[{"id":HtmlFolder_ID}]
                }

                result = drive_service.files().insert(body=body, media_body=media_body).execute()
                #print result
        
def InsertTable(title, link):
    InsertQuery="INSERT INTO"+ HtmlTable_ID + "(Title, HtmlLink) VALUES ("+"'"+title+"','"+link+"')"
    result=table_service.query().sql(sql=InsertQuery).execute()
    print result
    
def QueryLink():
    filelist=[]
    condition="'"+HtmlFolder_ID+ "' in parents"
    #condition="'0B1VcEjNwxq8SOERvWWF2ZFpINWs' in parents"
    print condition
    body = {
        'q':condition
    }
    result=drive_service.files().list(**body).execute();
    filelist.extend(result['items']) 
    for file in filelist:
        #print file['webContentLink'], file['title'] 
        ID=findID(file['title'])
        if(ID>-1):
            #InsertTable(file['title'], file['webContentLink'])
            IDQuery="SELECT ROWID from "+ AttrTable_ID + " where ID =" + str(ID)
            result=table_service.query().sql(sql=IDQuery).execute()
            if 'rows' in result.keys():
                rowID=int(result['rows'][0][0])
                UpdateQuery="UPDATE "+AttrTable_ID+" SET Link =" + "'" + file['webContentLink'] + "'" +" WHERE ROWID='"+str(rowID)+"'"
                result=table_service.query().sql(sql=UpdateQuery).execute()
                

def transformHtml(inputPath, outputPath):
    libpath="python"
    convpath="unoconv/unoconv"
    for (dirpath, dirnames, filenames) in os.walk(inputPath):
        for filename in filenames:
            if filename[-4:] == '.doc':
                outputname=filename[0:len(filename)-4]+'.html'
                outputpath=os.path.join(outputPath, outputname);
                print outputpath
                filepath=os.path.join(dirpath,filename)
                resultpath=os.path.join(dirpath,outputname)
                print filepath, resultpath
                
                command=libpath+' '+convpath+' '+'-f html "'+filepath+'"'
                print command
                try:
                    retcode = subprocess.call(command, shell=True)
                    if retcode < 0:
                        print >>sys.stderr, "Child was terminated by signal", -retcode
                    else:
                        print >>sys.stderr, "Child returned", retcode
                        shutil.copyfile(resultpath, outputpath)
                except OSError as e:
                    print >>sys.stderr, "Execution failed:", e
                
def LoadJsontoTable(filepath):
    f = open(filepath, 'r')
    addressinfo=[]
    for line in f: 
        addressinfo.append(json.loads(line))
    f.close()
     
    for point in addressinfo[0]['features']:
        address=point['properties']['MapAddress']
        title=point['properties']['Title']
        lng=str(point['geometry']['coordinates'][0])
        lat=str(point['geometry']['coordinates'][1])
        ID=point['properties']['ID']
                
        #query ID exist or not
        IDQuery="SELECT ROWID from "+AttrTable_ID+" where ID =" + str(ID)
        result=table_service.query().sql(sql=IDQuery).execute()
        if 'rows' in result.keys():
            print result
            rowID=int(result['rows'][0][0]) 
            #update ID
            UpdateQuery="UPDATE "+AttrTable_ID+" SET Title =" + "'" + title + "', Address=" + "'" + address +"', lat="+str(lat)+", lng="+str(lng)+" WHERE ROWID='"+str(rowID)+"'"
            result=table_service.query().sql(sql=UpdateQuery).execute()
            print result
        else:
            #if ID doesn't exist, inert it
            InsertQuery="INSERT INTO "+AttrTable_ID+" (ID, Title, Address, lat, lng) VALUES ("+str(ID)+",'"+title+"','"+address+"',"+lat+","+lng+")"
            result=table_service.query().sql(sql=InsertQuery).execute()
            print result
        
def printusage():
    print 'please input your option.\n'
    print '1:Transform doc to html. param: inputfolder_path outputfolder_path\n'
    print '2:Write address info to Google FusionTable. param: address_json_path\n'
    print '3:Upload html Files to Google Doc. parma:htmlfolder_path\n'
    print '4:Write html link to Google FusionTable.\n'
    
def main(argv):
    try:
        opts, args=getopt.getopt(argv, "h", ["-help"])
        
        credentials=Createcredentials()
        http = httplib2.Http()
        http = credentials.authorize(http)
        global drive_service 
        drive_service = build('drive', 'v2', http=http)
        global table_service 
        table_service= build('fusiontables', 'v1', http=http)
    
        if args[0]=='1' and len(args)==3:
            inputfolder=args[1]
            outputfolder=args[2]
            transformHtml(inputfolder, outputfolder)
        elif args[0]=='2' and len(args)==2:
            LoadJsontoTable(args[1])
        elif args[0]=='3' and len(args)==2:    
            folder=args[1]
            UploadFiles(folder)
        elif args[0]=='4' and len(args)==1:
            QueryLink()
    except IndexError:
        printusage()
        sys.exit(2)    
    
     
if __name__ == "__main__":
    main(sys.argv[1:])
