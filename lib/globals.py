import logging
import os

MYDIR = os.path.abspath(os.path.dirname( os.path.dirname('__file__') ))

ANSI2HTML = os.path.join( MYDIR, "share/ansi2html.sh" )

LOG_FILE  = os.path.join( MYDIR, 'log/main.log' )
FILE_QUERIES_LOG  = os.path.join( MYDIR, 'log/queries.log' )
TEMPLATES = os.path.join( MYDIR, 'share/templates' )
STATIC    = os.path.join( MYDIR, 'share/static' )

def error(text):
    if not text.startswith('Too many queries'):
        print text
    logging.error("ERROR "+text)
    raise RuntimeError(text)

def log(text):
    if not text.startswith('Too many queries'):
        print text
        logging.info(text)


