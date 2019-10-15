#!/bin/bash

#send all event changes via email
echo -e "Subject: nut[$HOSTNAME]: $NOTIFYTYPE\r\n\r\nUPS: $UPSNAME\r\nAlert type: $NOTIFYTYPE\r\n\r\n`upsc $UPSNAME`" | msmtp nut


#send shutdown command to LGR if UPS gets precarious
case $NOTIFYTYPE in
	FSD | SHUTDOWN | LOWBATT )
		echo -e "Subject: nut[$HOSTNAME]: $NOTIFYTYPE\r\n\r\nForced shutdown in effect for $HOSTNAME! Sending halt signal to LGR analyer..." | msmtp nut
		ssh root@10.42.0.10 -i /var/lib/nut/.ssh/id_rsa '/sbin/shutdown -h 0'
		;;
esac
