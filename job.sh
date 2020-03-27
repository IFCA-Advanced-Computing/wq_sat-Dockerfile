env
mkdir -p /onedata/output

ONECLIENT_AUTHORIZATION_TOKEN="$INPUT_ONEDATA_TOKEN" PROVIDER_HOSTNAME="$ONEDATA_PROVIDERS" oneclient --no_check_certificate --authentication token -o rw /onedata/output || exit 1

echo Start at $(date)

OUTPUTDIR="/onedata/output/$ONEDATA_SPACE/"
#OUTPUTDIR=$SAT_PATH

# Run
python3 wq_sat/wq_server/main.py -sat_args $SAT_ARGS -path "$OUTPUTDIR" $argfile > "$OUTPUTDIR""$REGION"/satellite_"$START_DATE"_"$END_DATE"_output.log
#python3 wq_sat/wq_server/main.py -sat_args $SAT_ARGS -path "$OUTPUTDIR"

echo End at $(date)
