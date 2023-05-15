# Portfolio2
-----------------

## overview 
--------------------------------
-s = Runs Server (python3 application.py -s)
-c = Runs Client and the filename
-t = representing the chosen test case, which can be one of 'loss' or 'skip_ack
-i = The IP address of the server
-p = The port number on which the server will listen and the client connects too
-r = reliable methods choose between stop and wait with (sw), Go Back N with (gbn) or sr was not implemented correctly so using the sr flag 
you have too run both server and client.
-f = Filename is the name of the file that will be transferred
---------------------------------------------------------

The server:

    python3 application.py -s -i <ip_address> -p <port_number> -r <reliable method>

If I want to skip an ack to trigger retransmission at the sender-side:
  
    python3 application.py -s -i <ip_address> -p <port_number> -r <reliable method> -t <test_case>

-------------------------------------------------------------------------------------------

If u want to filetransfore you have to send use -f, it can only be used on client side.
  
    python3 application.py -c -r sw -i "ip adress" -p "port" -f "filename"
