import sys
import tempfile
import os
import shutil
from subprocess import call
import cProfile
from django.conf import settings
from django.http import HttpResponse
from io import StringIO

class ProfileMiddleware(object):
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode,
    but you really shouldn't add this middleware to any production configuration.
    * Only tested on Linux
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.request = request

        self.process_request(request)
        if self.enabled:
            resp = self.prof.runcall(self.get_response, request)
        else:
            resp = self.get_response(request)
        self.process_response(request, resp)
        return resp

    def process_request(self, request):
        if settings.DEBUG:
            r = request.GET
            if 'prof' in r:
                self.tmpfile = tempfile.NamedTemporaryFile()
                self.prof = cProfile.Profile()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if self.enabled:
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    @property
    def enabled(self):
        return settings.DEBUG and 'prof' in self.request.GET

    def process_response(self, request, response):
        r = request.GET
        if self.enabled:
            out = StringIO()
            old_stdout = sys.stdout
            sys.stdout = out
            if 'prof' in r:
                self.prof.create_stats()
                self.prof.print_stats(1)
                self.prof.dump_stats(self.tmpfile.name)

            sys.stdout = old_stdout
            stats_str = out.getvalue()

            if 'out' in request.GET:
                shutil.copy(self.tmpfile.name, os.path.join('/tmp', request.GET['out']))
                f = open(self.tmpfile.name)
                response.content = f.read()
            elif 'graph' in request.GET:
                shutil.copy(self.tmpfile.name, '/tmp/graph.cprofile')
                os.chmod('/tmp/graph.cprofile', 666)
                old = os.path.abspath('.')
                os.chdir('/tmp')
                cmd = '/usr/bin/gprof2dot -f pstats /tmp/graph.cprofile | /usr/bin/dot -Tsvg -o /tmp/graph.svg'
                try:
                    ex = call(cmd, shell=True)
                except Exception:
                    ex = 'Error during call'
                os.chdir(old)
                if os.path.exists('/tmp/graph.svg'):
                    content = open('/tmp/graph.svg').read()
                    response = HttpResponse(mimetype='image/svg')
                    response.content = content
                else:
                    response.content = ex
            elif response and response.content and stats_str:
                response.content = "<pre>" + stats_str + "</pre>"

        return response
