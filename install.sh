#!/bin/bash

echo "Installing lgr2influx service files..."
cp -r src/* /
systemctl daemon-reload
systemctl enable lgr2influx
systemctl restart lgr2influx


echo "Finished"
