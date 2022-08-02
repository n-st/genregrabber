#!/usr/bin/env python
# coding: utf-8

import fileinput
import gettext
import pycountry
import re
import requests
import sys
import urllib.parse
import wikipedia
import wikitextparser as wtp


lang_strs = {
    'cs': {
        'band': 'kapela',
        'wikitemplate': ['Infobox - hudební umělec'],
        'name': 'jméno',
        'genre': 'žánr',
        'origin': 'původ',
        'origin2': 'birth_place',
        'years': 'aktivní roky',
    },
    'de': {
        'band': 'band',
        'wikitemplate': ['Infobox Band'],
        'name': 'Name',
        'genre': 'Genre',
        'origin': 'Herkunft',
        'origin2': 'birth_place',
        'years': 'Gründung',
    },
    'en': {
        'band': 'band',
        'wikitemplate': ['Infobox musical artist'],
        'name': 'name',
        'genre': 'genre',
        'origin': 'origin',
        'origin2': 'birth_place',
        'years': 'years_active',
    },
}














def get_country_code(lang, country_name):
    if not country_name:
        return '??'

    # According to https://en.wikipedia.org/wiki/Template:Infobox_musical_artist#origin
    # > For "United States" and "United Kingdom", it is preferred that they be abbreviated "U.S." and "UK"
    if country_name == 'U.S.':
        country_name = 'United States'
    if country_name == 'UK':
        country_name = 'United Kingdom'
    if country_name.lower() in ['england', 'wales', 'scotland', 'northern ireland']:
        # Workaround for https://github.com/flyingcircusio/pycountry/issues/94#issuecomment-1201863223
        country_name = 'United Kingdom'

    try:
        country_code = pycountry.countries.search_fuzzy(country_name)[0].alpha_2
    except:
        try:
            translate = gettext.translation('iso3166', pycountry.LOCALES_DIR, languages=[lang]).gettext
        except:
            # NOOP (English is the original language, it doesn't have translation files)
            translate = str

        country_code = '/'.join(
                [country.alpha_2 for country in pycountry.countries
                    if translate(country.name).lower() == country_name.lower()]
                )
    if not country_code:
        country_code = '??'
    return country_code







def find_article_name(lang, search_string):
    wikipedia.set_lang(lang)
    search = search_string + ' ' + strs['band']
    results = wikipedia.search(search, 1)
    if not results:
        raise Exception('No results for "%s" on %s.wikipedia.org.' % (search, lang))
    page_title = wikipedia.search(search, 1)[0]
    return page_title



def get_article_wikitext(lang, article_title):
    url = 'https://%s.wikipedia.org/w/api.php' % lang
    params = {
                'action': 'query',
                'format': 'json',
                'prop': 'revisions',
                'formatversion': 2,
                'rvprop': 'content',
                'rvslots': '*',
                'titles': article_title,
            }
     
    response = requests.get(url, params=params)
    data = response.json()
    content = data.get('query').get('pages')[0].get('revisions')[0].get('slots').get('main').get('content')
    return content






def untangle_template(wikitext):
    def template_mapper(template: wtp.Template):
        if template.normal_name() in {'dash', 'snd', 'spnd', 'sndash', 'spndash', 'spaced en dash'}:
            return ' –'  # &nbsp;&ndash;
        
        elif template.normal_name() in {'nowrap', 'hlist', 'Vlajka a název'}:
            # examples:
            #   {{hlist|[[Rock music|Rock]]|[[Pop music|pop]]|[[beat music|beat]]}}
            #   -> Rock, pop, beat
            #   {{nowrap|[[Christian metal]]}}
            #   -> Christian metal
            result = []
            for arg in template.arguments:
                result.append(arg.plain_text(replace_templates=template_mapper).lstrip('|').strip())
            return ', '.join(result)
        
        elif template.normal_name() in ('flatlist'):
            # examples:
            #   {{flatlist|
            #   * [[Metalcore]]
            #   * [[melodic metalcore]]
            #   }}
            #   -> Metalcore, melodic metalcore
            result = []
            for l in template.get_lists():
                for item in l.items:
                    result.append(wtp.parse(item).plain_text(replace_templates=template_mapper).strip())
            result = ', '.join(result)
            return result
        
        else:
            return ''  # remove other templates
    
    return wtp.parse(wikitext).plain_text(replace_templates=template_mapper).strip()

def extract_infos(lang, article_title, wikitext):
    band_info_templates = [template for template in wtp.parse(wikitext).templates if template.name.strip() in strs['wikitemplate']]
    if not band_info_templates:
        raise Exception('No band information in "%s" on %s.wikipedia.org.' % (article_title, lang))
    elif len(band_info_templates) > 1:
        raise Exception('Multiple band information blocks found in "%s" on %s.wikipedia.org.' % (article_title, lang))
    else:
        template = band_info_templates[0]

        name = template.get_arg(strs['name'])
        name = untangle_template(name.value) or article_title

        origin = template.get_arg(strs['origin']) or template.get_arg(strs['origin2'])
        origin = untangle_template(origin.value) or 'EMPTY'
        origin_country = origin.split(',')[-1].strip()
        origin_country_code = get_country_code(lang, origin_country)

        genre = template.get_arg(strs['genre'])
        # convert manual linebreaks into item separators
        genre.value = re.sub('(\s*,\s*)?<br[^>]*>\s*', ', ', genre.value)
        genres = untangle_template(genre.value)
        genres = [item.replace(';', ',').strip() for item in genres.split(',')]

        try:
            years = template.get_arg(strs['years'])
            # find all four-digit (year) numbers and take the lowest one
            first_year = min(map(int, re.findall(r'\b\d{4}\b', years.value)))
        except:
            first_year = 5555

        url = 'https://%s.wikipedia.org/wiki/%s' % (lang, urllib.parse.quote(article_title))

        return {
                    'name': name,
                    'url': url,
                    'genres': genres,
                    'country': origin_country,
                    'country_code': origin_country_code,
                    'year': first_year,
                }





for line in fileinput.input(encoding="utf-8"):
    line = line.strip()
    name = line.lower()
    for lang in lang_strs:
        strs = lang_strs[lang]
        try:
            article_title = find_article_name(lang, name)
            wikitext = get_article_wikitext(lang, article_title)
            infos = extract_infos(lang, article_title, wikitext)
            print('%s; %s; %s/%s; %s; %s' % (infos['name'], ' + '.join(infos['genres']), infos['country_code'], infos['country'], infos['year'], infos['url']))

        except Exception as e:
            sys.stderr.write('%s; ERROR: %s\n' % (line, str(e)))

