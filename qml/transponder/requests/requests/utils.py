# -*- coding: utf-8 -*-

"""
requests.utils
~~~~~~~~~~~~~~

This module provides utility functions that are used within Requests
that are also useful for external consumption.
"""

import codecs
import collections
import contextlib
import io
import os
import re
import socket
import struct
import sys
import tempfile
import warnings
import zipfile

from .__version__ import __version__
from . import certs
# to_native_string is unused here, but imported here for backwards compatibility
from ._internal_utils import to_native_string
from .compat import parse_http_list as _parse_list_header
from .compat import (
    quote, urlparse, bytes, str, OrderedDict, unquote, getproxies,
    proxy_bypass, urlunparse, basestring, integer_types, is_py3,
    proxy_bypass_environment, getproxies_environment)
from .cookies import cookiejar_from_dict
from .structures import CaseInsensitiveDict
from .exceptions import (
    InvalidURL, InvalidHeader, FileModeWarning, UnrewindableBodyError)

NETRC_FILES = ('.netrc', '_netrc')

DEFAULT_CA_BUNDLE_PATH = certs.where()


if sys.platform == 'win32':
    # provide a proxy_bypass version on Windows without DNS lookups

    def proxy_bypass_registry(host):
        try:
            if is_py3:
                import winreg
            else:
                import _winreg as winreg
        except ImportError:
            return False

        try:
            internetSettings = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings')
            # ProxyEnable could be REG_SZ or REG_DWORD, normalizing it
            proxyEnable = int(winreg.QueryValueEx(internetSettings,
                                              'ProxyEnable')[0])
            # ProxyOverride is almost always a string
            proxyOverride = winreg.QueryValueEx(internetSettings,
                                                'ProxyOverride')[0]
        except OSError:
            return False
        if not proxyEnable or not proxyOverride:
            return False

        # make a check value list from the registry entry: replace the
        # '<local>' string by the localhost entry and the corresponding
        # canonical entry.
        proxyOverride = proxyOverride.split(';')
        # now check if we match one of the registry values.
        for test in proxyOverride:
            if test == '<local>':
                if '.' not in host:
                    return True
            test = test.replace(".", r"\.")     # mask dots
            test = test.replace("*", r".*")     # change glob sequence
            test = test.replace("?", r".")      # change glob char
            if re.match(test, host, re.I):
                return True
        return False

    def proxy_bypass(host):  # noqa
        """Return True, if the host should be bypassed.

        Checks proxy settings gathered from the environment, if specified,
        or the registry.
        """
        if getproxies_environment():
            return proxy_bypass_environment(host)
        else:
            return proxy_bypass_registry(host)


def dict_to_sequence(d):
    """Returns an internal sequence dictionary update."""

    if hasattr(d, 'items'):
        d = d.items()

    return d


def super_len(o):
    total_length = None
    current_position = 0

    if hasattr(o, '__len__'):
        total_length = len(o)

    elif hasattr(o, 'len'):
        total_length = o.len

    elif hasattr(o, 'fileno'):
        try:
            fileno = o.fileno()
        except io.UnsupportedOperation:
            pass
        else:
            total_length = os.fstat(fileno).st_size

            # Having used fstat to determine the file length, we need to
            # confirm that this file was opened up in binary mode.
            if 'b' not in o.mode:
                warnings.warn((
                    "Requests has determined the content-length for this "
                    "request using the binary size of the file: however, the "
                    "file has been opened in text mode (i.e. without the 'b' "
                    "flag in the mode). This may lead to an incorrect "
                    "content-length. In Requests 3.0, support will be removed "
                    "for files in text mode."),
                    FileModeWarning
                )

    if hasattr(o, 'tell'):
        try:
            current_position = o.tell()
        except (OSError, IOError):
            # This can happen in some weird situations, such as when the file
            # is actually a special file descriptor like stdin. In this
            # instance, we don't know what the length is, so set it to zero and
            # let requests chunk it instead.
            if total_length is not None:
                current_position = total_length
        else:
            if hasattr(o, 'seek') and total_length is None:
                # StringIO and BytesIO have seek but no useable fileno
                try:
                    # seek to end of file
                    o.seek(0, 2)
                    total_length = o.tell()

                    # seek back to current position to support
                    # partially read file-like objects
                    o.seek(current_position or 0)
                except (OSError, IOError):
                    total_length = 0

    if total_length is None:
        total_length = 0

    return max(0, total_length - current_position)


def get_netrc_auth(url, raise_errors=False):
    """Returns the Requests tuple auth for a given url from netrc."""

    try:
        from netrc import netrc, NetrcParseError

        netrc_path = None

        for f in NETRC_FILES:
            try:
                loc = os.path.expanduser('~/{0}'.format(f))
            except KeyError:
                # os.path.expanduser can fail when $HOME is undefined and
                # getpwuid fails. See http://bugs.python.org/issue20164 &
                # https://github.com/requests/requests/issues/1846
                return

            if os.path.exists(loc):
                netrc_path = loc
                break

        # Abort early if there isn't one.
        if netrc_path is None:
            return

        ri = urlparse(url)

        # Strip port numbers from netloc. This weird `if...encode`` dance is
        # used for Python 3.2, which doesn't support unicode literals.
        splitstr = b':'
        if isinstance(url, str):
            splitstr = splitstr.decode('ascii')
        host = ri.netloc.split(splitstr)[0]

        try:
            _netrc = netrc(netrc_path).authenticators(host)
            if _netrc:
                # Return with login / password
                login_i = (0 if _netrc[0] else 1)
                return (_netrc[login_i], _netrc[2])
        except (NetrcParseError, IOError):
            # If there was a parsing error or a permissions issue reading the file,
            # we'll just skip netrc auth unless explicitly asked to raise errors.
            if raise_errors:
                raise

    # AppEngine hackiness.
    except (ImportError, AttributeError):
        pass


def guess_filename(obj):
    """Tries to guess the filename of the given object."""
    name = getattr(obj, 'name', None)
    if (name and isinstance(name, basestring) and name[0] != '<' and
            name[-1] != '>'):
        return os.path.basename(name)


def extract_zipped_paths(path):
    """Replace nonexistant paths that look like they refer to a member of a zip
    archive with the location of an extracted copy of the target, or else
    just return the provided path unchanged.
    """
    if os.path.exists(path):
        # this is already a valid path, no need to do anything further
        return path

    # find the first valid part of the provided path and treat that as a zip archive
    # assume the rest of the path is the name of a member in the archive
    archive, member = os.path.split(path)
    while archive and not os.path.exists(archive):
        archive, prefix = os.path.split(archive)
        member = '/'.join([prefix, member])

    if not zipfile.is_zipfile(archive):
        return path

    zip_file = zipfile.ZipFile(archive)
    if member not in zip_file.namelist():
        return path

    # we have a valid zip archive and a valid member of that archive
    tmp = tempfile.gettempdir()
    extracted_path = os.path.join(tmp, *member.split('/'))
    if not os.path.exists(extracted_path):
        extracted_path = zip_file.extract(member, path=tmp)

    return extracted_path


def from_key_val_list(value):
    """Take an object and test to see if it can be represented as a
    dictionary. Unless it can not be represented as such, return an
    OrderedDict, e.g.,

    ::

        >>> from_key_val_list([('key', 'val')])
        OrderedDict([('key', 'val')])
        >>> from_key_val_list('string')
        ValueError: need more than 1 value to unpack
        >>> from_key_val_list({'key': 'val'})
        OrderedDict([('key', 'val')])

    :rtype: OrderedDict
    """
    if value is None:
        return None

    if isinstance(value, (str, bytes, bool, int)):
        raise ValueError('cannot encode objects that are not 2-tuples')

    return OrderedDict(value)


def to_key_val_list(value):
    """Take an object and test to see if it can be represented as a
    dictionary. If it can be, return a list of tuples, e.g.,

    ::

        >>> to_key_val_list([('key', 'val')])
        [('key', 'val')]
        >>> to_key_val_list({'key': 'val'})
        [('key', 'val')]
        >>> to_key_val_list('string')
        ValueError: cannot encode objects that are not 2-tuples.

    :rtype: list
    """
    if value is None:
        return None

    if isinstance(value, (str, bytes, bool, int)):
        raise ValueError('cannot encode objects that are not 2-tuples')

    if isinstance(value, collections.Mapping):
        value = value.items()

    return list(value)


# From mitsuhiko/werkzeug (used with permission).
def parse_list_header(value):
    """Parse lists as described by RFC 2068 Section 2.

    In particular, parse comma-separated lists where the elements of
    the list may include quoted-strings.  A quoted-string could
    contain a comma.  A non-quoted string could have quotes in the
    middle.  Quotes are removed automatically after parsing.

    It basically works like :func:`parse_set_header` just that items
    may appear multiple times and case sensitivity is preserved.

    The return value is a standard :class:`list`:

    >>> parse_list_header('token, "quoted value"')
    ['token', 'quoted value']

    To create a header from the :class:`list` again, use the
    :func:`dump_header` function.

    :param value: a string with a list header.
    :return: :class:`list`
    :rtype: list
    """
    result = []
    for item in _parse_list_header(value):
        if item[:1] == item[-1:] == '"':
            item = unquote_header_value(item[1:-1])
        result.append(item)
    return result


# From mitsuhiko/werkzeug (used with permission).
def parse_dict_header(value):
    """Parse lists of key, value pairs as described by RFC 2068 Section 2 and
    convert them into a python dict:

    >>> d = parse_dict_header('foo="is a fish", bar="as well"')
    >>> type(d) is dict
    True
    >>> sorted(d.items())
    [('bar', 'as well'), ('foo', 'is a fish')]

    If there is no value for a key it will be `None`:

    >>> parse_dict_header('key_without_value')
    {'key_without_value': None}

    To create a header from the :class:`dict` again, use the
    :func:`dump_header` function.

    :param value: a string with a dict header.
    :return: :class:`dict`
    :rtype: dict
    """
    result = {}
    for item in _parse_list_header(value):
        if '=' not in item:
            result[item] = None
            continue
        name, value = item.split('=', 1)
        if value[:1] == value[-1:] == '"':
            value = unquote_header_value(value[1:-1])
        result[name] = value
    return result


# From mitsuhiko/werkzeug (used with permission).
def unquote_header_value(value, is_filename=False):
    r"""Unquotes a header value.  (Reversal of :func:`quote_header_value`).
    This does not use the real unquoting but what browsers are actually
    using for quoting.

    :param value: the header value to unquote.
    :rtype: str
    """
    if value and value[0] == value[-1] == '"':
        # this is not the real unquoting, but fixing this so that the
        # RFC is met will result in bugs with internet explorer and
        # probably some other browsers as well.  IE for example is
        # uploading files with "C:\foo\bar.txt" as filename
        value = value[1:-1]

        # if this is a filename and the starting characters look like
        # a UNC path, then just return the value without quotes.  Using the
        # replace sequence below on a UNC path has the effect of turning
        # the leading double slash into a single slash and then
        # _fix_ie_filename() doesn't work correctly.  See #458.
        if not is_filename or value[:2] != '\\\\':
            return value.replace('\\\\', '\\').replace('\\"', '"')
    return value


def dict_from_cookiejar(cj):
    """Returns a key/value dictionary from a CookieJar.

    :param cj: CookieJar object to extract cookies from.
    :rtype: dict
    """

    cookie_dict = {}

    for cookie in cj:
        cookie_dict[cookie.name] = cookie.value

    return cookie_dict


def add_dict_to_cookiejar(cj, cookie_dict):
    """Returns a CookieJar from a key/value dictionary.

    :param cj: CookieJar to insert cookies into.
    :param cookie_dict: Dict of key/values to insert into CookieJar.
    :rtype: CookieJar
    """

    return cookiejar_from_dict(cookie_dict, cj)


def get_encodings_from_content(content):
    """Returns encodings from given content string.

    :param content: bytestring to extract encodings from.
    """
    warnings.warn((
        'In requests 3.0, get_encodings_from_content will be removed. For '
        'more information, please see the discussion on issue #2266. (This'
        ' warning should only appear once.)'),
        DeprecationWarning)

    charset_re = re.compile(r'<meta.*?charset=["\']*(.+?)["\'>]', flags=re.I)
    pragma_re = re.compile(r'<meta.*?content=["\']*;?charset=(.+?)["\'>]', flags=re.I)
    xml_re = re.compile(r'^<\?xml.*?encoding=["\']*(.+?)["\'>]')

    return (charset_re.findall(content) +
            pragma_re.findall(content) +
            xml_re.findall(content))


def _parse_content_type_header(header):
    """Returns content type and parameters from given header

    :param header: string
    :return: tuple containing content type and dictionary of
         parameters
    """

    tokens = header.split(';')
    content_type, params = tokens[0].strip(), tokens[1:]
    params_dict = {}
    items_to_strip = "\"' "

    for param in params:
        param = param.strip()
        if param:
            key, value = param, True
            index_of_equals = param.find("=")
            if index_of_equals != -1:
                key = param[:index_of_equals].strip(items_to_strip)
                value = param[index_of_equals + 1:].strip(items_to_strip)
            params_dict[key] = value
    return content_type, params_dict


def get_encoding_from_headers(headers):
    """Returns encodings from given HTTP Header Dict.

    :param headers: dictionary to extract encoding from.
    :rtype: str
    """

    content_type = headers.get('content-type')

    if not content_type:
        return None

    content_type, params = _parse_content_type_header(content_type)

    if 'charset' in params:
        return params['charset'].strip("'\"")

    if 'text' in content_type:
        return 'ISO-8859-1'


def stream_decode_response_unicode(iterator, r):
    """Stream decodes a iterator."""

    if r.encoding is None:
        for item in iterator:
            yield item
        return

    decoder = codecs.getincrementaldecoder(r.encoding)(errors='replace')
    for chunk in iterator:
        rv = decoder.decode(chunk)
        if rv:
            yield rv
    rv = decoder.decode(b'', final=True)
    if rv:
        yield rv


def iter_slices(string, slice_length):
    """Iterate over slices of a string."""
    pos = 0
    if slice_length is None or slice_length <= 0:
        slice_length = len(string)
    while pos < len(string):
        yield string[pos:pos + slice_length]
        pos += slice_length


def get_unicode_from_response(r):
    """Returns the requested content back in unicode.

    :param r: Response object to get unicode content from.

    Tried:

    1. charset from content-type
    2. fall back and replace all unicode characters

    :rtype: str
    """
    warnings.warn((
        'In requests 3.0, get_unicode_from_response will be removed. For '
        'more information, please see the discussion on issue #2266. (This'
        ' warning should only appear once.)'),
        DeprecationWarning)

    tried_encodings = []

    # Try charset from content-type
    encoding = get_encoding_from_headers(r.headers)

    if encoding:
        try:
            return str(r.content, encoding)
        except UnicodeError:
            tried_encodings.append(encoding)

    # Fall back:
    try:
        return str(r.content, encoding, errors='replace')
    except TypeError:
        return r.content


# The unreserved URI characters (RFC 3986)
UNRESERVED_SET = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" + "0123456789-._~")


def unquote_unreserved(uri):
    """Un-escape any percent-escape sequences in a URI that are unreserved
    characters. This leaves all reserved, illegal and non-ASCII bytes encoded.

    :rtype: str
    """
    parts = uri.split('%')
    for i in range(1, len(parts)):
        h = parts[i][0:2]
        if len(h) == 2 and h.isalnum():
            try:
                c = chr(int(h, 16))
            except ValueError:
                raise InvalidURL("Invalid percent-escape sequence: '%s'" % h)

            if c in UNRESERVED_SET:
                parts[i] = c + parts[i][2:]
            else:
                parts[i] = '%' + parts[i]
        else:
            parts[i] = '%' + parts[i]
    return ''.join(parts)


def requote_uri(uri):
    """Re-quote the given URI.

    This function passes the given URI through an unquote/quote cycle to
    ensure that it is fully and consistently quoted.

    :rtype: str
    """
    safe_with_percent = "!#$%&'()*+,/:;=?@[]~"
    safe_without_percent = "!#$&'()*+,/:;=?@[]~"
    try:
        # Unquote only the unreserved characters
        # Then quote only illegal characters (do not quote reserved,
        # unreserved, or '%')
        return quote(unquote_unreserved(uri), safe=safe_with_percent)
    except InvalidURL:
        # We couldn't unquote the given URI, so let's try quoting it, but
        # there may be unquoted '%'s in the URI. We need to make sure they're
        # properly quoted so they do not cause issues elsewhere.
        return quote(uri, safe=safe_without_percent)


def address_in_network(ip, net):
    """This function allows you to check if an IP belongs to a network subnet

    Example: returns True if ip = 192.168.1.1 and net = 192.168.1.0/24
             returns False if ip = 192.168.1.1 and net = 192.168.100.0/24

    :rtype: bool
    """
    ipaddr = struct.unpack('=L', socket.inet_aton(ip))[0]
    netaddr, bits = net.split('/')
    netmask = struct.unpack('=L', socket.inet_aton(dotted_netmask(int(bits))))[0]
    network = struct.unpack('=L', socket.inet_aton(netaddr))[0] & netmask
    return (ipaddr & netmask) == (network & netmask)


def dotted_netmask(mask):
    """Converts mask from /xx format to xxx.xxx.xxx.xxx

    Example: if mask is 24 function returns 255.255.255.0

    :rtype: str
    """
    bits = 0xffffffff ^ (1 << 32 - mask) - 1
    return socket.inet_ntoa(struct.pack('>I', bits))


def is_ipv4_address(string_ip):
    """
    :rtype: bool
    """
    try:
        socket.inet_aton(string_ip)
    except socket.error:
        return False
    return True


def is_valid_cidr(string_network):
    """
    Very simple check of the cidr format in no_proxy variable.

    :rtype: bool
    """
    if string_network.count('/') == 1:
        try:
            mask = int(string_network.split('/')[1])
        except ValueError:
            return False

        if mask < 1 or mask > 32:
            return False

        try:
            socket.inet_aton(string_network.split('/')[0])
        except socket.error:
            return False
    else:
        return False
    return True


@contextlib.contextmanager
def set_environ(env_name, value):
    """Set the environment variable 'env_name' to 'value'

    Save previous value, yield, and then restore the previous value stored in
    the environment variable 'env_name'.

    If 'value' is None, do nothing"""
    value_changed = value is not None
    if value_changed:
        old_value = os.environ.get(env_name)
        os.environ[env_name] = value
    try:
        yield
    finally:
        if value_changed:
            if old_value is None:
                del os.environ[env_name]
            else:
                os.environ[env_name] = old_value


def should_bypass_proxies(url, no_proxy):
    """
    Returns whether we should bypass proxies or not.

    :rtype: bool
    """
    get_proxy = lambda k: os.environ.get(k) or os.environ.get(k.upper())

    # First check whether no_proxy is defined. If it is, check that the URL
    # we're getting isn't in the no_proxy list.
    no_proxy_arg = no_proxy
    if no_proxy is None:
        no_proxy = get_proxy('no_proxy')
    parsed = urlparse(url)

    if no_proxy:
        # We need to check whether we match here. We need to see if we match
        # the end of the hostname, both with and without the port.
        no_proxy = (
            host for host in no_proxy.replace(' ', '').split(',') if host
        )

        if is_ipv4_address(parsed.hostname):
            for proxy_ip in no_proxy:
                if is_valid_cidr(proxy_ip):
                    if address_in_network(parsed.hostname, proxy_ip):
                        return True
                elif parsed.hostname == proxy_ip:
                    # If no_proxy ip was defined in plain IP notation instead of cidr notation &
                    # matches the IP of the index
                    return True
        else:
            host_with_port = parsed.hostname
            if parsed.port:
                host_with_port += ':{0}'.format(parsed.port)

            for host in no_proxy:
                if parsed.hostname.endswith(host) or host_with_port.endswith(host):
                    # The URL does match something in no_proxy, so we don't want
                    # to apply the proxies on this URL.
                    return True

    # If the system proxy settings indicate that this URL should be bypassed,
    # don't proxy.
    # The proxy_bypass function is incredibly buggy on OS X in early versions
    # of Python 2.6, so allow this call to fail. Only catch the specific
    # exceptions we've seen, though: this call failing in other ways can reveal
    # legitimate problems.
    with set_environ('no_proxy', no_proxy_arg):
        try:
            bypass = proxy_bypass(parsed.hostname)
        except (TypeError, socket.gaierror):
            bypass = False

    if bypass:
        return True

    return False


def get_environ_proxies(url, no_proxy=None):
    """
    Return a dict of environment proxies.

    :rtype: dict
    """
    if should_bypass_proxies(url, no_proxy=no_proxy):
        return {}
    else:
        return getproxies()


def select_proxy(url, proxies):
    """Select a proxy for the url, if applicable.

    :param url: The url being for the request
    :param proxies: A dictionary of schemes or schemes and hosts to proxy URLs
    """
    proxies = proxies or {}
    urlparts = urlparse(url)
    if urlparts.hostname is None:
        return proxies.get(urlparts.scheme, proxies.get('all'))

    proxy_keys = [
        urlparts.scheme + '://' + urlparts.hostname,
        urlparts.scheme,
        'all://' + urlparts.hostname,
        'all',
    ]
    proxy = None
    for proxy_key in proxy_keys:
        if proxy_key in proxies:
            proxy = proxies[proxy_key]
            break

    return proxy


def default_user_agent(name="python-requests"):
    """
    Return a string representing the default user agent.

    :rtype: str
    """
    return '%s/%s' % (name, __version__)


def default_headers():
    """
    :rtype: requests.structures.CaseInsensitiveDict
    """
    return CaseInsensitiveDict({
        'User-Agent': default_user_agent(),
        'Accept-Encoding': ', '.join(('gzip', 'deflate')),
        'Accept': '*/*',
        'Connection': 'keep-alive',
    })


def parse_header_links(value):
    """Return a list of parsed link headers proxies.

    i.e. Link: <http:/.../front.jpeg>; rel=front; type="image/jpeg",<http://.../back.jpeg>; rel=back;type="image/jpeg"

    :rtype: list
    """

    links = []

    replace_chars = ' \'"'

    value = value.strip(replace_chars)
    if not value:
        return links

    for val in re.split(', *<', value):
        try:
            url, params = val.split(';', 1)
        except ValueError:
            url, params = val, ''

        link = {'url': url.strip('<> \'"')}

        for param in params.split(';'):
            try:
                key, value = param.split('=')
            except ValueError:
                break

            link[key.strip(replace_chars)] = value.strip(replace_chars)

        links.append(link)

    return links


# Null bytes; no need to recreate these on each call to guess_json_utf
_null = '\x00'.encode('ascii')  # encoding to ASCII for Python 3
_null2 = _null * 2
_null3 = _null * 3


def guess_json_utf(data):
    """
    :rtype: str
    """
    # JSON always starts with two ASCII characters, so detection is as
    # easy as counting the nulls and from their location and count
    # determine the encoding. Also detect a BOM, if present.
    sample = data[:4]
    if sample in (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE):
        return 'utf-32'     # BOM included
    if sample[:3] == codecs.BOM_UTF8:
        return 'utf-8-sig'  # BOM included, MS style (discouraged)
    if sample[:2] in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE):
        return 'utf-16'     # BOM included
    nullcount = sample.count(_null)
    if nullcount == 0:
        return 'utf-8'
    if nullcount == 2:
        if sample[::2] == _null2:   # 1st and 3rd are null
            return 'utf-16-be'
        if sample[1::2] == _null2:  # 2nd and 4th are null
            return 'utf-16-le'
        # Did not detect 2 valid UTF-16 ascii-range characters
    if nullcount == 3:
        if sample[:3] == _null3:
            return 'utf-32-be'
        if sample[1:] == _null3:
            return 'utf-32-le'
        # Did not detect a valid UTF-32 ascii-range character
    return None


def prepend_scheme_if_needed(url, new_scheme):
    """Given a URL that may or may not have a scheme, prepend the given scheme.
    Does not replace a present scheme with the one provided as an argument.

    :rtype: str
    """
    scheme, netloc, path, params, query, fragment = urlparse(url, new_scheme)

    # urlparse is a finicky beast, and sometimes decides that there isn't a
    # netloc present. Assume that it's being over-cautious, and switch netloc
    # and path if urlparse decided there was no netloc.
    if not netloc:
        netloc, path = path, netloc

    return urlunparse((scheme, netloc, path, params, query, fragment))


def get_auth_from_url(url):
    """Given a url with authentication components, extract them into a tuple of
    username,password.

    :rtype: (str,str)
    """
    parsed = urlparse(url)

    try:
        auth = (unquote(parsed.username), unquote(parsed.password))
    except (AttributeError, TypeError):
        auth = ('', '')

    return auth


# Moved outside of function to avoid recompile every call
_CLEAN_HEADER_REGEX_BYTE = re.compile(b'^\\S[^\\r\\n]*$|^$')
_CLEAN_HEADER_REGEX_STR = re.compile(r'^\S[^\r\n]*$|^$')


def check_header_validity(header):
    """Verifies that header value is a string which doesn't contain
    leading whitespace or return characters. This prevents unintended
    header injection.

    :param header: tuple, in the format (name, value).
    """
    name, value = header

    if isinstance(value, bytes):
        pat = _CLEAN_HEADER_REGEX_BYTE
    else:
        pat = _CLEAN_HEADER_REGEX_STR
    try:
        if not pat.match(value):
            raise InvalidHeader("Invalid return character or leading space in header: %s" % name)
    except TypeError:
        raise InvalidHeader("Value for header {%s: %s} must be of type str or "
                            "bytes, not %s" % (name, value, type(value)))


def urldefragauth(url):
    """
    Given a url remove the fragment and the authentication part.

    :rtype: str
    """
    scheme, netloc, path, params, query, fragment = urlparse(url)

    # see func:`prepend_scheme_if_needed`
    if not netloc:
        netloc, path = path, netloc

    netloc = netloc.rsplit('@', 1)[-1]

    return urlunparse((scheme, netloc, path, params, query, ''))


def rewind_body(prepared_request):
    """Move file pointer back to its recorded starting position
    so it can be read again on redirect.
    """
    body_seek = getattr(prepared_request.body, 'seek', None)
    if body_seek is not None and isinstance(prepared_request._body_position, integer_types):
        try:
            body_seek(prepared_request._body_position)
        except (IOError, OSError):
            raise UnrewindableBodyError("An error occurred when rewinding request "
                                        "body for redirect.")
    else:
        raise UnrewindableBodyError("Unable to rewind request body for redirect.")
