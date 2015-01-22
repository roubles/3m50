#!/usr/bin/env python

from datetime import date, datetime, timedelta
import argparse
import json
import urllib
import urllib2
import os
import time
import sys
import logging
import logging.handlers

# This script will poll the specified 3m50 and get usage data. The 3m50 does
# not store much onboard data, outside of yesterday's total usage, and today's
# current usage.
#
# The only required parameter is the ip address or hostname of the 3m50
# (--tstat).
#
# If you specify a --fileprefix the script will store the current usage to a
# data file. The data file will be suffixed with today's date in the format
# _YYYY_MM_DD.txt
#
# If a file is not specified, it will just dump current usage to STDOUT.
#
# The main use case I anticipate is a user calling this script via cron
# hourly with a --fileprefix. This way, the user is saving enough state to
# create a meaningful, usable periodic report. 
#
# The expectation is to call this script hourly from cron.  
# 0	*/1	*       *       *	root	3m50.py <arguments>
# 
# If this script finds data files, it will print a pretty printed report to
# STDOUT. If am email address is specified (--email) the script will also
# email the report. If --hour is specified, the email will only be sent at
# that hour.
#
# If --key and --url are specified, the script will poll weather underground
# to get current outdoor temperature. This makes the data more useful,
# because you can see the difference between the outdoor temperature and the
# current set indoor temperature.
#
# If --nickname is set, it will be used in the report as a friendly
# identifier for the thermostat in question. If --verbose is set we will
# print verbose debugs. If --logfile is set we will output logs to a
# logfile.

# Global variables are evil. Except this one.
logger = None

#Constants
first_commented_line = '{:>12}'.format('#      Date,') + \
                       '{:>12}'.format('       Time,') + \
                       '{:>12}'.format('   Out Temp,') + \
                       '{:>12}'.format('   Set Temp,') + \
                       '{:>12}'.format('    In Temp,') + \
                       '{:>12}'.format('  Temp Diff,') + \
                       '{:>12}'.format(' Heat Total,') + \
                       '{:>12}'.format(' Cool Total,') + \
                       '{:>12}'.format('   Heat Run,') + \
                       '{:>12}'.format('   Cool Run,') + \
                       '{:>12}'.format('       Mode,')

# For a certain minute offset, we still pretend like we are at the top of
# the hour. This enables an admin to kick this script off anytime before 
# minuteOffset in their crontabs
minuteOffset = 5

# Class definitions
class Temperature(object):
    def __init__(self, tempImperialUnit, tempMetricUnit):
        self.tempImperialUnit = tempImperialUnit
        self.tempMetricUnit = tempMetricUnit
    def __str__(self):
        return "Imperial: " + str(self.tempImperialUnit) + " F, Metric: " + str(self.tempMetricUnit) + " C" 

class Runtime(object):
    def __init__(self, coolRuntime, heatRuntime):
        self.heatRuntime = int(heatRuntime)
        self.coolRuntime = int(coolRuntime)
    def __str__(self):
        return "Heat Runtime: " + str(self.heatRuntime) + " minutes, Cool Runtime: " + str(self.coolRuntime) + " minutes" 

class Thermostat(object):
    def __init__(self, hostName):
        self.hostName = hostName
    def isUp (self):
        try:
            uri = 'http://' + self.hostName
            path = '/tstat'
            urllib2.urlopen(uri + path)
            return True
        except Exception as e:
            logger.error("Error checking if thermostat " + self.hostName + " is up")
            logger.exception(e)
            return False
    def getCurrentIndoorTemperature(self):
        try:
            uri = 'http://' + self.hostName
            path = '/tstat'
            data = json.load(urllib2.urlopen(uri + path))
            return data['temp']
        except Exception as e:
            logger.error("Error getting indoor temperature from " + self.hostName)
            logger.exception(e)
            return None
    def getMode(self):
        try:
            uri = 'http://' + self.hostName
            path = '/tstat'
            data = json.load(urllib2.urlopen(uri + path))
            mode = data['tmode']
            if mode == 2:
                return "COOL"
            elif mode == 1:
                return "HEAT"
        except Exception as e:
            logger.error("Error getting current set temperature from " + self.hostName)
            logger.exception
            return "UNKNOWN"
    def getCurrentSetTemperature(self):
        try:
            uri = 'http://' + self.hostName
            path = '/tstat'
            data = json.load(urllib2.urlopen(uri + path))
            mode = data['tmode']
            if mode == 2:
                return data['t_cool']
            elif mode == 1:
                return data['t_heat']
        except Exception as e:
            logger.error("Error getting current set temperature from " + self.hostName)
            logger.exception(e)
            return None
    def hasThermostatTransferredData(self):
        try:
            uri = 'http://' + self.hostName
            path = '/tstat'
            data = json.load(urllib2.urlopen(uri + path))

            hour = data['time']['hour']
            if hour == 0:
                return True
            return False
        except Exception as e:
            logger.error("Error checking if " + self.hostName + " has transferred data")
            logger.exception(e)
            return None
    def syncTime (self):
        try:
            uri = 'http://' + self.hostName
            path = '/tstat'
            data = json.load(urllib2.urlopen(uri + path))
            logger.info("Current time on thermostat is: " + '{:0>2}'.format(str(data['time']['hour'])) + ":" + '{:0>2}'.format(str(data['time']['minute'])))

            hour = datetime.now().hour
            minute = datetime.now().minute
            logger.info("Setting time on thermostat to: " + '{:0>2}'.format(str(hour)) + ":" + '{:0>2}'.format(str(minute).format(":0>2")))
            data = '{\"time\":{\"hour\":' + str(hour) + ',\"minute\":' + str(minute) + '}}'
            response = urllib2.urlopen(uri + path, data).read()
            return True
        except Exception as e:
            logger.error("Error Synchronizing time with " + self.hostName)
            logger.exception(e)
            return False

    def getCurrentRuntime(self, now):
        try:
            uri = 'http://' + self.hostName
            path = '/tstat/datalog'

            if now.hour == 0 and now.minute <= minuteOffset: 
                # We have been asked the current runtime at midnight. What is
                # actually being requested is the usage between 23:00 to midnight.
                #
                # However, the 3m50 will transfer today's statistics to
                # yesterday's bucket at midnight. So, essentially we need yesterday's usage.
                #
                # This part of the code is very sensitive to time
                # syncronization between the client machine and the 3m50
                # therefore you see sleeps.
                #
                # Also, note minuteOffset comes into play here. For any time
                # between 12:00 and 12:00 + minuteOffset, we consider that
                # we are going to get yesterdays usage
                attempt = 0
                while self.hasThermostatTransferredData() == False:
                    #Thermostat is still one day behind.
                    if attempt > 4:
                        # This means that the client machine is over 1.5 minutes
                        # off in time than the thermostat.
                        #
                        # This should not be the case, since both machines
                        # should be on NTP.
                        #
                        # We log this as an error by returning a negative
                        # runtime.
                        return Runtime(-1, -1)
                        break
                    logger.info("Sleeping 30")
                    time.sleep(30) #Give the thermostat 30 seconds to move todays usage to yestedays usage
                    attempt += 1

                time.sleep(5) # We know that the thermostat thinks it is tomorrow. 
                              # But we do not know the today's data has been
                              # successfully transferred to yesterdays. So we
                              # sleep for 5 seconds to give the thermostat time
                              # to transfer the data
                data = json.load(urllib2.urlopen(uri + path))
                coolRuntimeMinutes = data['yesterday']['cool_runtime']['hour']*60 + data['yesterday']['cool_runtime']['minute']
                heatRuntimeMinutes = data['yesterday']['heat_runtime']['hour']*60 + data['yesterday']['heat_runtime']['minute']
            else:
                data = json.load(urllib2.urlopen(uri + path))
                coolRuntimeMinutes = data['today']['cool_runtime']['hour']*60 + data['today']['cool_runtime']['minute']
                heatRuntimeMinutes = data['today']['heat_runtime']['hour']*60 + data['today']['heat_runtime']['minute']
            return Runtime(coolRuntimeMinutes, heatRuntimeMinutes)
        except Exception as e:
            logger.error("Error getting current runtime from " + self.hostName)
            logger.exception(e)
            return None
    def __str__(self):
        return "TSTAT Hostname: " + self.hostName

# Utility methods    
def convertMinutesToHHMM(totalMinutes):
    totalMinutes = abs(totalMinutes)
    hours = totalMinutes/60
    minutes = totalMinutes%60
    return str(hours) + "h " + str(minutes) + "m"

def convert_date_to_str_YYYYMMDD_with_slash(date):
    dateString = date.strftime('%Y/%m/%d')
    return dateString

def convert_date_to_str_YYYYMMDD_with_underscore(date):
    dateString = date.strftime('_%Y_%m_%d')
    return dateString

def convert_date_to_str_HHMM_with_colon(date):
    dateString = date.strftime('%H:%M')
    return dateString

def get_outdoor_temperature_right_now(wundergroundApiKey, url):
    try:
        uri = 'http://api.wunderground.com'
        path = '/api/' + wundergroundApiKey + '/conditions/' + url
        data = json.load(urllib2.urlopen(uri + path))
        tempImperialUnit = data['current_observation']['temp_f']
        tempMetricUnit = data['current_observation']['temp_c']
        return Temperature(tempImperialUnit, tempMetricUnit)
    except Exception as e:
        logger.error("Error getting current outdoor temperature using key " + wundergroundApiKey + " and url " + url)
        logger.exception(e)
        return None

def create_datafile_if_needed(fpath):
    try:
        with open(fpath) as f: pass
    except IOError as e:
        with open(fpath, 'a') as f:
            f.write(first_commented_line + "\n")
            f.close()

def get_last_runtime(filename):
    try:
        with open(filename, 'rb') as csvfile:
            lines = tail(csvfile)
            return Runtime(lines[0].strip().split(',')[7].strip(), lines[0].strip().split(',')[6].strip())
    except Exception as e:
        return None

def get_previous_runtime(filename, now):
    if os.path.isfile(filename):
        return get_last_runtime(filename)
    else:
        # If the file does not exist, this is the first log for the day at 1am
        # Runtime at midnight was nada. zip. zilch.
        return Runtime(0, 0)

#Credit for the python tail method to S. Lott: http://stackoverflow.com/a/136368/215120
def tail(f, lines=1, _buffer=4098):
    """Tail a file and get X lines from the end"""
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # we found enough lines, get out
        if len(lines_found) > lines:
            break

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]

def dump_data (tstat, filePrefix, key, url, now, email, nickname, html):
    # Get Date and Time in pretty formats for printing
    dateString = convert_date_to_str_YYYYMMDD_with_slash(now)
    timeString = convert_date_to_str_HHMM_with_colon(now)

    # Get the outdoor temperature from weather underground
    outdoorTemperature = None
    if key is not None:
        outdoorTemperature = get_outdoor_temperature_right_now(key, url)

    # Poll the 3m50 for data
    indoorTemperature = tstat.getCurrentIndoorTemperature()
    desiredTemperature = tstat.getCurrentSetTemperature()
    currentRuntime = tstat.getCurrentRuntime(now)
    mode = tstat.getMode()

    # Poll stateful file for previous data
    previousRuntime = None
    if filePrefix is not None:
        filename = get_current_datafile(filePrefix, now)
        previousRuntime = get_previous_runtime(filename, now)

    # Temp diff is calculated a little differently since we want to get a sign to indicate +/-
    if outdoorTemperature is None:
        tempDiff = '--'
    else:
        tempDiff = '{:+}'.format(outdoorTemperature.tempImperialUnit - desiredTemperature)

    csvLine = '{:>12}'.format(dateString + ",") + \
              '{:>12}'.format(timeString + ",") + \
              '{:>12}'.format(str(outdoorTemperature.tempImperialUnit) + "," if outdoorTemperature is not None else "--,") + \
              '{:>12}'.format(str(desiredTemperature) + "," if desiredTemperature is not None else "--,") + \
              '{:>12}'.format(str(indoorTemperature) + "," if indoorTemperature is not None else "--,") + \
              '{:>12}'.format(tempDiff + ",") + \
              '{:>12}'.format(str(currentRuntime.heatRuntime) + "," if currentRuntime is not None else "--,") + \
              '{:>12}'.format(str(currentRuntime.coolRuntime) + ","  if currentRuntime is not None else "--,") + \
              '{:>12}'.format(str(currentRuntime.heatRuntime - previousRuntime.heatRuntime) + "," if previousRuntime is not None else "--,") + \
              '{:>12}'.format(str(currentRuntime.coolRuntime - previousRuntime.coolRuntime) + "," if previousRuntime is not None else "--,") +\
              '{:>12}'.format(mode + ",") 

    # If a file is specified, we dump the data to the file
    if filePrefix is not None:
        # Dump data to data file
        create_datafile_if_needed(filename)
        with open(filename, "a") as myfile:
            myfile.write(csvLine + "\n")
    else:
        # No stateful data file, just output current stats to STDOUT
        logger.info(first_commented_line)
        logger.info(csvLine)
        if email:
            if nickname is not None:
                name = str(nickname)
            else:
                name = str(tstat)
            summary = name + ': Heat runtime: ' + convertMinutesToHHMM(currentRuntime.heatRuntime) + ", Cool runtime: " + convertMinutesToHHMM (currentRuntime.coolRuntime) + " on " + dateString + " at " + timeString
            message = create_email("rouble@gmail.com", email, summary, first_commented_line + "\n" + csvLine, html)
            send_email(email, message)

def create_email (fromH, to, subject, body, html):
    email = "From: " + fromH + "\n"
    email += "Subject: " + subject + "\n"
    if body: 
        if html:
            email += "MIME-Version: 1.0\n"
            email += "Content-Type: text/html\n"
            email += get_html_body(body)
        else:
            email += body
    return email

# End users may have to modify this method and customize it to send emails
# from their systems
def send_email (to, body):
    try:
        # Use the system command to send out the email
        os.system('echo -e \"' + body + '\" | /usr/sbin/sendmail -t ' + to)
    except Exception as e:
        logger.exception(e)
        logger.error("Error sending email to: " + email)

def get_html_body (body):
    html = "<html>\n<body>\n<pre>\n"
    html += body
    html += "\n</pre>\n</body>\n</html>"
    return html

def report (nickname, tstat, filePrefix, email, now, hour, html, subject):
    if nickname is not None:
        name = str(nickname)
    else:
        name = str(tstat)

    yesterdayDate = convert_date_to_str_YYYYMMDD_with_slash(now.today() - timedelta(1))
    if now.hour == 0 and now.minute <= minuteOffset:
        date = yesterdayDate
    else:
        date = convert_date_to_str_YYYYMMDD_with_slash(now.today())

    current_data_file = get_current_datafile(filePrefix, now)
    yesterdays_data_file = get_yesterdays_datafile(filePrefix, now)

    totalHeatRuntime = 0
    totalCoolRuntime = 0

    rt = get_last_runtime(current_data_file)
    if rt is not None:
        totalHeatRuntime += rt.heatRuntime
        totalCoolRuntime += rt.coolRuntime
        todaySummary = name + ': Heat runtime: ' + convertMinutesToHHMM(rt.heatRuntime) + ", Cool runtime: " + convertMinutesToHHMM (rt.coolRuntime) + " on " + date
    else:
        todaySummary = name + ': error getting last runtime.' 

    yrt = get_last_runtime(yesterdays_data_file)
    if yrt is not None:
        totalHeatRuntime += yrt.heatRuntime
        totalCoolRuntime += yrt.coolRuntime
        yesterdaySummary = name + ': Heat runtime: ' + convertMinutesToHHMM(yrt.heatRuntime) + ", Cool runtime: " + convertMinutesToHHMM (yrt.coolRuntime) + " on " + yesterdayDate
    else:
        yesterdaySummary = name + ': No data to get yesterdays summary.'     

    totalSummary = name + ': Heat runtime: ' + convertMinutesToHHMM(totalHeatRuntime) + ", Cool runtime: " + convertMinutesToHHMM (totalCoolRuntime) + " on " + date

    body = "Yesterday:\n" + yesterdaySummary + "\n" + get_file_as_string(yesterdays_data_file) + "\n\n" + "Today:\n" + todaySummary + "\n" + get_file_as_string(current_data_file)

    # Print report to STDOUT
    logger.info(todaySummary)
    logger.info(body)

    if email is not None:
        if hour is None or (now.hour == hour and now.minute <= minuteOffset):
            summary = yesterdaySummary
            if (subject == "yesterdays"):
                summary = yesterdaySummary
            elif (subject == "todays"):
                summary = todaySummary
            elif (subject == "total"):
                summary = totalSummary
            message = create_email("rouble@gmail.com", email, summary, body, html)
            send_email(email, message)

def report_failure (nickname, tstat, email):
    if nickname is not None:
        # We use a more specific name on failures.
        name = str(nickname) + "(" + str(tstat) + ")"
    else:
        name = str(tstat)

    subject = name + " is incommunicado."

    # Print failure report to STDOUT
    logger.info(subject)

    if email is not None:
        message = create_email("rouble@gmail.com", email, subject, None, False)
        send_email(email, message)

def get_current_datafile(filePrefix, now):
    if now.hour == 0 and now.minute <= minuteOffset:
        # We write all data to files suffixed with _YYYY_MM_DD. So, every day's 
        # data is in a separate file.
        # 
        # At midnight, the current data file is yesterday's data file. This
        # is because the last reading for the day happens at midnight.
        suffix = convert_date_to_str_YYYYMMDD_with_underscore(now.today() - timedelta(1))
    else:
        suffix = convert_date_to_str_YYYYMMDD_with_underscore(now)
    return filePrefix + suffix + ".txt"

def get_yesterdays_datafile(filePrefix, now):
    if now.hour == 0 and now.minute <= minuteOffset:
        # We write all data to files suffixed with _YYYY_MM_DD. So, every day's 
        # data is in a separate file.  
        #
        # At midnight, the current data file is yesterday's data file. So,
        # at midnight, yesterday's datafile is day before yesterday's
        # data file.
        suffix = convert_date_to_str_YYYYMMDD_with_underscore(now.today() - timedelta(2))
    else:
        suffix = convert_date_to_str_YYYYMMDD_with_underscore(now.today() - timedelta(1))
    return filePrefix + suffix + ".txt"

def get_file_as_string (filename):
    try:
        with open (filename, "r") as myfile:
            return myfile.read()
    except Exception as e:
        return "" # If the file does not exist, return an empty string

def setupLogger (logfile, verbose):
    global logger

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    #create a steam handler
    stdouthandler = logging.StreamHandler(sys.stdout)
    if verbose:
        stdouthandler.setLevel(logging.DEBUG)
    else:
        stdouthandler.setLevel(logging.INFO)

    # create a logging format for stdout
    stdoutformatter = logging.Formatter('%(message)s')
    stdouthandler.setFormatter(stdoutformatter)

    # add the stdout handler to the logger
    logger.addHandler(stdouthandler)

    if logfile is not None:
        # create a file handler
        # We rotate the log file when it hits 2MB, and we save at most 3 log
        # files, so 6MB of total log data.
        filehandler = logging.handlers.RotatingFileHandler(logfile, maxBytes=2097152, backupCount=3)
        if verbose:
            filehandler.setLevel(logging.DEBUG)
        else:
            filehandler.setLevel(logging.INFO)

        # create a logging format for the log file
        formatter = logging.Formatter('%(asctime)s - %(thread)d - %(message)s')
        filehandler.setFormatter(formatter)

        # add the file handler to the logger
        logger.addHandler(filehandler)

def get_absolute_path (path):
    if path is None:
        return path
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))

# int main(int argc, char *argv[]);
def crux ():
    now = datetime.now() #Get current runtime. This is used consistently throughout script.

    #Setup argparse
    parser = argparse.ArgumentParser(description='Dumps the date, time, outdoor temperature, desired indoor temperature, actual indoor temperature, heat runtime, cool runtime to the specified file in csv format.')
    summaryForSubject = ["yesterdays", "todays", "total"]
    parser.add_argument('-t', '--tstat', help='Thermostat hostname or IP Address', required=True)
    parser.add_argument('-k', '--key', help='Weather Underground Key')
    parser.add_argument('-u', '--url', help='Wunderground URL Suffix for your city (Default: \'/q/NC/Cary.json\')', default='/q/NC/Cary.json')
    parser.add_argument('-f', '--fileprefix', help='File to store CSV results in.  Note, script will attach a suffix of _YYYY_MM_DD.txt.')
    parser.add_argument('-e', '--email', help='Email address to send report')
    parser.add_argument('-n', '--nickname', help='Name for your thermostat for your emailed report')
    parser.add_argument('-r', '--hour', help="If hour is specified, we only email a report at specified time", type=int, choices=xrange(0, 24), default=None)
    parser.add_argument('-m', '--nohtml', help="Send email in text format", action="store_true", default=False)
    parser.add_argument('-s', '--subject', help="What usage summary to show in email subject", choices=summaryForSubject, default='yesterdays')
    parser.add_argument('-l', '--logfile', help="Logging file", action="store", default=None)
    parser.add_argument('-v', '--verbose', help="Enable verbose debugs", action="store_true", default=False)
    parser.add_argument('-y', '--sync', help="Syncronize thermostat's time with client machine", action="store_true", default=False)

    # Parse arguments
    args = vars(parser.parse_args())

    # Set variables 
    logfile = get_absolute_path(args['logfile'])
    nickname = args['nickname']
    tstat = args['tstat']
    email = args['email']
    verbose = args['verbose']
    key = args['key']
    url = args['url']
    fileprefix = get_absolute_path(args['fileprefix'])
    hour = args['hour']
    html = not args['nohtml']
    subject = args['subject']
    sync = args['sync']

    setupLogger (logfile, verbose)

    # Initialize the thermostat
    thermostat = Thermostat(tstat)

    # Test if the thermostat is up
    if thermostat.isUp() == False:
        # Send failure email
        report_failure(nickname, tstat, email)
        sys.exit(1)

    # Collect current data from 3m50 and dump it to the file
    dump_data(thermostat, fileprefix, key, url, now, email, nickname, html)

    # Print report to STDOUT and also email if necessary
    if fileprefix is not None:
        report(nickname, tstat, fileprefix, email, now, hour, html, subject)
    #else: dump_data takes care of sending an email if there are no stateful files.

    if sync:
        thermostat.syncTime()

if __name__ == "__main__":  crux()
