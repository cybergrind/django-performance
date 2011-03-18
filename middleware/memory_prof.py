

import sys
from cStringIO import StringIO

from django.conf import settings




class MemoryProfileMiddleware(object):
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode,
    but you really shouldn't add this middleware to any production configuration.
    * Only tested on Linux
    """
    def __process_request(self, request):
        if settings.DEBUG and request.GET.has_key('prof'):
            self.tmpfile = tempfile.NamedTemporaryFile()
            self.prof = hotshot.Profile(self.tmpfile.name)

    def __process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG and request.GET.has_key('prof'):
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if settings.DEBUG:
            if request.GET.has_key('mem_prof'):
                import guppy
                out = StringIO()
                heapy = guppy.hpy()
                out.write(str(heapy.heap()))
                out.write('\n\n\n\n')
                out_str = out.getvalue()

                if response and response.content and out_str:
                    response.content = "<pre>" + out_str + "</pre>"
            elif request.GET.has_key('mem_on'):
                from guppy.heapy.Remote import on
                on()
            elif request.GET.has_key('mem_off'):
                from guppy.heapy.Remote import off
                off()

        return response
