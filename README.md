# 3m50
Python script that polls 3m50's REST interface

# Examples
### Simplest usecase. Dump Current usage to STDOUT
```
$ 3m50.py --tstat 192.168.1.22
#      Date,       Time,   Out Temp,   Set Temp,    In Temp,  Temp Diff, Heat Total, Cool Total,   Heat Run,   Cool Run,       Mode,
 2015/01/21,      23:40,         --,       64.0,       65.5,         --,        131,          0,         --,         --,       HEAT,
```

### Use Weather undergrounds REST API to get outdoor temperature as well.
For this you will need a weather underground key. You also need to figure out the url suffix for your city. 

Once you have outdoor temperature the data becomes infinitely more revealing. Particularly because you can see the difference in temperature between the outdoor temperature and the set temperature.
```
$ 3m50.py --tstat 192.168.1.22 --key 4XXXXXXXX --url '/q/NC/Cary.json'
#      Date,       Time,   Out Temp,   Set Temp,    In Temp,  Temp Diff, Heat Total, Cool Total,   Heat Run,   Cool Run,       Mode,
 2015/01/21,      23:42,       37.6,       64.0,       65.5,      -26.4,        131,          0,         --,         --,       HEAT,
```

### Dump the data to a file
This will append the data to the file specified by --fileprefix. Note that suffixes _YYYY_MM_DD.txt to the --fileprefix, so every day has its own seperate file.
```
$ 3m50.py --tstat 192.168.1.22 --key 4XXXXXXXX --url '/q/NC/Cary.json' --fileprefix /some/path/first_floor
#      Date,       Time,   Out Temp,   Set Temp,    In Temp,  Temp Diff, Heat Total, Cool Total,   Heat Run,   Cool Run,       Mode,
 2015/01/21,      23:42,       37.6,       64.0,       65.5,      -26.4,        131,          0,         --,         --,       HEAT,
```

### Dump the data to a file and email the data
This will append the data to the file specified by --fileprefix and email the data at 10am. In every email it will include today's data and the data from the day before.  
```
$ 3m50.py --tstat 192.168.1.22 --key 4XXXXXXXX --fileprefix /some/path/first_floor --email rxxxxx@xxail.com --nickname 1stFloor --hour 10
#      Date,       Time,   Out Temp,   Set Temp,    In Temp,  Temp Diff, Heat Total, Cool Total,   Heat Run,   Cool Run,       Mode,
 2015/01/21,      23:42,       37.6,       64.0,       65.5,      -26.4,        131,          0,         --,         --,       HEAT,
```

# Usage
```
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
```
