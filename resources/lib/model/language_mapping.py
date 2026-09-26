'''
Maps between ISO-639-1 language codes and full language names.
'''

import os
import re

__code_re__ = re.compile(r'^[a-z]{2,3}(-[a-z0-9]+)*$')

# Kodi language names that carry a variant TED distinguishes.
__name_aliases__ = {
    'portuguese (brazil)': 'pt-br',
    'chinese (simple)': 'zh-cn',
    'chinese (simplified)': 'zh-cn',
    'chinese (traditional)': 'zh-tw',
    'french (canada)': 'fr-ca',
    'norwegian': 'nb',
    'norwegian bokmål': 'nb',
    'norwegian nynorsk': 'nb',
}

# Codes as used by Kodi/ISO mapped to the codes TED uses for subtitles.
__code_aliases__ = {
    'no': 'nb',
    'nn': 'nb',
    'iw': 'he',
    'tl': 'fil',
    'zh': 'zh-cn',
    'zh-hans': 'zh-cn',
    'zh-sg': 'zh-cn',
    'zh-hant': 'zh-tw',
    'zh-hk': 'zh-tw',
    'zh-mo': 'zh-tw',
    'pt-pt': 'pt',
}

# Closely related variants to try if the preferred one is not available.
__related_variants__ = {
    'zh-cn': ['zh-tw'],
    'zh-tw': ['zh-cn'],
    'pt': ['pt-br'],
    'pt-br': ['pt'],
    'fr': ['fr-ca'],
    'fr-ca': ['fr'],
}


def get_ted_language_codes(language):
    '''
    Returns the TED subtitle codes for a language code (optionally with region,
    e.g. "pt-BR") or a Kodi language name (e.g. "Portuguese (Brazil)"),
    most preferred first. Returns an empty list if the language is unknown.
    '''
    if not language:
        return []
    language = language.strip().lower().replace('_', '-')
    if not language:
        return []

    if language in __name_aliases__:
        code = __name_aliases__[language]
    elif __code_re__.match(language):
        code = language
    else:
        code = get_language_code(language)
        if not code:
            return []

    code = __code_aliases__.get(code, code)
    codes = [code]
    if '-' in code:
        base = code.split('-')[0]
        codes.append(__code_aliases__.get(base, base))
    for c in list(codes):
        codes.extend(__related_variants__.get(c, []))

    result = []
    for c in codes:
        if c not in result:
            result.append(c)
    return result

def get_language_code(language):
    '''
    This is ludicrous but I can't find XBMC APIs to do it for me :(
    APIs coming in Gotham...
    List taken from http://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt
    '''
    language = language.lower()
    
    file_path = os.path.join(os.path.dirname(__file__), "ISO-639-2_utf-8.txt")
    f = open(file_path, 'r', encoding='utf-8')
    try:
        for line in f:
            split = line.split('|')
            if split[2]:
                for l in split[3].split(';'):
                    if language.startswith(l.strip().lower()):
                        return split[2]
    finally:
        f.close()
    
    return None
