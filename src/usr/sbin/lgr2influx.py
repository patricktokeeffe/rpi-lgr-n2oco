#!/usr/bin/env python3
#
# LGR to Influxdb daemon : listen for data from Los Gatos N2O/CO analyzer on usb
# serial port and send to localhost Influxdb + Grafana setup.
#
# Patrick O'Keeffe
# Washington State University

import serial
from datetime import datetime
from influxdb import InfluxDBClient

 
# Serial port details
SERIAL_PORT = '/dev/ttyUSB0'
SERIAL_BAUD = 115200
SERIAL_BYTE = 8
SERIAL_PARITY = 'N'
SERIAL_STOP = 1
SERIAL_TIMEOUT = 1 #seconds

# Influx DB parameters
INFLUX_HOST = '127.0.0.1'
INFLUX_PORT = 8086
INFLUX_USER = 'lgr'
INFLUX_PASS = 'influxuserpassword'
INFLUX_DB = 'lgrtest1'

# LGR data output configuration
LGR_DATEFMT = "%m/%d/%y"  # mm/dd/yy, the 'American' default style
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
    posix_time = datetime.strptime(date_str, date_fmt+" %H:%M:%S.%f").timestamp()
    return int(posix_time * 1e9)


def build_influx_report(data):
    """Construct influxdb line protocol message from LGR data list"""
    prefix = "lgr"#,serialno=13-0199"
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
        print("Connected and listening for data...")

        while True:
            try:
                rec = ser.readline()
                print("Received serial record:\n{}".format(rec.decode()))

                data = [v.decode().strip() for v in rec.split(b',')]
                assert len(data) == len(LGR_COLUMNS)

                msmt = build_influx_report(data)
                print("Sending measurement to influxdb:\n{}".format(msmt))
                db.write(msmt, params={'db': INFLUX_DB}, protocol='line')

            except (KeyboardInterrupt, SystemExit):
                ser.close()
                raise
            except Exception as e:
                import traceback
                print("Avoiding potentially fatal error:\n{}".format(traceback.format_exc()))
                continue


if __name__=="__main__":
    main()






















