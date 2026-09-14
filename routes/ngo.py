import math
from flask import Blueprint, render_template, request, jsonify
from models import NGOVet

ngo_bp = Blueprint('ngo', __name__, url_prefix='/ngo')


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on Earth (in km)."""
    R = 6371  # Earth's radius in kilometers

    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


@ngo_bp.route('/nearest')
def nearest():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)

    ngos = NGOVet.query.all()
    results = []

    if lat is not None and lon is not None:
        for ngo in ngos:
            dist = haversine(lat, lon, ngo.latitude, ngo.longitude)
            results.append({
                'id': ngo.id,
                'name': ngo.name,
                'type': ngo.type,
                'address': ngo.address,
                'phone': ngo.phone,
                'latitude': ngo.latitude,
                'longitude': ngo.longitude,
                'accepting_cases': ngo.accepting_cases,
                'verified': ngo.verified,
                'distance_km': round(dist, 2)
            })
        results.sort(key=lambda x: x['distance_km'])
    else:
        for ngo in ngos:
            results.append({
                'id': ngo.id,
                'name': ngo.name,
                'type': ngo.type,
                'address': ngo.address,
                'phone': ngo.phone,
                'latitude': ngo.latitude,
                'longitude': ngo.longitude,
                'accepting_cases': ngo.accepting_cases,
                'verified': ngo.verified,
                'distance_km': None
            })

    return render_template('ngo_nearest.html', results=results, user_lat=lat, user_lon=lon)
