# epydoc -- Command line interface
#
# Copyright (C) 2005 Edward Loper
# Author: Edward Loper <edloper@loper.org>
# URL: <http://epydoc.sf.net>
#
# $Id$

"""
Command-line interface for epydoc.

[xx] this usage message is probably a little out-of-date.

Usage::

 epydoc [OPTIONS] MODULES...
 
     MODULES...                The Python modules to document.
     --html                    Generate HTML output (default).
     --latex                   Generate LaTeX output.
     --pdf                     Generate pdf output, via LaTeX.
     --check                   Run documentation completeness checks.
     -o DIR, --output DIR      The output directory.
     -n NAME, --name NAME      The documented project's name.
     -u URL, --url URL         The documented project's url.
     -t PAGE, --top PAGE       The top page for the HTML documentation.
     -c SHEET, --css SHEET     CSS stylesheet for HTML files.
     --private-css SHEET       CSS stylesheet for private objects.
     --inheritance STYLE       The format for showing inherited objects.
     --encoding ENCODING       Output encoding for HTML files (default: utf-8).
     -V, --version             Print the version of epydoc.
     -h, -?, --help, --usage   Display a usage message.
     -h TOPIC, --help TOPIC    Display information about TOPIC (docformat,
                               css, inheritance, usage, or version).

 Run \"epydoc --help\" for a complete option list.
 See the epydoc(1) man page for more information.

Verbosity levels::

                Progress    Markup warnings   Warnings   Errors
 -3               none            no             no        no
 -2               none            no             no        yes
 -1               none            no             yes       yes
  0 (default)     bar             no             yes       yes
  1               bar             yes            yes       yes
  2               list            yes            yes       yes
"""
__docformat__ = 'epytext en'

import sys, os, time
from optparse import OptionParser, OptionGroup
import epydoc
from epydoc.docbuilder import build_doc_index
from epydoc.docwriter.html import HTMLWriter
from epydoc.docwriter.plaintext import PlaintextWriter
from epydoc import log
from epydoc.util import wordwrap
from epydoc.apidoc import UNKNOWN
from epydoc import docstringparser

######################################################################
## Argument Parsing
######################################################################

def parse_arguments():
    # Construct the option parser.
    usage = '%prog ACTION [options] NAMES...'
    version = "Epydoc, version %s" % epydoc.__version__
    optparser = OptionParser(usage=usage, version=version)
    action_group = OptionGroup(optparser, 'Actions')
    options_group = OptionGroup(optparser, 'Options')

    # Add options -- Actions
    action_group.add_option(                                # --html
        "--html", action="store_const", dest="action", const="html",
        help="Write HTML output.")
    action_group.add_option(                                # --latex
        "--text", action="store_const", dest="action", const="text",
        help="Write plaintext output. (not implemented yet)")
    action_group.add_option(                                # --latex
        "--latex", action="store_const", dest="action", const="latex",
        help="Write LaTeX output. (not implemented yet)")
    action_group.add_option(                                # --dvi
        "--dvi", action="store_const", dest="action", const="dvi",
        help="Write DVI output. (not implemented yet)")
    action_group.add_option(                                # --ps
        "--ps", action="store_const", dest="action", const="ps",
        help="Write Postscript output. (not implemented yet)")
    action_group.add_option(                                # --pdf
        "--pdf", action="store_const", dest="action", const="pdf",
        help="Write PDF output. (not implemented yet)")
    action_group.add_option(                                # --check
        "--check", action="store_const", dest="action", const="check",
        help="Check completeness of docs. (not implemented yet)")

    # Options I haven't ported over yet are...
    # separate-classes (??) -- for latex only
    # command-line-order (??)
    # ignore-param-mismatch -- not implemented yet, but will be related
    #                          to DocInheriter
    # tests=...
    # --no-markup-warnings ?
    # --no-source, --incl-source?
    

    # Add options -- Options
    options_group.add_option(                                # --output
        "--output", "-o", dest="target", metavar="PATH",
        help="The output directory.  If PATH does not exist, then "
        "it will be created.")
    options_group.add_option(                                # --show-imports
        "--inheritance", dest="inheritance", metavar="STYLE",
        help="The format for showing inheritance objects.  STYLE "
        "should be \"grouped\", \"listed\", or \"inherited\".")
    options_group.add_option(                                # --output
        "--docformat", dest="docformat", metavar="NAME",
        help="The default markup language for docstrings.  Defaults "
        "to \"%default\".")
    options_group.add_option(                                # --css
        "--css", dest="css", metavar="STYLESHEET",
        help="The CSS stylesheet.  STYLESHEET can be either a "
        "builtin stylesheet or the name of a CSS file.")
    options_group.add_option(                                # --name
        "--name", dest="prj_name", metavar="NAME",
        help="The documented project's name (for the navigation bar).")
    options_group.add_option(                                # --url
        "--url", dest="prj_url", metavar="URL",
        help="The documented project's URL (for the navigation bar).")
    options_group.add_option(                                # --navlink
        "--navlink", dest="prj_link", metavar="HTML",
        help="HTML code for a navigation link to place in the "
        "navigation bar.")
    options_group.add_option(                                # --top
        "--top", dest="top_page", metavar="PAGE",
        help="The \"top\" page for the HTML documentation.  PAGE can "
        "be a URL, the name of a module or class, or one of the "
        "special names \"trees.html\", \"indices.html\", or \"help.html\"")
    # [XX] output encoding isnt' implemented yet!!
    options_group.add_option(                                # --encoding
        "--encoding", dest="encoding", metavar="NAME",
        help="The output encoding for generated HTML files.")
    options_group.add_option(                                # --help-file
        "--help-file", dest="help_file", metavar="FILE",
        help="An alternate help file.  FILE should contain the body "
        "of an HTML file -- navigation bars will be added to it.")
    options_group.add_option(                                # --frames
        "--show-frames", action="store_true", dest="show_frames",
        help="Include frames in the output.")
    options_group.add_option(                                # --no-frames
        "--no-frames", action="store_false", dest="show_frames",
        help="Do not include frames in the output.")
    options_group.add_option(                                # --private
        "--show-private", action="store_true", dest="show_private",
        help="Include private variables in the output.")
    options_group.add_option(                                # --no-private
        "--no-private", action="store_false", dest="show_private",
        help="Do not include private variables in the output.")
    options_group.add_option(                                # --show-imports
        "--show-imports", action="store_true", dest="show_imports",
        help="List each module's imports.")
    options_group.add_option(                                # --show-imports
        "--no-imports", action="store_false", dest="show_imports",
        help="Do not list each module's imports.")
    options_group.add_option(                                # --quiet
        "--quiet", "-q", action="count", dest="quiet",
        help="Decrease the verbosity.")
    options_group.add_option(                                # --verbose
        "--verbose", "-v", action="count", dest="verbose",
        help="Increase the verbosity.")
    options_group.add_option(                                # --debug
        "--debug", action="store_true", dest="debug",
        help="Show full tracebacks for internal errors.")
    options_group.add_option(                                # --parse-only
        "--parse-only", action="store_false", dest="introspect",
        help="Get all information from parsing (don't introspect)")
    options_group.add_option(                                # --introspect-only
        "--introspect-only", action="store_false", dest="parse",
        help="Get all information from introspecting (don't parse)")
    options_group.add_option(
        "--profile", action="store_true", dest="profile",
        help="Run the profiler.  Output will be written to profile.out")

    # Add the option groups.
    optparser.add_option_group(action_group)
    optparser.add_option_group(options_group)

    # Set the option parser's defaults.
    optparser.set_defaults(action="html", show_frames=True,
                           docformat='epytext', 
                           show_private=True, show_imports=False,
                           inheritance="grouped",
                           verbose=0, quiet=0,
                           parse=True, introspect=True,
                           debug=epydoc.DEBUG, profile=False)

    # Parse the arguments.
    options, names = optparser.parse_args()
    
    # Check to make sure all options are valid.
    if len(names) == 0:
        optparser.error("No names specified.")
    if options.inheritance not in ('grouped', 'listed', 'included'):
        optparser.error("Bad inheritance style.  Valid options are "
                        "grouped, listed, and included.")
    if not options.parse and not options.introspect:
        optparser.error("Invalid option combination: --parse-only "
                        "and --introspect-only.")
    if options.action == 'text' and len(names) > 1:
        optparser.error("--text option takes only one name.")

    # Calculate verbosity.
    options.verbosity = options.verbose - options.quiet

    # The target default depends on the action.
    if options.target is None:
        options.target = options.action
    
    # Return parsed args.
    return options, names

######################################################################
## Interface
######################################################################

def main(options, names):
    if options.action == 'text':
        if options.parse and options.introspect:
            options.parse = False
    
    # Set up the logger
    if options.action == 'text':
        logger = None # no logger for text output.
    elif options.verbosity > 1:
        logger = ConsoleLogger(options.verbosity)
        log.register_logger(logger)
    else:
        # Each number is a rough approximation of how long we spend on
        # that task, used to divide up the unified progress bar.
        stages = [40,  # Building documentation
                  7,   # Merging parsed & introspected information
                  1,   # Linking imported variables
                  3,   # Indexing documentation
                  30,  # Parsing Docstrings
                  1,   # Inheriting documentation
                  2,   # Sorting & Grouping
                  100] # Generating output
        if options.parse and not options.introspect:
            del stages[1] # no merging
        if options.introspect and not options.parse:
            del stages[1:3] # no merging or linking
        logger = UnifiedProgressConsoleLogger(options.verbosity, stages)
        log.register_logger(logger)

    # create the output directory.
    if options.action != 'text':
        if os.path.exists(options.target):
            if not os.path.isdir(options.target):
                return log.error("%s is not a directory" % options.target)
        else:
            try:
                os.mkdir(options.target)
            except Exception, e:
                return log.error(e)

    # Set the default docformat
    docstringparser.DEFAULT_DOCFORMAT = options.docformat

    # Build docs for the named values.
    docindex = build_doc_index(names, options.introspect, options.parse,
                               add_submodules=(options.action!='text'))

    # Perform the specified action.
    if options.action == 'html':
        html_writer = HTMLWriter(docindex, **options.__dict__)
        if options.verbose > 0:
            log.start_progress('Writing HTML docs to %r' % options.target)
        else:
            log.start_progress('Writing HTML docs')
            html_writer.write(options.target)
            log.end_progress()
    elif options.action == 'text':
        # hmm
        log.start_progress('Writing output')
        plaintext_writer = PlaintextWriter()
        s = ''
        for apidoc in docindex.root:
            s += plaintext_writer.write(apidoc)
        log.end_progress()
        print s
    else:
        print >>sys.stderr, '\nUnsupported action %s!' % options.action

    # If we supressed docstring warnings, then let the user know.
    if logger is not None and logger.supressed_docstring_warning:
        log.warning("%d markup error(s) were found while processing "
                    "docstrings.  Use the verbose switch (-v) to "
                    "display markup errors." %
                    logger.supressed_docstring_warning)

    # Basic timing breakdown:
    if options.verbosity >= 2 and logger is not None:
        logger.print_times()

def cli():
    # Parse command-line arguments.
    options, names = parse_arguments()

    try:
        if options.profile:
            _profile()
        else:
            main(options, names)
    except KeyboardInterrupt:
        print '\n\n'
        print >>sys.stderr, 'Keyboard interrupt.'
    except:
        if options.debug: raise
        print '\n\n'
        exc_info = sys.exc_info()
        if isinstance(exc_info[0], basestring): e = exc_info[0]
        else: e = exc_info[1]
        print >>sys.stderr, ('\nUNEXPECTED ERROR:\n'
                             '%s\n' % (str(e) or e.__class__.__name__))
        print >>sys.stderr, 'Use --debug to see trace information.'

def _profile():
    import profile, pstats, code
    profile.run('main(*parse_arguments())', 'profile.out')

    # Use the pstats statistical browser.  This is made unnecessarily
    # difficult because the whole browser is wrapped in an
    # if __name__=='__main__' clause.
    try:
        pstats_pyfile = os.path.splitext(pstats.__file__)[0]+'.py'
        sys.argv = ['pstats.py', 'profile.out']
        print
        execfile(pstats_pyfile, {'__name__':'__main__'})
    except:
        print 'Could not run the pstats browser'
    
    print 'Profiling output is in "profile.out"'
        
######################################################################
## Logging
######################################################################

import curses

class ConsoleLogger(log.Logger):
    TERM_WIDTH = 75
    """The width of the console terminal."""
    # Terminal control strings:
    _TERM_CR = _TERM_CLR_EOL = _TERM_UP = ''
    _TERM_HIDE_CURSOR = _TERM_HIDE_CURSOR = ''
    _TERM_NORM = _TERM_BOLD = ''
    _TERM_RED = _TERM_YELLOW = _TERM_GREEN = _TERM_CYAN = _TERM_BLUE = ''
    _DISABLE_COLOR = False
    
    def __init__(self, verbosity):
        self._verbosity = verbosity
        self._progress = None
        self._message_blocks = []
        # For ETA display:
        self._progress_start_time = None
        # For per-task times:
        self._task_times = []
        self._progress_header = None
        
        self.supressed_docstring_warning = 0
        """This variable will be incremented once every time a
        docstring warning is reported tothe logger, but the verbosity
        level is too low for it to be displayed."""
        
        # Examine the capabilities of our terminal.
        if sys.stdout.isatty():
            try:
                curses.setupterm()
                self._TERM_CR = curses.tigetstr('cr') or ''
                self.TERM_WIDTH = curses.tigetnum('cols')-1
                self._TERM_CLR_EOL = curses.tigetstr('el') or ''
                self._TERM_NORM =  curses.tigetstr('sgr0') or ''
                self._TERM_HIDE_CURSOR = curses.tigetstr('civis') or ''
                self._TERM_SHOW_CURSOR = curses.tigetstr('cnorm') or ''
                self._TERM_UP = curses.tigetstr('cuu1') or ''
                if self._TERM_NORM:
                    self._TERM_BOLD = curses.tigetstr('bold') or ''
                    term_setf = curses.tigetstr('setf')
                    if term_setf or self._DISABLE_COLOR:
                        self._TERM_RED = curses.tparm(term_setf, 4) or ''
                        self._TERM_YELLOW = curses.tparm(term_setf, 6) or ''
                        self._TERM_GREEN = curses.tparm(term_setf, 2) or ''
                        self._TERM_CYAN = curses.tparm(term_setf, 3) or ''
                        self._TERM_BLUE = curses.tparm(term_setf, 1) or ''
            except:
                pass

        # Set the progress bar mode.
        if verbosity >= 2: self._progress_mode = 'list'
        elif verbosity >= 0:
            if self.TERM_WIDTH < 15:
                self._progress_mode = 'simple-bar'
            if self._TERM_CR and self._TERM_CLR_EOL and self._TERM_UP:
                self._progress_mode = 'multiline-bar'
            elif self._TERM_CR and self._TERM_CLR_EOL:
                self._progress_mode = 'bar'
            else:
                self._progress_mode = 'simple-bar'
        else: self._progress_mode = 'hide'

    def start_block(self, header):
        self._message_blocks.append( (header, []) )

    def end_block(self):
        header, messages = self._message_blocks.pop()
        if messages:
            width = self.TERM_WIDTH - 5 - 2*len(self._message_blocks)
            prefix = self._TERM_CYAN+self._TERM_BOLD+"| "+self._TERM_NORM
            divider = self._TERM_CYAN + self._TERM_BOLD + '+' + '-'*(width-1)
            # Mark up the header:
            header = wordwrap(header, right=width-2).rstrip()
            header = '\n'.join([prefix+self._TERM_CYAN+l+self._TERM_NORM
                                for l in header.split('\n')])
            # Indent the body:
            body = '\n'.join(messages)
            body = '\n'.join([prefix+'  '+l for l in body.split('\n')])
            # Put it all together:
            message = divider + '\n' + header + '\n' + body + '\n'
            self._report(message, rstrip=False)
            
    def _format(self, prefix, message, color):
        """
        Rewrap the message; but preserve newlines, and don't touch any
        lines that begin with spaces.
        """
        lines = message.split('\n')
        startindex = indent = len(prefix)
        for i in range(len(lines)):
            if lines[i].startswith(' '):
                lines[i] = ' '*(indent-startindex) + lines[i] + '\n'
            else:
                width = self.TERM_WIDTH - 5 - 4*len(self._message_blocks)
                lines[i] = wordwrap(lines[i], indent, width, startindex)
            startindex = 0
        return color+prefix+self._TERM_NORM+''.join(lines)

    def log(self, level, message):
        if self._verbosity >= -2 and level >= log.ERROR:
            message = self._format('  Error: ', message, self._TERM_RED)
        elif self._verbosity >= -1 and level >= log.WARNING:
            message = self._format('Warning: ', message, self._TERM_YELLOW)
        elif self._verbosity >= 1 and level >= log.DOCSTRING_WARNING:
            message = self._format('Warning: ', message, self._TERM_YELLOW)
        elif self._verbosity >= 3 and level >= log.INFO:
            message = self._format('   Info: ', message, self._TERM_NORM)
        elif epydoc.DEBUG and level == log.DEBUG:
            message = self._format('  Debug: ', message, self._TERM_CYAN)
        else:
            if level >= log.DOCSTRING_WARNING:
                self.supressed_docstring_warning += 1
            return
            
        self._report(message)

    def _report(self, message, rstrip=True):
        if rstrip: message = message.rstrip()
        
        if self._message_blocks:
            self._message_blocks[-1][-1].append(message)
        else:
            # If we're in the middle of displaying a progress bar,
            # then make room for the message.
            if self._progress_mode == 'simple-bar':
                if self._progress is not None:
                    print
                    self._progress = None
            if self._progress_mode == 'bar':
                sys.stdout.write(self._TERM_CR+self._TERM_CLR_EOL)
            if self._progress_mode == 'multiline-bar':
                sys.stdout.write((self._TERM_CLR_EOL + '\n')*2 +
                                 self._TERM_CLR_EOL + self._TERM_UP*2)

            # Display the message message.
            print message
            sys.stdout.flush()
                
    def progress(self, percent, message=''):
        percent = min(1.0, percent)
        message = '%s' % message
        
        if self._progress_mode == 'list':
            if message:
                print '[%3d%%] %s' % (100*percent, message)
                sys.stdout.flush()
                
        elif self._progress_mode == 'bar':
            dots = int((self.TERM_WIDTH/2-5)*percent)
            background = '-'*(self.TERM_WIDTH/2-5)
            
            if len(message) > self.TERM_WIDTH/2:
                message = message[:self.TERM_WIDTH/2-3]+'...'

            sys.stdout.write(self._TERM_CR + '  ' + self._TERM_GREEN + '[' +
                             self._TERM_BOLD + '='*dots + background[dots:] +
                             self._TERM_NORM + self._TERM_GREEN + '] ' +
                             self._TERM_NORM + message + self._TERM_CLR_EOL)
            sys.stdout.flush()
            self._progress = percent
        elif self._progress_mode == 'multiline-bar':
            dots = int((self.TERM_WIDTH-10)*percent)
            background = '-'*(self.TERM_WIDTH-10)
            
            if len(message) > self.TERM_WIDTH-10:
                message = message[:self.TERM_WIDTH-10-3]+'...'
            else:
                message = message.center(self.TERM_WIDTH-10)

            time_elapsed = time.time()-self._progress_start_time
            if percent > 0:
                time_remain = (time_elapsed / percent) * (1-percent)
            else:
                time_remain = 0

            sys.stdout.write(
                # Line 1:
                self._TERM_CLR_EOL + '      ' +
                '%-8s' % self._timestr(time_elapsed) +
                self._TERM_BOLD + 'Progress:'.center(self.TERM_WIDTH-26) +
                self._TERM_NORM + '%8s' % self._timestr(time_remain) + '\n' +
                # Line 2:
                self._TERM_CLR_EOL + ('%3d%% ' % (100*percent)) +
                self._TERM_GREEN + '[' +  self._TERM_BOLD + '='*dots +
                background[dots:] + self._TERM_NORM + self._TERM_GREEN +
                ']' + self._TERM_NORM + '\n' +
                # Line 3:
                self._TERM_CLR_EOL + '      ' + message + self._TERM_CR +
                self._TERM_UP + self._TERM_UP)
            
            sys.stdout.flush()
            self._progress = percent
        elif self._progress_mode == 'simple-bar':
            if self._progress is None:
                sys.stdout.write('  [')
                self._progress = 0.0
            dots = int((self.TERM_WIDTH-2)*percent)
            progress_dots = int((self.TERM_WIDTH-2)*self._progress)
            if dots > progress_dots:
                sys.stdout.write('.'*(dots-progress_dots))
                sys.stdout.flush()
                self._progress = percent

    def _timestr(self, dt):
        dt = int(dt)
        if dt >= 3600:
            return '%d:%02d:%02d' % (dt/3600, dt%3600/60, dt%60)
        else:
            return '%02d:%02d' % (dt/60, dt%60)

    def start_progress(self, header=None):
        if self._progress is not None:
            raise ValueError
        self._progress = None
        self._progress_start_time = time.time()
        self._progress_header = header
        if self._progress_mode != 'hide' and header:
            print self._TERM_BOLD + header + self._TERM_NORM

    def end_progress(self):
        self.progress(1.)
        if self._progress_mode == 'bar':
            sys.stdout.write(self._TERM_CR+self._TERM_CLR_EOL)
        if self._progress_mode == 'multiline-bar':
                sys.stdout.write((self._TERM_CLR_EOL + '\n')*2 +
                                 self._TERM_CLR_EOL + self._TERM_UP*2)
        if self._progress_mode == 'simple-bar':
            print ']'
        self._progress = None
        self._task_times.append( (time.time()-self._progress_start_time,
                                  self._progress_header) )

    def print_times(self):
        print
        print 'Timing summary:'
        total = sum([time for (time, task) in self._task_times])
        max_t = max([time for (time, task) in self._task_times])
        for (time, task) in self._task_times:
            task = task[:31]
            print '  %s%s %7.1fs' % (task, '.'*(35-len(task)), time),
            if self.TERM_WIDTH > 55:
                print '|'+'=' * int((self.TERM_WIDTH-53) * time / max_t)
            else:
                print
        print

class UnifiedProgressConsoleLogger(ConsoleLogger):
    def __init__(self, verbosity, stages):
        self.stage = 0
        self.stages = stages
        self.task = None
        ConsoleLogger.__init__(self, verbosity)
        
    def progress(self, percent, message=''):
        #p = float(self.stage-1+percent)/self.stages
        i = self.stage-1
        p = ((sum(self.stages[:i]) + percent*self.stages[i]) /
             float(sum(self.stages)))

        if message == UNKNOWN: message = None
        if message: message = '%s: %s' % (self.task, message)
        ConsoleLogger.progress(self, p, message)

    def start_progress(self, header=None):
        self.task = header
        if self.stage == 0:
            ConsoleLogger.start_progress(self)
        self.stage += 1

    def end_progress(self):
        if self.stage == len(self.stages):
            ConsoleLogger.end_progress(self)

    def print_times(self):
        pass

######################################################################
## main
######################################################################

if __name__ == '__main__':
    try:
        cli()
    except:
        print '\n\n'
        raise

