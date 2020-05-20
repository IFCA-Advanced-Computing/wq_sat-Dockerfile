mkdir -p "$ONEDATA_MOUNT_POINT"

ONECLIENT_AUTHORIZATION_TOKEN="$INPUT_ONEDATA_TOKEN" ONECLIENT_PROVIDER_HOSTNAME="$ONEDATA_PROVIDERS" oneclient --no_check_certificate --authentication token -o rw "$ONEDATA_MOUNT_POINT" || exit 1

echo Start at $(date)
OUTPUTDIR="$ONEDATA_MOUNT_POINT/$ONEDATA_SPACE/$REGION/"

# Run
python3 wq_sat/wq_server/main.py -sat_args $SAT_ARGS -path "$OUTPUTDIR" $argfile > "$OUTPUTDIR"/satellite_"$START_DATE"_"$END_DATE"_output.log
#python3 wq_sat/wq_server/main.py -sat_args $SAT_ARGS -path "$OUTPUTDIR"

echo End at $(date)
