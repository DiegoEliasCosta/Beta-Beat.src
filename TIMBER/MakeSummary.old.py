
import datetime, time, os
now = datetime.datetime.now()
day= now.strftime("%Y-%m-%d")
hour=now.strftime("%H:%M:%S.000")


#   
#    Quick use to get last 1 hour every 1200 seconds in the local path:
#    python MakeSummary.py -l 1 -s 1200 -o./
#    (outputs 3 files, quad* tune* IntSi* with all the logged data)

from optparse import OptionParser
parser = OptionParser()

parser.add_option("-l", "--last",
                help="Last N hours. Use either -l or -t. Priority is given to -l",
                metavar="HOURS", default="6", dest="lastHours")

parser.add_option("-t", "--times",
                help="### NOT yet ready ###  Day and start and end times separated by , ex: 00:00:00.000,01:01:00.000. User either -l or -t",
                metavar="TIMES", default="0", dest="time")

parser.add_option("-s", "--seconds",
                help="Every How many seconds, default 10",
                metavar="SECS", default="10", dest="seconds")


parser.add_option("-o", "--output",
                help="Output path",
                metavar="OUT", default="./", dest="output")



parser.add_option("-c", "--conffile",
                help="Configuration file, normally just use default",
                metavar="CONFFILE", default="/afs/cern.ch/eng/sl/lintrack/Beta-Beat.src/TIMBER/ldb.conf", dest="conffile")


parser.add_option("-e", "--executable",
                help="Executable, normally just use default",
                metavar="EXE", default="/afs/cern.ch/group/si/slap/bin/cern-ldb", dest="exe")


(options, args) = parser.parse_args()



startfrom= now  + datetime.timedelta(hours=-int(options.lastHours))

startday = startfrom.strftime("%Y-%m-%d")
starthour = startfrom.strftime("%H:%M:%S.000")



print "From", startday, starthour, "TO", day, hour, "IN steps of ", options.seconds, "seconds"



QuadString="RPHE.UA23.RQD.A12:I_MEAS,RPHE.UA23.RQF.A12:I_MEAS,RPHE.UA27.RQD.A23:I_MEAS,RPHE.UA27.RQF.A23:I_MEAS,RPHE.UA43.RQD.A34:I_MEAS,RPHE.UA43.RQF.A34:I_MEAS,RPHE.UA47.RQD.A45:I_MEAS,RPHE.UA47.RQF.A45:I_MEAS,RPHE.UA63.RQD.A56:I_MEAS,RPHE.UA63.RQF.A56:I_MEAS,RPHE.UA67.RQD.A67:I_MEAS,RPHE.UA67.RQF.A67:I_MEAS,RPHE.UA83.RQD.A78:I_MEAS,RPHE.UA83.RQF.A78:I_MEAS,RPHE.UA87.RQD.A81:I_MEAS,RPHE.UA87.RQF.A81:I_MEAS,RPHFC.UA23.RQX.L2:I_MEAS,RPHFC.UA27.RQX.R2:I_MEAS,RPHFC.UA83.RQX.L8:I_MEAS,RPHFC.UA87.RQX.R8:I_MEAS,RPHFC.UJ14.RQX.L1:I_MEAS,RPHFC.UJ16.RQX.R1:I_MEAS,RPHFC.UJ56.RQX.R5:I_MEAS,RPHFC.USC55.RQX.L5:I_MEAS,RPHGA.RR13.RQ10.L1B1:I_MEAS,RPHGA.RR13.RQ10.L1B2:I_MEAS,RPHGA.RR13.RQ7.L1B1:I_MEAS,RPHGA.RR13.RQ7.L1B2:I_MEAS,RPHGA.RR13.RQ8.L1B1:I_MEAS,RPHGA.RR13.RQ8.L1B2:I_MEAS,RPHGA.RR13.RQ9.L1B1:I_MEAS,RPHGA.RR13.RQ9.L1B2:I_MEAS,RPHGA.RR17.RQ10.R1B1:I_MEAS,RPHGA.RR17.RQ10.R1B2:I_MEAS,RPHGA.RR17.RQ7.R1B1:I_MEAS,RPHGA.RR17.RQ7.R1B2:I_MEAS,RPHGA.RR17.RQ8.R1B1:I_MEAS,RPHGA.RR17.RQ8.R1B2:I_MEAS,RPHGA.RR17.RQ9.R1B1:I_MEAS,RPHGA.RR17.RQ9.R1B2:I_MEAS,RPHGA.RR53.RQ10.L5B1:I_MEAS,RPHGA.RR53.RQ10.L5B2:I_MEAS,RPHGA.RR53.RQ7.L5B1:I_MEAS,RPHGA.RR53.RQ7.L5B2:I_MEAS,RPHGA.RR53.RQ8.L5B1:I_MEAS,RPHGA.RR53.RQ8.L5B2:I_MEAS,RPHGA.RR53.RQ9.L5B1:I_MEAS,RPHGA.RR53.RQ9.L5B2:I_MEAS,RPHGA.RR57.RQ10.R5B1:I_MEAS,RPHGA.RR57.RQ10.R5B2:I_MEAS,RPHGA.RR57.RQ7.R5B1:I_MEAS,RPHGA.RR57.RQ7.R5B2:I_MEAS,RPHGA.RR57.RQ8.R5B1:I_MEAS,RPHGA.RR57.RQ8.R5B2:I_MEAS,RPHGA.RR57.RQ9.R5B1:I_MEAS,RPHGA.RR57.RQ9.R5B2:I_MEAS,RPHGA.UA23.RQ10.L2B1:I_MEAS,RPHGA.UA23.RQ10.L2B2:I_MEAS,RPHGA.UA23.RQ7.L2B1:I_MEAS,RPHGA.UA23.RQ7.L2B2:I_MEAS,RPHGA.UA23.RQ8.L2B1:I_MEAS,RPHGA.UA23.RQ8.L2B2:I_MEAS,RPHGA.UA23.RQ9.L2B1:I_MEAS,RPHGA.UA23.RQ9.L2B2:I_MEAS,RPHGA.UA27.RQ10.R2B1:I_MEAS,RPHGA.UA27.RQ10.R2B2:I_MEAS,RPHGA.UA27.RQ7.R2B1:I_MEAS,RPHGA.UA27.RQ7.R2B2:I_MEAS,RPHGA.UA27.RQ8.R2B1:I_MEAS,RPHGA.UA27.RQ8.R2B2:I_MEAS,RPHGA.UA27.RQ9.R2B1:I_MEAS,RPHGA.UA27.RQ9.R2B2:I_MEAS,RPHGA.UA43.RQ10.L4B1:I_MEAS,RPHGA.UA43.RQ10.L4B2:I_MEAS,RPHGA.UA43.RQ7.L4B1:I_MEAS,RPHGA.UA43.RQ7.L4B2:I_MEAS,RPHGA.UA43.RQ8.L4B1:I_MEAS,RPHGA.UA43.RQ8.L4B2:I_MEAS,RPHGA.UA43.RQ9.L4B1:I_MEAS,RPHGA.UA43.RQ9.L4B2:I_MEAS,RPHGA.UA47.RQ10.R4B1:I_MEAS,RPHGA.UA47.RQ10.R4B2:I_MEAS,RPHGA.UA47.RQ7.R4B1:I_MEAS,RPHGA.UA47.RQ7.R4B2:I_MEAS,RPHGA.UA47.RQ8.R4B1:I_MEAS,RPHGA.UA47.RQ8.R4B2:I_MEAS,RPHGA.UA47.RQ9.R4B1:I_MEAS,RPHGA.UA47.RQ9.R4B2:I_MEAS,RPHGA.UA83.RQ10.L8B1:I_MEAS,RPHGA.UA83.RQ10.L8B2:I_MEAS,RPHGA.UA83.RQ7.L8B1:I_MEAS,RPHGA.UA83.RQ7.L8B2:I_MEAS,RPHGA.UA83.RQ8.L8B1:I_MEAS,RPHGA.UA83.RQ8.L8B2:I_MEAS,RPHGA.UA83.RQ9.L8B1:I_MEAS,RPHGA.UA83.RQ9.L8B2:I_MEAS,RPHGA.UA87.RQ10.R8B1:I_MEAS,RPHGA.UA87.RQ10.R8B2:I_MEAS,RPHGA.UA87.RQ7.R8B1:I_MEAS,RPHGA.UA87.RQ7.R8B2:I_MEAS,RPHGA.UA87.RQ8.R8B1:I_MEAS,RPHGA.UA87.RQ8.R8B2:I_MEAS,RPHGA.UA87.RQ9.R8B1:I_MEAS,RPHGA.UA87.RQ9.R8B2:I_MEAS,RPHGA.UJ63.RQ10.L6B1:I_MEAS,RPHGA.UJ63.RQ10.L6B2:I_MEAS,RPHGA.UJ63.RQ8.L6B1:I_MEAS,RPHGA.UJ63.RQ8.L6B2:I_MEAS,RPHGA.UJ63.RQ9.L6B1:I_MEAS,RPHGA.UJ63.RQ9.L6B2:I_MEAS,RPHGA.UJ67.RQ10.R6B1:I_MEAS,RPHGA.UJ67.RQ10.R6B2:I_MEAS,RPHGA.UJ67.RQ8.R6B1:I_MEAS,RPHGA.UJ67.RQ8.R6B2:I_MEAS,RPHGA.UJ67.RQ9.R6B1:I_MEAS,RPHGA.UJ67.RQ9.R6B2:I_MEAS,RPHGB.RR13.RQ5.L1B1:I_MEAS,RPHGB.RR13.RQ5.L1B2:I_MEAS,RPHGB.RR13.RQ6.L1B1:I_MEAS,RPHGB.RR13.RQ6.L1B2:I_MEAS,RPHGB.RR17.RQ5.R1B1:I_MEAS,RPHGB.RR17.RQ5.R1B2:I_MEAS,RPHGB.RR17.RQ6.R1B1:I_MEAS,RPHGB.RR17.RQ6.R1B2:I_MEAS,RPHGB.RR53.RQ5.L5B1:I_MEAS,RPHGB.RR53.RQ5.L5B2:I_MEAS,RPHGB.RR53.RQ6.L5B1:I_MEAS,RPHGB.RR53.RQ6.L5B2:I_MEAS,RPHGB.RR57.RQ5.R5B1:I_MEAS,RPHGB.RR57.RQ5.R5B2:I_MEAS,RPHGB.RR57.RQ6.R5B1:I_MEAS,RPHGB.RR57.RQ6.R5B2:I_MEAS,RPHGB.UA23.RQ6.L2B1:I_MEAS,RPHGB.UA23.RQ6.L2B2:I_MEAS,RPHGB.UA27.RQ5.R2B1:I_MEAS,RPHGB.UA27.RQ5.R2B2:I_MEAS,RPHGB.UA27.RQ6.R2B1:I_MEAS,RPHGB.UA27.RQ6.R2B2:I_MEAS,RPHGB.UA83.RQ5.L8B1:I_MEAS,RPHGB.UA83.RQ5.L8B2:I_MEAS,RPHGB.UA83.RQ6.L8B1:I_MEAS,RPHGB.UA83.RQ6.L8B2:I_MEAS,RPHGB.UA87.RQ6.R8B1:I_MEAS,RPHGB.UA87.RQ6.R8B2:I_MEAS,RPHGC.UA23.RTQX2.L2:I_MEAS,RPHGC.UA27.RTQX2.R2:I_MEAS,RPHGC.UA83.RTQX2.L8:I_MEAS,RPHGC.UA87.RTQX2.R8:I_MEAS,RPHGC.UJ14.RTQX2.L1:I_MEAS,RPHGC.UJ16.RTQX2.R1:I_MEAS,RPHGC.UJ56.RTQX2.R5:I_MEAS,RPHGC.USC55.RTQX2.L5:I_MEAS,RPHH.RR13.RQ4.L1B1:I_MEAS,RPHH.RR13.RQ4.L1B2:I_MEAS,RPHH.RR17.RQ4.R1B1:I_MEAS,RPHH.RR17.RQ4.R1B2:I_MEAS,RPHH.RR53.RQ4.L5B1:I_MEAS,RPHH.RR53.RQ4.L5B2:I_MEAS,RPHH.RR57.RQ4.R5B1:I_MEAS,RPHH.RR57.RQ4.R5B2:I_MEAS,RPHH.UA23.RQ4.L2B1:I_MEAS,RPHH.UA23.RQ4.L2B2:I_MEAS,RPHH.UA23.RQ5.L2B1:I_MEAS,RPHH.UA23.RQ5.L2B2:I_MEAS,RPHH.UA27.RQ4.R2B1:I_MEAS,RPHH.UA27.RQ4.R2B2:I_MEAS,RPHH.UA43.RQ5.L4B1:I_MEAS,RPHH.UA43.RQ5.L4B2:I_MEAS,RPHH.UA43.RQ6.L4B1:I_MEAS,RPHH.UA43.RQ6.L4B2:I_MEAS,RPHH.UA47.RQ5.R4B1:I_MEAS,RPHH.UA47.RQ5.R4B2:I_MEAS,RPHH.UA47.RQ6.R4B1:I_MEAS,RPHH.UA47.RQ6.R4B2:I_MEAS,RPHH.UA63.RQ4.L6B1:I_MEAS,RPHH.UA63.RQ4.L6B2:I_MEAS,RPHH.UA63.RQ5.L6B1:I_MEAS,RPHH.UA63.RQ5.L6B2:I_MEAS,RPHH.UA67.RQ4.R6B1:I_MEAS,RPHH.UA67.RQ4.R6B2:I_MEAS,RPHH.UA67.RQ5.R6B1:I_MEAS,RPHH.UA67.RQ5.R6B2:I_MEAS,RPHH.UA83.RQ4.L8B1:I_MEAS,RPHH.UA83.RQ4.L8B2:I_MEAS,RPHH.UA87.RQ4.R8B1:I_MEAS,RPHH.UA87.RQ4.R8B2:I_MEAS,RPHH.UA87.RQ5.R8B1:I_MEAS,RPHH.UA87.RQ5.R8B2:I_MEAS,RPMBA.RR13.RQS.A81B1:I_MEAS,RPMBA.RR13.RQS.L1B2:I_MEAS,RPMBA.RR13.RQT12.L1B1:I_MEAS,RPMBA.RR13.RQT12.L1B2:I_MEAS,RPMBA.RR13.RQT13.L1B1:I_MEAS,RPMBA.RR13.RQT13.L1B2:I_MEAS,RPMBA.RR13.RQTL11.L1B1:I_MEAS,RPMBA.RR13.RQTL11.L1B2:I_MEAS,RPMBA.RR17.RQS.A12B2:I_MEAS,RPMBA.RR17.RQS.R1B1:I_MEAS,RPMBA.RR17.RQT12.R1B1:I_MEAS,RPMBA.RR17.RQT12.R1B2:I_MEAS,RPMBA.RR17.RQT13.R1B1:I_MEAS,RPMBA.RR17.RQT13.R1B2:I_MEAS,RPMBA.RR17.RQTL11.R1B1:I_MEAS,RPMBA.RR17.RQTL11.R1B2:I_MEAS,RPMBA.RR53.RQS.A45B1:I_MEAS,RPMBA.RR53.RQS.L5B2:I_MEAS,RPMBA.RR53.RQT12.L5B1:I_MEAS,RPMBA.RR53.RQT12.L5B2:I_MEAS,RPMBA.RR53.RQT13.L5B1:I_MEAS,RPMBA.RR53.RQT13.L5B2:I_MEAS,RPMBA.RR53.RQTL11.L5B1:I_MEAS,RPMBA.RR53.RQTL11.L5B2:I_MEAS,RPMBA.RR57.RQS.A56B2:I_MEAS,RPMBA.RR57.RQS.R5B1:I_MEAS,RPMBA.RR57.RQT12.R5B1:I_MEAS,RPMBA.RR57.RQT12.R5B2:I_MEAS,RPMBA.RR57.RQT13.R5B1:I_MEAS,RPMBA.RR57.RQT13.R5B2:I_MEAS,RPMBA.RR57.RQTL11.R5B1:I_MEAS,RPMBA.RR57.RQTL11.R5B2:I_MEAS,RPMBA.RR73.RQS.A67B1:I_MEAS,RPMBA.RR73.RQS.L7B2:I_MEAS,RPMBA.RR73.RQT12.L7B1:I_MEAS,RPMBA.RR73.RQT12.L7B2:I_MEAS,RPMBA.RR73.RQT13.L7B1:I_MEAS,RPMBA.RR73.RQT13.L7B2:I_MEAS,RPMBA.RR73.RQTL10.L7B1:I_MEAS,RPMBA.RR73.RQTL10.L7B2:I_MEAS,RPMBA.RR73.RQTL11.L7B1:I_MEAS,RPMBA.RR73.RQTL11.L7B2:I_MEAS,RPMBA.RR73.RQTL7.L7B1:I_MEAS,RPMBA.RR73.RQTL7.L7B2:I_MEAS,RPMBA.RR73.RQTL8.L7B1:I_MEAS,RPMBA.RR73.RQTL8.L7B2:I_MEAS,RPMBA.RR77.RQS.A78B2:I_MEAS,RPMBA.RR77.RQS.R7B1:I_MEAS,RPMBA.RR77.RQT12.R7B1:I_MEAS,RPMBA.RR77.RQT12.R7B2:I_MEAS,RPMBA.RR77.RQT13.R7B1:I_MEAS,RPMBA.RR77.RQT13.R7B2:I_MEAS,RPMBA.RR77.RQTL10.R7B1:I_MEAS,RPMBA.RR77.RQTL10.R7B2:I_MEAS,RPMBA.RR77.RQTL11.R7B1:I_MEAS,RPMBA.RR77.RQTL11.R7B2:I_MEAS,RPMBA.RR77.RQTL7.R7B1:I_MEAS,RPMBA.RR77.RQTL7.R7B2:I_MEAS,RPMBA.RR77.RQTL8.R7B1:I_MEAS,RPMBA.RR77.RQTL8.R7B2:I_MEAS,RPMBA.UA23.RQS.L2B1:I_MEAS,RPMBA.UA23.RQT12.L2B1:I_MEAS,RPMBA.UA23.RQT12.L2B2:I_MEAS,RPMBA.UA23.RQT13.L2B1:I_MEAS,RPMBA.UA23.RQT13.L2B2:I_MEAS,RPMBA.UA23.RQTL11.L2B1:I_MEAS,RPMBA.UA23.RQTL11.L2B2:I_MEAS,RPMBA.UA27.RQS.R2B2:I_MEAS,RPMBA.UA27.RQT12.R2B1:I_MEAS,RPMBA.UA27.RQT12.R2B2:I_MEAS,RPMBA.UA27.RQT13.R2B1:I_MEAS,RPMBA.UA27.RQT13.R2B2:I_MEAS,RPMBA.UA27.RQTL11.R2B1:I_MEAS,RPMBA.UA27.RQTL11.R2B2:I_MEAS,RPMBA.UA43.RQS.L4B1:I_MEAS,RPMBA.UA43.RQT12.L4B1:I_MEAS,RPMBA.UA43.RQT12.L4B2:I_MEAS,RPMBA.UA43.RQT13.L4B1:I_MEAS,RPMBA.UA43.RQT13.L4B2:I_MEAS,RPMBA.UA43.RQTL11.L4B1:I_MEAS,RPMBA.UA43.RQTL11.L4B2:I_MEAS,RPMBA.UA47.RQS.R4B2:I_MEAS,RPMBA.UA47.RQT12.R4B1:I_MEAS,RPMBA.UA47.RQT12.R4B2:I_MEAS,RPMBA.UA47.RQT13.R4B1:I_MEAS,RPMBA.UA47.RQT13.R4B2:I_MEAS,RPMBA.UA47.RQTL11.R4B1:I_MEAS,RPMBA.UA47.RQTL11.R4B2:I_MEAS,RPMBA.UA63.RQS.L6B1:I_MEAS,RPMBA.UA63.RQT12.L6B1:I_MEAS,RPMBA.UA63.RQT12.L6B2:I_MEAS,RPMBA.UA63.RQT13.L6B1:I_MEAS,RPMBA.UA63.RQT13.L6B2:I_MEAS,RPMBA.UA63.RQTL11.L6B1:I_MEAS,RPMBA.UA63.RQTL11.L6B2:I_MEAS,RPMBA.UA67.RQS.R6B2:I_MEAS,RPMBA.UA67.RQT12.R6B1:I_MEAS,RPMBA.UA67.RQT12.R6B2:I_MEAS,RPMBA.UA67.RQT13.R6B1:I_MEAS,RPMBA.UA67.RQT13.R6B2:I_MEAS,RPMBA.UA67.RQTL11.R6B1:I_MEAS,RPMBA.UA67.RQTL11.R6B2:I_MEAS,RPMBA.UA83.RQS.L8B1:I_MEAS,RPMBA.UA83.RQT12.L8B1:I_MEAS,RPMBA.UA83.RQT12.L8B2:I_MEAS,RPMBA.UA83.RQT13.L8B1:I_MEAS,RPMBA.UA83.RQT13.L8B2:I_MEAS,RPMBA.UA83.RQTL11.L8B1:I_MEAS,RPMBA.UA83.RQTL11.L8B2:I_MEAS,RPMBA.UA87.RQS.R8B2:I_MEAS,RPMBA.UA87.RQT12.R8B1:I_MEAS,RPMBA.UA87.RQT12.R8B2:I_MEAS,RPMBA.UA87.RQT13.R8B1:I_MEAS,RPMBA.UA87.RQT13.R8B2:I_MEAS,RPMBA.UA87.RQTL11.R8B1:I_MEAS,RPMBA.UA87.RQTL11.R8B2:I_MEAS,RPMBA.UJ33.RQS.A23B1:I_MEAS,RPMBA.UJ33.RQS.A34B2:I_MEAS,RPMBA.UJ33.RQS.L3B2:I_MEAS,RPMBA.UJ33.RQT12.L3B1:I_MEAS,RPMBA.UJ33.RQT12.L3B2:I_MEAS,RPMBA.UJ33.RQT12.R3B1:I_MEAS,RPMBA.UJ33.RQT12.R3B2:I_MEAS,RPMBA.UJ33.RQT13.L3B1:I_MEAS,RPMBA.UJ33.RQT13.L3B2:I_MEAS,RPMBA.UJ33.RQT13.R3B1:I_MEAS,RPMBA.UJ33.RQT13.R3B2:I_MEAS,RPMBA.UJ33.RQTL10.L3B1:I_MEAS,RPMBA.UJ33.RQTL10.L3B2:I_MEAS,RPMBA.UJ33.RQTL10.R3B1:I_MEAS,RPMBA.UJ33.RQTL10.R3B2:I_MEAS,RPMBA.UJ33.RQTL11.L3B1:I_MEAS,RPMBA.UJ33.RQTL11.L3B2:I_MEAS,RPMBA.UJ33.RQTL11.R3B1:I_MEAS,RPMBA.UJ33.RQTL11.R3B2:I_MEAS,RPMBA.UJ33.RQTL7.L3B1:I_MEAS,RPMBA.UJ33.RQTL7.L3B2:I_MEAS,RPMBA.UJ33.RQTL7.R3B1:I_MEAS,RPMBA.UJ33.RQTL7.R3B2:I_MEAS,RPMBA.UJ33.RQTL8.L3B1:I_MEAS,RPMBA.UJ33.RQTL8.L3B2:I_MEAS,RPMBA.UJ33.RQTL8.R3B1:I_MEAS,RPMBA.UJ33.RQTL8.R3B2:I_MEAS,RPMBB.RR73.RQ6.L7B1:I_MEAS,RPMBB.RR73.RQ6.L7B2:I_MEAS,RPMBB.RR73.RQTL9.L7B1:I_MEAS,RPMBB.RR73.RQTL9.L7B2:I_MEAS,RPMBB.RR77.RQ6.R7B1:I_MEAS,RPMBB.RR77.RQ6.R7B2:I_MEAS,RPMBB.RR77.RQTL9.R7B1:I_MEAS,RPMBB.RR77.RQTL9.R7B2:I_MEAS,RPMBB.UA23.RQSX3.L2:I_MEAS,RPMBB.UA23.RQTD.A12B1:I_MEAS,RPMBB.UA23.RQTD.A12B2:I_MEAS,RPMBB.UA23.RQTF.A12B1:I_MEAS,RPMBB.UA23.RQTF.A12B2:I_MEAS,RPMBB.UA27.RQSX3.R2:I_MEAS,RPMBB.UA27.RQTD.A23B1:I_MEAS,RPMBB.UA27.RQTD.A23B2:I_MEAS,RPMBB.UA27.RQTF.A23B1:I_MEAS,RPMBB.UA27.RQTF.A23B2:I_MEAS,RPMBB.UA43.RQTD.A34B1:I_MEAS,RPMBB.UA43.RQTD.A34B2:I_MEAS,RPMBB.UA43.RQTF.A34B1:I_MEAS,RPMBB.UA43.RQTF.A34B2:I_MEAS,RPMBB.UA47.RQTD.A45B1:I_MEAS,RPMBB.UA47.RQTD.A45B2:I_MEAS,RPMBB.UA47.RQTF.A45B1:I_MEAS,RPMBB.UA47.RQTF.A45B2:I_MEAS,RPMBB.UA63.RQTD.A56B1:I_MEAS,RPMBB.UA63.RQTD.A56B2:I_MEAS,RPMBB.UA63.RQTF.A56B1:I_MEAS,RPMBB.UA63.RQTF.A56B2:I_MEAS,RPMBB.UA67.RQTD.A67B1:I_MEAS,RPMBB.UA67.RQTD.A67B2:I_MEAS,RPMBB.UA67.RQTF.A67B1:I_MEAS,RPMBB.UA67.RQTF.A67B2:I_MEAS,RPMBB.UA83.RQSX3.L8:I_MEAS,RPMBB.UA83.RQTD.A78B1:I_MEAS,RPMBB.UA83.RQTD.A78B2:I_MEAS,RPMBB.UA83.RQTF.A78B1:I_MEAS,RPMBB.UA83.RQTF.A78B2:I_MEAS,RPMBB.UA87.RQSX3.R8:I_MEAS,RPMBB.UA87.RQTD.A81B1:I_MEAS,RPMBB.UA87.RQTD.A81B2:I_MEAS,RPMBB.UA87.RQTF.A81B1:I_MEAS,RPMBB.UA87.RQTF.A81B2:I_MEAS,RPMBB.UJ14.RQSX3.L1:I_MEAS,RPMBB.UJ16.RQSX3.R1:I_MEAS,RPMBB.UJ33.RQ6.L3B1:I_MEAS,RPMBB.UJ33.RQ6.L3B2:I_MEAS,RPMBB.UJ33.RQTL9.L3B1:I_MEAS,RPMBB.UJ33.RQTL9.L3B2:I_MEAS,RPMBB.UJ33.RQTL9.R3B1:I_MEAS,RPMBB.UJ33.RQTL9.R3B2:I_MEAS,RPMBB.UJ56.RQSX3.R5:I_MEAS,RPMBB.USC55.RQSX3.L5:I_MEAS,RPMBC.UA23.RTQX1.L2:I_MEAS,RPMBC.UA27.RTQX1.R2:I_MEAS,RPMBC.UA83.RTQX1.L8:I_MEAS,RPMBC.UA87.RTQX1.R8:I_MEAS,RPMBC.UJ14.RTQX1.L1:I_MEAS,RPMBC.UJ16.RTQX1.R1:I_MEAS,RPMBC.UJ56.RTQX1.R5:I_MEAS,RPMBC.USC55.RTQX1.L5:I_MEAS,RPMC.UJ33.RQ6.R3B1:I_MEAS,RPMC.UJ33.RQ6.R3B2:I_MEAS,RPMC.UJ33.RQT4.L3:I_MEAS,RPMC.UJ33.RQT4.R3:I_MEAS,RPMC.UJ33.RQT5.L3:I_MEAS,RPMC.UJ33.RQT5.R3:I_MEAS,RPMC.UJ76.RQT4.L7:I_MEAS,RPMC.UJ76.RQT4.R7:I_MEAS,RPMC.UJ76.RQT5.L7:I_MEAS,RPMC.UJ76.RQT5.R7:I_MEAS,RPTF.SR3.RQ4.LR3:I_MEAS,RPTF.SR3.RQ5.LR3:I_MEAS,RPTF.SR7.RQ4.LR7:I_MEAS,RPTF.SR7.RQ5.LR7:I_MEAS"


TuneString="LHC.BQBBQ.UA47.FFT1_B1:TUNE_H,LHC.BQBBQ.UA47.FFT1_B1:TUNE_V,LHC.BQBBQ.UA43.FFT1_B2:TUNE_H,LHC.BQBBQ.UA43.FFT1_B2:TUNE_V,LHC.BQBBQ.UA47.FFT1_B1:EIGEN_FREQ_1,LHC.BQBBQ.UA47.FFT1_B1:EIGEN_FREQ_2,LHC.BQBBQ.UA43.FFT1_B2:EIGEN_FREQ_1,LHC.BQBBQ.UA43.FFT1_B2:EIGEN_FREQ_2,RPHFC.UJ14.RQX.L1:I_MEAS,RPHFC.UJ16.RQX.R1:I_MEAS,RPHFC.UA23.RQX.L2:I_MEAS,RPHFC.UA27.RQX.R2:I_MEAS,RPHFC.USC55.RQX.L5:I_MEAS,RPHFC.UJ56.RQX.R5:I_MEAS,RPHFC.UA83.RQX.L8:I_MEAS,RPHFC.UA87.RQX.R8:I_MEAS"


IntensitiesAndSizes="LHC.BCTDC.A6R4.B1:BEAM_INTENSITY,LHC.BCTDC.A6R4.B2:BEAM_INTENSITY,LHC.BGIH.5L4.B1:BEAM_SIGMA,LHC.BGIH.5R4.B2:BEAM_SIGMA,LHC.BSRCTL.B1:CORR_SIGMA_H,LHC.BSRCTL.B1:CORR_SIGMA_V,LHC.BSRCTL.B2:CORR_SIGMA_H,LHC.BSRCTL.B2:CORR_SIGMA_V,LHC.BWS.5L4.B2V2:SIGMA_AVG_IN,LHC.BWS.5L4.B2V2:SIGMA_AVG_OUT,LHC.BWS.5L4.B2V1:SIGMA_AVG_IN,LHC.BWS.5L4.B2V1:SIGMA_AVG_OUT,LHC.BWS.5L4.B2H2:SIGMA_AVG_IN,LHC.BWS.5L4.B2H2:SIGMA_AVG_OUT,LHC.BWS.5L4.B2H1:SIGMA_AVG_IN,LHC.BWS.5L4.B2H1:SIGMA_AVG_OUT,LHC.BWS.5R4.B1V2:SIGMA_AVG_IN,LHC.BWS.5R4.B1V2:SIGMA_AVG_OUT,LHC.BWS.5R4.B1V1:SIGMA_AVG_IN,LHC.BWS.5R4.B1V1:SIGMA_AVG_OUT,LHC.BWS.5R4.B1H2:SIGMA_AVG_IN,LHC.BWS.5R4.B1H2:SIGMA_AVG_OUT,LHC.BWS.5R4.B1H1:SIGMA_AVG_IN,LHC.BWS.5R4.B1H1:SIGMA_AVG_OUT"



#First extract quads
outfile=options.output+"/quads."+startday+"_"+starthour[:-4]+"_"+hour[:-4]+".csv"
CommandString=options.exe+" -C "+options.conffile+" -vs \""+QuadString+"\""+" -t1 \""+startday+" "+starthour+"\" -t2 \""+day+" "+hour+"\" -sa REPEAT -ss "+options.seconds+" -si SECOND   -N "+outfile

os.system(CommandString)

#Extract tunes
outfile=options.output+"/tunes."+startday+"_"+starthour[:-4]+"_"+hour[:-4]+".csv"
CommandString=options.exe+" -C "+options.conffile+" -vs \""+TuneString+"\""+" -t1 \""+startday+" "+starthour+"\" -t2 \""+day+" "+hour+"\" -sa REPEAT -ss "+options.seconds+" -si SECOND   -N "+outfile


os.system(CommandString)

#Extract intensities and beam sizes
outfile=options.output+"/intSi."+startday+"_"+starthour[:-4]+"_"+hour[:-4]+".csv"
CommandString=options.exe+" -C "+options.conffile+" -vs \""+IntensitiesAndSizes+"\""+" -t1 \""+startday+" "+starthour+"\" -t2 \""+day+" "+hour+"\" -sa REPEAT -ss "+options.seconds+" -si SECOND   -N "+outfile


os.system(CommandString)

print "Total Vars in input=", len(IntensitiesAndSizes.split(","))+len(QuadString.split(","))+len(TuneString.split(","))
