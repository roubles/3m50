# 3m50
Python script that polls 3m50's REST interface


usage: 3m50.py [-h] -t TSTAT [-k KEY] [-u URL] [-f FILEPREFIX] [-e EMAIL]
               [-n NICKNAME]
               [-r {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23}]
               [-m] [-s {yesterdays,todays,total}] [-l LOGFILE] [-v] [-y]

Dumps the date, time, outdoor temperature, desired indoor temperature, actual
indoor temperature, heat runtime, cool runtime to the specified file in csv
format.

optional arguments:
  -h, --help            show this help message and exit
  -t TSTAT, --tstat TSTAT
                        Thermostat hostname or IP Address
  -k KEY, --key KEY     Weather Underground Key
  -u URL, --url URL     Wunderground URL Suffix for your city (Default:
                        '/q/NC/Cary.json')
  -f FILEPREFIX, --fileprefix FILEPREFIX
                        File to store CSV results in. Note, script will attach
                        a suffix of _YYYY_MM_DD.txt.
  -e EMAIL, --email EMAIL
                        Email address to send report
  -n NICKNAME, --nickname NICKNAME
                        Name for your thermostat for your emailed report
  -r {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23}, --hour {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23}
                        If hour is specified, we only email a report at
                        specified time
  -m, --nohtml          Send email in text format
  -s {yesterdays,todays,total}, --subject {yesterdays,todays,total}
                        What usage summary to show in email subject
  -l LOGFILE, --logfile LOGFILE
                        Logging file
  -v, --verbose         Enable verbose debugs
  -y, --sync            Syncronize thermostat's time with client machine

