import json, os, urllib.request, datetime, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'config/flight.json').read_text())
code = ''.join(c for c in config['flightCode'].upper() if c.isalnum())
now = datetime.datetime.now(datetime.timezone.utc)
next_at = now + datetime.timedelta(minutes=int(config.get('refreshMinutes', 30)))
out = {
    'flightCode': config['flightCode'], 'status': 'not_connected',
    'message': 'Live data connection is not enabled.',
    'lastUpdatedAt': None, 'nextUpdateAt': next_at.isoformat(),
    'latitude': None, 'longitude': None, 'altitudeFt': None,
    'speedKnots': None, 'heading': None,
    'airline': None, 'route': None, 'aircraft': None
}
if os.getenv('OPENSKY_AUTHORIZED', '').lower() != 'true':
    out['message'] = 'Not queried: enable only after obtaining required written authorization.'
else:
    try:
        url = 'https://opensky-network.org/api/states/all'
        req = urllib.request.Request(url, headers={'User-Agent':'SkyTrack position updater'})
        with urllib.request.urlopen(req, timeout=25) as r:
            payload = json.loads(r.read().decode('utf-8'))
        matches = [s for s in (payload.get('states') or []) if ''.join(c for c in str(s[1] or '').upper() if c.isalnum()) == code and s[5] is not None and s[6] is not None]
        if matches:
            s = matches[0]
            observed = datetime.datetime.fromtimestamp(s[3], datetime.timezone.utc) if s[3] else now
            out.update(status='ok', message='Verified aircraft position received.', lastUpdatedAt=observed.isoformat(), latitude=s[6], longitude=s[5], altitudeFt=round(s[7]*3.28084) if s[7] is not None else None, speedKnots=round(s[9]*1.94384) if s[9] is not None else None, heading=s[10])
        else:
            out['status'] = 'no_match'
            out['message'] = 'No exact callsign match with coordinates was found; no position was guessed.'
    except Exception as e:
        out['status'] = 'error'
        out['message'] = 'Position request failed: ' + str(e)[:300]
(ROOT / 'flight_position.json').write_text(json.dumps(out, indent=2) + '\n')
print(out['status'] + ': ' + out['message'])
