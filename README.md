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

# Sample email
```
From: rxxxxx@xxail.com 
To:  
Date: Wed, 21 Jan 2015 09:00:16 -0500 
Subject: 1stFloor: Heat runtime: 1h 42m, Cool runtime: 0h 0m on 2015/01/20 
 
Yesterday:
1stFloor: Heat runtime: 1h 42m, Cool runtime: 0h 0m on 2015/01/20
#      Date,       Time,   Out Temp,   Set Temp,    In Temp,  Temp Diff, Heat Total, Cool Total,   Heat Run,   Cool Run,       Mode,
 2015/01/20,      01:00,       41.5,       64.0,       67.0,      -22.5,          0,          0,          0,          0,       HEAT,
 2015/01/20,      02:00,       42.6,       64.0,       66.5,      -21.4,          0,          0,          0,          0,       HEAT,
 2015/01/20,      03:00,       44.8,       64.0,       66.0,      -19.2,          0,          0,          0,          0,       HEAT,
 2015/01/20,      04:00,       43.0,       64.0,       65.0,      -21.0,          0,          0,          0,          0,       HEAT,
 2015/01/20,      05:00,       42.1,       64.0,       64.5,      -21.9,          0,          0,          0,          0,       HEAT,
 2015/01/20,      06:00,       41.7,       64.0,       63.5,      -22.3,          0,          0,          0,          0,       HEAT,
 2015/01/20,      07:00,       40.6,       64.0,       63.0,      -23.4,          0,          0,          0,          0,       HEAT,
 2015/01/20,      08:00,       38.7,       67.0,       67.0,      -28.3,         25,          0,         25,          0,       HEAT,
 2015/01/20,      09:00,       46.0,       69.0,       68.5,      -23.0,         78,          0,         53,          0,       HEAT,
 2015/01/20,      10:00,       52.5,       69.0,       68.0,      -16.5,         97,          0,         19,          0,       HEAT,
 2015/01/20,      11:00,       56.5,       69.0,       68.0,      -12.5,        102,          0,          5,          0,       HEAT,
 2015/01/20,      12:00,       61.0,       69.0,       69.0,       -8.0,        102,          0,          0,          0,       HEAT,
 2015/01/20,      13:00,       63.7,       69.0,       69.5,       -5.3,        102,          0,          0,          0,       HEAT,
 2015/01/20,      14:00,       66.7,       69.0,       70.0,       -2.3,        102,          0,          0,          0,       HEAT,
 2015/01/20,      15:00,       67.8,       69.0,       70.5,       -1.2,        102,          0,          0,          0,       HEAT,
 2015/01/20,      16:00,       66.0,       69.0,       71.0,       -3.0,        102,          0,          0,          0,       HEAT,
 2015/01/20,      17:00,       63.0,       69.0,       70.0,       -6.0,        102,          0,          0,          0,       HEAT,
 2015/01/20,      18:00,       57.0,       69.0,       69.5,      -12.0,        102,          0,          0,          0,       HEAT,
 2015/01/20,      19:00,       52.3,       67.0,       69.0,      -14.7,        102,          0,          0,          0,       HEAT,
 2015/01/20,      20:00,       49.6,       67.0,       69.5,      -17.4,        102,          0,          0,          0,       HEAT,
 2015/01/20,      21:00,       48.4,       67.0,       69.5,      -18.6,        102,          0,          0,          0,       HEAT,
 2015/01/20,      22:00,       49.5,       67.0,       69.0,      -17.5,        102,          0,          0,          0,       HEAT,
 2015/01/20,      23:00,       50.0,       64.0,       67.5,      -14.0,        102,          0,          0,          0,       HEAT,
 2015/01/21,      00:00,       47.8,       64.0,       67.5,      -16.2,        102,          0,          0,          0,       HEAT,


Today:
1stFloor: Heat runtime: 0h 58m, Cool runtime: 0h 0m on 2015/01/21
#      Date,       Time,   Out Temp,   Set Temp,    In Temp,  Temp Diff, Heat Total, Cool Total,   Heat Run,   Cool Run,       Mode,
 2015/01/21,      01:00,       47.5,       64.0,       67.0,      -16.5,          0,          0,          0,          0,       HEAT,
 2015/01/21,      02:00,       46.0,       64.0,       66.5,      -18.0,          0,          0,          0,          0,       HEAT,
 2015/01/21,      03:00,       45.1,       64.0,       66.0,      -18.9,          0,          0,          0,          0,       HEAT,
 2015/01/21,      04:00,       44.1,       64.0,       65.5,      -19.9,          0,          0,          0,          0,       HEAT,
 2015/01/21,      05:00,       42.8,       64.0,       65.0,      -21.2,          0,          0,          0,          0,       HEAT,
 2015/01/21,      06:00,       40.6,       64.0,       64.5,      -23.4,          0,          0,          0,          0,       HEAT,
 2015/01/21,      07:00,       39.0,       64.0,       64.0,      -25.0,          0,          0,          0,          0,       HEAT,
 2015/01/21,      08:00,       38.7,       69.0,       67.0,      -30.3,         27,          0,         27,          0,       HEAT,
 2015/01/21,      09:00,       40.6,       67.0,       67.0,      -26.4,         58,          0,         31,          0,       HEAT,
```
