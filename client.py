import socket
import pickle
import _thread
import time
from timeit import default_timer
import sys, os
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk

window = Tk()
window.geometry("1200x750")
window.title("P2P File Transfer System")
window.configure(bg='#e7f4fc')

def p2pserver():
    serverPort = 11000
    serverSockettcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSockettcp.bind(('', serverPort))
    serverSockettcp.listen(1)
    print('Note: This p2p client is now acting as a transient server to serve other p2p client\nYou will see intermediate processing messages when it serves other p2p clients.')
    print('\nThe P2P server is ready to send files.')
    i=0

    def serverprocess(connectionsocket ,address):
        print('Connected in this connection: ',connectionsocket)
        fullpath='C:/Users/Tharun/Desktop/p2p1/'
        Response=[]
        gotthis = connectionsocket.recv(1024)
        gotthis=pickle.loads(gotthis)
        requeststring=' '.join(gotthis)
        print(requeststring)
        #sentencestring= sentence.decode("utf-8")
        fullpath += gotthis[1]
        error=''
        try:
            f = open(fullpath, 'r')
            strf=f.read()
            print(len(strf))
        except Exception as errtxt1:
            error=str(errtxt1)
            print(errtxt1)
            print('File Not Found')
        sendthis=[]
        if(gotthis[2]!='HTTP/1.1'):
             sendthis.append('HTTP/1.1')
             sendthis.append('505')
             sendthis.append('HTTPVersionNotSupported')
             sendthis=' '.join(sendthis)
             print(sendthis)
             connectionsocket.sendall(bytes(sendthis,'utf-8'))

        elif(gotthis[0]!='GET'):
            sendthis.append('HTTP/1.1')
            sendthis.append('400')
            sendthis.append('BadRequest')
            sendthis=' '.join(sendthis)
            print(sendthis)
            connectionsocket.sendall(bytes(sendthis,'utf-8'))

        elif(len(error)==0):
             sendthis.append('HTTP/1.1')
             sendthis.append('200')
             sendthis.append('Ok')
             sendthis.append(str(len(strf)))
             sendthis=' '.join(sendthis)
             sendthis+=' '+strf
             print('File was sent')
             #print(sendthis)
             connectionsocket.sendall(bytes(sendthis,'utf-8'))

        else:
            sendthis.append('HTTP/1.1')
            sendthis.append('404')
            sendthis.append('NotFound')
            sendthis=' '.join(sendthis)
            print(sendthis)
            connectionsocket.sendall(bytes(sendthis,'utf-8'))

        print('Closing Connection')
        connectionsocket.close()


    while 1:
        connectionSocket, addr = serverSockettcp.accept()
        _thread.start_new_thread(serverprocess,(connectionSocket,addr))


def p2pinterface():
    #print('Thread started')
    # change to server IP address when running on a different machine
    serverName = socket.gethostbyname(socket.gethostname()) 
    serverPort = 12000
    thisaddr=socket.gethostbyname(socket.gethostname())
    thishost=socket.gethostname()
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    seqnumber,reqnumber,partial=0,0,0
    partialmessages=[]
    alpha=0.125
    beta=0.25
    EstimatedRtt=2        #Default starting values
    TimeoutInterval=2     #Default starting values
    DevRtt=0
    #To request for a file
    time.sleep(0.1)

    def query():
        print('Query')
        nonlocal reqnumber
        reqnumber+=1
        nonlocal seqnumber
        seqnumber+=1
        nonlocal partial,clientSocket,TimeoutInterval,EstimatedRtt,DevRtt
        partial=0
        RequestMessage=[]
        RequestMessage.append(str(seqnumber))
        RequestMessage.append(str(reqnumber))
        RequestMessage.append(str(partial))
        RequestMessage.append('QueryForContent')
        RequestMessage.append(thishost)
        RequestMessage.append(thisaddr)
        # filename = input('Input file name(or press enter to get full directory listing): ')
        RequestMessage.append('')
        #RequestMessage = ['Query for content', message]
        temp=' '.join(RequestMessage)
        temp+='!'
        print(temp)
        x=0
        tobesent=temp
        while 1:
            print('Message that is sent:',tobesent)
            start = default_timer()
            clientSocket.sendto(bytes(tobesent,'utf-8'), (serverName, serverPort))
            try:
                clientSocket.settimeout(TimeoutInterval)
                ReceivedData, serverAddress = clientSocket.recvfrom(2048)
                SampleRtt = default_timer() - start
                clientSocket.settimeout(None)     #waiting maybe near this line...??
                EstimatedRtt=((1-alpha)*EstimatedRtt)+(alpha*SampleRtt)
                DevRtt=((1-beta)*DevRtt)+(beta*abs(SampleRtt-EstimatedRtt))
                TimeoutInterval=EstimatedRtt+(4*DevRtt)
                ResponseMessage=pickle.loads(ReceivedData)
                #print(ResponseMessage)
                if(ResponseMessage[0]==str(seqnumber) and partial==1 and (ResponseMessage[3]=='PartialMessageReceived') and ResponseMessage[5]=='Success'):
                    print('Got Partial Message Acknowledgement')
                    break #Break from the while 1 loop..kind of do while loop
                elif (ResponseMessage[0]==str(seqnumber) and ResponseMessage[3]=='QueryForContent'):
                    break
                else:
                    continue
            except Exception as errortext:
                print('Timed Out')
                continue
        if(ResponseMessage[3]=='QueryForContent'):
            print('Got Full Acknowledgement')
        seqnumber+=1
        # tobesent=str(seqnumber)+' '+str(reqnumber)+' '+str(partial)+' '
        #clientSocket.sendto(bytes(tobesent,'utf-8'), (serverName, serverPort))

        while 1:                                                            #for receiving entire response
            receivedstring, serverAddress = clientSocket.recvfrom(2048)
            #ResponseMessage=pickle.loads(ReceivedData)
            receivedstring=receivedstring.decode('utf-8')
            print('Received String', receivedstring)
            x=0
            temp=''
            requestmessage=[]
            while x<len(receivedstring):
                if (receivedstring[x]!=' ' and receivedstring[x]!='!'):
                    temp=temp+receivedstring[x]
                    x+=1
                    continue
                else:
                    x+=1
                requestmessage.append(temp)
                temp=''
            #listofrequestmessages.append(requestmessage)
            #print('Request Message/Received String :', receivedstring)
            receivedseqnumber=requestmessage[0]
            if(requestmessage[2]=='1'):
                print('Received message is a partial message..processing it now..')
                #Extracting data part alone removing seq no.,req no.,partial bits and store temporarily
                count,spaces=0,0
                while count<len(receivedstring):
                    if(receivedstring[count]==' ' and spaces<3):
                        spaces+=1
                    elif spaces==3:
                        break
                    count+=1
                tempstring=''
                while(count<len(receivedstring)):
                    tempstring+=receivedstring[count]
                    count+=1
                #checking for another part of partial message already present
                y,present=0,0
                while(y+2<len(partialmessages)):
                    if(serverAddress==partialmessages[y] and requestmessage[1]==partialmessages[y+1]):  #include check for sequence number
                        present=1
                        print('Partial Message was already received...combining this message with the previous message')
                        receivedstring=partialmessages[y+2]+tempstring
                        if(receivedstring[len(receivedstring)-1]=='!'):
                            print('Full message combined')
                            print(receivedstring)
                            responsemessage = []
                            responsemessage.append(str(int(receivedseqnumber)+1))
                            seqnumber+=1#seq numner+=1
                            responsemessage.append(requestmessage[1])
                            responsemessage.append('FullMessageReceived')
                            responsemessage.insert(4,'200')
                            responsemessage.insert(5,'Success')
                            print('Response Message:', responsemessage)
                            ackmessage=' '.join(responsemessage)
                            clientSocket.sendto(bytes(ackmessage,'utf-8'), (serverName, serverPort))

                        else:
                            print('The message is still partial, waiting for next packet...')
                            partialmessages[y+2]=receivedstring
                            responsemessage = []
                            responsemessage.append(str(int(receivedseqnumber)+1))#seqnumber+=1
                            seqnumber+=1
                            responsemessage.append(requestmessage[1])
                            responsemessage.append('PartialMessageReceived')
                            responsemessage.insert(4,'200')
                            responsemessage.insert(5,'Success')
                            print('Response Message:', responsemessage)
                            ackmessage=' '.join(responsemessage)
                            clientSocket.sendto(bytes(ackmessage,'utf-8'), (serverName, serverPort))
                        y+=3
                    else:
                        y+=3
                if present==0:
                    print('First partial message received..storing it for combining when the next message comes..')
                    partialmessages.append(serverAddress)
                    partialmessages.append(requestmessage[1])
                    partialmessages.append(receivedstring)
                    responsemessage = []
                    responsemessage.append(str(int(receivedseqnumber)+1))#seqnumber+=1
                    seqnumber+=1
                    responsemessage.append(requestmessage[1])
                    responsemessage.append('PartialMessageReceived')
                    responsemessage.insert(4,'200')
                    responsemessage.insert(5,'Success')
                    print('Response Message:', responsemessage)
                    ackmessage=' '.join(responsemessage)
                    clientSocket.sendto(bytes(ackmessage,'utf-8'), (serverName, serverPort))
            #print(receivedstring[len(receivedstring)-1])
            if(receivedstring[len(receivedstring)-1]=='!'):
                print('Processing full string: ', receivedstring)
                receivedmessage=[]
                x=0
                temp=''
                while x<len(receivedstring):
                    if (receivedstring[x]!=' 'and receivedstring[x]!='!'):
                        temp=temp+receivedstring[x]
                        x+=1
                        continue
                    else:
                        x+=1
                    receivedmessage.append(temp)
                    temp=''
                #print('Response Message as a list: ', receivedmessage)

                if receivedmessage[5] == 'Success':
                    print('\nThe file list, file size and corresponding peers: ')
                    count=6
                    total_rows = (len(receivedmessage) - 6)//3
                    while count<len(receivedmessage):
                        print(receivedmessage[count],' ',receivedmessage[count+1],' ',receivedmessage[count+2])
                        count+=3

                    top = Toplevel()
                    top.geometry("1100x700")
                    top.title("Query")
                    top.configure(bg='#e7f4fc')
                    l1 = Label(top, text="Query", font=("Arial", 25), bg='#e7f4fc', pady = 40).pack()

                    outputFrame = Frame(top, pady=40, bg='#e7f4fc')
                    outputFrame.pack()

                    h1 = Label(outputFrame, text="File Name", width=23, font=("Arial Bold", 16), bg='#e7f4fc', borderwidth=1, relief="solid", pady = 20).grid(row=0,column=0)
                    h2 = Label(outputFrame, text="File Size", width=23, font=("Arial Bold", 16), bg='#e7f4fc', borderwidth=1, relief="solid", pady = 20).grid(row=0,column=1)
                    h3 = Label(outputFrame, text="Peer IP", width=23, font=("Arial Bold", 16), bg='#e7f4fc', borderwidth=1, relief="solid", pady = 20).grid(row=0,column=2)

                    count=6
                    for i in range(total_rows):
                        for j in range(3):
                            e = Label(outputFrame, text=receivedmessage[count+j], width=25, font=('Arial',16), bg='#e7f4fc', borderwidth=1, relief="solid", pady = 15) 
                            e.grid(row=i+1, column=j)
                        count+=3

                    top.mainloop() 

                elif receivedmessage[5]=='Error':
                    print('The file is not available in any of the peers')
                break

    def inform():
        top = Toplevel()
        top.geometry("1100x700")
        top.title("Inform and Update")
        top.configure(bg='#e7f4fc')
        l1 = Label(top, text="Inform and Update", font=("Arial", 25), bg='#e7f4fc', pady = 40).pack()

        inputFrame = Frame(top, pady=80, bg='#e7f4fc')
        inputFrame.pack()

        def update():
            nonlocal reqnumber
            reqnumber+=1
            nonlocal seqnumber
            seqnumber+=1
            nonlocal partial,clientSocket,TimeoutInterval,EstimatedRtt,DevRtt
            partial=0
            fname = e1.get()
            fsize = e2.get()
            RequestMessage=[]
            RequestMessage.append(str(seqnumber))
            RequestMessage.append(str(reqnumber))
            RequestMessage.append(str(partial))
            RequestMessage.append('InformAndUpdate')
            RequestMessage.append(thishost)
            RequestMessage.append(thisaddr)
            RequestMessage.append(fname)
            RequestMessage.append(fsize)
            # RequestMessage = ['Inform and update', message]
            #clientSocket.sendto(pickle.dumps(RequestMessage), (serverName, serverPort))
            temp=' '.join(RequestMessage)
            temp+='!'
            print(temp)
            tobesent=temp
            while 1:
                print('Message that is sent:',tobesent)
                start = default_timer()
                clientSocket.sendto(bytes(tobesent,'utf-8'), (serverName, serverPort))
                try:
                    clientSocket.settimeout(TimeoutInterval)
                    ReceivedData, serverAddress = clientSocket.recvfrom(2048)   #waiting maybe near this line...??
                    SampleRtt = default_timer() - start
                    clientSocket.settimeout(None)
                    EstimatedRtt=((1-alpha)*EstimatedRtt)+(alpha*SampleRtt)
                    DevRtt=((1-beta)*DevRtt)+(beta*abs(SampleRtt-EstimatedRtt))
                    TimeoutInterval=EstimatedRtt+(4*DevRtt)
                    ResponseMessage=pickle.loads(ReceivedData)
                    print(ResponseMessage)
                    if(ResponseMessage[0]==str(seqnumber) and partial==1 and (ResponseMessage[3]=='PartialMessageReceived') and ResponseMessage[5]=='Success'):
                        print('Got Partial Message Acknowledgement')
                        break #Break from the while 1 loop..kind of do while loop
                    elif (ResponseMessage[0]==seqnumber and ResponseMessage[3]=='InformAndUpdate'):
                        break
                    else:
                        continue
                except Exception as errortext:
                    print('Timed Out',errortext)
                    continue

            if ResponseMessage[5] == 'Success':
                print('Acknowledged by server- The central directory server list was updated accordingly!')
                messagebox.showinfo("Info", fname + " Has Updated Successfully")

        h1 = Label(inputFrame, text="Enter File name you have: ", width=23, font=("Arial", 16), bg='#e7f4fc', pady = 20).grid(row=0,column=0)
        e1 = Entry(inputFrame, width=25, font=("Arial", 14))
        e1.grid(row=0,column=1,ipady=5)
        h2 = Label(inputFrame, text="Enter Size of File: ", width=23, font=("Arial", 16), bg='#e7f4fc', pady = 20).grid(row=1,column=0)
        e2 = Entry(inputFrame, width=25, font=("Arial", 14))
        e2.grid(row=1,column=1,ipady=5)
        
        btn = Button(top, text="Update", command = update, bg="#1287CE", fg="white", width = 15, padx = 20, pady = 10, font=("Arial Bold", 12)).pack()

        top.mainloop()
        

    def askFile():
        top = Toplevel()
        top.geometry("1100x700")
        top.title("Ask for File")
        top.configure(bg='#e7f4fc')
        l1 = Label(top, text="Ask for File", font=("Arial", 25), bg='#e7f4fc', pady = 40).pack()

        inputFrame = Frame(top, pady=80, bg='#e7f4fc')
        inputFrame.pack()


        def ask():
            serverName = e1.get()
            #serverName = socket.gethostbyname(socket.gethostname())
            serverPort = 11000
            clientSockettcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSockettcp.connect((serverName, serverPort))
            fname = e2.get()
            fullpath ='C:/Users/Tharun/Desktop/p2p1/rec/'
            fullpath = fullpath+fname
            sendthis=[]
            sendthis.append('GET')
            sendthis.append(fname)
            sendthis.append('HTTP/1.1')
            clientSockettcp.send(pickle.dumps(sendthis))
            size=10
            i=0
            spaces=0
            ReceivedData=''
            temp=''
            gotthis=[]
            while size > len(ReceivedData):
                data = clientSockettcp.recv(1024)
                if not data:
                    break
                data=data.decode('utf-8')
                count=0
                while(i==0 and count<len(data)):
                    if(data[count]!=' '):
                        temp=temp+data[count]
                        count=count+1
                    else:
                        gotthis.append(temp)
                        temp=''
                        spaces+=1
                        count+=1
                        if(spaces==4):
                            break
                if(gotthis[1]=='200'):
                    size=int(gotthis[3])
                i=1
                ReceivedData+= data[count:len(data)]
            #print('Status from server: ', Response[0])
            if(gotthis[1]=='200'):
                f = open(fullpath, 'w')
                f.write(ReceivedData)
                print('File was transfered')
                messagebox.showinfo("Info", fname + " File was transfered Successfully")
                f.close()
            elif(gotthis[1]=='404'):
                print('Server could not find the file..request a different file')
                messagebox.showerror("Error","Server could not find the file...Request a different file")
            elif(gotthis[1]=='400'):
                print('Bad Request was sent')
                messagebox.showerror("Error","Bad Request was sent")
            elif(gotthis[1]=='505'):
                print('HTTP version not supported by server')
                messagebox.showerror("Error","HTTP version not supported by server")

            clientSockettcp.close()

        h1 = Label(inputFrame, text="Enter IP of the server where file located: ", font=("Arial", 14), bg='#e7f4fc', pady = 20).grid(row=0,column=0)
        e1 = Entry(inputFrame, width=25, font=("Arial", 14))
        e1.grid(row=0,column=1,ipady=5)
        h2 = Label(inputFrame, text="Enter File name: ", width=23, font=("Arial", 16), bg='#e7f4fc', pady = 20).grid(row=1,column=0)
        e2 = Entry(inputFrame, width=25, font=("Arial", 14))
        e2.grid(row=1,column=1,ipady=5)
        
        btn = Button(top, text="Update", command = ask, bg="#1287CE", fg="white", width = 15, padx = 20, pady = 10, font=("Arial Bold", 12)).pack()

        top.mainloop()


    def exitBtn():
        print('Exit')
        nonlocal reqnumber
        reqnumber+=1
        nonlocal seqnumber
        seqnumber+=1
        nonlocal partial,clientSocket,TimeoutInterval,EstimatedRtt,DevRtt
        partial=0
        RequestMessage=[]
        RequestMessage.append(str(seqnumber))
        RequestMessage.append(str(reqnumber))
        RequestMessage.append(str(partial))
        RequestMessage.append('Exit')
        RequestMessage.append(thishost)
        RequestMessage.append(thisaddr)
        temp=' '.join(RequestMessage)
        temp+='!'
        while 1:
            print('Message that is sent:',temp)
            start = default_timer()
            clientSocket.sendto(bytes(temp,'utf-8'), (serverName, serverPort))
            try:
                clientSocket.settimeout(TimeoutInterval)
                ReceivedData, serverAddress = clientSocket.recvfrom(2048)       #waiting maybe near this line...??
                SampleRtt = default_timer() - start
                clientSocket.settimeout(None)
                EstimatedRtt=((1-alpha)*EstimatedRtt)+(alpha*SampleRtt)
                DevRtt=((1-beta)*DevRtt)+(beta*abs(SampleRtt-EstimatedRtt))
                TimeoutInterval=EstimatedRtt+(4*DevRtt)
                ResponseMessage=pickle.loads(ReceivedData)
                if (ResponseMessage[0]!=str(seqnumber)):
                    continue
                print(ResponseMessage)
            except Exception as errortext:
                    print('Timed Out',errortext)
                    continue
            if(ResponseMessage[5]=='Success'):
                print('Server acknowledges exit..all instance of your files in the directory list was removed')
                clientSocket.close()
                os._exit(1)


    #For Heading
    l1 = Label(window, text="Peer To Peer File Transfer System Using Central Directory", font=("Arial", 25), bg='#e7f4fc', pady = 20).pack()

    #For Image
    global bgImg
    bgImg = ImageTk.PhotoImage(Image.open('background.png').resize((800, 500)))
    l2 = Label(window, image = bgImg, pady = 40)
    l2.pack()

    btnFrame = Frame(window, pady=50, bg='#e7f4fc')
    btnFrame.pack()

    btn1 = Button(btnFrame, text="Query for Content", command = query, bg="#1287CE", fg="white", width = 15, padx = 20, pady = 10, font=("Arial Bold", 12))
    btn1.grid(row=0,column=0, padx = 25)

    btn2 = Button(btnFrame, text="Inform and Update", command = inform, bg="#1597e5", fg="white", width = 15, padx = 20, pady = 10, font=("Arial Bold", 12))
    btn2.grid(row=0,column=1, padx = 25)

    btn3 = Button(btnFrame, text="Ask for a File", command = askFile, bg="#1287CE", fg="white", width = 15, padx = 20, pady = 10, font=("Arial Bold", 12))
    btn3.grid(row=0,column=2, padx = 25)

    btn4 = Button(btnFrame, text="Exit", command = exitBtn, bg="#1597e5", fg="white", width = 15, padx = 20, pady = 10, font=("Arial Bold", 12))
    btn4.grid(row=0,column=3, padx = 25)


print('Trying to start thread: ')
try:
    _thread.start_new_thread(p2pinterface,())
    _thread.start_new_thread(p2pserver,())
    window.mainloop()
except Exception as errtxt:
    print(errtxt)
