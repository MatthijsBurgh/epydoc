############################################################
##  epydoc Makefile
##
##  Edward Loper
############################################################

# Python source files
PY_SRC = $(wildcard src/epydoc/*.py)
EXAMPLES_SRC = $(wildcard doc/*.py)
DOCS = $(wildcard doc/*.html) $(wildcard doc/*.css) $(wildcard doc/*.png)

# The location of the webpage.
HOST = shell.sf.net
DIR = /home/groups/e/ep/epydoc/htdocs

# The local location to build the web materials
WEBDIR = html
API = doc/api
EXAMPLES = doc/examples
STDLIB = stdlib

############################################################

.PHONY: all usage clean distributions web webpage xfer local
.PHONY: checkdocs refdocs examples stdlib

all: usage

usage:
	@echo "Usage:"
	@echo "  make webpage -- build the webpage and copy it to sourceforge"
	@echo "  make refdocs -- build the API reference docs"
	@echo "  make checkdoc -- check the documentation completeness"
	@echo "  make distributions -- build the distributions"
	@echo "  make clean -- remove all built files"
	@echo "  make stdlib -- build docs for the Python Standard Library"

clean:
	$(MAKE) -C src clean
	rm -rf ${WEBDIR} ${API} ${EXAMPLES} ${STDLIB}
	rm -rf .*.up2date

distributions: src/dist/.up2date
src/dist/.up2date: $(PY_SRC)
	$(MAKE) -C src distributions

web: xfer
webpage: xfer
xfer: .html.up2date
	rsync -arzv -e ssh ${WEBDIR}/* $(HOST):$(DIR)

local: .html.up2date
	cp -r ${WEBDIR}/* /var/www/epydoc

checkdocs:
	epydoc --check -v ${PY_SRC}

.html.up2date: refdocs examples #distributions
	rm -rf ${WEBDIR}
	mkdir -p ${WEBDIR}
	cp -r ${DOCS} ${WEBDIR}
	cp -r ${API} ${WEBDIR}
	cp -r ${EXAMPLES} ${WEBDIR}
#	cp -r src/dist/epydoc* ${WEBDIR}

# Use plaintext docformat by default.  But this is overridden by the
# __docformat__ strings in each epydoc module.  (So just
# xml.dom.minidom gets plaintext docstrings).
refdocs: .refdocs.up2date
.refdocs.up2date: ${PY_SRC}
	rm -rf ${API}
	mkdir -p ${API}
	epydoc -o ${API} -n epydoc -u http://epydoc.sourceforge.net \
	       --css blue --private-css green -vv --debug \
	       --docformat plaintext ${PY_SRC} xml.dom.minidom
	touch .refdocs.up2date

examples: .examples.up2date
.examples.up2date: ${EXAMPLES_SRC} ${PY_SRC}
	rm -rf ${EXAMPLES}
	mkdir -p ${EXAMPLES}
	epydoc -o ${EXAMPLES} -n epydoc -u http://epydoc.sourceforge.net \
	       --no-private --css blue ${EXAMPLES_SRC} sre
	touch .examples.up2date

#//////////////////////////////////////////////////////////////////////
# Build documentation for the Python Standard Library
SLNAME = '<font size="-2">Python&nbsp;2.1<br>Standard&nbsp;Library</font>'
SLURL = 'http://www.python.org/doc/2.1/lib/lib.html'
SLFILES = $(shell find /usr/lib/python2.1/ -name '*.py' -o -name '*.so' \
	      |grep -v '/python2.1/config/' \
	      |grep -v '/python2.1/lib-old/' \
	      |grep -v '/python2.1/site-packages/')
stdlib:
	rm -rf ${STDLIB}
	mkdir -p ${STDLIB}
	epydoc -o ${STDLIB} -v -q -c white --show-imports \
	       -n ${SLNAME} -u ${SLURL} --docformat plaintext \
	       --builtins ${SLFILES}

##//////////////////////////////////////////////////////////////////////
## Build documentation for everything installed on this system.
## Exclude the following libraries:
##   - lib-old/ni.py: Implements packages, but they're already standard
##   - eric: it fails and dies in an un-catchable way
##   - gnome/score.py: it forks a new process
#LNAME = '<font size="-2">Python&nbsp;2.1<br>Standard&nbsp;Library</font>'
#LIBS = $(shell find /usr/lib/python2.1/ -name '*.py' -o -name '*.so' \
#	      |grep -v '/gnome/score.py' \
#	      |grep -v '/eric/' \
#	      |grep -v '/lib-old/ni.py')
##	      |grep -v '/site-packages/') # for now (?)
#
#libdocs:
#	mkdir -p libs
#	epydoc -o libs -f -vvvv -q -n ${LNAME} \
#	       -u http://www.python.org -c white ${LIBS} -builtins- #\
##	       >libs/libdocs.out 2>libs/libdocs.err
#	rm -f TESTLispG* SQLTEST.mar sqlwhere.py 
#
