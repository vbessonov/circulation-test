import urllib
import urlparse

import requests
from flask import Blueprint, request, redirect, session, url_for, render_template

blueprint = Blueprint('auth', __name__, url_prefix='/auth')

AUTHENTICATION_DOCUMENT_URL = 'http://cm.hilbertteam.net:6500/authentication_document'
AUTHENTICATION_BASE_URL = 'http://cm.hilbertteam.net/SAML/saml_authenticate'
IDP_ENTITY_ID = 'http://idp.hilbertteam.net/idp/shibboleth'
PROVIDER_NAME = 'SAML 2.0'


def get_authentication_url(redirect_url):
    return AUTHENTICATION_BASE_URL + '?' + urllib.urlencode({
        'provider': PROVIDER_NAME,
        'idp_entity_id': IDP_ENTITY_ID,
        'redirect_uri': redirect_url
    })


@blueprint.route('/', methods=('GET',))
def index():
    response = requests.get(AUTHENTICATION_DOCUMENT_URL)
    authentication_document = response.json()

    authentication_documents = authentication_document['authentication']
    result_authentication_documents = []

    for authentication_document in authentication_documents:
        authenticate_link = list(filter(lambda link: link['rel'] == 'authenticate', authentication_document['links']))[0]
        result_authentication_document = {
            'display_name': authenticate_link['display_names'][0]['value'] if authenticate_link['display_names'] else '',
            'description': authenticate_link['descriptions'][0]['value'] if authenticate_link['descriptions'] else '',
            'information_url': authenticate_link['information_urls'][0]['value'] if authenticate_link['information_urls'] else '',
            'privacy_statement_url': authenticate_link['privacy_statement_urls'][0]['value'] if authenticate_link['privacy_statement_urls'] else '',
            'logo_url': authenticate_link['logo_urls'][0]['value'] if authenticate_link['logo_urls'] else '',
            'href': requests.utils.quote(authenticate_link['href'])
        }

        result_authentication_documents.append(result_authentication_document)

    return render_template('auth/index.html', authentication_documents=result_authentication_documents)


@blueprint.route('/login', methods=('GET', 'POST',))
def login():
    if request.referrer:
        referrer_parse_result = urlparse.urlparse(request.referrer)

        if 'idp.hilbertteam.net' in referrer_parse_result.netloc:
            token = request.args.get('access_token')
            session['ACCESS_TOKEN'] = token
        else:
            authentication_url = requests.utils.unquote(request.args.get('link'))
            redirect_uri = url_for('auth.login', _external=True)

            authentication_url += '&redirect_uri=' + requests.utils.quote(redirect_uri)
            # authentication_url = get_authentication_url(url_for('auth.login', _external=True))

            return redirect(authentication_url)

    return redirect(url_for('home.index'))


@blueprint.route('/logout', methods=('GET',))
def logout():
    del session['ACCESS_TOKEN']
    return redirect(url_for('home.index'))
