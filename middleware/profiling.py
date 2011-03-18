import sys
import tempfile
import os
import shutil
import hotshot
import hotshot.stats
import cProfile
from django.conf import settings
from cStringIO import StringIO

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
    def process_request(self, request):
        if settings.DEBUG:
            r = request.GET
            if r.has_key('prof'):
                self.tmpfile = tempfile.NamedTemporaryFile()
                self.prof = hotshot.Profile(self.tmpfile.name)
            elif r.has_key('cprof'):
                self.tmpfile = tempfile.NamedTemporaryFile()
                self.prof = cProfile.Profile()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        r = request.GET
        if settings.DEBUG and (r.has_key('prof') or r.has_key('cprof')):
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        r = request.GET
        if settings.DEBUG and (r.has_key('prof') or r.has_key('cprof')):
            out = StringIO()
            old_stdout = sys.stdout
            sys.stdout = out
            if r.has_key('prof'):
                self.prof.close()
                stats = hotshot.stats.load(self.tmpfile.name)
                stats.sort_stats('time', 'calls')
                stats.print_stats()
            else:
                self.prof.create_stats()
                self.prof.print_stats(1)
                self.prof.dump_stats(self.tmpfile.name)

            sys.stdout = old_stdout
            stats_str = out.getvalue()
            
            if request.GET.has_key('out'):
                shutil.copy(self.tmpfile.name, os.path.join('/tmp', request.GET['out']))
            if response and response.content and stats_str:
                response.content = "<pre>" + stats_str + "</pre>"

        return response
