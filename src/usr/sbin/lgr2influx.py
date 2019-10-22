#!/usr/bin/env python3
#
# LGR to Influxdb daemon : listen for data from Los Gatos N2O/CO analyzer on usb
# serial port and send to localhost Influxdb + Grafana setup.
#
# Patrick O'Keeffe
# Washington State University

import serial
from time import sleep
from datetime import datetime, timezone, timedelta
from influxdb import InfluxDBClient

# To see data messages in logs, set True
DEBUG = False

# Serial port details
SERIAL_PORT = '/dev/ttyUSB0'
SERIAL_BAUD = 115200
SERIAL_BYTE = 8
SERIAL_PARITY = 'N'
SERIAL_STOP = 1
SERIAL_TIMEOUT = 5 #seconds

# Influx DB parameters
INFLUX_HOST = '127.0.0.1'
INFLUX_PORT = 8086
INFLUX_USER = 'lgr'
INFLUX_PASS = 'influxuserpassword'
INFLUX_DB = 'losgatosn2oco'

# LGR data output configuration
LGR_SERIALNO = "13-0199"  # string serial number, nn-nnnn
LGR_DATEFMT = "%m/%d/%y"  # mm/dd/yy, the 'American' default style
LGR_TIMEZONE = -8         # offset from UTC in hours, HINT: not posix inverted
LGR_COLUMNS = ["Time",
                "CO_ppm",
                "CO_ppm_se",
                "N2O_ppm",
                "N2O_ppm_se",
                "H2O_ppm",
                "H2O_ppm_se",
                "CO_dry_ppm",
                "CO_dry_ppm_se",
                "N2O_dry_ppm",
                "N2O_dry_ppm_se",
                "GasP_torr",
                "GasP_torr_se",
                "GasT_C",
                "GasT_C_se",
                "AmbT_C",
                "AmbT_C_se",
                "LTC0_v",
                "LTC0_v_se",
                "AIN5",
                "AIN5_se",
                "DetOff",
                "DetOff_se",
                "Fit_Flag"]




def parse_lgr_timestamp(date_str, date_fmt):
    """Convert LGR time, assumed American format, into InfluxDB ns timestamp"""
    posix_time = datetime.strptime(date_str, date_fmt+" %H:%M:%S.%f").replace(
                    tzinfo=timezone(timedelta(hours=LGR_TIMEZONE))).timestamp()
    return int(posix_time * 1e9)


def build_influx_report(data):
    """Construct influxdb line protocol message from LGR data list"""
    prefix = "lgr,serialno={}".format(LGR_SERIALNO)
    timestamp = parse_lgr_timestamp(data[0], LGR_DATEFMT)
    vals = []
    for i in range(1, len(data)):
        vals.append("{}={}".format(LGR_COLUMNS[i], float(data[i])))
    return "{0} {1} {2:.0f}".format(prefix, ",".join(vals), timestamp)



def main():
    import sys
    print("Starting {}...".format(sys.argv[0]))

    print("Opening influxdb database {} on {}:{} using login {}:<REDACTED>".
            format(INFLUX_DB, INFLUX_HOST, INFLUX_PORT, INFLUX_USER))
    db = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT,
                        username=INFLUX_USER, password=INFLUX_PASS,
                        database=INFLUX_DB)
    print("Connected. Database version is {}".format( db.ping() ))


    with serial.Serial() as ser:
        ser.port=SERIAL_PORT
        ser.baudrate=SERIAL_BAUD
        ser.byte=SERIAL_BYTE
        ser.parity=SERIAL_PARITY
        ser.stopbits=SERIAL_STOP
        ser.timeout=SERIAL_TIMEOUT
        print("Opening serial port {} using {}/{}{}{}/{}s timeout...".
                format(SERIAL_PORT, SERIAL_BAUD, SERIAL_BYTE, SERIAL_PARITY,
                       SERIAL_STOP, SERIAL_TIMEOUT))
        ser.open()
        ser.flush()
        print("Connected and reporting data...")
        if not DEBUG:
            print("To view data messages, try the influxdb logs: `sudo journalctl -f -u influxdb`")

        while True:
            try:
                rec = ser.readline()
                if DEBUG:
                    print("Received serial record:\n{}".format(rec.decode()))

                data = [v.decode().strip() for v in rec.split(b',')]
                assert len(data) == len(LGR_COLUMNS)

                msmt = build_influx_report(data)
                if DEBUG:
                    print("Sending measurement to influxdb:\n{}".format(msmt))
                db.write(msmt, params={'db': INFLUX_DB}, protocol='line')

                sleep(0.050)

            except (KeyboardInterrupt, SystemExit):
                print("Received exit signal. Closing serial port...")
                ser.close()
                print("Exiting...")
                raise
            except AssertionError:
                if DEBUG:
                    print("Received partial/malformed serial record. Skipping...")
                sleep(0.050)
                continue
            except Exception as e:
                import traceback
                print("Avoiding potentially fatal error:\n{}".format(traceback.format_exc()))
                sleep(5) # avoid flooding logs
                continue


if __name__=="__main__":
    main()


