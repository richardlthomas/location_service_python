from flask import Flask, request, jsonify

import googlemaps
import os
import re


def create_app():
    app = Flask(__name__)

    gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

    @app.route('/')
    def app_root():
        return 'Please provide string values for any/all of the following: [address_string OR street, city, state, ' \
               'postal_code, country] OR numeric values for both latitude AND longitude.', 200

    @app.route('/geocode')
    def geocode():
        message = 'An Internal Server error occurred'
        status_code = 500
        result = jsonify(message=message, code=status_code)
        try:
            if 'address_string' in request.args:
                address = request.args.get('address_string')
                geocode_result = gmaps.geocode(address)
                return_values = parse_geocode_request(geocode_result)
                result = jsonify(return_values)
            elif any(item in['street', 'city', 'state', 'postal_code', 'country'] for item in request.args):
                components = {
                    'street': request.args.get('street') or None,
                    'city': request.args.get('city') or None,
                    'state': request.args.get('state') or None,
                    'postal_code': request.args.get('postal_code') or None,
                    'country': request.args.get('country') or None
                }
                sent_components = {k: v for k, v in components.items() if v is not None}
                full_address = re.sub(' +', ' ', ' '.join(str(value) for value in sent_components.values()).strip())
                geocode_result = gmaps.geocode(full_address)
                return_values = parse_geocode_request(geocode_result)
                result = jsonify(return_values)
            elif all(key in request.args for key in ('latitude', 'longitude')):
                geocode_result = gmaps.reverse_geocode((request.args.get('latitude'), request.args.get('longitude')))
                return_values = parse_geocode_request(geocode_result)
                result = jsonify(return_values)
            else:
                raise Exception('Please provide string values for any/all of the following: [addressString OR street, '
                                'city, state, postalCode, country] OR numeric values for both latitude AND longitude.')
            status_code = 200
        except IndexError:
            message = "This input did not appear to return a result. Please ensure that the address is valid."
            status_code = 400
            result = jsonify(message=message, code=status_code)
        except Exception as e:
            message = f'error: {str(e)}'
            status_code = 400
            result = jsonify(message=message, code=status_code)
        finally:
            return result, status_code

    def parse_geocode_request(geocode_result):
        return_values = {}
        first_location_match = geocode_result[0]
        coordinates = first_location_match['geometry']['location']
        return_values.update({
            'latitude': coordinates['lat'],
            'longitude': coordinates['lng']
        })
        street_number = ""
        street_name = ""
        for component in first_location_match['address_components']:
            types = component['types']
            if 'street_number' in types:
                street_number = component['short_name']
            elif 'route' in types:
                street_name = component['short_name']
            elif 'locality' in types:
                return_values.update({'city': component['short_name']})
            elif 'administrative_area_level_1' in types:
                return_values.update({'state': component['short_name']})
            elif 'postal_code' in types:
                return_values.update({'postal_code': component['short_name']})
            elif 'country' in types:
                return_values.update({'country': component['short_name']})
        street = re.sub(" +", " ", " ".join(str(value) for value in [street_number, street_name]).strip())
        if street != "":
            return_values.update({'street': street})
        return return_values

    return app


if __name__ == '__main__':
    create_app().run()
