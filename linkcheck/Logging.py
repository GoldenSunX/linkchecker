""" linkcheck/Logger.py

    Copyright (C) 2000  Bastian Kleineidam

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

Every Logger has to implement the following functions:
init(self)
  Called once to initialize the Logger. Why do we not use __init__(self)?
  Because we initialize the start time in init and __init__ gets not
  called at the time the checking starts but when the logger object is
  created.

newUrl(self,urlData)
  Called every time an url finished checking. All data we checked is in
  the UrlData object urlData.

endOfOutput(self)
  Called at the end of checking to close filehandles and such.

Passing parameters to the constructor:
__init__(self, **args)
  The args dictionary is filled in Config.py. There you can specify
  default parameters. Adjust these parameters in the configuration
  files in the appropriate logger section.
"""
import sys,time,string
import Config, StringUtil
import linkcheck
_ = linkcheck._

# HTML shortcuts
RowEnd="</td></tr>\n"

# keywords
KeyWords = ["Real URL",
    "Result",
    "Base",
    "Parent URL",
    "Info",
    "Warning",
    "D/L Time",
    "Check Time",
    "URL",
]
MaxIndent = max(map(lambda x: len(_(x)), KeyWords))+1
Spaces = {}
for key in KeyWords:
    Spaces[key] = " "*(MaxIndent - len(_(key)))

EntityTable = {
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;',
    '"': '&quot;',
    '\'': '&apos;',
}

def quote(s):
    res = list(s)
    for i in range(len(res)):
        c = res[i]
        res[i] = EntityTable.get(c, c)
    return string.joinfields(res, '')

# return formatted time
def _strtime(t):
    return time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(t))

class StandardLogger:
    """Standard text logger.
    Informal text output format spec:
    Output consists of a set of URL logs separated by one or more
    blank lines.
    A URL log consists of two or more lines. Each line consists of
    keyword and data, separated by whitespace.
    Unknown keywords will be ignored.
    """

    def __init__(self, **args):
        self.errors = 0
        self.warnings = 0
        if args.has_key('fileoutput'):
            self.fd = open(args['filename'], "w")
	elif args.has_key('fd'):
            self.fd = args['fd']
        else:
	    self.fd = sys.stdout


    def init(self):
        self.starttime = time.time()
        self.fd.write("%s\n%s\n" % (Config.AppInfo, Config.Freeware))
        self.fd.write(_("Get the newest version at %s\n") % Config.Url)
        self.fd.write(_("Write comments and bugs to %s\n\n") % Config.Email)
        self.fd.write(_("Start checking at %s\n") % _strtime(self.starttime))
        self.fd.flush()


    def newUrl(self, urldata):
        self.fd.write("\n"+_("URL")+Spaces["URL"]+urldata.urlName)
        if urldata.cached:
            self.fd.write(_(" (cached)\n"))
        else:
            self.fd.write("\n")
        if urldata.parentName:
            self.fd.write(_("Parent URL")+Spaces["Parent URL"]+
	                  urldata.parentName+_(", line ")+
	                  str(urldata.line)+"\n")
        if urldata.baseRef:
            self.fd.write(_("Base")+Spaces["Base"]+urldata.baseRef+"\n")
        if urldata.url:
            self.fd.write(_("Real URL")+Spaces["Real URL"]+urldata.url+"\n")
        if urldata.downloadtime:
            self.fd.write(_("D/L Time")+Spaces["D/L Time"]+
	                  _("%.3f seconds\n") % urldata.downloadtime)
        if urldata.checktime:
            self.fd.write(_("Check Time")+Spaces["Check Time"]+
	                  _("%.3f seconds\n") % urldata.checktime)
        if urldata.infoString:
            self.fd.write(_("Info")+Spaces["Info"]+
	                  StringUtil.indent(
                          StringUtil.blocktext(urldata.infoString, 65),
			  MaxIndent)+"\n")
        if urldata.warningString:
            self.warnings = self.warnings+1
            self.fd.write(_("Warning")+Spaces["Warning"]+
	                  StringUtil.indent(
                          StringUtil.blocktext(urldata.warningString, 65),
			  MaxIndent)+"\n")
        
        self.fd.write(_("Result")+Spaces["Result"])
        if urldata.valid:
            self.fd.write(urldata.validString+"\n")
        else:
            self.errors = self.errors+1
            self.fd.write(urldata.errorString+"\n")
        self.fd.flush()


    def endOfOutput(self, linknumber=-1):
        self.fd.write(_("\nThats it. "))

        if self.warnings==1:
            self.fd.write(_("1 warning, "))
        else:
            self.fd.write(str(self.warnings)+_(" warnings, "))
        if self.errors==1:
            self.fd.write(_("1 error"))
        else:
            self.fd.write(str(self.errors)+_(" errors"))
        if linknumber >= 0:
            if linknumber == 1:
                self.fd.write(_(" in 1 link"))
            else:
                self.fd.write(_(" in %d links") % linknumber)
        self.fd.write(_(" found\n"))
        self.stoptime = time.time()
        duration = self.stoptime - self.starttime
        name = _("seconds")
        self.fd.write(_("Stopped checking at %s") % _strtime(self.stoptime))
        if duration > 60:
            duration = duration / 60
            name = _("minutes")
        if duration > 60:
            duration = duration / 60
            name = _("hours")
        self.fd.write("	(%.3f %s)\n" % (duration, name))
        self.fd.flush()
        self.fd = None



class HtmlLogger(StandardLogger):
    """Logger with HTML output"""

    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.colorbackground = args['colorbackground']
        self.colorurl = args['colorurl']
        self.colorborder = args['colorborder']
        self.colorlink = args['colorlink']
        self.tablewarning = args['tablewarning']
        self.tableerror = args['tableerror']
        self.tableok = args['tableok']

    def init(self):
        self.starttime = time.time()
        self.fd.write('<!DOCTYPE html PUBLIC "-//W3C//DTD html 4.0//'+
              linkcheck.LANG+
	      '">\n<html><head><title>'+Config.App+"</title>\n"
	      '<style type="text/css">\n<!--\n'
              "h2 { font-family: Verdana,sans-serif; font-size: 22pt; \n"
	      "     font-style: bold; font-weight: bold }\n"
              "body { font-family: Arial,sans-serif; font-size: 11pt }\n"
              "td   { font-family: Arial,sans-serif; font-size: 11pt }\n"
              "code { font-family: Courier }\n"
              "a:hover      { color: #34a4ef }\n"
	      "//-->\n</style>\n</head>\n"+
              "<body bgcolor="+self.colorbackground+" link="+self.colorlink+
              " vlink="+self.colorlink+" alink="+self.colorlink+">"+
              "<center><h2>"+Config.App+"</h2></center>"+
              "<br><blockquote>"+Config.Freeware+"<br><br>"+
              (_("Start checking at %s\n") % _strtime(self.starttime))+
	      "<br><br>")
        self.fd.flush()


    def newUrl(self, urlData):
        self.fd.write('<table align=left border="0" cellspacing="0"'
              ' cellpadding="1" bgcolor='+self.colorborder+' summary="Border"'
              '><tr><td><table align="left" border="0" cellspacing="0"'
              ' cellpadding="3" summary="checked link" bgcolor='+
	      self.colorbackground+
              "><tr><td bgcolor="+self.colorurl+">"+
              "URL</td><td bgcolor="+self.colorurl+">"+urlData.urlName)
        if urlData.cached:
            self.fd.write(_(" (cached)\n"))
        self.fd.write(RowEnd)
        
        if urlData.parentName:
            self.fd.write("<tr><td>"+_("Parent URL")+"</td><td>"+
			  '<a href="'+urlData.parentName+'">'+
                          urlData.parentName+"</a> line "+str(urlData.line)+
                          RowEnd)
        if urlData.baseRef:
            self.fd.write("<tr><td>"+_("Base")+"</td><td>"+
	                  urlData.baseRef+RowEnd)
        if urlData.url:
            self.fd.write("<tr><td>"+_("Real URL")+"</td><td>"+
	                  "<a href=\""+urlData.url+
			  '">'+urlData.url+"</a>"+RowEnd)
        if urlData.downloadtime:
            self.fd.write("<tr><td>"+_("D/L Time")+"</td><td>"+
	                  (_("%.3f seconds") % urlData.downloadtime)+RowEnd)
        if urlData.checktime:
            self.fd.write("<tr><td>"+_("Check Time")+
	                  "</td><td>"+
			  (_("%.3f seconds") % urlData.checktime)+RowEnd)
        if urlData.infoString:
            self.fd.write("<tr><td>"+_("Info")+"</td><td>"+
	                  StringUtil.htmlify(urlData.infoString)+RowEnd)
        if urlData.warningString:
            self.warnings = self.warnings+1
            self.fd.write("<tr>"+self.tablewarning+_("Warning")+
	                  "</td>"+self.tablewarning+
			  urlData.warningString+RowEnd)
        if urlData.valid:
            self.fd.write("<tr>"+self.tableok+_("Result")+"</td>"+
	                  self.tableok+urlData.validString+RowEnd)
        else:
            self.errors = self.errors+1
            self.fd.write("<tr>"+self.tableerror+_("Result")+
	                  "</td>"+self.tableerror+
			  urlData.errorString++RowEnd)

        self.fd.write("</table></td></tr></table><br clear=all><br>")
        self.fd.flush()


    def endOfOutput(self, linknumber=-1):
        self.fd.write(_("\nThats it. "))
        if self.warnings==1:
            self.fd.write(_("1 warning, "))
        else:
            self.fd.write(str(self.warnings)+_(" warnings, "))
        if self.errors==1:
            self.fd.write(_("1 error"))
        else:
            self.fd.write(str(self.errors)+_(" errors"))
        if linknumber >= 0:
            if linknumber == 1:
                self.fd.write(_(" in 1 link"))
            else:
                self.fd.write(_(" in %d links") % linknumber)
        self.fd.write(_(" found\n")+"<br>")
        self.stoptime = time.time()
        duration = self.stoptime - self.starttime
        name = _("seconds")
        self.fd.write(_("Stopped checking at %s") % _strtime(self.stoptime))
        if duration > 60:
            duration = duration / 60
            name = _("minutes")
        if duration > 60:
            duration = duration / 60
            name = _("hours")
        self.fd.write("	(%.3f %s)\n" % (duration, name))
	self.fd.write("</blockquote><br><hr noshade size=1><small>"+
             Config.HtmlAppInfo+"<br>")
	self.fd.write(_("Get the newest version at %s\n") %\
             ('<a href="'+Config.Url+'" target="_top">'+Config.Url+
	      "</a>.<br>"))
        self.fd.write(_("Write comments and bugs to %s\n\n") %\
	     ("<a href=\"mailto:"+Config.Email+"\">"+Config.Email+"</a>."))
	self.fd.write("</small></body></html>")
        self.fd.flush()
        self.fd = None


class ColoredLogger(StandardLogger):
    """ANSI colorized output"""

    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.colorparent = args['colorparent']
        self.colorurl = args['colorurl']
        self.colorreal = args['colorreal']
        self.colorbase = args['colorbase']
        self.colorvalid = args['colorvalid']
        self.colorinvalid = args['colorinvalid']
        self.colorinfo = args['colorinfo']
        self.colorwarning = args['colorwarning']
        self.colordltime = args['colordltime']
        self.colorreset = args['colorreset']
        self.currentPage = None
        self.prefix = 0

    def newUrl(self, urlData):
        if urlData.parentName:
            if self.currentPage != urlData.parentName:
                if self.prefix:
                    self.fd.write("o\n")
                self.fd.write("\n"+_("Parent URL")+Spaces["Parent URL"]+
		              self.colorparent+urlData.parentName+
			      self.colorreset+"\n")
                self.currentPage = urlData.parentName
                self.prefix = 1
        else:
            if self.prefix:
                self.fd.write("o\n")
            self.prefix = 0
            self.currentPage=None
            
        if self.prefix:
            self.fd.write("|\n+- ")
        else:
            self.fd.write("\n")
        self.fd.write(_("URL")+Spaces["URL"]+self.colorurl+urlData.urlName+
	              self.colorreset)
        if urlData.line: self.fd.write(_(", line ")+`urlData.line`+"")
        if urlData.cached:
            self.fd.write(_(" (cached)\n"))
        else:
            self.fd.write("\n")
            
        if urlData.baseRef:
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(_("Base")+Spaces["Base"]+self.colorbase+
	                  urlData.baseRef+self.colorreset+"\n")
            
        if urlData.url:
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(_("Real URL")+Spaces["Real URL"]+self.colorreal+
	                  urlData.url+self.colorreset+"\n")
        if urlData.downloadtime:
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(_("D/L Time")+Spaces["D/L Time"]+self.colordltime+
	        (_("%.3f seconds") % urlData.downloadtime)+self.colorreset+"\n")
        if urlData.checktime:
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(_("Check Time")+Spaces["Check Time"]+
                self.colordltime+
	        (_("%.3f seconds") % urlData.checktime)+self.colorreset+"\n")
            
        if urlData.infoString:
            if self.prefix:
                self.fd.write("|  "+_("Info")+Spaces["Info"]+
                      StringUtil.indentWith(StringUtil.blocktext(
                        urlData.infoString, 65), "|      "+Spaces["Info"]))
            else:
                self.fd.write(_("Info")+Spaces["Info"]+
                      StringUtil.indentWith(StringUtil.blocktext(
                        urlData.infoString, 65), "    "+Spaces["Info"]))
            self.fd.write(self.colorreset+"\n")
            
        if urlData.warningString:
            self.warnings = self.warnings+1
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(_("Warning")+Spaces["Warning"]+self.colorwarning+
	                  urlData.warningString+self.colorreset+"\n")

        if self.prefix:
            self.fd.write("|  ")
        self.fd.write(_("Result")+Spaces["Result"])
        if urlData.valid:
            self.fd.write(self.colorvalid+urlData.validString+
	                  self.colorreset+"\n")
        else:
            self.errors = self.errors+1
            self.fd.write(self.colorinvalid+urlData.errorString+
	                  self.colorreset+"\n")
        self.fd.flush()        


    def endOfOutput(self, linknumber=-1):
        if self.prefix:
            self.fd.write("o\n")
        StandardLogger.endOfOutput(self, linknumber=linknumber)


class GMLLogger(StandardLogger):
    """GML means Graph Modeling Language. Use a GML tool to see
    your sitemap graph.
    """
    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.nodes = {}
        self.nodeid = 0

    def init(self):
        self.starttime = time.time()
        self.fd.write("# "+(_("created by %s at %s\n") % (Config.AppName,
                      _strtime(self.starttime))))
	self.fd.write("# "+(_("Get the newest version at %s\n") % Config.Url))
        self.fd.write("# "+(_("Write comments and bugs to %s\n\n") % \
	                    Config.Email))
	self.fd.write("graph [\n  directed 1\n")
        self.fd.flush()


    def newUrl(self, urlData):
        """write one node and all possible edges"""
        node = urlData
        if node.url and not self.nodes.has_key(node.url):
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid = self.nodeid + 1
            self.fd.write("  node [\n")
	    self.fd.write("    id     %d\n" % node.id)
            self.fd.write('    label  "%s"\n' % node.url)
            if node.downloadtime:
                self.fd.write("    dltime %d\n" % node.downloadtime)
            if node.checktime:
                self.fd.write("    checktime %d\n" % node.checktime)
            self.fd.write("    extern %d\n" % (node.extern and 1 or 0))
	    self.fd.write("  ]\n")
        self.writeEdges()


    def writeEdges(self):
        """write all edges we can find in the graph in a brute-force
           manner. Better would be a mapping of parent urls.
	"""
        for node in self.nodes.values():
            if self.nodes.has_key(node.parentName):
                self.fd.write("  edge [\n")
		self.fd.write('    label  "%s"\n' % node.urlName)
	        self.fd.write("    source %d\n" % \
		              self.nodes[node.parentName].id)
                self.fd.write("    target %d\n" % node.id)
                self.fd.write("    valid  %d\n" % (node.valid and 1 or 0))
                self.fd.write("  ]\n")
        self.fd.flush()


    def endOfOutput(self, linknumber=-1):
        self.fd.write("]\n")
        self.stoptime = time.time()
        duration = self.stoptime - self.starttime
        name = _("seconds")
        self.fd.write("# "+_("Stopped checking at %s") % \
	              _strtime(self.stoptime))
        if duration > 60:
            duration = duration / 60
            name = _("minutes")
        if duration > 60:
            duration = duration / 60
            name = _("hours")
        self.fd.write("	(%.3f %s)\n" % (duration, name))
        self.fd.flush()
        self.fd = None


class XMLLogger(StandardLogger):
    """XML output mirroring the GML structure. Easy to parse with any XML
       tool."""
    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.nodes = {}
        self.nodeid = 0

    def init(self):
        self.starttime = time.time()
        self.fd.write('<?xml version="1.0"?>\n')
        self.fd.write("<!--\n")
        self.fd.write("  "+_("created by %s at %s\n") % \
	              (Config.AppName, _strtime(self.starttime)))
        self.fd.write("  "+_("Get the newest version at %s\n") % Config.Url)
        self.fd.write("  "+_("Write comments and bugs to %s\n\n") % \
	              Config.Email)
        self.fd.write("-->\n\n")
	self.fd.write('<GraphXML>\n<graph isDirected="true">\n')
        self.fd.flush()

    def newUrl(self, urlData):
        """write one node and all possible edges"""
        node = urlData
        if node.url and not self.nodes.has_key(node.url):
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid = self.nodeid + 1
            self.fd.write('  <node name="%d" ' % node.id)
            self.fd.write(">\n")
            self.fd.write("    <label>%s</label>\n" % quote(node.url))
            self.fd.write("    <data>\n")
            if node.downloadtime:
                self.fd.write("      <dltime>%f</dltime>\n" \
                                  % node.downloadtime)
            if node.checktime:
                self.fd.write("      <checktime>%f</checktime>\n" \
                              % node.checktime)
            self.fd.write("      <extern>%d</extern>\n" % \
	                  (node.extern and 1 or 0))
            self.fd.write("    </data>\n")
	    self.fd.write("  </node>\n")
        self.writeEdges()

    def writeEdges(self):
        """write all edges we can find in the graph in a brute-force
           manner. Better would be a mapping of parent urls.
	"""
        for node in self.nodes.values():
            if self.nodes.has_key(node.parentName):
                self.fd.write("  <edge")
                self.fd.write(' source="%d"' % \
		              self.nodes[node.parentName].id)
                self.fd.write(' target="%d"' % node.id)
                self.fd.write(">\n")
		self.fd.write("    <label>%s</label>\n" % quote(node.urlName))
                self.fd.write("    <data>\n")
                self.fd.write("      <valid>%d</valid>\n" % \
		              (node.valid and 1 or 0))
                self.fd.write("    </data>\n")
                self.fd.write("  </edge>\n")
        self.fd.flush()

    def endOfOutput(self, linknumber=-1):
        self.fd.write("</graph>\n</GraphXML>\n")
        self.stoptime = time.time()
        duration = self.stoptime - self.starttime
        name = _("seconds")
        self.fd.write("<!-- ")
        self.fd.write(_("Stopped checking at %s") % _strtime(self.stoptime))
        if duration > 60:
            duration = duration / 60
            name = _("minutes")
        if duration > 60:
            duration = duration / 60
            name = _("hours")
        self.fd.write("	(%.3f %s)\n" % (duration, name))
        self.fd.write("-->")
        self.fd.flush()
        self.fd = None



class SQLLogger(StandardLogger):
    """ SQL output for PostgreSQL, not tested"""
    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.dbname = args['dbname']
        self.separator = args['separator']

    def init(self):
        self.starttime = time.time()
        self.fd.write("-- "+(_("created by %s at %s\n") % (Config.AppName,
                      _strtime(self.starttime))))
        self.fd.write("-- "+(_("Get the newest version at %s\n") % Config.Url))
        self.fd.write("-- "+(_("Write comments and bugs to %s\n\n") % \
	                     Config.Email))
        self.fd.flush()

    def newUrl(self, urlData):
        self.fd.write("insert into %s(urlname,recursionlevel,parentname,"
              "baseref,errorstring,validstring,warningstring,infoString,"
	      "valid,url,line,checktime,downloadtime,cached) values "
              "(%s,%d,%s,%s,%s,%s,%s,%s,%d,%s,%d,%d,%d,%d)%s\n" % \
	      (self.dbname,
	       StringUtil.sqlify(urlData.urlName),
               urlData.recursionLevel,
	       StringUtil.sqlify(urlData.parentName),
               StringUtil.sqlify(urlData.baseRef),
               StringUtil.sqlify(urlData.errorString),
               StringUtil.sqlify(urlData.validString),
               StringUtil.sqlify(urlData.warningString),
               StringUtil.sqlify(urlData.infoString),
               urlData.valid,
               StringUtil.sqlify(urlData.url),
               urlData.line,
               urlData.checktime,
               urlData.downloadtime,
               urlData.cached,
	       self.separator))
        self.fd.flush()

    def endOfOutput(self, linknumber=-1):
        self.stoptime = time.time()
        duration = self.stoptime - self.starttime
        name = _("seconds")
        self.fd.write("-- "+_("Stopped checking at %s") % \
	              _strtime(self.stoptime))
        if duration > 60:
            duration = duration / 60
            name = _("minutes")
        if duration > 60:
            duration = duration / 60
            name = _("hours")
        self.fd.write("	(%.3f %s)\n" % (duration, name))
        self.fd.flush()
        self.fd = None


class BlacklistLogger:
    """Updates a blacklist of wrong links. If a link on the blacklist
    is working (again), it is removed from the list. So after n days
    we have only links on the list which failed for n days.
    """
    def __init__(self, **args):
        self.errors = 0
        self.blacklist = {}
        self.filename = args['filename']

    def init(self):
        pass

    def newUrl(self, urlData):
        if urlData.valid:
            self.blacklist[urlData.getCacheKey()] = None
        elif not urlData.cached:
            self.errors = 1
            self.blacklist[urlData.getCacheKey()] = urlData

    def endOfOutput(self, linknumber=-1):
        """write the blacklist"""
        fd = open(args['filename'], "w")
        for url in self.blacklist.keys():
            if self.blacklist[url] is None:
                fd.write(url+"\n")


class CSVLogger(StandardLogger):
    """ CSV output. CSV consists of one line per entry. Entries are
    separated by a semicolon.
    """
    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.separator = args['separator']

    def init(self):
        self.starttime = time.time()
        self.fd.write("# "+(_("created by %s at %s\n") % (Config.AppName,
                      _strtime(self.starttime))))
	self.fd.write("# "+(_("Get the newest version at %s\n") % Config.Url))
	self.fd.write("# "+(_("Write comments and bugs to %s\n\n") % \
	                    Config.Email))
        self.fd.write(_("# Format of the entries:\n")+\
                      "# urlname;\n"
                      "# recursionlevel;\n"
                      "# parentname;\n"
                      "# baseref;\n"
                      "# errorstring;\n"
                      "# validstring;\n"
                      "# warningstring;\n"
                      "# infostring;\n"
                      "# valid;\n"
                      "# url;\n"
                      "# line;\n"
                      "# downloadtime;\n"
                      "# checktime;\n"
                      "# cached;\n")
        self.fd.flush()

    def newUrl(self, urlData):
        self.fd.write(
	    "%s%s%d%s%s%s%s%s%s%s%s%s%s%s%s%s%d%s%s%s%d%s%d%s%d%s%d\n" % (
	    urlData.urlName, self.separator,
	    urlData.recursionLevel, self.separator,
	    urlData.parentName, self.separator,
            urlData.baseRef, self.separator,
            urlData.errorString, self.separator,
            urlData.validString, self.separator,
            urlData.warningString, self.separator,
            urlData.infoString, self.separator,
            urlData.valid, self.separator,
            urlData.url, self.separator,
            urlData.line, self.separator,
            urlData.downloadtime, self.separator,
            urlData.checktime, self.separator,
            urlData.cached))
        self.fd.flush()

    def endOfOutput(self, linknumber=-1):
        self.stoptime = time.time()
        duration = self.stoptime - self.starttime
        name = _("seconds")
        self.fd.write("# "+_("Stopped checking at %s") % _strtime(self.stoptime))
        if duration > 60:
            duration = duration / 60
            name = _("minutes")
        if duration > 60:
            duration = duration / 60
            name = _("hours")
        self.fd.write("	(%.3f %s)\n" % (duration, name))
        self.fd.flush()
        self.fd = None

